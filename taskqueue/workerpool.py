"""Worker pool functionality."""

import sys
import logging
import pkg_resources

from time import sleep
from multiprocessing import Process
from taskqueue.daemonlib import Daemon

LOG = logging.getLogger(__name__)

class WorkerPool(Daemon):
    """Worker pool manager."""

    pidfile = "/var/run/workerpool.pid"

    def __init__(self, config):
        """Initialize application."""

        self.processes = []
        self.plugins = {}
        super(WorkerPool, self).__init__(config)

    def create_worker(self, worker_type, props):
        """Create one worker process."""
        target = self.plugins[worker_type]()
        proc = Process(target=target,
                       args=(props, self.amqp_params,
                             "worker_%s" % worker_type))
        proc.start()
        self.processes.append((worker_type, proc, props))

    def create_workers(self, worker_type, props):
        """Create worker processes."""
        for i in range(0, int(props['instances'])):
            LOG.debug("creating new %d worker of type %r" % (i, worker_type))
            self.create_worker(worker_type, props)

    def run(self):
        """Application entry point."""

        LOG.debug("WorkerPool.run()")

        # use settings from DEFAULT for unconfigured worker plugins
        if not self.config.has_section('workers'):
            self.config.add_section('workers')

        defaults = {
            'enabled_plugins': '*',
            'instances': '1'
        }
        defaults.update(self.config.items('workers'))

        group = "worker.plugins"
        for entrypoint in pkg_resources.iter_entry_points(group=group):
            wtype = entrypoint.name
            LOG.info("register plugin %r" % wtype)
            try:
                self.plugins[wtype] = entrypoint.load()
            except ImportError:
                LOG.info("worker of type %r not installed" % wtype)
                continue

            grp_sect = "%s_%s" % ('worker', wtype)
            grp_opts = dict(self.config.items(grp_sect, defaults=defaults))

            if 'subgroups' in grp_opts:
                subgrp_sects = ['%s_%s' % (grp_sect, subgrp.strip())
                                for subgrp in grp_opts['subgroups'].split(',')]
                for subgrp_sect in subgrp_sects:
                    subgrp_opts = self.config.items(subgrp_sect,
                                                    defaults=grp_opts)
                    self.create_workers(wtype, dict(subgrp_opts))
            else:
                self.create_workers(wtype, grp_opts)

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
        """Handler for termination signals."""

        LOG.debug("cleanup")
        for _, proc, _ in self.processes:
            LOG.debug("terminating %r" % proc.name)
            proc.terminate()
        sys.exit(0)

