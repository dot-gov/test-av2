__author__ = 'mlosito'

from androguard.core.bytecodes import apk


def get_package_from_apk(apk_file):
    a = apk.APK(apk_file)
    return a.get_package()