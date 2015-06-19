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

class SpecificTestFunctionalBase:
    __metaclass__ = ABCMeta

    service = 'com.android.dvci'

    @abstractmethod
    def test_device(self, args, command_dev, c, results):
        pass

    @abstractmethod
    def final_assertions(self, results):
        return True

    @abstractmethod
    def get_name(self):
        return "common"

    def want_demo(self):
        return True

    def want_persist(self):
        return True

    def want_admin(self):
        return True

    def melting_app(self):
        return ""

    def get_config(self):
        return open('assets/config_mobile_%s.json' % self.get_name()).read()

    def get_params(self):
        params = {u'binary': {u'admin': self.want_admin(), u'demo': self.want_demo(),
                              u'persist': self.want_persist()},
                  u'melt': {u'appname': u'autotest'},
                  u'package': {u'type': u'installation'},
                  u'platform': u'android'}
        return params

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
        print "check_evidences %s" % type
        kinds = c.kinds()
        if type in kinds.keys():
            print "Present"
            return True
        else:
            print "Not present"
            return False


    def check_evidences(self, command_dev, c, results, timestamp=""):
        time.sleep(60)
        #evidences, kinds = c.evidences()
        stat = c.kinds()

        print "stat: ", stat

        ev = "\n"
        ok = stat.keys()
        ok.sort()

        programs = {}

        for k in ok:
            ev += "\t\t%s: %s\n" % (k, stat[k])
            if k in ["chat", "addressbook", "call"]:
                program = [e['data']['program'] for e in c.evidences(k)]
                chat = set(program)
                programs[k]=[]
                for t in chat:
                    programs[k].append(t)
                    ev += "\t\t\t%s\n" % (t)

        #counter = collections.Counter([ e['type'] for e in evidences ])
        results['evidences' + timestamp] = ev
        results['evidence_programs' + timestamp] = programs
        results['evidence_stat' + timestamp] = stat
        results['evidence_types' + timestamp] = stat.keys()

        results['uptime' + timestamp] = command_dev.get_uptime()
