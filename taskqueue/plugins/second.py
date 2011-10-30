import logging

from taskqueue.worker import BaseWorker

LOG = logging.getLogger(__name__)

class Worker(BaseWorker):

    def handle_task(self, channel, method, header, body):
        LOG.debug("Method: %r" % method)
        LOG.debug("Header: %r" % header)
        LOG.debug("Body: %r" % body)
        channel.basic_ack(method.delivery_tag)

