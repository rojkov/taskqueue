import logging
import os

from taskqueue.worker import BaseWorker
from subprocess import Popen, PIPE, STDOUT, call
from derek import Client

LOG = logging.getLogger(__name__)

class Worker(BaseWorker):

    def handle_task(self, workitem):
        LOG.debug("Body: %r" % workitem)
        pname = workitem['fields']['pkgname']
        pver = workitem['fields']['pkgversion']
        workdir = workitem['fields']['workdir']
        call(["dpkg-source", "-x", "%s_%s.dsc" % (pname, pver)], cwd=workdir)
        pdir = os.path.join(workdir, "%s-%s" %
                            (pname, pver))
        process = Popen(["dpkg-buildpackage", "-rfakeroot"],
                        cwd=pdir,
                        stdout=PIPE, stderr=STDOUT)
        while True:
            line = process.stdout.readline()
            LOG.debug(line.strip('\n'))
            if line == '' and process.poll() is not None:
                break
        # publish the built package
        client = Client("vasya", "qwerty")
        branch = client.branch("%s/%s/%s" % (workitem['fields']['user'],
                                             workitem['fields']['repo'],
                                             workitem['fei']['wfid']))
        branch.upload_packages([os.path.join(workdir, "%s_%s_amd64.changes" %
                                                      (pname, pver))])

        return workitem
