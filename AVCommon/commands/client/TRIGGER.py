__author__ = 'marcol'

# THERE ARE SOME CODE DUPLICATIONS. SAME CODE IS IN BUILD.PY
from AVAgent import util_agent

from AVCommon.logger import logging


def on_init(protocol, args):
    return True


def on_answer(vm, success, answer):
    pass


def execute(vm, args):

    trigger_failed = False

    logging.debug("Idle time BEFORE trigger: %s", util_agent.get_idle_duration())

    logging.debug("Triggering sync with keyinject for 30 seconds")
    util_agent.trigger_keyinject()

    logging.debug("Triggering sync with mouse")
    util_agent.trigger_python_mouse()

    #if idle time > 20 seconds, trigger have failed
    trigger_failed, log = util_agent.trigger_worked(logging)

    return trigger_failed, log
