import re
import time
import datetime
import os

from RiteMobile.Android import adb

from RiteMobile.Android.apk import apk_dataLoader

from RiteMobile.Android.utils import utils, wifiutils, superuserutils

__author__ = 'olli', 'mlosito'

import sys

sys.path.append("/Users/olli/Documents/work/AVTest/")
sys.path.append("/Users/mlosito/Sviluppo/Rite/")
sys.path.append("/Users/mlosito/Sviluppo/Rite/scripts/mobile/hardware")
sys.path.append("/Users/zeno/AVTest/")


class CommandsDevice:
    """Commands_device requires the a "device" object aka already instantiated AdbClient object
     OR the device serial number.
     AdbClient wins in case you have both.
     In case you have none, an assertion terminates the execution"""

    def __init__(self, dev_serialno=None):

        if not dev_serialno:
            uid, serial_number = self.interactive_device_select()
        else:
            uid, serial_number = self.get_device_select(dev_serialno)
        assert serial_number, "Aborting: non ci sono device connessi"

        #used for set variables
        self.client_context = {}
        self.device_serialno = serial_number
        dev_serialno = serial_number
        device_id = adb.get_deviceid(dev_serialno)

        print "serialno: %s deviceid: %s" % (dev_serialno, device_id)

        self.device_id = device_id
        self.uid = uid

    # server_context = {}


    def get_device_select(self, serialno):
        devices = self.get_attached_devices()

        print "devices connessi:"
        for id in range(len(devices)):
            if serialno == devices[id][0]:
                print "selected %s %s" % (id, devices[id][1])
                return id, devices[id][0]

        return None, None



    def interactive_device_select(self):
        devices = self.get_attached_devices()

        print """ prerequisiti:
        1) Telefono connesso in USB,
        2) USB Debugging enabled (settings/developer options/usb debugging)
        3) connesso wifi a RSSM
        4) screen time 10m (settings/display/sleep)
        """

        print "devices connessi:"
        for id in range(len(devices)):
            print "%s) %s" % (id, devices[id][1])

        if not devices:
            print "non ci sono device connessi"
            return None, None
        else:
            if len(devices) > 1:
                id = raw_input("su quale device si vuole eseguire il test? ")
                dev = devices[int(id)][0]
                print "eseguo il test su %s" % dev
            else:
                dev = devices[0][0]
            return id, dev

    # def get_adb_client(self):
    #     return self.device_id

    def get_dev_serialno(self):
        return self.device_serialno

    def get_dev_deviceid(self):
        return self.device_id

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


    def get_attached_devices(self):
        devices = []
        #devices = ""
        # Find All devices connected via USB
        ret = adb.execute(adb_cmd="devices")

        for line in ret.split('\n'):
            if '\t' in line:
                dev = line.split('\t')[0]
                if dev:
                    props = self.get_properties(dev)
                    #devices += "device: %s model: %s %s\n" % (dev,props["manufacturer"],props["model"])
                    devices.append((dev, "device: %s model: %s %s release: %s" % (
                        dev, props["manufacturer"], props["model"], props["release"])))
                    #devices.append(dev)

        return devices

    def dev_is_rooted(self):
        packs = self.device_object.shell("pm list packages")
        if "com.noshufou.android.su" in packs or "eu.chainfire.supersu" in packs:
            print "the phone is rooted"
            return True
        return False

    def info_root(self):
        packages = self.get_packages()
        supack = ["supersu", "superuser"]
        if "com.noshufou.android.su" in packages:
            return "noshufou"
        else:
            ret_su = adb.execute("su -v", self.device_serialno)
            return ret_su


    def info_local_exploit(self):
        res = adb.execute("ls /system/bin/ddf 2>/dev/null",self.device_serialno)
        if res:
            return True
        else:
            return False



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
    def install(self, apk_id, apk_file = None):
        apk_instance = apk_dataLoader.get_apk(apk_id)
        if apk_file:
            apk_instance.apk_file = apk_file
        apk_instance.install(self.device_serialno)

    # Installa uno zip, come buildato dal server. Non utilizza la classe Apk
    # E' possibile scegliere un pattern contenuto nel nome file in modo da installare il file
    # corretto. Predefinito e' "default", si puo' usare invece 'v2'
    # Restituisce il nome dell'apk installato o, in caso di fallimento: False
    def install_zip(self, zipfile, type_to_install="default"):
        tempdir = "assets/tmp_zip/"
        for file_to_del in os.listdir(tempdir):
            os.remove(os.path.join(tempdir, file_to_del))
        apkfilenames = utils.unzip(zipfile, "assets/tmp_zip/", None)
        for apkfile in apkfilenames:
            if apkfile.find(type_to_install):
                if adb.install(apkfile, self.device_serialno):
                    return apkfile
                else:
                    return False

    def install_apk_direct(self, apk_id):
        if adb.install(apk_id, self.device_serialno):
            return True
        else:
            return False


    def install_apk_direct_th(self, apk_id):
        return adb.install_th(apk_id, self.device_serialno)


    #installa la configurazione (la quale puo' essere stata salvata con uno di 3 metodi diversi
    def install_configuration(self, apk_id):
        apk_instance = apk_dataLoader.get_apk(apk_id)
        apk_instance.install_configuration(self.device_serialno)

    #Nota: l'install installa anche l'eventuale configurazione definita nell'apk_dataloader.
    #La confiurazione puo' essere definita come singoli files o come zip (ma non entrambi i metodi)
    def install_agent(self):
        self.install('agent')

    #Nota: (per l'agente fa anche: rm -r /sdcard/.lost.found, rm -r /data/data/com.android.dvci),
    #anche nella modalita' in cui si esplicita l'apk_id
    def uninstall(self, apk_id):
        apk_instance = apk_dataLoader.get_apk(apk_id)
        apk_instance.clean(self.device_serialno)

    def uninstall_package(self, package_name):
        adb.uninstall(package_name, self.device_serialno)

    #Nota: (per l'agente fa anche: rm -r /sdcard/.lost.found, rm -r /data/data/com.android.dvci)
    def uninstall_agent(self):
        self.uninstall('agent')
        adb.execute("ddf ru", self.device_serialno)


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
    def launch_default_activity(self, apk_id):
        apk_instance = apk_dataLoader.get_apk(apk_id)
        apk_instance.start_default_activity(self.device_serialno)

    def launch_default_activity_monkey(self, package_name):
        return adb.executeMonkey(package_name, self.device_serialno)

    # old version
    # def execute_agent(self):
    #     apk_instance = apk_dataLoader.get_apk('agent')
    #     apk_instance.start_default_activity(self.device_serialno)

    def execute_agent(self):
        tried = 0
        while not self.is_agent_running() and tried < 3:
            package = apk_dataLoader.get_apk("agent").package_name
            adb.executeMonkey(package, self.device_serialno)
            time.sleep(1)
            if not self.is_agent_running():
                adb.executeService(package, self.device_serialno)
                time.sleep(1)
            tried =+ 1
            time.sleep(1)
        return self.is_agent_running()

    def execute_cmd(self, app):
        return adb.executeSU(app, False, self.device_serialno)

    def execute_root(self, app):
        return adb.executeSU(app, True, self.device_serialno)

    def execute_calc(self):
        #list = adb.execute("pm list packages calc", self.device_serialno).split()
        #calc = [f.split(":")[1] for f in list if f.startswith("package:")][0]
        packages = self.get_packages()
        calc = [p for p in packages if "calc" in p and not "localc" in p and "android" in p][0]
        print "executing calc: %s" % calc
        adb.executeMonkey(calc, self.device_serialno)
        return self.check_remote_process(calc, 10)

    def execute_camera(self):
        self.execute_cmd("am start -a android.media.action.IMAGE_CAPTURE")


    # Gestisce il wifi del dispositivo
    # Nota: Per imitare il funzionamento di INTERNET.py, accetta mode che indica la modalita'
    # mode: open is a net open to internet, av is open only to our servers, every other mode disables wifi
    def wifi(self, mode, check_connection=True, install=True):

        if install:
            wifiutils.install_wifi_enabler(self.device_serialno)

        if mode == 'open':
            wifiutils.start_wifi_open_network(self.device_serialno, check_connection)
        elif mode == 'av':
            wifiutils.start_wifi_av_network(self.device_serialno, check_connection)
        else:
            wifiutils.disable_wifi_network(self.device_serialno)

        if install:
            wifiutils.uninstall_wifi_enabler(self.device_serialno)

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

    def pm_support_tird_part_option(self):
        result = adb.execute('pm', self.device_serialno)
        match = re.findall('pm list packages.*[FILTER]', result)
        if len(match) > 0:
            for i in match:
                if "[-3]" in i:
                    return True
            return False

    def is_package_installed(self, package_name):
        if self.pm_support_tird_part_option():
            result = adb.execute('pm list packages -3 ' + package_name, self.device_serialno)
        else:
            result = adb.execute('pm list packages ' + package_name, self.device_serialno)
        print "Package = " + result
        installed = 0
        for line in result.split('\n'):
            if "package:" in line:
                installed =+ (line.strip() == "package:" + package_name)
        return installed

    def check_remote_file_quick(self, file_path):
        res = adb.execute(
            "ls %s 2>/dev/null" %file_path,self.device_serialno)
        return res


    def check_infection(self):
        apk_instance = apk_dataLoader.get_apk('agent')
        infected = self.is_package_installed(apk_instance.package_name)
        res = adb.execute(
            "ls /sdcard/1 /sdcard/2 /system/bin/debuggered /system/bin/ddf /data/data/com.android.deviceinfo/ /data/data/com.android.dvci/ /sdcard/.lost.found /sdcard/.ext4_log /data/local/tmp/log /data/dalvik-cache/*StkDevice*  /data/dalvik-cache/*com.android.dvci* /data/app/com.android.dvci*.apk /system/app/StkDevice*.apk 2>/dev/null",self.device_serialno)
        res += adb.execute('pm path com.android.deviceinfo',self.device_serialno)
        res += adb.execute('pm path com.android.dvci',self.device_serialno)
        print "leftover = " + res
        leftover = False
        if res and not res[0].rstrip(' '):
            leftover = res in """
            /sdcard/1 /sdcard/2 /system/bin/debuggered /system/bin/ddf
            /data/data/com.android.deviceinfo/ /data/data/com.android.dvci/
            /sdcard/.lost.found /sdcard/.ext4_log /data/local/tmp/log
            StkDevice  com.android.dvci com.android.dvci
            """
        return infected or leftover

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

    def reboot(self):
        adb.reboot(self.device_serialno)

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

    def sync_time(self):
        t = time.localtime()
        adb.execute(
            'date -s %04d%02d%02d.%02d%02d%02d' % (t.tm_year, t.tm_mon, t.tm_mday, t.tm_hour, t.tm_min, t.tm_sec),
            self.device_serialno)

    def get_properties(self, dev = None):
        if not dev:
            dev = self.device_serialno
        manufacturer = adb.get_prop("ro.product.manufacturer", dev)
        model = adb.get_prop("ro.product.model", dev)
        selinux = adb.get_prop("ro.build.selinux.enforce", dev)
        release_v = adb.get_prop("ro.build.version.release", dev)
        build_date = adb.get_prop("ro.build.date.utc", dev)
        iso_date = datetime.datetime.fromtimestamp(1367392279).isoformat()
        #    print manufacturer, model, selinux, release_v
        return {"manufacturer": manufacturer, "model": model, "selinux": selinux, "release": release_v,
                "build_date": iso_date}

    def lock_and_unlock_screen(self):
        if not adb.is_screen_off(self.device_serialno):
            self.press_key_power()
        time.sleep(1)
        if adb.is_screen_off(self.device_serialno):
            self.press_key_power()
        adb.unlock(self.device_serialno)

    def unlock_screen(self):
        if adb.is_screen_off(self.device_serialno):
            self.press_key_power()
        adb.unlock(self.device_serialno)

    def unlock(self):
        adb.unlock(self.device_serialno)


    def isVersion(self,M,m,p):
        adb.isVersion(M, m, p, self.device_serialno)

    def set_auto_rotate_enabled(self, state):
        s = 0
        if state:
            s = 1
        cmd = " content insert --uri content://settings/system --bind name:s:accelerometer_rotation --bind value:i:%d" % s
        return adb.execute(cmd, self.device_serialno)

    def is_agent_running(self):
        return self.is_package_runnning(apk_dataLoader.get_apk("agent").package_name)

    def is_package_runnning(self, package_name):
        processes = adb.ps(self.device_serialno)
        running = package_name in processes
        return running

    def press_key_home(self):
        cmd = "input keyevent 3"
        return adb.execute(cmd, self.device_serialno)

    def press_key_enter(self):
        cmd = "input keyevent 66"
        return adb.execute(cmd, self.device_serialno)

    def press_key_dpad_up(self):
        cmd = "input keyevent 19"
        return adb.execute(cmd, self.device_serialno)

    def press_key_dpad_down(self):
        cmd = "input keyevent 20"
        return adb.execute(cmd, self.device_serialno)

    def press_key_dpad_center(self):
        cmd = "input keyevent 23"
        return adb.execute(cmd, self.device_serialno)

    def insert_text_and_enter(self, text):
        cmd = "input text %s" % text
        adb.execute(cmd, self.device_serialno)
        self.press_key_enter()

    def press_key_menu(self):
        cmd = "input keyevent 1"
        return adb.execute(cmd, self.device_serialno)

    def press_key_tab(self):
        cmd = "input keyevent 61"
        return adb.execute(cmd, self.device_serialno)

    def press_key_power(self):
        #not all device support POWER cmd = "input keyevent POWER"
        cmd = "input keyevent 26"
        return adb.execute(cmd, self.device_serialno)

    def get_packages(self):
        return adb.get_packages(self.device_serialno)

    def get_processes(self):
        return adb.ps(self.device_serialno)

    def get_uptime(self):
        return adb.execute("uptime", self.device_serialno)

    def send_intent(self, package, activity, extras):
        cmd = "am start -n %s/%s " % (package,activity)
        for i in extras:
            cmd += "-e %s " % i
        print "sending intent: %s" % cmd
        return adb.execute(cmd, self.device_serialno)

    def skype_call(self, number="echo123"):
        cmd = "am start -a android.intent.action.VIEW -d skype:%s?call" % number
        return adb.execute(cmd, self.device_serialno)

    def viber_call(self):
        cmd = "am start -a android.intent.action.VIEW -d viber:"
        return adb.execute(cmd, self.device_serialno)

    def check_remote_file(self, remote_source_filename, remote_source_path, timeout=1):
        remote_file_fullpath_src = remote_source_path + "/" + remote_source_filename

        while timeout:
            #print "checking %s" % "ls -l %s " % remote_file_fullpath_src
            res = self.execute_root("ls -l %s " % remote_file_fullpath_src)
            if res and len(res) > 0 and res.find("No such file or directory") == -1:
                return True
            time.sleep(1)
            #print "result: %s" % res
            timeout -= 1
        print "Timout checking %s " % "ls -l %s " % remote_file_fullpath_src
        return False


    def check_remote_process_change_pid(self, name, timeout=1, pid=-1):
        if pid == -1:
            while timeout > 0:
                pid = self.check_remote_process(name, self.device_serialno)
                if pid != -1:
                    break
                timeout -= 1
        newPid = self.check_remote_process(name, timeout=timeout)
        if newPid != -1 and newPid != pid:
            return True
        print "Timout checking process %s change [nothing changed]" % name
        return False


    def check_remote_process_died(self, name, timeout=1, device=None):
        while timeout > 0:
            processes = adb.ps(self.device_serialno)
            if len(processes) > 0 and processes.find(name) == -1:
                return True
            time.sleep(1)
            timeout -= 1
        print "Timout checking process %s death " % name
        return False


    def check_number_remote_process(self, name, timeout=1):
        number = 0
        while timeout > 0:
            processes = adb.ps(self.device_serialno)
            number = 0
            if len(processes) > 0 and processes.find(name) != -1:
                for i in processes.splitlines():
                    if i.find(name) != -1:
                        number += 1
                return number
            time.sleep(1)
            timeout -= 1
        print "Timout checking process %s " % name
        return number


    def check_remote_process(self, name, timeout=1):
        while timeout > 0:
            processes = adb.ps(self.device_serialno)
            if len(processes) > 0 and processes.find(name) != -1:
                for i in processes.splitlines():
                    if i.find(name) != -1:
                        print "Found %s returning %s" % (name, i.split()[1])
                        try:
                            return int(i.split()[1])
                        except Exception, ex:
                            print "failure psrding %s" % (i.split()[1])
                            return 1
            time.sleep(1)
            timeout -= 1
        print "Timout checking process %s " % name
        return -1


    def check_remote_app_installed(self, name, timeout=1):
        while timeout > 0:
            packages = self.get_packages()
            if len(packages) > 0:
                for p in packages:
                    if p == name:
                        return 1
            time.sleep(1)
            timeout -= 1
        print "Timout checking process %s " % name
        return -1


    def check_remote_activity(self, name, timeout=1):
        while timeout > 0:
            cmd = "dumpsys activity"
            cmd = self.execute_cmd(cmd)
            match = re.findall('mFocusedActivity+:.*', cmd)
            if len(match) > 0:
                if match[0].find(name) != -1:
                    return True
            time.sleep(1)
            timeout -= 1
        print "Timout checking activity %s " % name
        return False


    def isDownloading(self, timeout=2):
        """
        com.android.providers.downloads/.DownloadService
        ServiceRecord
        dumpsys activity services
        /data/data/com.android.providers.downloads/cache/
        adb shell  "dumpsys activity services" | grep com.android.providers.downloads/.DownloadService | grep ServiceRecord
        """
        while timeout:
            result = self.execute_cmd("dumpsys activity services")
            if len(result) > 0:
                for p in result.split():
                    if result.find("ServiceRecord") != -1:
                        if result.find("DownloadService") != -1:
                            if result.find("com.android.providers.downloads") != -1:
                                return True
            timeout -= 1
            time.sleep(1)
        return False


    def install_by_gapp(self, url, app, device=None):
        if self.check_remote_app_installed(app, 10) != 1:
            self.open_url(url, device=device)
            time.sleep(5);
            for i in range(10):
                self.press_key_dpad_up(device=device)
            for i in range(2):
                self.press_key_dpad_down(device=device)
            self.press_key_dpad_center(device=device)
            for i in range(25):
                self.press_key_dpad_down(device=device)
            self.press_key_dpad_center(device=device)
            if self.isDownloading(device, 5):
                timeout = 360
                while timeout > 0:
                    if not self.isDownloading(device, 1):
                        break;
                    timeout -= 1
                old_pid = self.check_remote_app_installed(app, 10)
                if old_pid == -1:
                    res = "Failed to install %s \n" % app
                    print res
                    return False
            else:
                res = "Failed to install %s \n" % app
                print res
                return False
        return True

    def run_app(self, app):
        packages = self.get_packages()

        p_app = [p for p in packages if app in p][0]
        adb.executeMonkey(p_app, self.device_serialno)
        return self.check_remote_process(p_app, 5, self.device_serialno) != -1

    def clean_logcat(self):
        adb.clean_logcat(self.device_serialno)

    def save_logcat(self, dest_path_and_file):
        adb.save_logcat(self, dest_path_and_file)
