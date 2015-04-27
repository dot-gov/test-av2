__author__ = 'mlosito'
import os
import glob
import yaml
import sys
import copy
import socket

sys.path.append("./Rite/")
# from AVMaster.av_master import AVMaster
from AVCommon.procedure import Procedure

from dbreport import DBReport
from resultdata import ResultData
from resultstates import ResultStates
from summarydata import SummaryData
from mailsender import MailSender
from ocrdict import OcrDict
import sys

debug = False
send_mail = True
write_retests = True

not_to_retest = ["UPD_AV", "UPD_REFRESH", "VM_PUSH_VIRUS"]


def main():

    global write_retests
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

    filenames = []

    #first argument is the script
    #if more than one argument, i'll process every file in order.

    #if no arguments, parses the daily (and update, positive)
    if len(sys.argv) == 1:
        write_retests = True
        print "No filename provided in command line, I'll use the latest (using file modification date) UPDATE_AV," \
              "SYSTEM_POSITIVE and SYSTEM_DAILY_*SRV from the logs dirs."
        filenames = ["UPDATE_AV", "SYSTEM_POSITIVE", "SYSTEM_DAILY_SRV"]
    else:
        write_retests = False
        filenames = sys.argv[1:]

    prefix = '/home/avmonitor/logs/'
    hostname = socket.gethostname()
    if hostname == 'rite':
        prefix = '/home/avmonitor/Rite/logs/'

    results_to_receive = []
    # # parser = argparse.ArgumentParser(description='AVMonitor master.')
    # # args = parser.parse_args()
    # # av_master = AVMaster(args)
    Procedure.load_procedures()

    filenames2 = []
    for name in filenames:
        #if the file is not a filename but a test name, extract the last filename for this test from filesystem
        if not name.lower().endswith(".yaml"):
            filename = sorted(glob.glob(prefix + "*/report_for_analyzer.*.%s.yaml" % name), key=os.path.getmtime, reverse=True)[0]
            filenames2.append(filename)
            x, resultslist = Procedure.check_procedure(name)
            results_to_receive.extend(i for i in resultslist if i not in results_to_receive)
        else:
            filenames2.append(name)

    filenames = filenames2

    print "I'll process: %s" % str(filenames)

    process_yaml(filenames, results_to_receive)


def process_yaml(filenames, results_to_receive):

    #I parse the files in order. ORDER MATTERS!

    commands_results = {}
    #opening updates

    for f in filenames:
        fil = open(f)
        commands = yaml.load(fil)
        for vm, com in commands.items():
            if vm in commands_results:
                commands_results[vm].extend(com)
            else:
                commands_results[vm] = com

    if not commands_results:
        print "No results in yaml file."
        #TODO qui bisognerebbe mandare un'email di avviso (volendo con yaml allegato)
        return

    print "Recreating database..."
    with DBReport() as db:
        db.recreate_database(debug)

    total_vms = len(commands_results)
    print "Number of VM to analyze: ", total_vms
    print "Tests to analyze: ", results_to_receive

    vms = commands_results.keys()

    retests = {}

    # this splits the dictionary into the different VMS
    vm_count = 1

    mailsender = MailSender()

    mailsender.yaml_analyzed = filenames
    mailsender.results_to_receive = results_to_receive

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

            # also rite failed tests can have popups
            if not comparison_result['rite_ok'] and not comparison_result['saved_error']:
                mailsender.add_result(vm, test_name, mailsender.ResultTypes.RITE_FAILS, message, popup_results=comparison_result['popup_results'])
            elif not comparison_result['rite_ok'] and comparison_result['saved_error']:
                mailsender.add_result(vm, test_name, mailsender.ResultTypes.RITE_KNOWN_FAILS, message)
            elif not comparison_result['success'] and not comparison_result['saved_error']:
                if test_name not in mailsender.invert_result_tests:
                    mailsender.add_result(vm, test_name, mailsender.ResultTypes.NEW_ERRORS, message,
                                          details=comparison_result['rows_obj'].get_causes(),
                                          save_strings=comparison_result['rows_obj'].get_manual_save_string(),
                                          crop_filenames=comparison_result['crop_filenames'], popup_results=comparison_result['popup_results'])
                    #adds retest
                    if test_name not in retests:
                        retests[test_name] = set()
                    retests[test_name].add(vm)
                #invert
                else:
                    mailsender.add_result(vm, test_name, mailsender.ResultTypes.OK, message,
                                          crop_filenames=comparison_result['crop_filenames'], popup_results=comparison_result['popup_results'])
                # mailsender.crop_filenames_add(vm, test_name, comparison_result['crop_filenames'])
            elif not comparison_result['success'] and comparison_result['saved_error']:
                mailsender.add_result(vm, test_name, mailsender.ResultTypes.KNOWN_ERRORS, message,
                                      saved_error_comment=comparison_result['saved_error_comment'])
            #case in wich we saved an error but the test passed
            elif comparison_result['success'] and comparison_result['saved_error']:
                mailsender.add_result(vm, test_name, mailsender.ResultTypes.KNOWN_ERRORS_BUT_PASSED, message,
                                      comparison_result['saved_error_comment'])
            # ok
            else:
                if test_name not in mailsender.invert_result_tests:
                    mailsender.add_result(vm, test_name, mailsender.ResultTypes.OK, message)
                else:
                    mailsender.add_result(vm, test_name, mailsender.ResultTypes.NEW_ERRORS, message,
                                          details=comparison_result['rows_obj'].get_causes(),
                                          save_strings=comparison_result['rows_obj'].get_manual_save_string(),
                                          crop_filenames=comparison_result['crop_filenames'], popup_results=comparison_result['popup_results'])
                    #NB does not sets retest for inverted results

            #try to print yesterday's data
            # if 'oldies' in comparison_result:
            #     print "*********************     DEBUG YESTERDAY     *********************"
            #     oldies = comparison_result['oldies']
            #     print oldies

        #count processed vms
        vm_count += 1

    #print retests

    retestlist_important = ""
    retestlist_less_important = ""

    tests_to_analyze = "UPDATE_AV SYSTEM_POSITIVE SYSTEM_DAILY_SRV"
    for testname, machines in retests.items():
        #add to retest only some tests (es: i do not re-test and do not re-analyze UPD_AV)
        if testname not in not_to_retest:
            testname_system = testname.replace("VM", "SYSTEM")
            retest = "./run.sh %s -m " % testname_system
            for vm in machines:
                retest += "%s," % vm
            if testname in mailsender.important_tests:
                retestlist_important += "%s -c -p 44<br>" % retest[0:-1]
            else:
                retestlist_less_important += "%s -c -p 44<br>" % retest[0:-1]
            tests_to_analyze += " " + testname_system

    retestlist = retestlist_important + retestlist_less_important

    # command to re-run analysis.
    retestlist += "python ./Rite/Analyzer/analyzer.py %s" % tests_to_analyze

    mailsender.retestlist = retestlist

    print retestlist
    if write_retests:
        #writing to file retests
        file_retest_name = "/opt/AVTest2/rite_retest_analyzer.sh"
        retestlist = '''#!/bin/sh\ncd /home/avmonitor\n''' + retestlist.replace("<br>", "\n")
        with open(file_retest_name, 'w') as retestfile:
            retestfile.write(retestlist)

        os.chmod(file_retest_name, 0755)

    #For now I send both mails
    #if not write_retests and send_mail:
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
    test_approximate_end_time = comms[-1].timestamp

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

        ocrd = OcrDict()

        prg = 0
        #inserts the parsed line into the db for reference
        print "Inserting results and summary from yaml data! (%s lines in yaml)" % len(comms)
        rows_omitted = 0
        for i in comms:
            #this was commented because the tables are growing too big and this historic data is not so important
            # db.insert_result(i)
            summ_data = SummaryData(test_approximate_start_time, test_name, vm, i.command, prg, 0, "", i.rite_result_log, i.parsed_result,
                                    i.rite_failed, i.rite_fail_log)

            #refine crops with tesseract
            summ_data.refine_crop_with_tesseract(ocrd)

            #that save the refined data into he Database
            if not db.insert_summary(summ_data):
                rows_omitted += 1

            prg += 1

        if rows_omitted:
            print('%s inserts were skipped, because the summary already existed. This analysis was already run.' % rows_omitted)
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

        # test_comparison_result['not_enabled'] = current_state_rows.get_not_to_test()[0]
        # test_comparison_result['message'] = current_state_rows.get_not_to_test()[1]
        # test_comparison_result['rows_string_short'] = current_state_rows.state_rows_to_string_short()
        # test_comparison_result['commands'] = comms
        test_comparison_result['rows_obj'] = current_state_rows

        # if not current_state_rows.get_not_to_test()[0]:

        #checks for Rite Failure or other anomalies in failure states
        message, rite_ok, saved_error = current_state_rows.compare_three_states_failure(manual_state_rows, message, previous_state_rows)
        test_comparison_result['rite_ok'] = rite_ok
        test_comparison_result['success'] = False
        test_comparison_result['message'] = message
        test_comparison_result['saved_error'] = saved_error
        test_comparison_result['crop_filenames'] = None
        test_comparison_result['popup_results'] = None

        #if there are anomalies, then it IGNORES the states ad returns
        #else if the failure state is ok, it compares the results
        if rite_ok:
            message, ok, saved_error, saved_error_comment = current_state_rows.compare_three_states_results(manual_state_rows, previous_state_rows)
            test_comparison_result['success'] = ok
            test_comparison_result['message'] = message
            test_comparison_result['saved_error'] = saved_error
            test_comparison_result['saved_error_comment'] = saved_error_comment
            if not ok:
                test_comparison_result['crop_filenames'] = current_state_rows.get_crop_filenames()
                test_comparison_result['popup_results'] = current_state_rows.get_popup_results()

        #     return True, ok, message, saved_error, current_state_rows.state_rows_to_string_short(), comms, current_state_rows
        # else:
        #     #rite failed. Also the rite_fail can have a saved error or not. "ok" is False because the test didn't complete
        #     return False, False, message, saved_error, current_state_rows.state_rows_to_string_short(), comms, current_state_rows

        # TODO
        # yesterday_state_rows = db.get_previous_summary_rows(vm, test_name, 1, debug)
        #
        # test_comparison_result['oldies'] = yesterday_state_rows

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


def load_procedures(procedure):
    if os.path.exists("AVMaster/conf/procedures.yaml"):
        procedure.load_from_file("AVMaster/conf/procedures.yaml")

    confs = glob.glob("AVMaster/conf/procedures/*.yaml")
    for conf in confs:
        # logging.info("Loading conf: %s" % conf)
        procedure.load_from_file(conf)
    if not procedure.check():
        raise SyntaxError("Errors in procedures")


if __name__ == "__main__":
    main()