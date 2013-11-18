import logging

from AVCommon import procedure

def execute(vm, args):
    logging.debug("    CS Execute ARGS: %s" % args)
    protocol, proc_name = args

    proc_new = procedure.procedures[proc_name]
    assert proc_new,"EMPTY proc %s" % proc_name

    logging.debug("inserting new procedure: %s" % proc_new)
    protocol.proc.insert(proc_new)

    return True, ""
