__author__ = 'zeno'

from AVCommon.logger import logging
import socket

from AVCommon import command

def execute(vm, protocol, level):
    """ client side, returns (bool,*) """
    logging.debug("    VM_ALL")

    assert vm, "null vm"
    assert command.context is not None

    #vm_first = "avast,avast32,avg,avg32,avira,kis,kis14,kis32,mcafee,norton,panda,comodo,eset,msessential".split(',')
    vm_first = "avast,avast32,avg,avg32,avira,avira15,kis,kis14,kis32,kis15,mcafee,norton,comodo,eset,eset7,msessential,panda,panda15".split(',')
    #disattivato temporaneamente norman
    vm_second = "drweb,360cn5,adaware,ahnlab,bitdef,bitdef15,fsecure,gdata,iobit32,vba32,fortinet,mbytes,risint,syscare,trendm,trendm15,zoneal,clamav,fprot".split(',')
    # just as a documentation
    # vm_not_working_first = "".split(',')
    # vm_not_working_second = "norman".split(',')
    vm_ignored = ""

    #in case of "puppet" host, I have different vms
    if "avmaster" == socket.gethostname():
        # 29
        vm_first = "avast,avast32,avg,avg32,avg8,avira,comodo,kis14,kis,mcafee,msessential,norton,panda,kis32".split(',')
        vm_second = "360cn,adaware,bitdef,drweb,fsecure,gdata,mbytes,norman,risint,trendm,iobit32,zoneal".split(',')
        # just as a documentation
        # vm_not_working_first = "eset".split(',')
        # vm_not_working_second = "ahnlab".split(',')
        vm_ignored = "emsisoft".split(',')

    if level and level.lower() == "important":
        vm_all = vm_first
    elif level and level.lower() == "irrilevant":
        vm_all = vm_second
    else:
        vm_all = vm_first + vm_second
    assert isinstance(vm_all, list), "VM expects a list"

    command.context["VM"] = vm_all

    logging.debug("vm_all items: %s" % (vm_all))
    return True, vm_all