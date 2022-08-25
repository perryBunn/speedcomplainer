class DaemonApp():
    def __init__(self, pidFilePath, stdout_path='/dev/null', stderr_path='/dev/null'):
        self.stdin_path = '/dev/null'
        self.stdout_path = stdout_path
        self.stderr_path = stderr_path
        self.pidfile_path = pidFilePath
        self.pidfile_timeout = 1

    def run(self):
        main(__file__, sys.argv[1:])
