__author__ = 'fabrizio'

import socket

from AVCommon.logger import logging
from AVCommon import command


def on_init(protocol, args):
    if not "clean_evidences" in command.context:
        command.context["clean_evidences"] = set()
        logging.debug("It's the first run so I'll clean targets and disable analysis")
        logging.debug("args: %s" % args)
    #aggiungo l'hostname (del server) se manca (cioe' se esiste il solo parametro fittizio 'Ok')
    if len(args) == 1:
        args.append(socket.gethostname())

    logging.debug("args: %s" % args)

    ret = None
    if not command.context["clean_evidences"]:
        ret = True

    command.context["clean_evidences"].add(protocol.vm)
    return ret


def on_answer(vm, success, answer):
    pass


def execute(vm, args):
    from AVAgent import build

    # logging.debug("args: %s" % args)

    backend = command.context["backend"]
    pupp = args[1]

    logging.debug("puppet: %s" % pupp)

    build.create_user(pupp, vm, backend)
    build.uninstall(backend)

    build.disable_analysis(backend)

    numtargets = build.clean(backend, pupp)
    return True, "Cleaned targets: %s from oper: AOP_%s and disabled analysis" % (numtargets, pupp)

    # return True, "Skipping clean because it was already executed"
