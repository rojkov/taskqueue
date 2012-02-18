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

# We run under daemontools and it communicates via signals
Signal.trap('SIGTERM') do
    puts 'Shutdown gracefully'
    engine.shutdown
    puts 'Asked engine to stop'
end

# This spawns a thread which listens for amqp responses
RuoteAMQP::Receiver.new( engine, :launchitems => true )

class FakeParticipant
    include Ruote::LocalParticipant
    def consume(workitem)
        puts workitem.inspect
        puts "workitem consumed\n" + workitem.inspect
        reply_to_engine(workitem)
    end
end

class PythonParticipant
    include Ruote::LocalParticipant

    def consume(workitem)
        wi_str = workitem.as_json
        out_wi_str = ""
        IO.popen("pyparticipant #{workitem.params['name']}", 'w+') do |subprocess|
            subprocess.write(wi_str)
            subprocess.close_write()
            subprocess.read.split("\n").each do |line|
                wi_line = line[/^~~~WORKITEM~~~(.*)$/, 1]
                if wi_line then
                    out_wi_str += ' ' + wi_line
                end
            end
        end
        if out_wi_str != "" then
            new_wi = Ruote::Workitem.from_json(out_wi_str)
            reply_to_engine(new_wi)
        else
            puts "Wrapper haven't returned workitem"
            reply_to_engine(workitem)
        end
    rescue
        puts "problem occured: " + $!
    end

end

engine.register_participant :fake1, FakeParticipant
engine.register_participant :python, PythonParticipant
engine.register_participant :hardworker, RuoteAMQP::ParticipantProxy, :queue => 'taskqueue'

pdef = Ruote.process_definition do
    python :name => 'branch_repo'
    fake1 :p1 => 'gggght'
end

wfid = engine.launch(pdef, :repo => "test_repo", :user => 'vasya')

puts "Engine running"
engine.join()
puts "Engine stopped"
