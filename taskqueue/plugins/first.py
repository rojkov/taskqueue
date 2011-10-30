import logging

LOG = logging.getLogger(__name__)

class FirstHandler(object):

    def __init__(self):

        # TODO: get it from config file
        self.prefetch_count = 6

    def handle_task(self, channel, method, header, body):
        LOG.debug("Method: %r" % method)
        LOG.debug("Header: %r" % header)
        LOG.debug("Body: %r" % body)
        channel.basic_ack(method.delivery_tag)

def make_plugin():
    first = FirstHandler()
    return first
