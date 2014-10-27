import collections
import datetime

from scripts.mobile.hardware import adb
from scripts.mobile.hardware.apk import apk_dataLoader


def get_config(device, av):
    apk = apk_dataLoader.get_apk_av(av)

    adb.install_busybox('assets/busybox-android', device)
    apk.pack_app_data(device)
    adb.uninstall_busybox(device)


def get_apk(device, av):
    apk = apk_dataLoader.get_apk_av(av)
    apk.retrieve_apk(device)