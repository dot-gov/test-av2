import logging
import copy
import threading
from AVCommon import config

import command

import traceback

class ProtocolClient:
    """ Protocol, client side. When the command is received, it's executed and the result resent to the server. """

    def __init__(self, mq, vm, timeout = 0):
        self.mq = mq
        self.vm = vm
        self.timeout = 0

        assert(isinstance(vm, str))

    def _execute_command(self, cmd):
        try:
            ret = cmd.execute(self.vm, cmd.payload)
            if config.verbose:
                logging.debug("cmd.execute ret: %s" % str(ret))
            cmd.success, cmd.payload = ret
        except Exception, e:
            logging.error("ERROR: %s %s %s" % (type(e), e, traceback.format_exc(e)))
            cmd.success = False
            cmd.payload = e

        assert isinstance(cmd.success, bool)
        self.send_answer(cmd)
        return cmd

    # client side
    def receive_command(self):
        assert(isinstance(self.vm, str))
        #logging.debug("PROTO receiveCommand %s" % (self.client))
        msg = self.mq.receive_client(self.vm, blocking=True, timeout=self.timeout)
        if config.verbose:
            logging.debug("PROTO C receive_command %s, %s" % (self.vm, msg))
        cmd = command.unserialize(msg)
        cmd.vm = self.vm

        return self._execute_command(cmd)

    def send_answer(self, reply):
        if config.verbose:
            logging.debug("PROTO C send_answer %s" % reply)
        self.mq.send_server(self.vm, reply.serialize())


class Protocol(ProtocolClient):
    """ A protocol implements the server behavior."""
    proc = None
    last_command = None

    def __init__(self, mq, vm, proc=None, timeout = 0):
        ProtocolClient.__init__(self, mq, vm, timeout)
        self.mq = mq
        self.vm = vm
        self.proc = copy.deepcopy(proc)
        assert (isinstance(vm, str))

    # server side
    def _send_command_mq(self, cmd):
        cmd.on_init(self.vm, cmd.payload)
        self.mq.send_client(self.vm, cmd.serialize())

    def _execute(self, cmd, blocking=False):
        #logging.debug("PROTO S executing server")
        t = threading.Thread(target=self._execute_command, args=(cmd,))
        t.start()

        if blocking:
            t.join()

    def _meta(self, cmd):
        if config.verbose:
            logging.debug("PROTO S executing meta")
        ret = cmd.execute( self.vm, [self, cmd.payload] )
        cmd.success, cmd.payload = ret
        assert isinstance(cmd.success, bool)
        self.send_answer(cmd)
        return cmd

    def send_next_command(self):
        if not self.proc:
            self.last_command = None
            return False
        self.last_command = self.proc.next_command()
        self.send_command(copy.deepcopy(self.last_command))
        return True

    def send_command(self, cmd):
        if config.verbose:
            logging.debug("PROTO S send_command: %s  side: %s" % (str(cmd), cmd.side))
        #cmd = command.unserialize(cmd)
        cmd.vm = self.vm
        try:
            if cmd.side == "client":
                self._send_command_mq(cmd)
            elif cmd.side == "server":
                self._execute(cmd)
            elif cmd.side == "meta":
                self._meta(cmd)
            return True
        except Exception, ex:
            logging.error("Error sending command %s: %s" % (cmd, ex))
            return False

    def receive_answer(self, vm, msg):
        """ returns a command with name, success and payload """
        #msg = self.mq.receiveClient(self, client)

        cmd = command.unserialize(msg)
        cmd.vm = vm
        if config.verbose:
            logging.debug("PROTO S manage_answer %s: %s" % (vm, cmd))

        assert(cmd.success is not None)
        cmd.on_answer(vm, cmd.success, cmd.payload)

        return cmd
