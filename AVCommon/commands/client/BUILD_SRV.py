__author__ = 'fabrizio'

from AVCommon.logger import logging
import time
import socket

from AVCommon import command
from AVAgent import build

report_level = 1


def on_init(protocol, args):
    """ server side """
    factory = create_factory(args)
    exe = build_local(args, factory)

    push_exe(exe)

    puppet =  socket.gethostname()
    args.append(puppet)
    args.append(factory)
    args.append(exe)

    return True


def on_answer(vm, success, answer):
    """ server side """
    if isinstance(answer, list) and len(answer) > 0:
        logging.info("BUILD ANSWER LAST: %s" % answer[-1])
    else:
        logging.info("BUILD ANSWER: %s" % str(answer))


def execute(vm, args):
    """ client side, returns (bool,*) """
    logging.debug("    BUILD %s" % args)
    assert vm, "null vm"
    assert command.context, "Null context"

    backend = command.context["backend"]
    frontend = command.context["frontend"]
    params = command.context["build_parameters"].copy()
    blacklist = command.context["blacklist"][:]
    soldierlist = command.context["soldierlist"][:]
    nointernetcheck = command.context["nointernetcheck"][:]

    report = command.context["report"]

    logging.debug("args: %s", args)
    action, platform, kind, puppet, factory, exe = args

    operation = "AOP_%s" % puppet

    param = params[platform]
    platform_type = param['platform_type']

    assert kind in ['silent', 'melt'], "kind: %s" % kind
    assert action in ['scout', 'elite', 'elite_fast', 'soldier_fast'], "action: %s" % action
    assert platform_type in ['desktop', 'mobile'], "platform_type: %s" % platform_type


    class Args:
        pass

    args = Args()

    args.action = action
    args.platform = platform
    args.kind = kind
    args.backend = backend
    args.frontend = frontend
    args.param = param
    args.blacklist = blacklist
    args.soldierlist = soldierlist
    args.platform_type = platform_type
    args.nointernetcheck = nointernetcheck
    args.operation = operation
    args.puppet = puppet
    args.asset_dir = "AVAgent/assets"
    args.factory = factory
    args.exe = exe
    args.server_side = True

    results, success, errors = build.build(args, report)

    try:
        last_result = results[-1]
    except:
        last_result = "NO RESULTS"

    return success, results


