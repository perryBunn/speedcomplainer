"""
"""

from argparse import ArgumentParser
from datetime import datetime
#from logger import Logger

import json
import os
import random
#import re
import signal
import subprocess
import sys
import time
import threading
import traceback
import pingparsing
import speedtest
import twitter      # python-twitter, not twitter

import humanize
import daemon
import configdata

from configdata import configdata as CONFIGURATION
#from csv_common import BaseCsvFile
from rotating_csv import RotatingCsvFile
from lib.logger import get_logger
from lib.monitor import Monitor

csv_ping_headers =  ['Date', 'target', 'Success', 'Sent', 'Received', 'Packet Loss #', 'Min', 'Avg', 'Max']
csv_speed_headers = ['Date', 'target', 'Location', 'Upload Speed', 'Up readable', 'Download Speed',
                     'Down readable', 'Ping', 'Latency']
csv_traceroute_headers = ["Date", "target", "Ping DateTime", "Packet Loss #", "capture"]

SHUTDOWN_FLAG = False


def main(filename, argv):
    print("======================================")
    print(" Starting Speed Complainer!           ")
    print(" Lets get noisy!                      ")
    print("======================================")

    configdata.load_data(filename="settings.ini",
        ini_group=("PING", "SPEEDTEST", "TWITTER", "TRACEROUTE", "LOG"))
    print(CONFIGURATION)
    signal.signal(signal.SIGINT, shutdownHandler)

    monitor = Monitor()

    while not SHUTDOWN_FLAG:
        try:
            monitor.run()
            for _ in range(0, 5):
                if SHUTDOWN_FLAG:
                    break
                time.sleep(1)

        except Exception as err:
            print(f'Error: {err}')
            traceback.print_exc()
            sys.exit(1)

    sys.exit()


def shutdownHandler(signo, stack_frame):
    global shutdownFlag
    print('Got shutdown signal (%s: %s).' % (signo, stack_frame))
    shutdownFlag = True


if __name__ == '__main__':
    parser = ArgumentParser("Speed Complainer")
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



