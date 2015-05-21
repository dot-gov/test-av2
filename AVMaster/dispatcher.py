import os
import sys
from collections import OrderedDict


sys.path.append(os.path.split(os.getcwd())[0])
sys.path.append(os.getcwd())

from AVCommon.protocol import Protocol
from AVCommon import command
from AVCommon import config
from AVMaster import report
from AVCommon.helper import red
from AVCommon.logger import logging

class Dispatcher(object):
    """docstring for Dispatcher"""

    vms = []

    def __init__(self, mq, vms, timeout=1100):
        self.vms = vms
        self.mq = mq
        self.timeout = timeout

    def end(self, c):
        logging.debug("- END: %s" % c)
        self.ended.add(c)
        if self.pool:
            m = self.pool.pop(0)
            logging.debug("pool popped: %s, remains: %s" % (m.vm, len(self.pool)))
            self.start(m)
        else:
            logging.info("pool is empty")

        report.Report().pool = [ p.vm for p in self.pool]
        logging.debug("- pool: %s" % report.Report().pool)

    def start(self, p):
        logging.debug("- START: %s" % p.vm)
        self.mq.clean(p)
        r = p.send_next_command()
        c = p.last_command

        report.sent(p.vm, c)
        logging.info("- SENT: %s" % c)

    def pool_start(self, machines, size):
        logging.debug("pool start, size: %s" % size )
        self.pool = machines

        for i in range(size):
            if not self.pool:
                break
            m = self.pool.pop(0)
            self.start(m)

        report.Report.pool = [ p.vm for p in self.pool]

    def dispatch(self, procedure, pool=0 ):
        global received
        exit = False

        command.context = {}
        procedure.add_begin_end()

        #logging.debug("- SERVER len(procedure): %s" % len(procedure))
        self.num_commands = len(procedure)

        report.init(procedure.name)

        assert self.vms
        assert self.vms[0], "please specify at least one VM"
        logging.debug("self.vms: %s" % self.vms)
        av_machines = OrderedDict()
        p_id = 0
        for vm in self.vms:
            av_machines[vm] = Protocol(self, vm, procedure, id = p_id)
            p_id += 1

        if pool == 0:
            pool = len(self.vms)

        Protocol.pool = pool
        self.pool_start(av_machines.values(), pool)

        self.ended = set()
        answered = 0
        #timed out vms
        no_answer = 0

        while not exit and len(self.ended) < len(self.vms):
            rec = self.mq.receive_server(blocking=True, timeout=self.timeout)
            if rec is not None:
                c, msg = rec
                try:
                    command_unserialize = command.unserialize(msg)
                except:
                    logging.exception("cannot unserialize: %s" % msg)
                    #exit = True
                    continue
                    #command_unserialize =

                logging.info("- RECEIVED %s, %s" % (c, red(command_unserialize)))
                if c not in av_machines.keys():
                    logging.warn("A message for %s probably belongs to another test!" % c)
                    continue

                p = av_machines[c]

                try:
                    answer = p.receive_answer(c, command_unserialize)
                except:
                    logging.exception("cannot receive: %s" % command_unserialize)
                    continue

                report.received(c, command_unserialize)

                if answer.success == None:
                    #logging.debug("- SERVER IGNORING")
                    continue

                answered += 1
                #logging.debug("- SERVER RECEIVED ANSWER: %s" % answer.success)
                if answer.name == "END":
                    self.end(c)
                    logging.info("- RECEIVE END: %s, %s" % (c, self.ended))
                    logging.debug("ended: (%s/%s) %s" % (len(self.ended), len(self.vms), self.ended))
                    remained = set(self.vms).difference(set(self.ended))
                    logging.debug("remained: (%s/%s) %s" % (len(remained), len(self.vms), remained))

                elif p.on_error != "DISABLED" and (answer.success or p.on_error == "CONTINUE"):
                    r = p.send_next_command()
                    cmd = p.last_command

                    report.sent(p.vm, cmd)

                    logging.info("- SENT: %s, %s" % (c, red(cmd)))
                    if not r:
                        logging.info("- SENDING ERROR, ENDING: %s" %c)
                        self.end(c)
                        logging.debug("self.ended: (%s/%s) %s" % (len(self.ended), len(self.vms), self.ended))

                else:
                    # answer.success == False
                    # deve skippare fino al command: END_PROC

                    if p.on_error == "SKIP":
                        logging.debug("on_error == %s" % p.on_error)
                        r = p.send_next_call()
                        cmd = p.last_command
                        if cmd:
                            report.sent(p.vm, cmd)
                        else:
                            logging.info("- RECEIVE ERROR, ENDING: %s" %c)
                            self.end(c)
                            logging.debug("self.ended: (%s/%s) %s" % (len(self.ended), len(self.vms), self.ended))
                    elif p.on_error == "DISABLED":
                        logging.debug("on_error == DISABLED")
                        r = p.send_next_proc()
                        cmd = p.last_command
                        if cmd:
                            report.sent(p.vm, cmd)
                        else:
                            logging.info("- RECEIVE ERROR, ENDING: %s" %c)
                            self.end(c)
                            logging.debug("self.ended: (%s/%s) %s" % (len(self.ended), len(self.vms), self.ended))
                    else:
                        assert p.on_error == "STOP"

                        logging.info("- RECEIVE ERROR, STOP: %s" %c)
                        self.end(c)
                        logging.debug("self.ended: (%s/%s) %s" % (len(self.ended), len(self.vms), self.ended))

            else:
                logging.info("- SERVER RECEIVED empty")
                no_answer += 1
                exit = True

        report.finish()

        logging.debug("answered: %s, ended: %s, num_commands: %s, not_answered: %s" % (answered, len(self.ended), self.num_commands, no_answer))
        #assert len(self.ended) == len(self.vms), "answered: %s, ended: %s, num_commands: %s" % ( answered, len(self.ended), len(self.vms))
        if len(self.ended) != len(self.vms):
            logging.error("ended: %s, num_vms: %s, not_answered: %s. Probably some timeout occurred" % (len(self.ended), len(self.vms), no_answer))
        #assert answered >= (len(self.vms) * (self.num_commands)), "answered: %s, len(vms): %s, num_commands: %s" % (answered , len(self.vms), self.num_commands)
        return answered