__author__ = 'mlosito,fabrizio'


from AVCommon.logger import logging
import time
import socket

from AVCommon import command
from AVCommon import build_common
from AVCommon import helper
from AVCommon import utils

from AVAgent import build

report_level = 1

asset_dir = "AVAgent/assets"

def on_init(protocol, args):
    """ server side """
    from AVMaster import build_server_with_cache

    command.load_context_from_file("AVAgent/default.yaml")

    puppet = socket.gethostname()
    operation = "AOP_%s" % puppet

    # FACTORY CREATION
    #factory = create_factory(args)
    action, platform, kind = args
    hostname = helper.get_hostname()
    ftype = 'desktop'
    factory_id = '%s_%s_%s_%s' % (hostname, ftype, platform, kind)
    logging.debug("creating factory: %s", factory_id)
    config = "%s/config_%s.json" % (asset_dir, ftype)
    target_id, factory_id, ident = build_common.create_new_factory(ftype, command.context["frontend"], command.context["backend"], operation, build.get_target_name(), factory_id, config)
    factory = target_id, factory_id, ident
    logging.debug("created factory: %s", factory)

    # EXE CREATION
    zipfilename = 'build/%s/build.zip' % platform
    params_all = command.context["build_parameters"].copy()
    params = params_all[platform]
    build_common.build_agent(factory_id, hostname, params, logging.debug, zipfilename)

    #unzip OVERWRITES the files
    exe = utils.unzip(zipfilename, "build/%s" % platform, logging.debug)

    # push_exe(exe)
    logging.debug("Pushing file: %s", exe[0])
    build_server_with_cache.push_file(protocol.vm, exe[0])


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
    assert action in ['pull', 'scout', 'elite', 'elite_fast', 'soldier_fast'], "action: %s" % action
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
    args.nointernetcheck = socket.gethostname().lower()
    args.operation = operation
    args.puppet = puppet
    args.asset_dir = asset_dir
    args.factory = factory
    args.exe = exe
    args.server_side = True

    results, success, errors = build.build(args, report)

    try:
        last_result = results[-1]
    except:
        last_result = "NO RESULTS"

    return success, results