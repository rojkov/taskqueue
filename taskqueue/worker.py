import logging
import pika
import signal

LOG = logging.getLogger(__name__)

class BaseWorker(object):

    @classmethod
    def factory(cls):
        """Produce new worker callable."""
        return cls()

    def __init__(self):
        self.channel = None
        self.connection = None

    def __call__(self, props, conn_params, queue):
        self.connection = pika.BlockingConnection(conn_params)
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue=queue, durable=True,
                                   exclusive=False, auto_delete=False)
        self.channel.basic_qos(prefetch_count=1)
        self.channel.basic_consume(self.handle_delivery, queue=queue)
        signal.signal(signal.SIGTERM, self.cleanup)
        LOG.debug("created new process with props %r" % props)
        self.channel.start_consuming()

    def handle_task(self, channel, method, header, body):
        """Handle task."""
        raise NotImplementedError

    def handle_delivery(self, channel, method, header, body):
        LOG.debug("Method: %r" % method)
        LOG.debug("Header: %r" % header)
        result = self.handle_task(body)
        channel.basic_publish(exchange='',
                              routing_key='results',
                              body=result,
                              properties=pika.BasicProperties(
                                  delivery_mode=2
                              ))
        channel.basic_ack(method.delivery_tag)

    def cleanup(self, signum, frame):
        """Cleanup worker process."""

        LOG.debug("target cleanup")
        self.channel.stop_consuming()
        self.connection.close()
