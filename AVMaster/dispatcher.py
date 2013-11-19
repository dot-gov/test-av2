import os
import sys
import threading
import logging
 
sys.path.append(os.path.split(os.getcwd())[0])
sys.path.append(os.getcwd())
 
from AVCommon.mq import MQStar
from av_machine import AVMachine
from AVCommon import command
from AVCommon import config


class Dispatcher(object):
    """docstring for Dispatcher"""
 
    vms = []
    def __init__(self, mq, vms, report=None, timeout=0):
        self.vms = vms
        self.mq = mq
        self.report = report
        self.timeout = timeout
        logging.debug("Dispatcher, vms: %s" % vms )
 
    def dispatch(self, procedure, ):
        global received
        exit = False

        procedure.add_begin_end()

        logging.debug("- SERVER len(procedure): %s"% len(procedure))
        self.num_commands = len(procedure)

        av_machines = {}
        for c in self.vms:
            av_machines[c] = AVMachine(self.mq, c, procedure)
 
        for a in av_machines.values():
            #a.start()
            #self.mq.clean(a)
            r, c = a.execute_next_command()
            if self.report:
                self.report.sent(a.name, str(c))
            logging.debug("- SERVER SENT: %s" % c)

        ended = 0
        answered = 0
        len_vms =  len(self.vms)
        logging.debug("len vms: %s" % len_vms)
        while not exit and ended < len_vms:
            rec = self.mq.receive_server(timeout=self.timeout)
            if rec is not None:
                logging.debug("- SERVER RECEIVED %s %s" % (rec, type(rec)))
                c, msg = rec
                m = av_machines[c]
                answer = m.manage_answer(msg)
                if self.report:
                    self.report.received(c, command.unserialize(msg))
                answered += 1
                #logging.debug("- SERVER RECEIVED ANSWER: %s" % answer.success)
                if answer.name == "END":
                    ended += 1
                    logging.debug("- SERVER END: %s" % answer)
                elif answer.success:
                    r, cmd = av_machines[c].execute_next_command()
                    if self.report:
                        self.report.sent(a.name, str(cmd))
                    logging.debug("- SERVER SENT: %s, %s" % (c, cmd))
                else:
                    if config.auto_stop_agent:
                        logging.debug("- SERVER ERROR, SENDING END")
                        r, cmd = av_machines[c].send_stop_agent()
                    else:
                        logging.debug("- SERVER ERROR, ENDING")
                        ended += 1

 
            else:
                logging.debug("- SERVER RECEIVED empty")
                exit = True
 
        logging.debug("answered: %s, ended: %s, num_commands: %s" %( answered, ended, self.num_commands))
        assert ended == len_vms, "vms: %s ended: %s" % (len_vms, ended)
        #assert answered >= (len(self.vms) * (self.num_commands)), "answered: %s, len(vms): %s, num_commands: %s" % (answered , len(self.vms), self.num_commands)
        return ended, answered