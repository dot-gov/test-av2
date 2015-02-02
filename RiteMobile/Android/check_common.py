import time
import csv
import os
import traceback
import collections
import datetime
import argparse
import inspect
import sys
from abc import ABCMeta
from abc import abstractmethod

class Check:
    __metaclass__ = ABCMeta

    service = 'com.android.dvci'

    @abstractmethod
    def test_device(self, args, command_dev, c, results):
        pass

    @abstractmethod
    def final_assertions(self, results):
        return True

    def check_install(self, command_dev, results):
        still_infected = False
        if command_dev.check_infection():
            print "Manual uninstall required !!! Clean the phone !!!"
            return False
            # command_dev.uninstall_agent()

            still_infected = command_dev.check_infection()

        if still_infected:
            print "Error, still installed"
            return False

        results["packages_remained"] = still_infected
        return True


    def check_uninstall(self, commands_device, results, reboot=True):
        if reboot:
            print ".... reboot"
            commands_device.reboot()
            time.sleep(60)

        processes = commands_device.get_processes()
        running = "still running: %s" % self.service in processes
        results['running'] = running

        res = commands_device.execute_cmd(
            "ls /sdcard/1 /sdcard/2 /system/bin/debuggered /system/bin/ddf /data/data/com.android.deviceinfo/ /data/data/com.android.dvci/ /sdcard/.lost.found /sdcard/.ext4_log /data/local/tmp/log /data/dalvik-cache/*StkDevice*  /data/dalvik-cache/*com.android.dvci* /data/app/com.android.dvci*.apk /system/app/StkDevice*.apk 2>/dev/null")
        results["files_remained"] = res

        # res = adb.executeSU('cat /data/system/packages.list  | grep -i -e "dvci" -e "deviceinfo" -e "StkDevice"')
        # res += adb.executeSU('cat /data/system/packages.xml  | grep -i -e "dvci" -e "device" -e "StkDevice"')
        res = commands_device.execute_cmd('pm path com.android.deviceinfo')
        res += commands_device.execute_cmd('pm path com.android.dvci')

        results["packages_remained"] = res


    def check_evidences_present(self, c, type):
        print "... check_evidences %s" % type
        evidences, kinds = c.evidences()
        if type in kinds.keys():
            print "Present"
            return True
        else:
            print "Not present"
            return False


    def check_evidences(self, command_dev, c, results, timestamp=""):
        print "... check_evidences"
        time.sleep(60)
        evidences, kinds = c.evidences()

        for k in ["call", "chat", "camera", "application", "mic"]:
            if k not in kinds.keys():
                kinds[k] = []

        ev = "\n"
        ok = kinds.keys()
        ok.sort()
        for k in ok:
            ev += "\t\t%s: %s\n" % (k, len(kinds[k]))
            if k in ["chat", "addressbook", "call"]:
                program = [e['data']['program'] for e in evidences if e['type'] == k]
                chat = set(program)
                for c in chat:
                    ev += "\t\t\t%s\n" % (c)

        results['evidences' + timestamp] = ev
        results['evidence_types' + timestamp] = kinds.keys()

        results['uptime' + timestamp] = command_dev.get_uptime()
