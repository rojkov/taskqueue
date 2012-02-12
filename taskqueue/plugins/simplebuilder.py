import logging
import os

from taskqueue.worker import BaseWorker
from subprocess import Popen, PIPE, STDOUT, call

LOG = logging.getLogger(__name__)

class Worker(BaseWorker):

    def handle_task(self, workitem):
        LOG.debug("Body: %r" % workitem)
        pname = workitem['fields']['pkgname']
        pver = workitem['fields']['pkgversion']
        call(["dpkg-source", "-x", "%s_%s.dsc" % (pname, pver)],
             cwd=workitem['fields']['workdir'])
        pdir = os.path.join(workitem['fields']['workdir'], "%s-%s" %
                            (pname, pver))
        process = Popen(["dpkg-buildpackage", "-rfakeroot"],
                        cwd=pdir,
                        stdout=PIPE, stderr=STDOUT)
        while True:
            line = process.stdout.readline()
            LOG.debug(line.strip('\n'))
            if line == '' and process.poll() is not None:
                break
        return workitem
