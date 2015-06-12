from AVCommon.logger import logging
from time import sleep


def execute(vm, protocol, args):
    """ server side """
    from AVMaster import vm_manager

    assert vm, "null vm"
    mq = protocol.mq

    if not args:
        args = ""

    check_avagent = ("AV_AGENT" in args)
    no_check = ("NO_CHECK" in args)

    mq.reset_connection(vm)

    #300 seconds. Sometimes it takes very long (when windows is not licensed?)!
    max_tries = 30

    # just startup
    if no_check:
        if vm_manager.execute(vm, "pm_poweron"):
            return True, "Started VM (no win startup check)"
        return False, "Error Occurred: Timeout while starting VM"
    # starup and vmtools check
    elif not check_avagent:
        if vm_manager.execute(vm, "pm_poweron_and_check"):
            return True, "Started VM (VMtools running)"
        return False, "Error Occurred: Timeout while starting VM or no VMtools"
    # startup and complete check (vmtools + redis connection)
    else:
        if vm_manager.execute(vm, "pm_poweron_and_check"):
            for i in range(max_tries):
                if mq.check_connection(vm):
                    logging.debug("got connection from %s" % vm)

                    #debug
                    iplist = vm_manager.execute(vm, "pm_ip_addresses")

                    return True, "Started VM (connection to redis OK) (ip: %s)" % iplist
                sleep(10)
            #if i'm here we have no redi connection. Now I log the IP for diagnostic!
            iplist = vm_manager.execute(vm, "pm_ip_addresses")
            return False, "Error Occurred: VMtools ok but no Redis Connection (ip: %s)" % iplist
        else:
            return False, "Error Occurred: Timeout while starting VM or no VMtools"