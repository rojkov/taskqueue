#!/usr/bin/env python
import pika
import sys

from optparse import OptionParser

from taskqueue.confparser import ConfigParser, NoSectionError


def parse_cmdline(defaults):
    """Parse commandline options."""

    parser = OptionParser()
    parser.add_option("-c", "--config", dest="config",
                      default="/etc/taskqueue/config.ini",
                      help="path to config file")
    parser.add_option("-t", "--content-type", dest="ctype",
                      default="text/plain",
                      help="content type of AMQP message.")

    return parser.parse_args()

options, args = parse_cmdline({})

config = ConfigParser()
config.read(options.config)

amqp_items  = dict(config.items("amqp"))
amqp_host   = amqp_items.get("host", "localhost")
amqp_user   = amqp_items.get("user", "guest")
amqp_passwd = amqp_items.get("passwd", "guest")
amqp_vhost  = amqp_items.get("vhost", "/")
credentials = pika.PlainCredentials(amqp_user, amqp_passwd)

connection = pika.BlockingConnection(pika.ConnectionParameters(
    credentials=credentials,
    host=amqp_host,
    virtual_host=amqp_vhost))
channel = connection.channel()

channel.queue_declare(queue='taskqueue', durable=True)

message = ' '.join(args) or "Hello World!"
channel.basic_publish(exchange='',
                      routing_key='taskqueue',
                      body=message,
                      properties=pika.BasicProperties(
                         delivery_mode=2, # make message persistent
                         content_type=options.ctype
                      ))
print " [x] Sent %r" % (message,)
connection.close()
