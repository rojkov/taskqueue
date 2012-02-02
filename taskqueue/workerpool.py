import sys
import logging
import pika
import pkg_resources

from time import sleep
from multiprocessing import Process
from taskqueue.daemonlib import Daemon

from ConfigParser import NoSectionError

LOG = logging.getLogger(__name__)

class Application(Daemon):

    pidfile = "/var/run/workerpool.pid"

    def __init__(self, config):
        """Initialize application."""

        self.processes = []
        self.plugins = {}
        # TODO: set config in base class
        self.config = config
        try:
            amqp_host   = config.get("amqp", "host")
            amqp_user   = config.get("amqp", "user")
            amqp_passwd = config.get("amqp", "passwd")
            amqp_vhost  = config.get("amqp", "vhost")
            credentials = pika.PlainCredentials(amqp_user, amqp_passwd)
            self.amqp_params = pika.ConnectionParameters(
                credentials=credentials,
                host=amqp_host,
                virtual_host=amqp_vhost)
        except NoSectionError:
            self.amqp_params = pika.ConnectionParameters(host="localhost")

    def create_worker(self, worker_type, props):
        LOG.debug("creating new worker of type %r" % worker_type)
        target = self.plugins[worker_type]()
        proc = Process(target=target,
                       args=(props, self.amqp_params,
                             "worker_%s" % worker_type))
        proc.start()
        self.processes.append((worker_type, proc, props))

    def run(self):
        """Application entry point."""

        LOG.debug("run!")

        group = "worker.plugins"
        for entrypoint in pkg_resources.iter_entry_points(group=group):
            worker_type = entrypoint.name
            LOG.info("register plugin %r" % worker_type)
            try:
                plugin = entrypoint.load()
            except ImportError:
                LOG.info("worker of type %r not installed" % worker_type)
                continue

            self.plugins[worker_type] = plugin
            workers_attr = self.config.get(worker_type, 'workers')
            try:
                int(workers_attr)
                sections = [worker_type]
            except ValueError:
                sections = ["%s_%s" % (worker_type, sect.strip()) for sect in
                            self.config.get(worker_type, 'workers').split(",")]
            for section in sections:
                max_workers = self.config.getint(section, 'workers')
                for i in range(0, max_workers):
                    self.create_worker(worker_type,
                                       self.config.items(section))

        self.monitor()

    def monitor(self):
        """Monitor created worker processes."""

        while True:
            sleep(2)
            for process in self.processes:
                worker_type, proc, props = process
                if not proc.is_alive():
                    LOG.error("process %r of type %r crashed unexpectedly" %
                              (proc, worker_type))
                    proc.join()
                    self.processes.remove(process)
                    self.create_worker(worker_type, props)

    def cleanup(self, signum, frame):
        """Handler for terminationsignals."""

        LOG.debug("cleanup")
        for _, proc, _ in self.processes:
            LOG.debug("terminating %r" % proc.name)
            proc.terminate()
        sys.exit(0)

