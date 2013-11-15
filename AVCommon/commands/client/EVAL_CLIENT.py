import logging

import AVCommon
import AVAgent

def on_init(vm, args):
    pass

def on_answer(vm, success, answer):
    pass


def execute(vm, args):
    """ client side, returns (bool,*) """
    logging.debug("    CS Execute")
    assert vm, "null vm"

    ret = eval(args)
    return True, ret


