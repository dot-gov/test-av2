import logging

from AVCommon import procedure

def execute(vm, args):
    logging.debug("    CS Execute ARGS: %s" % args)
    protocol, proc_name = args

    proc = procedure.procedures[proc_name]
    protocol.procedure.insert(proc)

    return True, ""
