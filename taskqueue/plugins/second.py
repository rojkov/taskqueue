import logging

from taskqueue.worker import BaseWorker

LOG = logging.getLogger(__name__)

class Worker(BaseWorker):

    def handle_task(self, body):
        LOG.debug("Body: %r" % body)
        return "done"

