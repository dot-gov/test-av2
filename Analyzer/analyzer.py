__author__ = 'mlosito'
import os
import glob
import yaml
import sys
import copy
import socket

from dbreport import DBReport
from resultdata import ResultData
from resultstates import ResultStates
from summarydata import SummaryData
from mailsender import MailSender
import sys

debug = False
send_mail = True


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

    print "       ___      .__   __.      ___       __      ____    ____  ________   _______ .______"
    print "      /   \     |  \ |  |     /   \     |  |     \   \  /   / |       /  |   ____||   _  \\"
    print "     /  ^  \    |   \|  |    /  ^  \    |  |      \   \/   /  `---/  /   |  |__   |  |_)  |"
    print "    /  /_\  \   |  . `  |   /  /_\  \   |  |       \_    _/      /  /    |   __|  |      /"
    print "   /  _____  \  |  |\   |  /  _____  \  |  `----.    |  |       /  /----.|  |____ |  |\  \----."
    print "  /__/     \__\ |__| \__| /__/     \__\ |_______|    |__|      /________||_______|| _| `._____|"
    print ""

    filename = ""

    #first argument is the script
    if len(sys.argv) == 2:
        filename = sys.argv[1]
    else:
        print "No filename provided in command line, I'll use the latest (using file modification date) SYSTEM_DAILY_*SRV from the logs dirs."
        #finds report for analyzer files
        prefix = '/home/avmonitor/logs/'
        hostname = socket.gethostname()
        if hostname == 'rite':
            prefix = '/home/avmonitor/Rite/logs/'

        filelist = sorted(glob.glob(prefix + "*/report_for_analyzer.*.SYSTEM_DAILY_*SRV.yaml"), key=os.path.getmtime, reverse=True)

        if not len(filelist):
            print "No yaml report files found in logs dirs:"
            sys.exit()

        filename = os.path.join(prefix, filelist[0])
        #print filelist

    print "I'll process: %s" % filename

    process_yaml(filename)


def process_yaml(filename):
    f = open(filename)
    commands_results = yaml.load(f)
    if not commands_results:
        print "No results in yaml file."
        #TODO qui bisognerebbe mandare un'email di avviso (volendo con yaml allegato)
        return

    print "Recreating database..."
    with DBReport() as db:
        db.recreate_database(debug)

    #global test name splitted from filename (for the report)
    testname = filename.split(".")[-2]
    total_vms = len(commands_results)
    print "Number of VM to analyze: ", total_vms
    print ""
    vms = commands_results.keys()

    retests = {}

    # this splits the dictionary into the different VMS
    vm_count = 1

    mailsender = MailSender()

    mailsender.yaml_analyzed = filename

    for vm, v in commands_results.items():
        comm2 = preparse_command_list(v)
        #this splits various test for a single av
        splitted_list = []
        if len(comm2) > 0:
            templist = []
            current_test = comm2[0].test_name
            for i in comm2:
                if i.test_name == current_test:
                    templist.append(i)
                else:
                    current_test = i.test_name
                    splitted_list.append(copy.copy(templist))
                    templist = []
                    templist.append(i)
            splitted_list.append(templist)

        for listz in splitted_list:
            test_name = listz[0].test_name

            #############################################################
            ################### HERE I CALL THE ANALZER #################
            #############################################################

            comparison_result = analyze(vm, listz)
            #OLD rite_ok, ok, message, saved_error, errors_list, error_log, current_state_rows

            message = comparison_result['message']

            #CREATING EMAIL AND PRINTING RESULTS
            text = "* Analyzed VM: %s (%s of %s) - Test: %s\n" % (vm, vm_count, total_vms, test_name)
            #text += "VM passed test?: %s\n" % ok
            text += "* Analyzer Message: %s" % message
            #text += "Known Error: %s\n" % saved_error
            #text += "* Errorlist: %s\n" % errors_list

            print "####################     RESULTS     ####################"
            print text
            print "####################   RESULTS END   ####################"

            if comparison_result['not_enabled']:
                mailsender.rite_not_enabled_add(vm, test_name, message)
            elif not comparison_result['rite_ok'] and not comparison_result['saved_error']:
                mailsender.rite_fails_add(vm, test_name, message)
            elif not comparison_result['rite_ok'] and comparison_result['saved_error']:
                mailsender.rite_known_fails_add(vm, test_name, message)
            elif not comparison_result['success'] and not comparison_result['saved_error']:
                mailsender.errors_add(vm, test_name, message, comparison_result['rows_obj'].get_causes(), comparison_result['rows_obj'].get_manual_save_string())
                #adds retest
                if test_name not in retests:
                    retests[test_name] = set()
                retests[test_name].add(vm)

            elif not comparison_result['success'] and comparison_result['saved_error']:
                mailsender.known_errors_add(vm, test_name, message, comparison_result['saved_error_comment'])
            #case in wich ew saved an error but the test passed
            elif comparison_result['success'] and comparison_result['saved_error']:
                mailsender.known_errors_but_test_passed_add(vm, test_name, message, comparison_result['saved_error_comment'])
            # ok
            else:
                mailsender.ok_add(vm, test_name, message)

        #count processed vms
        vm_count += 1

    #print retests
    retestlist = ""
    for testname, machines in retests.items():
        testname_system = testname.replace("VM", "SYSTEM")
        retest = "./run.sh %s -m " % testname_system
        for vm in machines:
            retest += "%s," % vm
        retestlist += "%s -c -p 40<br>" % retest[0:-1]

    mailsender.retestlist = retestlist

    print retestlist

    if send_mail:
        mailsender.send_mail()

    print "End. Exiting."


def analyze(vm, comms):

    print "Analyzing..."
    if not len(comms):
        return
    # DEBUG
    # for i in comms:
    #     i.print_short()
    #     #i.print_me()

    test_name = comms[0].test_name
    test_approximate_start_time = comms[0].timestamp

    print "################### STARTING TEST ######################"
    print "# Analyzing %s commands for VM: %s #" % (len(comms), vm)
    print "# Test: %s #" % test_name
    print "################### STARTING TEST ######################"
    with DBReport() as db:
        #eventual error message
        message = None
        #If the machine manifests an error which is already known, this string is assigned with the vm name
        saved_error = None

        #loads previous and manual states
        if debug:
            print "\n>>>>>>>>>>>>>>>>>>>>>>>>>>> PREVIOUS <<<<<<<<<<<<<<<<<<<<<<<<<<<<"
        previous_state_rows = db.get_latest_summary_rows(vm, test_name, debug)
        if debug:
            print "\n>>>>>>>>>>>>>>>>>>>>>>>>>>> MANUAL <<<<<<<<<<<<<<<<<<<<<<<<<<<<"
        manual_state_rows = db.get_known_summary_rows(vm, test_name, debug)

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
        #db.get_results_rows(vm, test_name, True)
        #debug, prints summary
        #db.get_latest_summary_rows(vm, test_name, True)

        #loads current states (the rows were added little before)
        if debug:
            print "\n>>>>>>>>>>>>>>>>>>>>>>>>>>> CURRENT <<<<<<<<<<<<<<<<<<<<<<<<<<<<"
        current_state_rows = db.get_latest_summary_rows(vm, test_name, debug)
        if debug:
            print "manual rows", manual_state_rows.get_rows_count()
            print "manual Error rows", manual_state_rows.get_error_rows_count()
            print "current rows", current_state_rows.get_rows_count()
            print "current Error rows", current_state_rows.get_error_rows_count()

        test_comparison_result = dict()

        test_comparison_result['not_enabled'] = current_state_rows.get_not_to_test()[0]
        test_comparison_result['message'] = current_state_rows.get_not_to_test()[1]
        # test_comparison_result['rows_string_short'] = current_state_rows.state_rows_to_string_short()
        # test_comparison_result['commands'] = comms
        test_comparison_result['rows_obj'] = current_state_rows

        if not current_state_rows.get_not_to_test()[0]:
            #checks for Rite Failure or other anomalies in failure states
            message, rite_ok, saved_error = current_state_rows.compare_three_states_failure(manual_state_rows, message, previous_state_rows)
            test_comparison_result['rite_ok'] = rite_ok
            test_comparison_result['success'] = False
            test_comparison_result['message'] = message
            test_comparison_result['saved_error'] = saved_error
            #if there are anomalies, then it IGNORES the states ad returns
            #else if the failure state is ok, it compares the results
            if rite_ok:
                message, ok, saved_error, saved_error_comment = current_state_rows.compare_three_states_results(manual_state_rows, previous_state_rows)
                test_comparison_result['success'] = ok
                test_comparison_result['message'] = message
                test_comparison_result['saved_error'] = saved_error
                test_comparison_result['saved_error_comment'] = saved_error_comment

        #     return True, ok, message, saved_error, current_state_rows.state_rows_to_string_short(), comms, current_state_rows
        # else:
        #     #rite failed. Also the rite_fail can have a saved error or not. "ok" is False because the test didn't complete
        #     return False, False, message, saved_error, current_state_rows.state_rows_to_string_short(), comms, current_state_rows

        return test_comparison_result


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


if __name__ == "__main__":
    main()