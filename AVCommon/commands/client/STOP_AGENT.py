__author__ = 'zeno'
import logging

def on_init(vm, args):
    pass

def on_answer(vm, success, answer):
    pass

def execute(vm, args):
    """ client side, returns (bool,*) """
    logging.debug("    STOP_AGENT")
    assert vm, "null vm"

    #TODO: stops a AVAgent on vm
    return True, ""