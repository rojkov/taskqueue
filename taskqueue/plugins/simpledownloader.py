import logging
import json
import os

from derek import Client

from taskqueue.worker import BaseWorker

LOG = logging.getLogger(__name__)

class Worker(BaseWorker):

    ACCEPT = ['application/x-ruote-workitem']

    def handle_task(self, workitem):
        LOG.debug("Body: %r" % workitem)

        client = Client("vasya", "qwerty")
        branch = client.branch("%s/%s/%s" % (workitem.fields['user'],
                                             workitem.fields['repo'],
                                             workitem.fei['wfid']))
        branch.download_package(workitem.fields['pkgname'],
                                workitem.fields['pkgversion'],
                                workitem.fields['workdir'])

        return workitem
