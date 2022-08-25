"""
"""

from datetime import datetime

from .pingtest import PingTest
from .speedtest import SpeedTest


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
