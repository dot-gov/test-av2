__author__ = 'fabrizio, mlosito, olli'

from AVCommon.logger import logging
from AVCommon import command
import socket
from AVAgent import build

from AVMaster import build_server_with_cache

report_level = 1


def on_init(protocol, args):
    """ server side """
    puppet = socket.gethostname()
    if len(args) == 3:
        args.append(puppet)

    zipfilename = create_built_file(protocol.vm, args)
    #TODO: push to client THIS SHOULD USE THE PUSH COMMAND (so build_srv should be a metacommand!)
    build_server_with_cache.push_file(protocol.vm, zipfilename)

    return True


def on_answer(vm, success, answer):
    """ server side """
    if isinstance(answer, list) and len(answer) > 0:
        logging.info("BUILD ANSWER LAST: %s" % answer[-1])
    else:
        logging.info("BUILD ANSWER: %s" % str(answer))


def execute(vm, args):

    #TODO: unzip the file
    filenames = build_server_with_cache.unzip_agent()

    #TODO: check static
    build_server_with_cache.check_static(filenames)

    #TODO We do not execute - to be implemented
    #usually the push is called by other actions like scout.
    #for now it's just never called!
    #
    # """ client side, returns (bool,*) """
    # logging.debug("    BUILD %s" % args)
    # assert vm, "null vm"
    # assert command.context, "Null context"
    #
    # backend = command.context["backend"]
    # frontend = command.context["frontend"]
    # params = command.context["build_parameters"].copy()
    # blacklist = command.context["blacklist"][:]
    # soldierlist = command.context["soldierlist"][:]
    # nointernetcheck = command.context["nointernetcheck"][:]
    #
    # report = command.context["report"]
    #
    # logging.debug("args: %s", args)
    # action, platform, kind, puppet = args[0:4]
    #
    # operation = "AOP_%s" % puppet
    #
    # param = params[platform]
    # platform_type = param['platform_type']
    #
    # assert kind in ['silent', 'melt'], "kind: %s" % kind
    # assert action in ['scout', 'elite', 'elite_fast', 'soldier_fast', 'internet', 'test', 'clean', 'pull'], "action: %s" % action
    # assert platform_type in ['desktop', 'mobile'], "platform_type: %s" % platform_type
    #
    #
    # class Args:
    #     pass
    #
    # args = Args()
    #
    # args.action = action
    # args.platform = platform
    # args.kind = kind
    # args.backend = backend
    # args.frontend = frontend
    # args.param = param
    # args.blacklist = blacklist
    # args.soldierlist = soldierlist
    # args.platform_type = platform_type
    # args.nointernetcheck = nointernetcheck
    # args.operation = operation
    # args.puppet = puppet
    # args.asset_dir = "AVAgent/assets"
    # args.factory = None
    #
    # results, success, errors = build.build(args, report)
    #
    # try:
    #     last_result = results[-1]
    # except:
    #     last_result = "NO RESULTS"
    #
    # return success, results

    return True, "fake results by ml"


#If the files is in cache prepares it for pull
#else it creates a new build file, puts it in cache and prepares it for pull
def create_built_file(vm, args):
    #TODO: we should create a factory
    #build_common.create_new_factory()
    # target_id, factory_id, ident = build_common.create_new_factory(
    #         operation, target, factory, config)
    # build_common.build_agent(factory_id, add_result, zipfilename, melt=meltfile, kind=self.kind)

    # Uses method from this class to build the file
    # NB: we should pass the new created factory

    # since it's a srv build, the file will not be checked and executed in this step, so we set an optional arg
    args.append("build_srv")
    # args.build_srv = True

    #TODO: somehow we should get back the zip filename
    success, result, zipfilename = execute_server(vm, args)

    return zipfilename


def execute_server(vm, args):
    """ client side, returns (bool,*) """
    logging.debug("    BUILD SERVER %s" % args)
    assert vm, "null vm"

    # Per Matteo:
    # si spacca a questa assert perch' il context e' null nella on_init (almeno credo)
    assert command.context, "Null context"

    backend = command.context["backend"]
    frontend = command.context["frontend"]
    params = command.context["build_parameters"].copy()
    blacklist = command.context["blacklist"][:]
    soldierlist = command.context["soldierlist"][:]
    nointernetcheck = command.context["nointernetcheck"][:]

    report = command.context["report"]

    logging.debug("args: %s", args)
    action, platform, kind, puppet = args[0:4]

    operation = "AOP_%s" % puppet

    param = params[platform]
    platform_type = param['platform_type']

    assert kind in ['silent', 'melt'], "kind: %s" % kind
    assert action in ['scout', 'elite', 'elite_fast', 'soldier_fast', 'internet', 'test', 'clean', 'pull'], "action: %s" % action
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
    args.factory = None

    results, success, errors, filename = build.build(args, report)

    try:
        last_result = results[-1]
    except:
        last_result = "NO RESULTS"

    return success, results, filename