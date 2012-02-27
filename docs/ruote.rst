Integration with Ruote
======================

If you use Ruote_ to run workflows and want to offload heavy jobs to a cluster
of workers then taskqueue is what you need.

First you need to have a running Ruote worker with a registered AMQP participant:

.. code-block:: ruby

    #!/usr/bin/ruby

    require 'yajl/json_gem'
    require 'ruote'
    require 'ruote/storage/fs_storage'
    require 'ruote-amqp'

    STDOUT.sync = true

    engine = Ruote::Engine.new(
        Ruote::Worker.new(Ruote::FsStorage.new('work')))

    #engine.noisy = true

    #AMQP.logging = true
    AMQP.settings[:host] = 'localhost'
    AMQP.settings[:user] = 'wfworker'
    AMQP.settings[:pass] = 'wfworker'
    AMQP.settings[:vhost] = '/wfworker'

    # This spawns a thread which listens for amqp responses
    RuoteAMQP::Receiver.new( engine, :launchitems => true )

    # prints workitems to stdout
    class InspectParticipant
        include Ruote::LocalParticipant
        def consume(workitem)
            puts workitem.inspect
            reply_to_engine(workitem)
        end
    end

    engine.register_participant :debug, InspectParticipant
    engine.register_participant :hardworker, RuoteAMQP::ParticipantProxy, :queue => 'taskqueue'

    puts "Engine running"
    engine.join()

The proxy participant `hardworker` transmits workitems to the default direct
AMQP exchange with the routing key `taskqueue`. These workitems will be
recieved by taskqueue's dispatcher.

Next you need to configure taskqueue to report task results back to the AMQP.
By default `RuoteAMQP::Receiver` instances listen to the queue
`ruote_workitems` thus update the file `/etc/taskqueue/config.ini` to set
the setting `results_routing_key` to `ruote_workitems`:

.. code-block:: guess

    [DEFAULT]
    results_routing_key = ruote_workitems

Make sure that some taskqueue dispetchers and workpools are running. Now you
can submit tasks for processing::

    #!/usr/bin/python

    import json
    import pika

    process = """
    Ruote.process_definition do
        sequence :on_error => 'error_handler' do
            hardworker :worker_type => 'simpledownloader'
            hardworker :worker_type => 'simplebuilder'
        end
        define 'error_handler' do
            debug
        end
    end
    """

    pdef = {
        "definition": process,
        "fields":
            {
                "user": "vasya",
                "repo": "test_repo",
                "pkgname": "python-taskqueue",
                "workdir": "/tmp"
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

.. _Ruote: http://ruote.rubyforge.org/
