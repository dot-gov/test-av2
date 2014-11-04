import zipfile
import os

from RiteMobile.Android import adb
from RiteMobile.Android.apk import apk_dataLoader


def get_config(device, av):
    apk = apk_dataLoader.get_apk_av(av)

    adb.install_busybox('assets/busybox-android', device)
    apk.pack_app_data(device)
    adb.uninstall_busybox(device)


def get_apk(device, av):
    apk = apk_dataLoader.get_apk_av(av)
    apk.retrieve_apk(device)


#this was duplicated from AVCommon/utils
def unzip(filename, fdir, logging_function=None):
    zfile = zipfile.ZipFile(filename)
    names = []
    for name in zfile.namelist():
        if os.path.exists(name):
            os.remove(name)
        (dirname, filename) = os.path.split(name)
        if logging_function:
            logging_function("- Decompress: %s / %s" % (fdir, filename))
        else:
            print("- Decompress: %s / %s" % (fdir, filename))
        zfile.extract(name, fdir)
        names.append(os.path.join(fdir, name))
    return names