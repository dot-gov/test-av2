from AVCommon.logger import logging
from time import sleep
import random
from AVCommon import command
from AVCommon.protocol import Protocol

#experimental. but the command is a server command!
# def execute(vm, protocol, args):
#     assert isinstance(args, int)
#         #"Sleep needs only an int as argument"
#         #logging.debug("    CS Sleep for %s" % args)
#     assert protocol.id >= 0
#     sleep_time = int(args * protocol.id)
#
#     if sleep_time > 60 and command.context["report"]:
#         for i in range(int(sleep_time/60)):
#             sleep(60)
#             report = command.context["report"]
#             report("+ SUCCESS - sleep_incremental command liket to ping the server to prevent timeout")
#         sleep(sleep_time % 60)
#     else:
#         sleep(sleep_time)
#
#     logging.debug("%s  protocol.id: %s - sleep per vm: %s - sleep time: %s" % (vm, protocol.id, args, sleep_time))
#
#     return True, "slept for %s" % sleep_time


def execute(vm, protocol, args):
    #fast startup is 20 seconds
    fast_startup_time = 20

    if isinstance(args, int):
        time_per_vm = args
        fast_startup_vm = 0
    elif isinstance(args, list) and len(args) == 2:
        time_per_vm, fast_startup_vm = args
    else:
        return False, "Wrong syntax for SLEEP_INCREMENTAL"

    assert protocol.id >= 0

    if protocol.id < fast_startup_vm:
        sleep_time = fast_startup_time * protocol.id
    else:
        sleep_time = fast_startup_time * fast_startup_vm + time_per_vm * (protocol.id - fast_startup_vm)

    sleep(int(sleep_time))

    logging.debug("%s  protocol.id: %s - sleep per vm: %s - sleep time: %s" % (vm, protocol.id, args, sleep_time))

    return True, "slept for %s" % sleep_time