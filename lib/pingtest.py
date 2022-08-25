"""
"""

import threading


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
            self.doTraceRoute(pingResults)

    def doTraceRoute(self, pingResults):
        #csv_traceroute_headers = ["Date", "target", "Ping DateTime", "Packet Loss #", "capture"]
        print("Performing Traceroute, due to packet loss being detected...")
        Traceroutelogger = RotatingCsvFile(suffix=CONFIGURATION["TRACEROUTE"]["logfilename"],
                                                output_headers=csv_traceroute_headers,
                                                directory="data")
        Traceroutelogger.setup_append(writeheader=True)
        row_data = Traceroutelogger.clear_record()
        if CONFIGURATION["TRACEROUTE"]["logfilename"] != "":
            try:
                tracerouteoutput = subprocess.check_output(CONFIGURATION["TRACEROUTE"]["commandline"] +\
                                                          [str(CONFIGURATION["TRACEROUTE"]["timeout"])] +\
                                                          [CONFIGURATION["TRACEROUTE"]["traceroute_target"]],
                                                                    stderr=subprocess.PIPE)#STDOUT, shell=True)
            except subprocess.CalledProcessError:
                row_data["Date"] = datetime.now()
                row_data["capture"] = "Error running Traceroute.  Traceroute returned an error code."
                Traceroutelogger.writerow(row_data)
                return

            print("Traceroute Captured....")
            output = tracerouteoutput.decode('ascii').split("\n")
            row_data["Date"] = datetime.now()
            row_data["capture"] = "\n\r".join(output)
            row_data["target"] = CONFIGURATION["TRACEROUTE"]["traceroute_target"]
            row_data["Ping DateTime"] = pingResults["Date"]
            row_data["Packet Loss #"] = pingResults["Packet Loss #"]
            Traceroutelogger.writerow(row_data)
            print("Traceroute completed")
#             with open(os.path.join("Data", CONFIGURATION["TRACEROUTE"]["logfilename"]+'.txt'), 'a') as tracelog:
#                 tracelog.writelines(["%s" % datetime.now(), '\n',
#                                      '\tTraceRoute to %s' % CONFIGURATION["TRACEROUTE"]["traceroute_target"],
#                                      '\n'])
#                 for line in output:
#                     tracelog.write("\t\t"+line+'\n')
#                 tracelog.writelines(["-"*30, '\n'])

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
