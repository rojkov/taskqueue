#!/usr/bin/python

import json
import pika

TODO_process = """
Ruote.process_definition do
    make_tmp_repo_branch # create request branch
    hardworker :worker_type => 'src_downloader' # download sources from Git and dput to request branch
    hardworker :worker_type => 'simplebuilder' # get source to local drive, build, dput
    merge_tmp_branch_to_master # merge built binaries to master branch
end
"""

process = """
Ruote.process_definition do
    fake1 :fkey1 => 'aaa'
    python :name => 'branch_repo'
    hardworker :worker_type => 'simpledownloader'
    hardworker :worker_type => 'simplebuilder'
    fake1 :fkey1 => 'bbb'
end
"""

pdef = {
    "definition": process,
    "fields":
        {
            "user": "vasya",
            "repo": "test_repo",
            "pkgname": "python-riak",
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
