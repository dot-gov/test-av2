__author__ = 'mlosito'
import os
import glob
import yaml
import sys
import copy
import socket
import mailsender
import re

from dbreport import DBReport
from resultdata import ResultData
from resultstates import ResultStates
from summarydata import SummaryData

debug = True
send_mail = False

def main():

    global debug

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

    print "       ___      .__   __.      ___       __      ____    ____  ________   _______ .______"
    print "      /   \     |  \ |  |     /   \     |  |     \   \  /   / |       /  |   ____||   _  \\"
    print "     /  ^  \    |   \|  |    /  ^  \    |  |      \   \/   /  `---/  /   |  |__   |  |_)  |"
    print "    /  /_\  \   |  . `  |   /  /_\  \   |  |       \_    _/      /  /    |   __|  |      /"
    print "   /  _____  \  |  |\   |  /  _____  \  |  `----.    |  |       /  /----.|  |____ |  |\  \----."
    print "  /__/     \__\ |__| \__| /__/     \__\ |_______|    |__|      /________||_______|| _| `._____|"

    if not len(filelist):
        print "No yaml report files found in logs dirs:"
        sys.exit()

    filelist.sort(reverse=True)

    # debug
    #print filelist
    print ""
    print "I'll process: %s" % filelist[0]

    process_yaml(os.path.join(prefix, filelist[0]))


def process_yaml(filename):
    f = open(filename)
    commands_results = yaml.load(f)

    #global test name splitted from filename (for the report)
    testname = filename.split(".")[-2]
    print "Number of VM to analyze: ", len(commands_results)
    print ""
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

            #############################################################
            ################### HERE I CALL THE ANALZER #################
            #############################################################
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
                    mail_message_error_details += i.get_cause(False) + "\n"
                mail_message_error_details += "------------------------------------------------------------------\n"

    mail_message = mail_message_errors + "\n\n" + mail_message_known_errors_summary + "\n\n" + mail_message_ok + "\n\n" + mail_message_error_details
    if send_mail:
        mailsender.analyzer_mail(testname, vms, mail_message)


def compare_three_states(current_state_rows, current_state_rows_full, manual_state_rows, message, previous_state_rows, saved_error):
    #first of all, I check for failure. If there is a failure I don't check results
    ok = True
    #if current run failed
    if rite_failed(current_state_rows):
        if rite_failed(manual_state_rows):
            message = "All OK! Actual state is: RITE_FAILED, known state is: RITE_FAILED (previous_state was: %s)" % rite_failed(previous_state_rows)
            saved_error = True
        else:
            message = "New RITE Failure! Actual state is: RITE_FAILED, known state is: RITE_NOT_FAILED (previous_state was: %s)" % rite_failed(previous_state_rows)
            ok = False
    #in case saved state is failed and current is not
    elif rite_failed(manual_state_rows):
        message = "Anomaly! Actual state is RITE NOT FAILED, but known state is RITE_FAIlED (previous_state was: %s)" % rite_failed(previous_state_rows)
        saved_error = True
    #Now I check the results
    if len(current_state_rows) == 0 and len(previous_state_rows) == 0 and len(manual_state_rows) == 0:
        message = "All OK! Actual state is: PASSED, previous state was: PASSED, (known state is: PASSED)"
        if debug:
            print message
    elif len(current_state_rows) == 0 and len(previous_state_rows) > 0 and len(manual_state_rows) == 0:
        message = "All Ok! Actual state is PASSED, we recovered from previous errorlist: %s" % state_rows_to_string_short(previous_state_rows)
        if debug:
            print message
    elif len(current_state_rows) > 0 and len(previous_state_rows) == 0 and len(manual_state_rows) == 0:
        message = "New error! Actual errorlist is: %s, previous state was: PASSED, (known state is: PASSED)" % state_rows_to_string_short(
            current_state_rows_full)
        if debug:
            print message
        ok = False
    elif len(current_state_rows) > 0 and len(previous_state_rows) > 0 and len(manual_state_rows) == 0:
        message = "New recurrent error! Actual errorlist is: %s, previous errorlist is: %s:, (known state is: PASSED)" % (
        state_rows_to_string_short(current_state_rows_full), state_rows_to_string_short(previous_state_rows))
        if debug:
            print message
        ok = False
    elif len(current_state_rows) == 0 and len(manual_state_rows) > 0:
        message = "Anomaly! Actual state is PASSED, known errorlist is: %s" % state_rows_to_string_short(manual_state_rows)
        if debug:
            print message
        ok = False
    elif len(current_state_rows) > 0 and compare_current_to_manual(current_state_rows, manual_state_rows) == 0:
        message = "OK, but known errors occurred. Actual errorlist and known errorlist are %s (previous errorlist is: %s)" % (
        state_rows_to_string_short(current_state_rows_full), state_rows_to_string_short(previous_state_rows))
        if debug:
            print message
        saved_error = True
    elif len(current_state_rows) > 0 and compare_current_to_manual(current_state_rows, manual_state_rows) != 0:
        message = "Anomaly! Actual errors differs from saved errors. Actual errorlist is: %s, known errorlist is: %s (previous errorlist is: %s)" % (
        state_rows_to_string_short(current_state_rows_full), state_rows_to_string_short(manual_state_rows),
        state_rows_to_string_short(previous_state_rows))
        if debug:
            print message
        ok = False
    else:
        message = "Sorry, the analyzer does not know this kind of error :,-( Actual errorlist is: %s, known errorlist is: %s (previous errorlist is: %s)" % (
        state_rows_to_string_short(current_state_rows_full), state_rows_to_string_short(manual_state_rows),
        state_rows_to_string_short(previous_state_rows))
        if debug:
            print message
        ok = False
    return message, ok, saved_error


def analyze(vm, comms):

    if not len(comms):
        return
    # DEBUG
    # for i in comms:
    #     i.print_short()
    #     #i.print_me()

    test_name = comms[0].test_name
    test_approximate_start_time = comms[0].timestamp

    print "#########################################"
    print "# Analyzing %s commands for VM: %s #" % (len(comms), vm)
    print "# Test: %s #" % test_name
    print "############  RESULTS  ##################"
    print "#########################################"
    with DBReport() as db:
        #eventual error message
        message = None
        #If the machine manifests an error which is already known, this string is assigned with the vm name
        saved_error = None

        #loads previous and manual states
        if debug:
            print ">>>>>>>>>>>>>>>>>>>>>>>>>>> PREVIOUS <<<<<<<<<<<<<<<<<<<<<<<<<<<<"
        previous_state_rows = db.get_latest_summary_rows(vm, test_name, debug, True)
        if debug:
            print ">>>>>>>>>>>>>>>>>>>>>>>>>>> MANUAL <<<<<<<<<<<<<<<<<<<<<<<<<<<<"
        manual_state_rows = db.get_known_summary_rows(vm, test_name, debug, False)

        prg = 0
        #inserts the parsed line into the db for reference
        print "Inserting results and summary from yaml data! (%s lines in yaml)" % len(comms)
        for i in comms:
            db.insert_result(i)
            # if i.get_value() > 0:

            db.insert_summary(SummaryData(test_approximate_start_time, test_name, vm, i.command, prg, 0, "", i.rite_result_log, i.parsed_result,
                                          i.rite_failed, i.rite_fail_log))
            prg += 1

        #debug, prints results
        # db.get_results_rows(vm, test_name, True)
        #debug, prints summary
        #db.get_latest_summary_rows(vm, test_name, True)

        #loads current states (the rows were added little before)
        if debug:
            print ">>>>>>>>>>>>>>>>>>>>>>>>>>> CURRENT <<<<<<<<<<<<<<<<<<<<<<<<<<<<"
        current_state_rows = db.get_latest_summary_rows(vm, test_name, debug, True)
        current_state_rows_full = db.get_latest_summary_rows(vm, test_name, False, False)
        if debug:
            print "manual rows", len(manual_state_rows)
            print "rows", len(current_state_rows)
            print "rows_full", len(current_state_rows_full)

        message, ok, saved_error = compare_three_states(current_state_rows, current_state_rows_full, manual_state_rows, message, previous_state_rows,
                                                        saved_error)


    return ok, message, saved_error, state_rows_to_string_short(current_state_rows_full), comms


def preparse_command_list(comms):
    parsed = []
    for i in comms:
        # print i
        # from
        # mylist = [comm.timestamp, test_name, comm.vm, comm.name, argslist, comm.success, comm.result, False, "", comm.side]
        #      [1421403290.337639, 'VM_MELT_SRV_UTO', 'avira', 'INTERNET', False, True, 'Internet False', False, '', 'server']
        # to
        # timestamp, start_timestamp, test_name, vm, command, args=None, rite_result=None, rite_result_log=None, parsed_result=ResultStates.NONE, rite_failed=False, rite_fail_log=None, side=None):

        parsed.append(ResultData(i[0], i[0], i[1], i[2], i[3], i[4], i[5], i[6], ResultStates.NONE, i[7], i[8], i[9]))
    return parsed


def rite_failed(state_rows):
    if len(state_rows) == 0:
        return False
    else:
        failed = False
        for i in state_rows:
            if i.rite_failed:
                failed = True
        return failed



def compare_current_to_manual(current_state_rows, manual_state_rows):
    #checks if there are a different number of commands
    if len(current_state_rows) != len(manual_state_rows):
        return False, "Different number of commands"
    else:
        different_results = []
        different_logs = []

        for x in range(len(current_state_rows)):
            #check if there are different command names (es: BUILD vs SCREENSHOT)
            if current_state_rows[x].command != manual_state_rows[x].command:
                return False, "Commands sequence is different"
            #check if there are different command results (es FAILED vs NO SYNC)
            elif current_state_rows[x].parsed_result[1] != manual_state_rows[x].parsed_result[1]:
                different_results.append("Current:%s=%s, Manual:%s=%s" % (current_state_rows[x].command, current_state_rows[x].parsed_result[0],
                                                                          manual_state_rows[x].command, manual_state_rows[x].parsed_result[0]))
            #check if there are different error logs
            elif re.match(manual_state_rows[x].rite_result_log, current_state_rows[x].rite_result_log):
                different_logs.append("Current:%s=%s(%s), Manual:%s=%s(%s)" % (current_state_rows[x].command, current_state_rows[x].parsed_result[0],
                                                                               current_state_rows[x].rite_result_log, manual_state_rows[x].command,
                                                                               manual_state_rows[x].parsed_result[0], manual_state_rows[x].rite_result_log))
        if len(different_results) > 0:
            return False, "Commands results are different: %s" % different_results
        elif len(different_logs) > 0:
            return False, "Commands logs patterns didn't match: %s" % different_logs
        else:
            return True, "Same execution results and logs"


def state_rows_to_string_short(state_rows):
    state_rows_to_string_full(state_rows, full=False)


def state_rows_to_string_full(state_rows, full=True):
    output = "{"
    for row in state_rows:
        # if full: prints "RITE FAILED" if rite failed, else the result
        # if NOT full: prints "RITE FAILED" if rite failed, else the result, but only if it's a failed result (omits success)

        # rite failed
        if row.rite_failed:
            output += "["+row.command+"=RITE FAILED!("+row.rite_fail_log+")]"
        # test failed
        elif row.parsed_result[0] not in ['PASSED', 'NONE'] or full:
            output += "["+row.command+"="+row.parsed_result[0]+"("+row.rite_result_log+")]"
    output += "}"
    return output


if __name__ == "__main__":
    main()