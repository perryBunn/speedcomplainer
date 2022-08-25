import threading


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
            tester = SpeedTest()
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
            test_results = {'Date':datetime.now(),
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
                                    self.config['tweetTo']).replace('{internetSpeed}', self.config['internetSpeed']).replace('{downloadResult}', str(speedTestResults['Download Speed']))

        if message:
            api = twitter.Api(consumer_key=self.config['twitter']['twitterConsumerKey'],
                            consumer_secret=self.config['twitter']['twitterConsumerSecret'],
                            access_token_key=self.config['twitter']['twitterToken'],
                            access_token_secret=self.config['twitter']['twitterTokenSecret'])
            if api:
                status = api.PostUpdate(message)
