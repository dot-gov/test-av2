__author__ = 'fabrizio'

import os
from AVCommon.logger import logging
from AVCommon import logger
from AVCommon import helper
import pickle
import yaml
import time
import random
import uuid
import ast
import shutil
from AVCommon import package
from AVCommon import config
from AVCommon import command
from collections import OrderedDict
from AVCommon.helper import red

report = None
from AVCommon.singleton import Singleton

@Singleton
class Report:
    def init(self, o):
        self.c_sent = o.c_sent
        self.c_received = o.c_received

        self.test_id = o.test_id
        self.timestamp = o.timestamp

        self.reports = o.reports
        self.current_procedure = o.current_procedure
        self.procedures = o.procedures
        self.name = o.name

    def __init__(self):
        # key is av, value is a command
        self.c_sent = OrderedDict()
        # key is av, value is a command list
        self.c_received = OrderedDict()

        # unique id
        self.test_id = str(uuid.uuid1())

        self.timestamp = time.strftime("%y%m%d-%H%M%S", time.localtime(time.time()))

        #self.timestamp = int(time.time())

        # proc is the key
        self.reports = {}

        # vm is the key, represents the current REPORT_KIND
        self.current_procedure = {}

        # list of all the REPORT_KIND
        self.procedures = []
        self.name = ""


def init(name):
    report = Report()
    report.name = name

def clean():
    Report().__init__()

def end(vm):
    report = Report()
    logging.debug("setting end to %s" % vm)
    set_procedure(vm, None)
    dump()

def mail_summary(mail_recipients, mail_server = "mail.hackingteam.com"):

    logging.info("sending mail to %s" % mail_recipients)
    # Import smtplib for the actual sending function
    import smtplib

    # Import the email modules we'll need
    from email.mime.text import MIMEText

    report = Report()
    # Open a plain text file for reading.  For this example, assume that
    # the text file contains only ASCII characters.

    sum = summary()
    # Create a text/plain message
    for recipient in mail_recipients:
        msg = MIMEText(sum)
        # me == the sender's email address
        # you == the recipient's email address
        hostname = helper.get_hostname()

        msg['Subject'] = '%s@%s: %s' % (report.name, hostname, report.timestamp)
        msg['From'] = "avtest@hackingteam.com"
        msg['To'] = recipient

        logging.debug("    msg to: %s" % msg['To'])
        # Send the message via our own SMTP server, but don't include the
        # envelope header.
        s = smtplib.SMTP(mail_server)
        s.sendmail(msg['From'], [msg['To']], msg.as_string())
        s.quit()

def finish():
    logging.debug("report finish")
    #dump_yaml()

    report = Report()
    create_report_for_analyzer(report)

    logging.debug("context: %s" % command.context)
    mail_recipients = command.context.get("mail_recipients", [])
    if mail_recipients:
        mail_summary(mail_recipients)

def set_procedure(vm, proc_name):
    report = Report()

    assert vm in report.c_received, "%s not in %s" % (vm, report.c_received)

    if vm in report.current_procedure.keys():
        proc = report.current_procedure[vm]

        # qui si deve salvare il record: t_id = report.test_id, name = vm,  kind = proc, result = res

    report.current_procedure[vm] = proc_name
    assert vm in report.current_procedure.keys(), "%s not in %s" % (vm, report.current_procedure.keys())

def summary():
    report = Report()
    report.vm = {}

    hostname = helper.get_hostname()

    summary_header = "SUMMARY @%s \n-- %s --\n %s\n" % (hostname, report.name, report.timestamp)
    summary = "\n"
    failed = OrderedDict()
    failed_kind = OrderedDict()
    important_commands = [] # ["BUILD", "CHECK_STATIC"]
    for vm in report.c_received.keys():
        report.vm[vm] = []
        current_proc = None
        summary += "\n[ %s ]\n" % vm
        one_report = False
        for cmd in report.c_received[vm]:
            #cmd = Cmd(c)
            if cmd.name == "REPORT_KIND_END":
                current_proc, report_args = cmd.args
                report.vm[vm].append(current_proc)
                success = "SUCCESS" if cmd.success else "FAILED"
                if not cmd.success:
                    if vm not in failed:
                        failed[vm] = []
                    if  current_proc not in failed_kind:
                        failed_kind[current_proc] = []
                    failed_kind[current_proc].append(vm)
                    failed[vm].append(current_proc)
                summary += "    %s: %s\n" % (current_proc, success)
                one_report = True
            else:
                if current_proc:
                    if cmd.success == False:
                        summary+="        %s\n" % (str(cmd))
                    elif cmd.name in important_commands and cmd.success:
                        #check = ['+ ERROR','+ FAILED']
                        #errors = any([ s in c for s in check ])
                        #if errors:
                        summary+="        %s\n" % (red(str(cmd), 80))
        if not one_report:
            if vm not in failed:
                failed[vm] = []
            failed[vm].append("NO REPORT")

    if failed:
        fail_err = "\nFAILED VM:\n"
        for vm, err in failed.items():
            fail_err += "%s %s\n" % (vm, err)
        summary = fail_err + summary

    if failed_kind:
        fail_err = "\nFAILED KIND:\n"
        for kind, err in failed_kind.items():
            fail_err += "%s %s\n" % (kind, err)
        summary = fail_err + summary
        append_retest(failed_kind)

    return summary_header + summary

def append_retest(failed_kind):
    try:
        retest = "/home/avmonitor/Rite/rite_retest.sh"
        logging.debug("saving retest: %s" % retest)
        f = open(retest, "w+")
        f.write("#!/bin/sh\ncd ~/Rite/AVMaster\n")
        for kind, err in failed_kind.items():
            sys = kind.replace("VM_","SYSTEM_")
            l = ",".join(err)
            f.write("python main.py -r %s -m %s -c $*\n" % (sys, l))
        f.close()
    except:
        logging.exception("cannot save rite_retest.sh")

# arriva pulito
# report si ricorda di un solo comando, per ogni av
# c_sent e' un comando
def sent(av, cmd):
    report = Report()

    assert isinstance( av, basestring)
    assert isinstance( cmd, command.Command), "type: %s" % type(cmd)

    if config.verbose:
        logging.debug("sent (%s): %s (%s)" % (report.current_procedure.get(av,""), av, cmd))
    report.c_sent[av] = cmd
    dump()

# arriva pulito
# report si ricorda tutti i comandi ricevuti
# c_received e' una lista di comandi
def received(av, cmd):
    report = Report()

    assert isinstance( av, basestring)
    assert isinstance( cmd, command.Command), "type: %s" % type(cmd)

    if config.verbose:
        logging.debug("received (%s): %s (%s)" % (report.current_procedure.get(av,""), av, cmd))
    if av not in report.c_received.keys():
        report.c_received[av] = []
    report.c_received[av].append(cmd)
    #db_save(test_id, proc, av, command)
    dump()

def dump_yaml():
    report = Report()

    f=open("%s/report.%s.%s.yaml" % (logger.logdir, report.timestamp, report.name), "w+")
    f.write(yaml.dump(report, default_flow_style=False, indent=4))
    f.close()


# genera un report.log e un summary log
def create_report_for_analyzer(report):

    report_for_analyzer_name = "%s/report_for_analyzer.%s.%s.yaml" % (logger.logdir, report.timestamp, report.name)
    # also create a last run log file in /home/avmonitor/last_log/
    lastlog_dir = os.path.join(package.basedir, "lastlog")
    # if not os.path.exists(lastlog_dir):
    #     os.mkdir(lastlog_dir)
    # lastlog_name = "%s/report_for_analyzer.%s.yaml" % (lastlog_dir, report.name)
    # previous_lastlog_name = "%s/report_for_analyzer.%s-LAST.yaml" % (lastlog_dir, report.name)
    # #se c'e un file precedente, allora lo setto come file precedente (eventualmente socrascrivendo) e
    # #salvo l'attuale come precedente
    # if os.path.exists(lastlog_name):
    #     if os.path.exists(previous_lastlog_name):
    #         os.unlink(previous_lastlog_name)
    #     os.rename(lastlog_name, previous_lastlog_name)

    with open(report_for_analyzer_name, "a") as report_for_analyzer_file:
        to_serialize = {}
        # qui ho il report con tutte le vm. Prendo una vm alla volta
        for k, v in report.c_received.items():
            vm = []
            test_name = None
            # failed_vm = False
            # prendoi singoli comandi della vm corrente
            for comm in v:
                #prendo solo la parte di REPORT, quindi aspetto la REPORT_KIND_INIT, recupero il test,
                # e processo i dati fino all'REPORT_KIND_END. poi ignoro il resto fino al REPORT_KIND_INIT
                if comm.name == "REPORT_KIND_INIT":
                    # se qui ho un test name, allora ho gia' fatto un init di cui non c'e' mai stato il
                    # if test_name:
                    #     failed_vm = True
                    if len(vm) > 0:
                        if vm[-1][3] != "REPORT_KIND_END":
                            mark_as_failed(vm, vm[-1][1], "No Report")

                    test_name = comm.args
                if comm.name == "REPORT_KIND_END":
                    #report_kind_end and report_kind_init are included
                    vm.append(command_to_array(comm, test_name))
                    test_name = None
                if not test_name:
                    #if not in a report_kind range, then does not save the command
                    continue
                vm.append(command_to_array(comm, test_name))

            to_serialize[k] = vm

        yaml.dump(to_serialize, report_for_analyzer_file)

    #no more needed
    #shutil.copyfile(report_for_analyzer_name, lastlog_name)


def dump():
    report = Report()

    report_name = "%s/report.%s.%s.log" % (logger.logdir, report.timestamp, report.name)

    f = open(report_name, "w+")
    for vm in report.c_received.keys():
        f.write("\n%s:\n" % vm)
        indent = ""
        for cmd in report.c_received[vm]:
            mark = "  "
            if cmd.name == "REPORT_KIND_END":
                indent = ""
            if not cmd.success:
                mark = "- "
            f.write("%s    %s%s\n" % (indent, mark, red(str(cmd))))
            if cmd.name == "REPORT_KIND_INIT":
                indent = "    "
        f.write("   SENT: %s\n" % report.c_sent[vm])
    f.close()

    r = summary()
    summary_name = "%s/summary.%s.%s.log" % (logger.logdir, report.timestamp, report.name)
    sym_sum_name = "%s/last.summary.%s.log" % (logger.logdir, report.name)

    f = open(summary_name, "w+")
    f.write(r)
    f.close()

    return
    #i think this is old (and unreachable)
    # if os.path.exists(sym_rep_name):
    #     logging.debug("removing: %s" % sym_rep_name)
    #     os.remove(sym_rep_name)
    # logging.debug("ln -s %s %s" % (report_name, sym_rep_name))
    # os.symlink(report_name, sym_rep_name)
    #
    # if os.path.exists(sym_sum_name):
    #     logging.debug("removing: %s" % sym_sum_name)
    #     os.remove(sym_sum_name)
    # logging.debug("ln -s %s %s" % (summary_name, sym_sum_name))
    # os.symlink(summary_name, sym_sum_name)

def restore(file_name):
    #report = Report()
    logging.debug("dir: %s list: %s" % (os.getcwd(), os.listdir(".")))

    assert os.path.exists(file_name)

    f = open(file_name)
    lines = []
    while True:
        l = f.readline()
        if not l:
            break
        if "lambda" in l:
            continue
        lines.append(l)

    y = "".join(lines)

    r = yaml.load(y)
    Report().init(r)
    return r


def command_to_array(comm, test_name):
    #as now, logs are not integrated
    if type(comm.args) is tuple:
        argslist = list(comm.args)
    else:
        argslist = comm.args
        #IMPORTANT!
        #Here rite_failed and rite_failed_log are False and "" because they are set later!
    mylist = [comm.timestamp, test_name, comm.vm, comm.name, argslist, comm.success, comm.result, False, "", comm.side]
    return mylist


def mark_as_failed(vm, test_name, reason):
    for v in vm:
        if v[1] == test_name:
            v[7] = True
            v[8] = reason
