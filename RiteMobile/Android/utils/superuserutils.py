from RiteMobile.Android import adb

__author__ = 'mlosito'


def check_su_permissions(devSerialnumber):
        check_su = adb.executeSU('id', True, devSerialnumber)
        print check_su
        if check_su.startswith('uid=0'):
            return True
        else:
            return False


def install_ddf_shell(devSerialnumber):

        #trying method 1
        #installs (to tmp) necessary files for root (rilcap shell installing)
        adb.copy_tmp_file("avassets/android_exploit/suidext", devSerialnumber)
        #installs RILCAP /data/local/tmp/in/local_exploit "/data/local/tmp/in/suidext rt"
        adb.call('shell /system/bin/su -c "/data/local/tmp/in/suidext rt"', devSerialnumber)
        #remove temp files
        adb.remove_temp_file('suidext', device=devSerialnumber)
        #checks if root
        if (check_su_permissions(devSerialnumber)):
            return True

        #trying method 2
        #installs (to tmp) necessary files for root (rilcap shell installing)
        adb.copy_tmp_file("avassets/android_exploit/local_exploit", devSerialnumber)
        adb.copy_tmp_file("avassets/android_exploit/suidext", devSerialnumber)
        #installs RILCAP /data/local/tmp/in/local_exploit "/data/local/tmp/in/suidext rt"
        adb.call('shell /data/local/tmp/in/local_exploit "/data/local/tmp/in/suidext rt"', devSerialnumber)
        #remove temp files
        adb.remove_temp_file('local_exploit', device=devSerialnumber)
        adb.remove_temp_file('suidext', device=devSerialnumber)

        #checks if root
        if (check_su_permissions(devSerialnumber)):
            return True

        #trying method 3
        #installs SUIDEXT shell
        #installs (to tmp) necessary files for root (rilcap shell installing)
        adb.copy_tmp_file("avassets/android_exploit/selinux_exploit", devSerialnumber)
        adb.copy_tmp_file("avassets/android_exploit/selinux_suidext", devSerialnumber)
        #installs RILCAP
        adb.call('shell /data/local/tmp/in/selinux_exploit "selinux_suidext rt"', devSerialnumber)
        #cleanup
        adb.remove_temp_file('selinux_exploit', device=devSerialnumber)
        adb.remove_temp_file('selinux_suidext', device=devSerialnumber)

        if (check_su_permissions(devSerialnumber)):
            return True
        else:
            assert False


def uninstall_ddf_shell(devSerialnumber):
    #uninstalls RILCAP - adb shell rilcap ru
    adb.call('shell rilcap ru', devSerialnumber)

