import logging

from taskqueue.worker import BaseWorker
from subprocess import Popen, PIPE, STDOUT

LOG = logging.getLogger(__name__)

class Worker(BaseWorker):

    def handle_task(self, workitem):
        LOG.debug("Body: %r" % workitem)
        process = Popen(["dpkg-buildpackage", "-rfakeroot"],
                        cwd=workitem["fields"]["pkg_path"],
                        stdout=PIPE, stderr=STDOUT)
        while True:
            line = process.stdout.readline()
            LOG.debug(line.strip('\n'))
            if line == '' and process.poll() is not None:
                break
        return workitem
