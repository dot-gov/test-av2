__author__ = 'mlosito, olli'

import sys
import socket

#TODO: REMOVE
sys.path.append("/Users/olli/Documents/work/AVTest/")
sys.path.append("/Users/mlosito/Sviluppo/Rite/")
sys.path.append("/Users/zeno/AVTest/")


#TODO: REMOVE should not dependo on old build
from AVAgent import build


#TODO: REMOVE
servers = {
    "castore": { "backend": "192.168.100.100",
                 "frontend": "192.168.100.100",
                 "operation": "QA",
                 "target_name": "HardwareFunctional"},
    "polluce": { "backend": "",
                 "frontend": "",
                 "operation": "QA",
                 "target_name": "HardwareFunctional"},
    "zeus": { "backend": "",
              "frontend": "",
              "target_name": "QA",
              "operation": "HardwareFunctional"},
    "minotauro": { "backend": "192.168.100.201",
                   "frontend": "192.168.100.204",
                   "target_name": "QA",
                   "operation": "HardwareFunctional"},
    }

#TODO: REMOVE
params = {
    'platform_type': 'desktop',
    'binary': {'admin': False, 'demo': False},
    'melt': {'admin': False, 'bit64': True, 'codec': True, 'scout': True},
    'platform': 'windows',
    'meltfile': 'AVAgent/assets/windows/meltapp.exe',
    'sign': {},
}


#new build function by olli
def build_server(kind, platform_type, platform, srv, factory=None):
    class Args:
        pass

    report = None

    try:
        srv_params = servers[srv]
    except KeyError:
        return False


    args = Args()

    args.action = "pull"
    args.platform = platform
    args.kind = kind
    args.backend = srv_params["backend"]
    args.frontend = srv_params["frontend"]
    args.platform_type = platform_type
    args.operation = srv_params["operation"]
    args.param = params
    args.asset_dir = "/Users/olli/Documents/work/AVTest/AVAgent/assets"

    # servono??
    args.blacklist = ""
    args.soldierlist = ""
    args.nointernetcheck = socket.gethostname()
    args.puppet = "rite"
    args.factory = factory

    build.connection.host = srv_params["backend"]
    #build.connection.user = "avmonitor"
    build.connection.passwd = "testriteP123"

    results, success, errors = build.build(args, report)
    print "after build", results, success, errors
    if success:
        return results
    else:
        return errors
#    return success

#If the files is in cache prepares it for pull
#else it creates a new build file, puts it in cache and prepares it for pull
def get_built_file():
    pass


#pushes the file to client, to be executed
def push_file():
    pass


#creates a factory
#TODO: we should also cache factories
def _create_new_factory(self, operation, target, factory, config):
    pass


#TODO: remove
def main():
    print "let's build ya"
    if build_server("silent", "desktop", "windows", "castore") is False:
        print "problem build from server"


#TODO: remove
if __name__ == "__main__":
    main()