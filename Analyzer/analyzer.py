__author__ = 'mlosito'
import os
import glob
import time
import yaml
import sys
import copy
import socket
import mailsender

from dbreport import DBReport
from resultdata import ResultData
from resultstates import ResultStates


def main():

    #f = open('/home/avmonitor/logs/150108/report_for_analyzer.150108-103448.SYSTEM_ELITE_FAST_DEMO_SRV.yaml', 'r')
    #yaml_dir = os.path.join('/home/avmonitor/logs/', time.strftime("%y%m%d", time.localtime(time.time())))
    #print yaml_dir
    # #gets all files and get the latest report_for_analyzer
    # filelist = []
    # for dirname, dirnames, filenames in os.walk(yaml_dir):
    #     # print path to all filenames.
    #     for filename in filenames:
    #         #print filename
    #         if filename.endswith(".yaml") and filename.startswith("report_for_analyzer"):
    #             filelist.append(filename)

    #finds report for analyzer files
    prefix = '/home/avmonitor/logs/'
    hostname = socket.gethostname()
    if hostname == 'rite':
        prefix = '/home/avmonitor/Rite/logs/'

    filelist = glob.glob(prefix + "*/report_for_analyzer.*.yaml")

    if not len(filelist):
        print "No yaml report files found in logs dirs:"
        sys.exit()

    filelist.sort(reverse=True)

    # debug
    #print filelist

    print "I'll process: %s" % filelist[0]

    process_yaml(os.path.join(prefix, filelist[0]))


def process_yaml(filename):
    f = open(filename)
    commands_results = yaml.load(f)

    #global test name splitted from filename (for the report)
    testname = filename.split(".")[-2]

    print "Number of VM to analyze: ", len(commands_results)

    vms = commands_results.keys()

    mail_message_errors = "###################  UNKNOWN ERRORS   ###################\n"
    mail_message_ok = "###################     OK     ###################\n"
    mail_message_error_details = "################### ERROR DETAILS ###################\n"
    mail_message_known_errors_summary = "################### KNOWN ERRORS ###################\n"

    # this splits the dictionary into the different VMS
    for k, v in commands_results.items():
        comm2 = preparse_command_list(v)
        #this splits various test for a single av
        splitted_list = []
        if len(comm2) > 0:
            templist = []
            current_test = comm2[0].test_name
            for i in comm2:
                if i.test_name == current_test:
                    templist.append(i)
                    # print templist
                else:
                    current_test = i.test_name
                    splitted_list.append(copy.copy(templist))
                    templist = []
                    templist.append(i)
            splitted_list.append(templist)
        # print "splitt", splitted_list

        for listz in splitted_list:
            test_name = listz[0].test_name
            ok, message, saved_error, errors_list, error_log = analyze(k, listz)
            partial_mail_message = "Analyzed VM: %s - Test: %s\n" % (k, test_name)
            #partial_mail_message += "VM passed test?: %s\n" % ok
            partial_mail_message += "Analyzer Message: %s" % message
            #partial_mail_message += "Known Error: %s\n" % saved_error
            partial_mail_message += "(Errorlist: %s)\n" % errors_list
            partial_mail_message += "------------------------------------------------------------------\n"

            if not ok:
                mail_message_errors += partial_mail_message
            elif not saved_error:
                mail_message_ok += partial_mail_message
            else:
                mail_message_known_errors_summary += partial_mail_message

            print partial_mail_message

            if not ok:
                mail_message_error_details += partial_mail_message
                #mail_message_error_details += "------------------------------------------------------------------\n"
                mail_message_error_details += "-------------------       ERROR LOG          ---------------------\n"
                mail_message_error_details += "------------------------------------------------------------------\n"
                for i in error_log:
                    mail_message_error_details += i.get_cause() + "\n"
                mail_message_error_details += "------------------------------------------------------------------\n"

    mail_message = mail_message_errors + "\n\n" + mail_message_known_errors_summary + "\n\n" + mail_message_ok + "\n\n" + mail_message_error_details
    mailsender.analyzer_mail(testname, vms, mail_message)


def analyze(vm, comms):
    print "Analyzing %s commands for VM: %s" % (len(comms), vm)

    if not len(comms):
        return
    # DEBUG
    # for i in comms:
    #     i.print_short()
    #     #i.print_me()

    test_name = comms[0].test_name
    test_approximate_start_time = comms[0].timestamp

    print "#########################################"
    print "############  RESULTS  ##################"
    print "#########################################"
    with DBReport() as db:
        #eventual error message
        message = None
        #If the machine manifests an error which is already known, this string is assigned with the vm name
        saved_error = None

        # #for testing only
        db.annichilate_table()

        errors_list = []

        #inserts the parsed line into the db for reference
        for i in comms:
            db.insert_result(i)
            if i.get_value() > 0:
                errors_list.append(i.parsed_result[0])

        # debug
        print "Errors_list = %s" % errors_list

        db.insert_summary(test_approximate_start_time, test_name, vm, errors_list, False, False)

        #debug, prints results
        db.get_results_rows(vm, None, True)
        #debug, prints summary
        db.get_summary_rows(vm, test_name, True)

        #loads all states
        all_states = db.get_summary_rows(vm, test_name, False)
        manual_state_row = db.get_known_error(vm, test_name)

        #rs = ResultStates()
        this_state = all_states[0][3]
        print "this_errorlist: ", errors_list
        if len(all_states) > 1:
            previous_errorlist = all_states[1][3]
        else:
            previous_errorlist = []
        print "previous_errorlist: ", previous_errorlist
        if manual_state_row:
            manual_errorlist = manual_state_row[3]
        else:
            manual_errorlist = []
        print "manual_errorlist: ", manual_errorlist

        ok = True

        if len(errors_list) == 0 and len(previous_errorlist) == 0 and len(manual_errorlist) == 0:
            message = "All OK! Actual state is: PASSED, previous state was: PASSED, (known state is: PASSED) "
            print message
        elif len(errors_list) == 0 and len(previous_errorlist) > 0 and len(manual_errorlist) == 0:
            message = "All Ok! Actual state is PASSED, we recovered from previous errorlist: %s" % previous_errorlist
            print message
        elif len(errors_list) > 0 and len(previous_errorlist) == 0 and len(manual_errorlist) == 0:
            message = "New error! Actual errorlist is: %s, previous state was: PASSED, (known state is: PASSED) " % errors_list
            print message
            ok = False
        elif len(errors_list) > 0 and len(previous_errorlist) > 0 and len(manual_errorlist) == 0:
            message = "New recurrent error! Actual errorlist is: %s, previous errorlist is: %s:, (known state is: PASSED) " % (errors_list, previous_errorlist)
            print message
            ok = False
        elif len(errors_list) == 0 and len(manual_errorlist) > 0:
            message = "Anomaly! Actual state is PASSED, known errorlist is: %s" % manual_errorlist
            print message
            ok = False
        elif len(errors_list) > 0 and cmp(errors_list, manual_errorlist) == 0:
            message = "OK, but known errors occurred. Actual errorlist and known errorlist are %s (previous errorlist is: %s)" % (errors_list, previous_errorlist)
            print message
            saved_error = True
        elif len(errors_list) > 0 and cmp(errors_list, manual_errorlist) != 0:
            message = "Anomaly! Actual errors differs from saved errors. Actual errorlist is: %s, known errorlist is: %s (previous errorlist is: %s)" % (errors_list, manual_errorlist, previous_errorlist)
            print message
            ok = False

        #
        # #se il nuovo stato e' di errore, e il precedente no, lo comunico (indipendentemente dallo stato salvato)
        # if len(this_state[1])==0 previous_state[1]:
        #
        # #se il nuovo stato e' Passed, e il precedente di errore, lo comunico (indipendentemente dallo stato salavato)
        # elif this_state[1] < previous_state[1]:
        #     message = "Error recovered! Actual state is: %s, old state was: %s, (known state is: %s ) " % (this_state[0], previous_state[0], manual_state[0])
        #     print message
        # # se sono qui, allora lo stato precedente e' uguale a quello attuale
        # # quindi vedo cosa dice lo stato salvato, se e' uguale, allora non segnalo nulla (ma lo salvo poi come riepilogo)
        # elif this_state[1] != manual_state[1]:
        #     #se lo stato attuale e' diverso da quello salvato e l'attuale e' di errore, allora c'e un errore. E permane da piu' di un test.
        #     if this_state[1] != 0:
        #         message = "Not known, persistent error! Actual state is: %s, old state was: %s, (known state is: %s ) " % (this_state[0], previous_state[0], manual_state[0])
        #         print message
        #     #se lo stato attuale e' diverso da quello salvato e l'attuale e' di passed, allora probabilmente lo stato salvato e' sbagliato.
        #     elif this_state[1] == 0:
        #         message = "Strange! Test is passed but known state is not. Maybe saved state is wrong. Actual state is: %s, old state was: %s, (known state is: %s ) " % (this_state[0], previous_state[0], manual_state[0])
        #         print message
        # else:
        #     # stato precedente = all'attuale, e uguale anche allo stato salvato
        #     # quindi non devo fare nulla, mi annoto pero' le macchine in errore e con stato salvato di errore.
        #     if this_state[1] != 0:
        #         saved_error = vm
        #     # stato precedente = all'attuale, e uguale anche allo stato salvato
        #     # quindi non devo fare nulla, Messaggio = Tutto ok

    return ok, message, saved_error, errors_list, comms


def preparse_command_list(comms):
    parsed = []
    for i in comms:
        #comm.timestamp, comm.test_name, comm.vm, comm.name, comm.args, comm.success, comm.result, "", "", comm.side
        #timestamp,         test_name,      vm,      command,               args=None,     rite_result=None, rite_result_log=None,  parsed_result=ResultStates.NONE, rite_failed=False, rite_fail_log=None, side=None):
        #1421098490.708954, 'VM_STATIC_SRV', 'avg15', 'REPORT_KIND_INIT', 'VM_STATIC_SRV', True,             'avg15| VM_STATIC_SRV',     '',   '', 'meta']
        print i
        parsed.append(ResultData(i[0], i[1], i[2], i[3], i[4], i[5], i[6], ResultStates.NONE, False, "", i[9]))
    return parsed


if __name__ == "__main__":
    main()