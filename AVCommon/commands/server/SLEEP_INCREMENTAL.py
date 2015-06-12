from AVCommon.logger import logging
from time import sleep
import random
from AVCommon import command
from AVCommon.protocol import Protocol


def execute(vm, protocol, args):
    assert isinstance(args, int)
        #"Sleep needs only an int as argument"
        #logging.debug("    CS Sleep for %s" % args)
    assert protocol.id >= 0
    sleep_time = args * protocol.id
    sleep(int(sleep_time))

    logging.debug("%s  protocol.id: %s - sleep per vm: %s - sleep time: %s" % (vm, protocol.id, args, sleep_time))

    return True, "slept for %s" % sleep_time