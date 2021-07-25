import configdata
from configdata import CONFIGURATION
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
from logger import Logger
import subprocess
import re

shutdownFlag = False

def main(filename, argv):
    print "======================================"
    print " Starting Speed Complainer!           "
    print " Lets get noisy!                      "
    print "======================================"

    global shutdownFlag
    configdata.load_config_data(settings_file="settings.ini",
        sections=("PING", "SPEEDTEST", "TWITTER", "TRACEROUTE", "LOG"))
    print CONFIGURATION
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
            print 'Error: %s' % e
            import traceback
            traceback.print_exc()
            sys.exit(1)

    sys.exit()

def shutdownHandler(signo, stack_frame):
    global shutdownFlag
    print 'Got shutdown signal (%s: %s).' % (signo, stack_frame)
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
        if not os.path.exists(self.config['log']['files']['ping']):
            print "Ping Log File does not exist.. Creating Header"
            header_output = True
        self.pinglogger = Logger(self.config['log']['type'], { 'filename': CONFIGURATION["PING"]["logfilename"]})
#        if CONFIGURATION["TRACEROUTE"]["logfilename"] is not "":
        self.tracelogger = Logger(self.config['log']['type'], { 'filename': CONFIGURATION["TRACEROUTE"]["logfilename"]})
        if header_output:
            self.pinglogger.log( ['Date', 'Success', 'Sent', 'Received', 'Packet Loss %', 'Min', 'Avg', 'Max'])


    def run(self):
        pingResults = self.doPingTest()
        if pingResults is None:
            print "Ping test failed"
        self.logPingResults(pingResults)

    def doPingTest(self):
        if sys.platform == "darwin":
            try:
                pingoutput = subprocess.check_output('ping -c %s -W %s -t %s %s' % (self.numPings,
                                                                                    (self.pingTimeout * 1000),
                                                                                    self.maxWaitTime,
                                                                                    self.pingTarget),
                                                                                    shell=True)
                pingoutput = pingoutput.split('\n')[-3:]
                xmit_stats = pingoutput[0].split(",")
                timing_stats = pingoutput[1].split("=")[1].split("/")
                sent = int(xmit_stats[0].strip().split(" ")[0])
                received = int(xmit_stats[1].strip().split(" ")[0])
                packet_loss = float(xmit_stats[2].split("%")[0])

                ping_min = float(timing_stats[0])
                ping_avg = float(timing_stats[1])
                ping_max = float(timing_stats[2])
                response = packet_loss
    #            response = os.system("ping -c %s -W %s -t %s 8.8.8.8 > /dev/null 2>&1" % (self.numPings, (self.pingTimeout * 1000), self.maxWaitTime))
    #        else:
    #            response = os.system("ping -c %s -W %s -w %s 8.8.8.8 > /dev/null 2>&1" % (self.numPings, (self.pingTimeout * 1000), self.maxWaitTime))
                success = 0
                if response == 0:
                    success = 1
                if int(packet_loss) > 0  and CONFIGURATION["TRACEROUTE"]["traceroute_target"] is not "":
                    print "Packet Loss Detected, running traceroute...",
#                     tracerouteoutput = subprocess.check_output('traceroute -w %s %s' % (self.maxWaitTime,
#                                                                                         CONFIGURATION["TRACEROUTE"]["traceroute_target"]),
#                                                                                         stderr=subprocess.PIPE, shell=True)#STDOUT, shell=True)
                    print '%s %s' % (CONFIGURATION["TRACEROUTE"]["commandline"],
                                                                        CONFIGURATION["TRACEROUTE"]["traceroute_target"])
                    tracerouteoutput = subprocess.check_output('%s %s' % (CONFIGURATION["TRACEROUTE"]["commandline"],
                                                                        CONFIGURATION["TRACEROUTE"]["traceroute_target"]),
                                                                        stderr=subprocess.PIPE, shell=True)#STDOUT, shell=True)
                    print "Traceroute Captured...."
                    self.tracelogger.log(["-"*30])
                    self.tracelogger.log(["%s" % datetime.now()])
                    self.tracelogger.log(["%s" % tracerouteoutput])
                    self.tracelogger.log(["-"*30])

            except subprocess.CalledProcessError:
                print "Error running ping command @ %s " % datetime.now()
                return { 'date': datetime.now(), 'success': 0, 'packet_loss' : '-',
                         'min' : "-", 'max' : "-", 'avg' : "-", 'sent':"-", 'received':"-"} #, "trace":tracerouteoutput}

        return { 'date': datetime.now(), 'success': success, 'packet_loss' : packet_loss,
                 'min' : ping_min, 'max' : ping_max, 'avg' : ping_avg, 'sent':sent, 'received':received}#,
#                 "trace":tracerouteoutput}

    def logPingResults(self, pingResults):
        self.pinglogger.log([ pingResults['date'].strftime('%Y-%m-%d %H:%M:%S'),
                          str(pingResults['success']),
                          str(pingResults['sent']),
                          str(pingResults['received']),
                          str(pingResults['packet_loss']),
                          str(pingResults['min']),
                          str(pingResults['avg']),
                          str(pingResults['max'])])#,


class SpeedTest(threading.Thread):
    def __init__(self):
        super(SpeedTest, self).__init__()
        header_output = False
        self.config = json.load(open('./config.json'))
        if not os.path.exists(self.config['log']['files']['speed']):
            print "Speed Test Log File does not exist, creating header."
            header_output = True
        self.logger = Logger(self.config['log']['type'], {'filename': CONFIGURATION["SPEEDTEST"]["logfilename"]})
        if header_output:
            self.logger.log([ 'Date', 'Upload Speed', 'Download Speed', 'Ping Speed' ])

    def run(self):
        speedTestResults = self.doSpeedTest()
        self.logSpeedTestResults(speedTestResults)
        self.tweetResults(speedTestResults)

    def doSpeedTest(self):
        # run a speed test
        try:
            result = os.popen("/usr/local/bin/speedtest-cli --simple").read()
        except socket.timeout:
            pass
        if 'Cannot' in result or result == None:
            return { 'date': datetime.now(), 'uploadResult': '-', 'downloadResult': '-', 'ping': '-' }

        # Result:
        # Ping: 529.084 ms
        # Download: 0.52 Mbit/s
        # Upload: 1.79 Mbit/s

        resultSet = result.split('\n')
        pingResult = resultSet[0]
        downloadResult = resultSet[1]
        uploadResult = resultSet[2]

        pingResult = float(pingResult.replace('Ping: ', '').replace(' ms', ''))
        downloadResult = float(downloadResult.replace('Download: ', '').replace(' Mbit/s', ''))
        uploadResult = float(uploadResult.replace('Upload: ', '').replace(' Mbit/s', ''))

        return { 'date': datetime.now(), 'uploadResult': uploadResult, 'downloadResult': downloadResult, 'ping': pingResult }

    def logSpeedTestResults(self, speedTestResults):
        self.logger.log([ speedTestResults['date'].strftime('%Y-%m-%d %H:%M:%S'), str(speedTestResults['uploadResult']), str(speedTestResults['downloadResult']), str(speedTestResults['ping']) ])


    def tweetResults(self, speedTestResults):
        thresholdMessages = self.config['tweetThresholds']
        message = None
        for (threshold, messages) in thresholdMessages.items():
            threshold = float(threshold)
            if speedTestResults['downloadResult'] < threshold:
                message = messages[random.randint(0, len(messages) - 1)].replace('{tweetTo}', self.config['tweetTo']).replace('{internetSpeed}', self.config['internetSpeed']).replace('{downloadResult}', str(speedTestResults['downloadResult']))

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



