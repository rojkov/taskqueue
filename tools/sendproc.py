#!/usr/bin/python

import json
import pika

process = """
Ruote.process_definition do
    fake1 :fkey1 => 'aaa'
    hardworker :worker_type => 'first'
    fake1 :fkey1 => 'bbb'
end
"""

pdef = {
    "definition": process,
    "fields": {"f1_key": "f1_value"}
}

msg = json.dumps(pdef)

credentials = pika.PlainCredentials('wfworker', 'wfworker')
parameters = pika.ConnectionParameters(credentials=credentials,
                                       host="localhost",
                                       virtual_host="/wfworker")

connection = pika.BlockingConnection(parameters)
channel = connection.channel()
channel.basic_publish(exchange='',
                      routing_key='ruote_workitems',
                      body=msg,
                      properties=pika.BasicProperties(
                          delivery_mode=2
                      ))
connection.close()
