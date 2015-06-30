__author__ = 'zeno'

from AVCommon.logger import logging
import socket

from AVCommon import command


#vm_first = "avast,avast32,avg,avg32,avira,kis,kis14,kis32,mcafee,norton,panda,comodo,eset,msessential".split(',')
vm_first_rite = "eset7,avast,avastf,avg,avg15,panda15,avg32,avira,avira15,kis15,kis14,kis32,bitdef15,norton,comodo,eset,msessential,panda,norton15,avira15f,avg15f,defender,comodo7,mbytes,mcafee".split(',')
#disattivato DEFINITIVAMENTE kis (kis e' un kis 2013 che ormai non si usa piu')

#disattivato DEFINITIVAMENTE avast32, kis
vm_deactivated_temp = "ahnlab"

vm_second_rite = "fortinet,drweb,cmcav,adaware,fprot,bitdef,fsecure,gdata,vba32,risint,syscare,trendm15,zoneal,clamav,360ts,norman,spybot,zoneal7,win10preview".split(',')
#disattivati DEFINITIVAMENTE trendm (abbiamo trendm15) e 360cn5 (abbiamo 360ts), iobit32,


vm_ignored_rite = ""


def execute(vm, protocol, level):
    """ client side, returns (bool,*) """
    logging.debug("    VM_ALL")

    assert vm, "null vm"
    assert command.context is not None

    vm_first = vm_first_rite
    vm_second = vm_second_rite

    #in case of "puppet" host, I have different vms
    if "avmaster" == socket.gethostname():
        # 29
        vm_first = "avast,avg32,avira,comodo,kis14,kis,mcafee,msessential,norton,panda,kis32".split(',')
        vm_second = "360cn,adaware,bitdef,drweb,fsecure,gdata,mbytes,norman,risint,trendm,iobit32,zoneal".split(',')
        # just as a documentation
        # vm_not_working_first = "eset,avast32".split(',')
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