__author__ = 'zeno'

from AVCommon.logger import logging
import time

from AVCommon import command

def execute(vm, protocol, level):
    """ client side, returns (bool,*) """
    logging.debug("    VM_ALL")

    assert vm, "null vm"
    assert command.context is not None

    #vm_first = "avast,avast32,avg,avg32,avira,kis,kis14,kis32,mcafee,norton,panda,comodo,eset,msessential".split(',')
    vm_first = "avast,avast32,avg,avg32,avira,kis,kis14,kis32,kis15,mcafee,norton,comodo,eset,eset7,msessential,panda,panda15".split(',')
    #disattivato temporaneamente norman
    vm_second = "drweb,360cn5,adaware,ahnlab,bitdef,bitdef15,fsecure,gdata,iobit32,vba32,fortinet,mbytes,risint,syscare,trendm,trendm15,zoneal,clamav,fprot".split(',')
    vm_ignored = ""

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