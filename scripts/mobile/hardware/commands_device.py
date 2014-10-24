__author__ = 'olli', 'mlosito'

import sys
import socket
import os
import re

sys.path.append("/Users/olli/Documents/work/AVTest/")
sys.path.append("/Users/mlosito/Sviluppo/Rite/")
sys.path.append("/Users/mlosito/Sviluppo/Rite/scripts/mobile/hardware")
sys.path.append("/Users/zeno/AVTest/")

from scripts.mobile.hardware.apk import apk_dataLoader
from scripts.mobile.hardware.utils import wifiutils, superuserutils, utils

import adb

from AVCommon import build_common
from AVAgent import build

#from AVCommon import logger
#from AVAgent.build import build


# servers = {
#     "castore": { "backend": "192.168.100.100",
#                  "frontend": "192.168.100.100",
#                  "operation": "QA",
#                  "target_name": "HardwareFunctional"},
#     "polluce": { "backend": "",
#                  "frontend": "",
#                  "operation": "QA",
#                  "target_name": "HardwareFunctional"},
#     "zeus": { "backend": "",
#               "frontend": "",
#               "target_name": "QA",
#               "operation": "HardwareFunctional"},
#     "minotauro": { "backend": "192.168.100.201",
#               "frontend": "192.168.100.204",
#               "target_name": "QA",
#               "operation": "HardwareFunctional"},
# }
#
# params = {
#     'platform': 'android',
#     'binary': {'demo': False, 'admin': True},
#     'sign': {},
#     'melt': {}
# }


class CommandsDevice:
    """Commands_device requires the device object to be istantiated (not the device serial number)"""

    def __init__(self, device_object):
        self.device_object = device_object
        self.device_serialno = device_object.serialno
        #used for set variables
        self.client_context = {}

    # server_context = {}

    @staticmethod
    def _set_util(context_elements, context):
        for k, v in context_elements.items():
            context[k] = v

    @staticmethod
    def _get_util(context_element, context):
        key = context_element
        if key not in context:
            return "Key not found: %s" % context.keys()
        value = context[key]

        print "key: %s value: %s" % (key, value)
        return value

    # def get_server(context_element):
    #     return _get_util(context_element, server_context)

    # def set_server(context_elements):
    #     return _set_util(context_elements, server_context)

    # Used get_client because 'set' is a builin funciton
    def get_client(self, context_element):
        return self._get_util(context_element, self.client_context)

    # Used set_client because 'get' is a builin function
    def set_client(self, context_elements):
        return self._set_util(context_elements, self.client_context)

    def dev_is_rooted(self):
        packs = self.device_object.shell("pm list packages")
        if "com.noshufou.android.su" in packs or "eu.chainfire.supersu" in packs:
            print "the phone is rooted"
            return True
        return False

    # """
    #     build apk on given server with given configuration
    # """
    # def build_apk(kind, srv, factory):
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
    #     args.action = "pull"
    #     args.platform = "android"
    #     args.kind = kind
    #     args.backend = srv_params["backend"]
    #     args.frontend = srv_params["frontend"]
    #     args.platform_type = "mobile"
    #     args.operation = srv_params["operation"]
    #     args.param = params
    #     args.asset_dir = "assets"
    #
    #     # servono??
    #     args.blacklist = ""
    #     args.soldierlist = ""
    #     args.nointernetcheck = socket.gethostname()
    #     args.puppet = "rite"
    #     args.factory = factory
    #     args.server_side = False
    #
    #     build_common.connection.host = srv_params["backend"]
    #     #build.connection.user = "avmonitor"
    #     build_common.connection.passwd = "testriteP123"
    #
    #     results, success, errors = build.build(args, report)
    #     print "after build", results, success, errors
    #     return success
    #
    # def modify_json_app_name(app_name, to_json, from_json):
    #     #TODO: make a method to build ad hoc json, instead of this shit
    #     assert os.path.exists(from_json)
    #     config = open(from_json).read()
    #     config = re.sub(r'({"appname":")([^"]*)',r'\1%s' % app_name, config)
    #     config = config.replace('{"appname":".*"}', '{"appname":"%s"}' % app_name)
    #     f = open(to_json, "w")
    #     f.write(config)
    #     f.close()
    #
    #
    # def build_apk_ruby(rebuild=False, user="avmonitor", password="testriteP123", server="castore",
    #                    conf_json_filename="build.and.json", zipfilenamebackend="and.zip",
    #                    factory_id="RCS_0000002135", apk_path_and_filename='assets/autotest.default.apk'):
    #
    #     if rebuild:
    #         os.remove(apk_path_and_filename)
    #     if not os.path.exists(apk_path_and_filename):
    #         srv_params = servers[server]
    #         #factory_id e' l'ident della factory
    #         os.system(
    #             #'ruby assets/rcs-core.rb -u zenobatch -p castoreP123 -d rcs-castore -f RCS_0000002050 -b build.and.json -o and.zip'
    #             #Rite_Mobile->HardwareFunctional
    #             'ruby assets/rcs-core.rb -u %s -p %s -d %s -f %s -b %s -o %s' % (user, password, srv_params["backend"],
    #                                                                              factory_id, conf_json_filename,
    #                                                                              zipfilenamebackend))
    #         os.system('unzip -o  %s -d assets' % zipfilenamebackend)
    #         os.remove(zipfilenamebackend)
    #     if not os.path.exists(apk_path_and_filename):
    #         print "ERROR, cannot build apk"
    #         exit(0)
    #     return apk_path_and_filename
    #
    # """
    #     check evidences on server passed as "backend"
    # """
    #
    # def check_evidences(backend, type_ev, key=None, value=None, imei=None):
    # #    #backend = command.context["backend"]
    # #    try:
    #         build_common.connection.host = backend
    #         build_common.connection.user = "avmonitor"
    #         build_common.connection.passwd = "testriteP123"
    #         #success, ret = build.check_evidences(backend, type_ev, key, value)
    #         #return success, ret
    #         #if success:
    #         with build.connection() as client:
    #             instance_id, target_id = build.get_instance(client, imei)
    #             print "instance_id: ", instance_id
    #             if not instance_id:
    #                 print "instance not found"
    #                 return False, target_id
    #
    #             evidences = client.evidences(target_id, instance_id, "type", type_ev)
    #             if evidences:
    #                 return True, evidences
    #             return False, "No evidences found for that type"
    # #    except:
    # #        return False, "Error checking evidences"
    # #        else:
    # #            return False, "no evidences found at all"
    #
    #
    # def do_test():
    #     assert build_apk("silent","castore"), "Build failed. It have to be succeded."
    #     assert build_apk("silent","castoro") is False, "Build succeded. It have to dont be succeded."
    #
    #     print "all done"
    #
    # if __name__ == "__main__":
    #     do_test()

    # Nota: l'install installa anche l'eventuale configurazione definita nell'apk_dataloader.
    # La confiurazione puo' essere definita come singoli files o come zip (ma non entrambi i metodi)
    def install(self, apk_id):
        apk_instance = apk_dataLoader.get_apk(apk_id)
        apk_instance.install(self.device_serialno)

    #installa la configurazione (la quale puo' essere stata salvata con uno di 3 metodi diversi
    def install_configuration(self, apk_id):
        apk_instance = apk_dataLoader.get_apk(apk_id)
        apk_instance.install_configuration(self.device_object)

    #Nota: l'install installa anche l'eventuale configurazione definita nell'apk_dataloader.
    #La confiurazione puo' essere definita come singoli files o come zip (ma non entrambi i metodi)
    def install_agent(self):
        self.install('agent')

    #Nota: (per l'agente fa anche: rm -r /sdcard/.lost.found, rm -r /data/data/com.android.dvci),
    #anche nella modalita' in cui si esplicita l'apk_id
    def uninstall(self, apk_id):
        apk_instance = apk_dataLoader.get_apk(apk_id)
        apk_instance.clean(self.device_serialno)

    #Nota: (per l'agente fa anche: rm -r /sdcard/.lost.found, rm -r /data/data/com.android.dvci)
    def uninstall_agent(self):
        self.uninstall('agent', self.device_serialno)

    def backup_app_data(self, apk_id):
        apk_instance = apk_dataLoader.get_apk(apk_id)
        apk_instance.backup_app_data(self.device_serialno)

    def restore_app_data(self, apk_id):
        apk_instance = apk_dataLoader.get_apk(apk_id)
        apk_instance.restore_app_data(self.device_serialno)

    # Nota: attualmente segue sempre solo l'activity definita come starting activity nell'apk_dataloader.
    #           Implementare un'execute generica e' molto smplice ma tende a spargere in giro activity da lanciare...
    #           Piuttosto possiamo arricchire l'apk_dataloader con altre activity (gli AV ne hanno gia' una in piu'
    #           ma non viene usata)
    def execute(self, apk_id):
        apk_instance = apk_dataLoader.get_apk(apk_id)
        apk_instance.start_default_activity(self.device_serialno)

    def execute_agent(self):
        apk_instance = apk_dataLoader.get_apk('agent')
        apk_instance.start_default_activity(self.device_serialno)

    # Gestisce il wifi del dispositivo
    # Nota: Per imitare il funzionamento di INTERNET.py, accetta mode che indica la modalita'
    # mode: open is a net open to internet, av is open only to our servers, every other mode disables wifi
    def wifi(self, mode, check_connection=True):
        if mode == 'open':
            wifiutils.start_wifi_open_network(self.device_serialno, check_connection)
        elif mode == 'av':
            wifiutils.start_wifi_av_network(self.device_serialno, check_connection)
        else:
            wifiutils.disable_wifi_network(self.device_serialno)

    #this checks which wifi network is active and return the SSID
    def info_wifi_network(self):
        return wifiutils.info_wifi_network(self.device_serialno)

    #this tries to ping google's ip (173.194.35.114) twice and checks result
    def can_ping_google(self):
        ping_ok = wifiutils.ping_google(self.device_serialno)
        if ping_ok.strip() == "0":
            return True
        else:
            return False

    def check_su_permissions(self):
        return superuserutils.check_su_permissions(self.device_serialno)

    def check_infection(self):
        apk_instance = apk_dataLoader.get_apk('agent')
        result = adb.execute('pm list packages -3 '+apk_instance.package_name, self.device_serialno)
        print "Package = " + result
        if result.strip() == "package:" + apk_instance.package_name:
            return True
        else:
            return False

    def init_device(self, install_eicar=False):
        self.reset_device()

        #install everythings!

        #install ddf, if not root ERROR
        if not superuserutils.install_ddf_shell(self.device_serialno):
            exit()

        if install_eicar:
            #install eicar
            self.install('eicar')

        #install BusyBox
        adb.install_busybox('assets/busybox-android', self.device_serialno)

        wifiutils.install_wifi_enabler(self.device_serialno)

    def reset_device(self):
        #prima di tutto disattivo il wifi (questo installa anche il wifi manager)
        self.wifi('disable')

        #Clean all the things!
        self.uninstall_agent()
        self.uninstall('wifi_enabler')
        for av_to_delete in apk_dataLoader.get_av_list():
            self.uninstall(av_to_delete)
        self.uninstall('eicar')

        #uninstall BusyBox
        adb.uninstall_busybox(self.device_serialno)

        superuserutils.uninstall_ddf_shell(self.device_serialno)

    #updates project data, using new data from a physical device
    def update(self, apk_id):
        utils.get_config(self.device_serialno, apk_id)
        utils.get_apk(self.device_serialno, apk_id)

    def update_apk(self, apk_id):
        utils.get_apk(self.device_serialno, apk_id)

    #this gets a LIST of file. Remember it
    def pull(self, src_files, src_dir, dst_dir):
        for file_to_get in src_files:
            adb.get_remote_file(file_to_get, src_dir, dst_dir, True, self.device_serialno)

    #this puts a LIST of file. Remember it
    def push(self, src_files, src_dir, dst_dir):
        for file_to_put in src_files:
            adb.copy_file(src_dir + "/" + file_to_put, dst_dir, True, self.device_serialno)

