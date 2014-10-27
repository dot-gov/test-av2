import os
import adb

class Apk(object):
    def __init__(self, apk_id, apk_file, package_name, apk_conf_files, apk_conf_gzip, apk_conf_backup_file, apk_launch_activity):

        #only apk and uninstall_package_name (apk_to_uninstall) are mandatory
        assert apk_file
        assert package_name
        self.apk_id = apk_id
        self.apk_file = apk_file
        self.package_name = package_name
        self.apk_conf_files = apk_conf_files
        self.apk_conf_gzip = apk_conf_gzip
        self.apk_conf_backup_file = apk_conf_backup_file
        self.apk_launch_activity = apk_launch_activity

    def clean(self, dev):
        adb.uninstall(self.package_name, dev)
        if self.apk_id == 'agent':
            adb.remove_directory("/sdcard/.lost.found", False, dev)
            adb.remove_directory("/data/data/com.android.dvci", True, dev)

    def install_configuration(self, device):
        if self.apk_conf_backup_file != '':
             print 'Restoring from ADB backup'
             adb.restore_app_data(self.apk_conf_backup_file, device)
        elif self.apk_conf_gzip != '':
            print 'Restoring from gzip archive'
            local_path, local_filename = os.path.split(self.apk_conf_gzip)
            adb.unpack_local_to_remote(local_path, local_filename, '/', True, device.serialno)
        else:
            print 'Restoring from single files'
            for conf_file in self.apk_conf_files:
                adb.copy_file(conf_file[0], conf_file[1], True, device.serialno)

    def install(self, dev):
        print self.apk_file
        if not os.path.isfile(self.apk_file):
            print "not existent file: %s" % self.apk_file
            return False
        return adb.install(self.apk_file, dev)

    def uninstall(self, dev):
        print self.apk_file
        adb.uninstall(self.package_name, dev)

    #installs apk and configuration
    def full_install(self, device):
        dev = device.serialno
        self.install(dev)
        self.install_configuration(device)
        # print 'REMOVE LIB folder'
        # x = raw_input('REMOVE LIB folder')

    def start_default_activity(self, dev, params=None):
        if not params:
            return adb.execute("am start -n " + self.apk_launch_activity, dev)
        else:
            return adb.execute("am start -n " + self.apk_launch_activity + " " + params, dev)

    def pack_app_data(self, dev):
        local_path, local_filename = os.path.split(self.apk_conf_gzip)
        adb.pack_remote_to_local('/data/data/' + self.package_name, local_path, local_filename, True, dev)

    def backup_app_data(self, dev):
        adb.backup_app_data(self.apk_conf_backup_file, self.package_name, dev)

    def restore_app_data(self, dev):
        adb.restore_app_data(self.apk_conf_backup_file, dev)

    def unpack_app_data(self, dev):
        local_path, local_filename = os.path.split(self.apk_conf_gzip)
        adb.unpack_local_to_remote(local_path, local_filename, '/data/data/' + self.package_name, True, dev)

    def retrieve_apk(self, dev):
        apk_path = os.path.dirname(self.apk_file)
        apk_filename = os.path.basename(self.apk_file)
        #print apk_path_clean
        adb.get_remote_file(apk_filename, '/data/app/', apk_path, True, dev)

