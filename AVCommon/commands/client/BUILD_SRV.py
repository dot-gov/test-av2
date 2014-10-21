__author__ = 'mlosito,fabrizio'


from AVCommon.logger import logging
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

    #I pick the first 4 args, there can be a fifth one that is the server name (aka puppet)
    action, platform, kind, final_action = args[:4]
    hostname = helper.get_hostname()
    ftype = 'desktop'

    factory_name = '%s_%s_%s_%s_%s' % (hostname, ftype, platform, kind, final_action)

    # elite_fast and soldier_fast assumes that you already have a scout in execution.
    # So you have not to create a new factory, you should get the current factory
    #and also you have NOT to build, store, unzip and push anything!
    if action not in ['elite_fast', 'soldier_fast']:
        #FACTORY CREATION

        logging.debug("creating factory: %s", factory_name)
        config = "%s/config_%s.json" % (asset_dir, ftype)

        #Tries to see if there is already a factory
        factory_data = build_common.get_factory(factory_name, command.context["backend"], operation)

        if factory_data is None:

            target_id, factory_id, ident = build_common.create_new_factory(ftype, command.context["frontend"], command.context["backend"], operation, build.get_target_name(), factory_name, config)
            factory = target_id, factory_id, ident
            logging.debug("created factory: %s", factory)
        else:
            logging.debug("reusing factory with name: %s", factory_name)
            factory_data = build_common.get_factory(factory_name, command.context["backend"], operation)
            factory = (factory_data[2][1], factory_data[0], factory_data[1])
            factory_id = factory[1]
            logging.debug("reusing factory - ID: %s", factory_id)

        # EXE CREATION
        zipfilename = 'build_cache/build_%s_%s_%s_%s.zip' % (platform, action, kind, final_action)
        params_all = command.context["build_parameters"].copy()
        params = params_all[platform]
        meltfile = params.get('meltfile', None)
        #TODO should be: build.add_result but does not works!
        build_common.build_agent(factory_id, hostname, params, None, zipfilename, melt=meltfile, kind=kind, use_cache=True)

        #unzip OVERWRITES the files
        exe = utils.unzip(zipfilename, "build/%s" % platform, logging.debug)

        # push_exe(exe)
        logging.debug("Pushing file: %s", exe[0])
        build_server_with_cache.push_file(protocol.vm, exe[0])

    else:
        logging.debug("reusing factory: %s", factory_name)
        factory_data = build_common.get_factory(factory_name, command.context["backend"], operation)
        factory = (factory_data[2][1], factory_data[0], factory_data[1])
        logging.debug("reusing factory - DETAILS: %s", factory)
        #no need for factory
        #factory = "aa", "bb", "cc"
        #factory_id = factory_data[0] # also is factory[1]
        #logging.debug("factory_id for buildinge: %s", factory_id)
        exe = "no-exe-for-elite_fast-or-soldier_fast"

    #no puppet
    if len(args) < 4:
        logging.error("Wrong args number. Args: %s", str(args))
        return False
    if len(args) == 4:
        args.append(puppet)
        args.append(factory)
        args.append(exe)
    #puppet but no other params
    elif len(args) == 5:
        args[4] = puppet
        args.append(factory)
        args.append(exe)
    #puppet and factory
    elif len(args) == 6:
        args[4] = puppet
        args[5] = factory
        args.append(exe)
    #there are only old params
    else:
        args[4] = puppet
        args[5] = factory
        args[6] = exe

    # #args.append(puppet)
    # if len(args) == 5:
    #     args.append(factory)
    # if len(args) == 6:
    #     args.append(exe)

    return True


def on_answer(vm, success, answer):
    """ server side """
    if isinstance(answer, list) and len(answer) > 0:
        logging.info("BUILD ANSWER LAST: %s" % answer[-1])
    else:
        logging.info("BUILD ANSWER: %s" % str(answer))


def execute(vm, args):
    """ client side, returns (bool,*) """
    logging.debug("    BUILD SRV (CLIENT SIDE) - Args: %s" % args)
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
    action, platform, kind, final_action, puppet, factory, exe = args

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
    args.final_action = final_action

    results, success, errors = build.build(args, report)

    try:
        last_result = results[-1]
    except:
        last_result = "NO RESULTS"

    return success, results