__author__ = 'mlosito'

import sys
import socket
from AVCommon import build_common
from AVCommon.logger import logging
from AVCommon import command

# TODO: no avmaster imports!
from AVMaster import vm_manager
from AVAgent import build


#TODO: REMOVE
sys.path.append("/Users/olli/Documents/work/AVTest/")
sys.path.append("/Users/mlosito/Sviluppo/Rite/")
sys.path.append("/Users/zeno/AVTest/")




# #new build function by olli to check if all the parameters are good!
# def build_server(kind, platform_type, platform, srv, puppet, factory=None):
#     # global params
#
#     class Args:
#         pass
#
#     report = None
#
#     try:
#         srv_params = servers[srv]
#     except KeyError:
#         return False
#
#
#     args = Args()
#
#     args.action = "pull_server"
#     args.platform = platform
#     args.kind = kind
#     args.backend = srv_params["backend"]
#     args.frontend = srv_params["frontend"]
#     args.platform_type = platform_type
#     args.operation = srv_params["operation"]
#     args.param = command.context["build_parameters"].copy()
#     args.asset_dir = "assets"
#
#     # servono??
#     # ML: si', servono, vanno presi dal context oppure rimarranno vuoti !
#     args.blacklist = command.context["blacklist"][:]
#     args.soldierlist = command.context["soldierlist"][:]
#     args.nointernetcheck = command.context["nointernetcheck"][:]
#     args.puppet = puppet
#     args.factory = factory
#
#     # questi non servono perche' la pwd e' cablata, mentre l'host e' settato da build
#     # in base ad args.backend
#
#     # build_common.connection.host = srv_params["backend"]
#     # #build.connection.user = "avmonitor"
#     # build_common.connection.passwd = "testriteP123"
#
#     results, success, errors = build.build(args, report)
#     print "after build", results, success, errors
#     if success:
#         return results
#     else:
#         return errors
# #    return success




#pushes the file to client, to be executed
def push_file(vm, exefilename):
    remote_name = "C:\\AVTest\\AVAgent\\buildsrv.exe"
    vm_manager.execute(vm, "copyFileToGuest", exefilename, remote_name)
    logging.debug("Pushed file: %s to: %s" % (exefilename, remote_name))

# TODO tobe implemented
def unzip_agent():
    return ""  #filenames

# TODO tobe implemented
def check_static(filenames):
    pass


#creates a factory
#TODO: we should also cache factories
def _create_new_factory(self, operation, target, factory, config):
    pass

