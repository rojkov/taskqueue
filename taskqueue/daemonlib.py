import logging
import socket
import daemon
import signal
import sys

from logging.handlers import SysLogHandler
from ConfigParser import SafeConfigParser as ConfigParser

LOG = logging.getLogger(__name__)

class Daemon(object):

    def __init__(self, config):
        self.config = config

    def cleanup(self, signum, frame):
        """Abstract cleanup."""
        raise NotImplemented

    @classmethod
    def main(cls):
        """Dispatcher entry point."""

        # configure logging
        rootlogger = logging.getLogger()
        rootlogger.setLevel(logging.DEBUG)
        sh = SysLogHandler(address='/dev/log',
                           facility=SysLogHandler.LOG_DAEMON,
                           socktype=socket.SOCK_STREAM)
        sh.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(name)s:%(levelname)s:%(message)s')
        sh.setFormatter(formatter)
        rootlogger.addHandler(sh)
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
        ch.setFormatter(formatter)
        rootlogger.addHandler(ch)

        config = ConfigParser()
        config.read('config.ini')

        daemon_obj = cls(config)

        context = daemon.DaemonContext()
        context.detach_process = False # for development purposes
        context.stdout = sys.stdout
        context.stderr = sys.stdout

        context.signal_map = {
            signal.SIGTERM: daemon_obj.cleanup,
            signal.SIGHUP: daemon_obj.cleanup
        }

        with context:
            daemon_obj.run()
