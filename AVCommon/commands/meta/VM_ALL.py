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
    vm_first = "eset7,avast,avast32,avg,panda15,avg32,avira,avira15,kis15,kis14,kis32,mcafee,bitdef15,norton,comodo,eset,msessential,panda".split(',')
    #disattivato temporaneamente norman
    #disattivato DEFINITIVAMENTE kis e ahnlab (kis e' un kis 2013 che ormai non si usa piu', ahnlab e' scaduto e non si riesce a riattivare)
    vm_second = "fortinet,drweb,360cn5,adaware,fprot,bitdef,fsecure,gdata,vba32,iobit32,mbytes,risint,syscare,trendm,trendm15,zoneal,clamav".split(',')
    # just as a documentation
    # vm_not_working_first = "".split(',')
    # vm_not_working_second = "norman".split(',')
    vm_ignored = ""

    #in case of "puppet" host, I have different vms
    if "avmaster" == socket.gethostname():
        # 29
        vm_first = "avast,avast32,avg,avg32,avira,comodo,kis14,kis,mcafee,msessential,norton,panda,kis32".split(',')
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