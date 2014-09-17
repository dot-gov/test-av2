import collections
import datetime

from adbclient import AdbClient
from scripts.mobile.hardware import adb
from scripts.mobile.hardware.apk import apk_dataLoader


def get_deviceId(device):
    device = AdbClient(device.serialno)
    d_out = device.shell("dumpsys iphonesubinfo")
    lines = d_out.strip()
    devline = lines.split("\n")[2]
    dev_id = devline.split("=")[1].strip()
    return dev_id


def get_properties(device, av, *props):

    def get_property(device, prop_name):
        return device.getProperty(prop_name)

    res = {}
    for prop in props:
        if "." in prop:
            name = prop.split(".")[-1]
        else:
            name = prop
        res[name] = get_property(device, prop)
    print res

    dev_name = "%s %s" % (res["manufacturer"], res["model"])

    results = collections.OrderedDict()
    results['time'] = "%s" % datetime.datetime.now()
    results['device'] = dev_name
    results['antivirus'] = av
    results['id'] = get_deviceId(device)
    results['release'] = res["release"]
    results['selinux'] = res["enforce"]
    results['error'] = ""
    results["return"] = ""

    return results


def get_config(device, av):
    apk = apk_dataLoader.get_apk_av(av)

    adb.install_busybox('assets/busybox-android', device)
    apk.pack_app_data(device)
    adb.uninstall_busybox(device)


def get_apk(device, av):
    apk = apk_dataLoader.get_apk_av(av)
    apk.retrieve_apk(device)