import configdata
from configdata import configdata as CONFIGURATION
#from csv_common import BaseCsvFile
from rotating_csv import RotatingCsvFile
import os
import sys
import time
from datetime import datetime
import daemon
import signal
import threading
import twitter      # python-twitter, not twitter
import json
import random
#from logger import Logger
import subprocess
#import re
import speedtest
import pingparsing
import humanize

csv_ping_headers =  ['Date', 'target', 'Success', 'Sent', 'Received', 'Packet Loss #', 'Min', 'Avg', 'Max']
csv_speed_headers = ['Date', 'target', 'Location', 'Upload Speed', 'Up readable', 'Download Speed',
                     'Down readable', 'Ping', 'Latency']


shutdownFlag = False

def main(filename, argv):
    print("======================================")
    print(" Starting Speed Complainer!           ")
    print(" Lets get noisy!                      ")
    print("======================================")

    global shutdownFlag
    configdata.load_data(filename="settings.ini",
        ini_group=("PING", "SPEEDTEST", "TWITTER", "TRACEROUTE", "LOG"))
    print(CONFIGURATION)
    signal.signal(signal.SIGINT, shutdownHandler)

    monitor = Monitor()

    while not shutdownFlag:
        try:

            monitor.run()

            for i in range(0, 5):
                if shutdownFlag:
                    break
                time.sleep(1)

        except Exception as e:
            print('Error: %s' % e)
            import traceback
            traceback.print_exc()
            sys.exit(1)

    sys.exit()

def shutdownHandler(signo, stack_frame):
    global shutdownFlag
    print('Got shutdown signal (%s: %s).' % (signo, stack_frame))
    shutdownFlag = True

class Monitor():
    def __init__(self):
        self.lastPingCheck = None
        self.lastSpeedTest = None

    def run(self):
        if not self.lastPingCheck or (datetime.now() - self.lastPingCheck).total_seconds() >= CONFIGURATION["PING"]["runevery"]:
            self.runPingTest()
            self.lastPingCheck = datetime.now()

        if not self.lastSpeedTest or (datetime.now() - self.lastSpeedTest).total_seconds() >= CONFIGURATION["SPEEDTEST"]["runevery"]:
            self.runSpeedTest()
            self.lastSpeedTest = datetime.now()

    def runPingTest(self):
        pingThread = PingTest(numPings=CONFIGURATION["PING"]["numpings"],
                              pingTimeout=CONFIGURATION["PING"]["pingtimeout"],
                              maxWaitTime=CONFIGURATION["PING"]["maxwaittime"],
                              target=CONFIGURATION["PING"]["pingtarget"])
        pingThread.start()

    def runSpeedTest(self):
        speedThread = SpeedTest()
        speedThread.start()

class PingTest(threading.Thread):
    def __init__(self, numPings=5, pingTimeout=4, maxWaitTime=8, target="8.8.8.8"):
        super(PingTest, self).__init__()
        self.numPings = numPings
        self.pingTimeout = pingTimeout
        self.maxWaitTime = maxWaitTime
        self.pingTarget = target
        header_output = False

        self.config = json.load(open('./config.json'))
        self.pinglogger = RotatingCsvFile(suffix=CONFIGURATION["PING"]["logfilename"],
                                          output_headers=csv_ping_headers,
                                          directory="data")
        self.pinglogger.setup_append(writeheader=True)

    def run(self):
        pingResults = self.doPingTest()
        if pingResults is None:
            print("Ping test failed")
        self.logPingResults(pingResults)
        if pingResults["Packet Loss #"] > 0  and CONFIGURATION["TRACEROUTE"]["traceroute_target"] != "":
#            print("Packet Loss Detected, running traceroute...", end=' ')
            self.doTraceRoute()

    def doTraceRoute(self):
       if CONFIGURATION["TRACEROUTE"]["logfilename"] != "":
            tracerouteoutput = subprocess.check_output(CONFIGURATION["TRACEROUTE"]["commandline"] +\
                                                      [str(CONFIGURATION["TRACEROUTE"]["timeout"])] +\
                                                      [CONFIGURATION["TRACEROUTE"]["traceroute_target"]],
                                                                stderr=subprocess.PIPE)#STDOUT, shell=True)
            print("Traceroute Captured....")
            with open(CONFIGURATION["TRACEROUTE"]["logfilename"]+'.txt', 'a') as tracelog:
#                tracelog.writelines(["-"*30, '\n'])
                tracelog.writelines(["%s" % datetime.now(), '\n',
                                     '\tTraceRoute to %s' % CONFIGURATION["TRACEROUTE"]["traceroute_target"],
                                     '\n'])
                output = tracerouteoutput.decode('ascii').split("\n")
                for line in output:
#                    print(line)
                    tracelog.write("\t\t"+line+'\n')
                tracelog.writelines(["-"*30, '\n'])

    def doPingTest(self):
        ping_parser = pingparsing.PingParsing()
        transmitter = pingparsing.PingTransmitter()
        transmitter.destination = self.pingTarget
        transmitter.count = self.numPings
        text_output = transmitter.ping()
        results = ping_parser.parse(text_output).as_dict()
#csv_ping_headers =  ['Date', 'target', 'Success', 'Sent', 'Received', 'Packet Loss %', 'Min', 'Avg', 'Max']
        return { 'Date': datetime.now(),
                 'target':self.pingTarget,
                 'Success': results["packet_receive"],
                 'Packet Loss #' : results["packet_loss_count"],
                 'Min' : results["rtt_min"],
                 'Max' : results["rtt_max"],
                 'Avg' : results["rtt_avg"],
                 'Sent': results["packet_transmit"],
                 'Received':results["packet_receive"]}#,

    def logPingResults(self, pingResults):
        self.pinglogger.writerow(pingResults)


class SpeedTest(threading.Thread):
    """
    >>> results
{'download': 53248457.88897891, 'upload': 3830040.891172554, 'ping': 42.373,
'server': {'url': 'http://st.buf.as201971.net:8080/speedtest/upload.php', 'lat': '42.8864',
           'lon': '-78.8786', 'name': 'Buffalo, NY', 'country': 'United States', 'cc': 'US',
           'sponsor': 'CreeperHost LTD', 'id': '31483', 'host': 'st.buf.as201971.net:8080',
           'd': 109.47235274008302, 'latency': 42.373}, 'timestamp': '2021-07-23T01:50:53.316870Z',
           'bytes_sent': 5242880, 'bytes_received': 66706596,
           'share': 'http://www.speedtest.net/result/11769129726.png',
           'client': {'ip': '98.10.204.21', 'lat': '43.114', 'lon': '-77.5689',
           'isp': 'Spectrum', 'isprating': '3.7', 'rating': '0', 'ispdlavg': '0',
           'ispulavg': '0', 'loggedin': '0', 'country': 'US'}}
    """
    def __init__(self):
        super(SpeedTest, self).__init__()
        header_output = False
        self.config = json.load(open('./config.json'))
#         if not os.path.exists(self.config['log']['files']['speed']):
#             print("Speed Test Log File does not exist, creating header.")
#             header_output = True
        self.speedlogger = RotatingCsvFile(suffix=CONFIGURATION["SPEEDTEST"]["logfilename"],
                                          output_headers=csv_speed_headers,
                                          directory="data")
        self.speedlogger.setup_append(writeheader=True)
#        self.speedlogger = BaseCsvFile(CONFIGURATION["SPEEDTEST"]["logfilename"],
#                                      output_headers=csv_speed_headers)
#        self.speedlogger.setup_append(writeheader=True)

    def run(self):
        speedTestResults = self.doSpeedTest()
        self.logSpeedTestResults(speedTestResults)
        self.tweetResults(speedTestResults)

    def doSpeedTest(self):
        try:
            tester = speedtest.Speedtest()
            servers = tester.get_closest_servers()
            if CONFIGURATION["SPEEDTEST"]["exclude_hosts"] not in ["", None]:
                new_servers = []
                for server in servers:
                    if str(server["id"]) not in CONFIGURATION["SPEEDTEST"]["exclude_hosts"]:
                        new_servers.append(server)
                    else:
                        print("Skipping Host ID ", server["id"])
            else:
                new_servers=servers
            #tester.get_best_server(exclude=[])
            tester.get_best_server(servers=new_servers)
            tester.download()
            tester.upload()
            results = tester.results.dict()
#            csv_speed_headers = ['Date', 'target', 'Location', 'Upload Speed', 'Up readable', 'Download Speed',
#                     'Down readable', 'Ping', 'Latency']

            test_results = {'Date':datetime.now(),
                            'target':results["server"]["host"],
                            'Location':results["server"]["name"],
                            'Ping':results["ping"],
                            'Upload Speed':results["upload"],
                            'Up readable':humanize.naturalsize(results["upload"]),
                            'Download Speed':results["download"],
                            'Down readable':humanize.naturalsize(results["download"]),
                            'Latency':results["server"]["latency"]}
        except speedtest.SpeedtestBestServerFailure:
            results = {'Date':datetime.now(),
                       'target':"Error (Best Server)",
                       'Ping':255,
                       'Upload Speed':-1,
                       'Download Speed':-1,
                       'Latency':255}
        return test_results

    def logSpeedTestResults(self, speedTestResults):
        self.speedlogger.writerow(speedTestResults)


    def tweetResults(self, speedTestResults):
        thresholdMessages = self.config['tweetThresholds']
        message = None
        for (threshold, messages) in list(thresholdMessages.items()):
            threshold = float(threshold)
            if speedTestResults['Download Speed'] < threshold:
                message = messages[random.randint(0,len(messages) - 1)].replace('{tweetTo}',
                                    self.config['tweetTo']).replace('{internetSpeed}', self.config['internetSpeed']).replace('{downloadResult}', str(speedTestResults['downloadResult']))

        if message:
            api = twitter.Api(consumer_key=self.config['twitter']['twitterConsumerKey'],
                            consumer_secret=self.config['twitter']['twitterConsumerSecret'],
                            access_token_key=self.config['twitter']['twitterToken'],
                            access_token_secret=self.config['twitter']['twitterTokenSecret'])
            if api:
                status = api.PostUpdate(message)

class DaemonApp():
    def __init__(self, pidFilePath, stdout_path='/dev/null', stderr_path='/dev/null'):
        self.stdin_path = '/dev/null'
        self.stdout_path = stdout_path
        self.stderr_path = stderr_path
        self.pidfile_path = pidFilePath
        self.pidfile_timeout = 1

    def run(self):
        main(__file__, sys.argv[1:])

if __name__ == '__main__':
    main(__file__, sys.argv[1:])

    workingDirectory = os.path.basename(os.path.realpath(__file__))
    stdout_path = '/dev/null'
    stderr_path = '/dev/null'
    fileName, fileExt = os.path.split(os.path.realpath(__file__))
    pidFilePath = os.path.join(workingDirectory, os.path.basename(fileName) + '.pid')
    from daemon import runner
    dRunner = runner.DaemonRunner(DaemonApp(pidFilePath, stdout_path, stderr_path))
    dRunner.daemon_context.working_directory = workingDirectory
    dRunner.daemon_context.umask = 0o002
    dRunner.daemon_context.signal_map = { signal.SIGTERM: 'terminate', signal.SIGUP: 'terminate' }
    dRunner.do_action()



