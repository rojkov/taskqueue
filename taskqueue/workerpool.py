"""Worker pool functionality."""

import sys
import logging
import pkg_resources

from time import sleep
from multiprocessing import Process
from taskqueue.daemonlib import Daemon

LOG = logging.getLogger(__name__)

# TODO: move the constants to confparser
SECTION_WORKERS = 'workers'

PREFIX_GROUP = 'worker'

OPT_SUBGROUPS = 'subgroups'
OPT_INSTANCES = 'instances'
OPT_PLUGINS   = 'enabled_plugins'

class WorkerPool(Daemon):
    """Worker pool manager."""

    pidfile = "/var/run/workerpool.pid"

    def __init__(self, config):
        """Initialize application."""

        self.processes = []
        self.plugins = {}
        self._enabled_plugins = '*'
        super(WorkerPool, self).__init__(config)

    def is_plugin_enabled(self, name):
        """Return True if given plugin is enabled in config."""

        if self._enabled_plugins == "*":
            return True
        return name in self._enabled_plugins

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
        for i in range(0, int(props[OPT_INSTANCES])):
            LOG.debug("creating new %d worker of type %r" % (i, worker_type))
            self.create_worker(worker_type, props)

    def run(self):
        """Application entry point."""

        LOG.debug("WorkerPool.run()")

        # use settings from DEFAULT for unconfigured worker plugins
        if not self.config.has_section(SECTION_WORKERS):
            self.config.add_section(SECTION_WORKERS)

        defaults = {
            OPT_PLUGINS:   '*',
            OPT_INSTANCES: '1'
        }
        defaults.update(self.config.items(SECTION_WORKERS))

        if defaults[OPT_PLUGINS] != '*':
            self._enabled_plugins = \
                    [plgn.strip() for plgn in defaults[OPT_PLUGINS].split(",")]

        group = "worker.plugins"
        for entrypoint in pkg_resources.iter_entry_points(group=group):
            wtype = entrypoint.name

            if not self.is_plugin_enabled(wtype):
                LOG.info("the plugin '%s' is not enabled in the config" % wtype)
                continue

            LOG.info("register plugin %r" % wtype)
            try:
                self.plugins[wtype] = entrypoint.load()
            except ImportError:
                LOG.info("worker of type %r not installed" % wtype)
                continue

            grp_sect = "%s_%s" % (PREFIX_GROUP, wtype)
            grp_opts = dict(self.config.items(grp_sect, defaults=defaults))

            if OPT_SUBGROUPS in grp_opts:
                subgrp_sects = ['%s_%s' % (grp_sect, sgrp.strip())
                                for sgrp in grp_opts[OPT_SUBGROUPS].split(',')]
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

