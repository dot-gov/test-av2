__author__ = 'mlosito'
from RiteMobile.Android.apk.apk import Apk

class Antivirus_apk(Apk):
    def __init__(self, apk_id, apk, package_name, apk_conf_files, apk_conf_gzip, apk_conf_backup_file, apk_launch_activity, av_start_scan_activity):
        Apk.__init__(self, apk_id, apk, package_name, apk_conf_files, apk_conf_gzip, apk_conf_backup_file, apk_launch_activity)
        self.av_start_scan_activity = av_start_scan_activity
