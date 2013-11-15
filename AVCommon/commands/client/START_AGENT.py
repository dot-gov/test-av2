import logging

def on_init(vm, args):
    pass

def on_answer(vm, success, answer):
    pass

def execute(vm, args):
    """ client side, returns (bool,*) """
    logging.debug("    START AGENT, args: %s" % args)
    assert vm, "null vm"

    return True, "AGENT STARTED"


