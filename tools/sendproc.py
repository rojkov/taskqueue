#!/usr/bin/python

import json
import pika

process = """
Ruote.process_definition do
    sequence :on_error => 'error_handler' do
        debug :msg => 'start'
        python :name => 'branch_repo'
        hardworker :worker_type => 'simpledownloader'
        hardworker :worker_type => 'simplebuilder'
        python :name => 'accept_request'
        debug :msg => 'success'
    end
    define 'error_handler' do
        debug :msg => 'error'
    end
end
"""

pdef = {
    "definition": process,
    "fields":
        {
            "user":    "vasya",
            "repo":    "testrepo1",
            "branch":  "master2",
            "pkgname": "python-riak",
            "pkgversion": "1.2.1",
            "workdir": "/home/rozhkov/tmp"
        }
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
