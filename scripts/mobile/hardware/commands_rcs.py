__author__ = 'zeno'
import sys, time
import csv
import os
import inspect
import traceback
import collections
import datetime
import adb
import argparse
import commands
from scripts.mobile.hardware.utils import wifiutils

import package
from AVCommon.logger import logging
from AVAgent.rcs_client import Rcs_client


from AVCommon import build_common as build

class CommandsRCS:

    def __init__(self, host, device_id, login_id = "0", login = "avtest", password = "avtest", operation = "Rite_Mobile", target_name = "HardwareFunctional", factory = 'RCS_0000002050'):
        self.host = host
        self.login = login
        self.password = password
        self.device_id = device_id
        self.login_id = login_id

        assert device_id
        assert len(device_id) >= 8

        build.connection.host = host
        build.connection.user = login
        build.connection.passwd = password

        self.set_factory(operation, target_name, factory)

        pass

    def create_login(self, id = 0):
        login = "qa_android_test_%s" % id
        build.create_user(login)
        build.connection.user = login
        return login

    def set_factory(self, operation = "Rite_Mobile", target_name = "HardwareFunctional", factory = 'RCS_0000002050'):
        self.operation = operation
        self.target_name = target_name
        self.factory = factory

    def __enter__(self):
        print "Connecting to %s @ %s : %s" % (build.connection.user, build.connection.host, build.connection.operation)
        self.create_login(self.login_id)
        logging.debug("DBG login %s@%s" % (build.connection.user, build.connection.host))
        assert build.connection.host
        self.conn = Rcs_client(build.connection.host, build.connection.user, build.connection.passwd)
        self.conn.login()

        self.operation_id, self.group_id = self.conn.operation(self.operation)
        self.target_id = self.conn.targets(self.operation_id, self.target_name)[0]

        return self

    def __exit__(self, type, value, traceback):
        logging.debug("DBG logout")
        self.conn.logout()

    def delete_old_instance(self):
        instances = self.conn.instances_by_factory(self.device_id, self.factory)
        if not instances:
            print "no previous instances"
        assert len(instances) <= 1, "too many instances: %s" % instances ;
        for i in instances:
            print "... deleted old instance"
            self.conn.instance_delete(i["_id"])
        time.sleep(5)
        self.instances = self.conn.instances_by_factory(self.device_id, self.factory)
        assert not self.instances
        return self.instances

    def wait_for_sync(self):
        print "... sleeping for sync"
        time.sleep(60)
        for i in range(10):
            # print "operation: %s, %s" % (operation_id, group_id)
            instances = self.conn.instances_by_factory(self.device_id, self.factory)
            if not instances:
                print "... waiting for sync"
                time.sleep(10)
            else:
                break
        assert len(instances) == 1
        self.instance_id = instances[0]['_id']
        self.stat = instances[0]['stat']
        self.last_sync = self.stat['last_sync']
        # print "instance_id: %s " % instance_id

        self.wait_for_start()
        print "sync: OK"
        return self.instance_id

    def wait_for_next_sync(self, last_sync = 0):
        print "... wait for next sync"
        if not last_sync:
            last_sync = self.last_sync

        for i in range(18):
            # print "operation: %s, %s" % (operation_id, group_id)
            instances = self.conn.instances_by_factory(self.device_id, self.factory)
            if not instances:
                print "... waiting for sync"
                time.sleep(10)
            else:
                self.stat = instances[0]['stat']
                sync = instances[0]['stat']['last_sync']
                if sync > last_sync:
                    print "... new sync: %s" % sync
                    self.last_sync = sync
                    return True

        print "... no new sync"
        return False


    def rename_instance(self, device_info):
        info = self.conn.instance_info(self.instance_id)
        self.conn.instance_rename(self.instance_id, info['name'] + " " + device_info)
        info = self.conn.instance_info(self.instance_id)
        print "instance name: %s" % info['name']
        return info['name']

    def wait_for_start(self, starts = 1):
        info_evidences = []
        counter = 0
        while not info_evidences and counter < 10:
            infos = self.conn.infos(self.target_id, self.instance_id)
            info_evidences = [ (e['data']['content'],e['da']) for e in infos if 'Started' in e['data']['content']]
            counter += 1
            if len(info_evidences) < starts:
                print "... waiting for info Started: %s/%s" % (len(info_evidences), starts)
                time.sleep(10)
            else:
                print "... got Started: %s/%s" % (len(info_evidences), starts)
                self.last_start = info_evidences[-1][1]

    def check_root(self):
        # check root
        info_evidences = []
        counter = 0
        result = False
        root = ""
        info = 0
        if not self.last_start:
            self.wait_start()

        while not info_evidences and counter < 10:
            infos = self.conn.infos(self.target_id, self.instance_id)
            info_evidences = [e['data']['content'] for e in infos if 'Root' in e['data']['content'] and e['da'] > self.last_start]
            counter += 1
            if not info_evidences or not 'Root' in info_evidences[-1]:
                print "... waiting for info Root: %s" % info_evidences
                time.sleep(10)

        # print "info_evidences: %s: " % info_evidences
        if not info_evidences:
            root = 'No'
            print "No Root"
        else:
            print "root: OK"

            info = len(info_evidences) > 0
            root_method = info_evidences[0]
            root = root_method
            roots = [r for r in info_evidences if 'previous' not in r]
            # print "roots: %s " % roots
            assert len(roots) >= 1
        return True, root, info


    def evidences(self):
        evidences = self.conn.evidences(self.target_id, self.instance_id)
        kinds = {}
        for e in evidences:
            t = e['type']
            if not t in kinds.keys():
                kinds[t] = []
            kinds[t].append(e)

        return evidences, kinds

    def infos(self, keyword = ''):
        infos = self.conn.infos(self.target_id, self.instance_id)
        return [e['data']['content'] for e in infos if keyword in e['data']['content']]

    def uninstall(self):
        self.conn.instance_close(self.instance_id);
        ret = self.wait_for_next_sync()
        assert ret