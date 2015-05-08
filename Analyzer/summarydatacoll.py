__author__ = 'mlosito'
import re


#this class contains a list of "SummaryData"
class SummaryDataColl(object):
    rows = []

    def __init__(self, rows):
        self.rows = rows

    def set_rows(self, rows):
        self.rows = rows

    def get_rows(self):
        return self.rows

    def get_rows_count(self):
        return len(self.rows)

    def get_error_rows(self):
        error_rows = []
        for i in self.rows:
            if i.parsed_result[0] not in ['PASSED', 'NONE', 'GOOD_CROP'] or i.rite_failed:
                error_rows.append(i)
        return error_rows

    def get_error_rows_count(self):
        error_num = 0
        for i in self.rows:
            if i.parsed_result[0] not in ['PASSED', 'NONE', 'GOOD_CROP'] or i.rite_failed:
                error_num += 1
        return error_num

    def get_good_crops_rows_count(self):
        good_crop_num = 0
        for i in self.rows:
            if i.parsed_result[0] in ['GOOD_CROP']:
                good_crop_num += 1
        return good_crop_num

    # def get_not_to_test(self):
    #     for i in self.rows:
    #         if i.parsed_result[0] in ['NOT_TO_TEST']:
    #             return True, i.rite_result_log
    #     return False, "Have to be tested"

    def is_rite_failed(self):
        if len(self.rows) == 0:
            return False
        else:
            failed = False
            for i in self.rows:
                if i.rite_failed:
                    failed = True
            return failed

    def is_test_error(self):
        return self.get_error_rows()

    def get_manual_comment(self):
        return self.rows[0].manual_comment

    def get_error_descriptions(self):
        if len(self.rows) == 0:
            return "Nothing was executed - 0 rows"
        output = "<br><ol class='doubletab'>"
        for row in self.rows:
            if row.rite_failed:
                output += "<li>"+row.command+"=RITE FAILED! - "+row.rite_fail_log+"</li><br>"
            elif row.parsed_result[0].strip() not in ['PASSED', 'NONE', 'GOOD_CROP']:
                output += "<li>"+row.command+"="+row.parsed_result[0]+" - "+row.get_error_description()+"</li><br>"
        output += "</ol>"
        if output == "<br><ol></ol>":
            return "All ok - 0 error rows<br>"
        return output

    #old
    def state_rows_to_string_short(self):
        return self.state_rows_to_string_full(full=False)

    def state_rows_to_string_full(self, full=True):
        if len(self.rows) == 0:
            return "Nothing was executed - 0 rows"
        output = "<br>{"
        for row in self.rows:
            # if full: prints "RITE FAILED" if rite failed, else the result
            # if NOT full: prints "RITE FAILED" if rite failed, else the result, but only if it's a failed result (omits success)

            # rite failed
            if row.rite_failed:
                output += "["+row.command+"=RITE FAILED!("+row.rite_fail_log+")]<br>"
            # test failed
            elif row.parsed_result[0].strip() not in ['PASSED', 'NONE', 'GOOD_CROP'] or full:
                output += "["+row.command+"="+row.parsed_result[0]+"("+row.rite_result_log+")]<br>"
        output += "}"
        if output == "{}" and not full:
            return "All ok - 0 error rows<br>"
        return output

    def get_crop_filenames(self):
        filenames = []
        for i in self.rows:
            if i.parsed_result[0] in ['CROP']:
                #log example: [3]
                log = eval(i.rite_result_log)
                # if len(log) > 0:
                #     for crop in log:
                if isinstance(log, list):
                    filenames.extend(log)
                else:
                    filenames.append(log)
        print ("Debug: crop numbers= %s" % filenames)
        return filenames

    def get_popup_results(self):
        pop_results = []
        for i in self.rows:
            if i.parsed_result[0] in ['POPUP']:
                print "POPUP debug: %s" % i.rite_result_log
                #log example: [3]
                log = eval(i.rite_result_log)
                # if len(log) > 0:
                #     for crop in log:
                pop_results.extend(log)
        print ("Debug: popup results= %s" % pop_results)
        return pop_results

    def refine_crops_with_tesseract(self, ocrd=None):
        for i in self.rows:
            i.refine_crop_with_tesseract(ocrd)

        #new errors and anomalies (manual state different from current state), and other problems are considered NOT OK
        #saved state = current state is considered "SAVED STATE=True".
        # Other cases are NOT OK
    def compare_three_states_results(self, manual_state_rows, previous_state_rows):

        ok = True
        saved_error = False

        cur_err = self.get_error_rows_count()
        man_err = manual_state_rows.get_error_rows_count()
        prev_err = previous_state_rows.get_error_rows_count()
        saved_error_comment = ""

        good_crop_curr_num = self.get_good_crops_rows_count()

        if cur_err == 0 and prev_err == 0 and man_err == 0:
            message = "<b>All OK! Actual state is: PASSED, previous state was: PASSED, (known state is: PASSED)</b>"

        elif cur_err == 0 and prev_err > 0 and man_err == 0:
            message = "<b>All Ok! Actual state is PASSED, we recovered from previous errorlist:</b> %s" % previous_state_rows.get_error_descriptions()

        elif cur_err > 0 and prev_err == 0 and man_err == 0:
            message = "<b>New error! Actual errorlist is:</b> %s <b>previous state was: PASSED <br> (known state is: PASSED)</b>" % self.get_error_descriptions()
            ok = False
        elif cur_err > 0 and prev_err > 0 and man_err == 0:
            message = "<b>New recurrent error! Actual errorlist is:</b>%s <b>previous errorlist is:</b> %s<b>(known state is: PASSED)</b>" % (
                self.get_error_descriptions(), previous_state_rows.get_error_descriptions())
            ok = False
        elif cur_err == 0 and man_err > 0:
            message = "<b>Anomaly! Actual state is PASSED, known errorlist is:</b> %s" % manual_state_rows.get_error_descriptions()
            ok = True
            saved_error = True
            saved_error_comment = manual_state_rows.get_manual_comment()
        #compare_current_to_manual is true if commands are equal
        elif cur_err > 0 and self.compare_current_to_manual(manual_state_rows)[0]:
            message = "<b>OK, but known errors occurred (known error comment is: %s).Actual errorlist is:</b> %s <b>known errorlist is:</b> %s <b>previous errorlist is:</b> %s" % (manual_state_rows.get_manual_comment(), self.get_error_descriptions(),  self.get_error_descriptions(), previous_state_rows.get_error_descriptions())
            ok = False
            saved_error = True
            saved_error_comment = manual_state_rows.get_manual_comment()
        elif cur_err > 0 and not self.compare_current_to_manual(manual_state_rows)[0]:
            x, differ_reason = self.compare_current_to_manual(manual_state_rows)
            message = "<b>Anomaly! Actual errors differs from saved errors (reason: </b> %s <b>).<br>Actual errorlist is:</b> %s <b>known errorlist is:</b> %s " \
                      "<b>previous errorlist is:</b> %s" %\
                      (differ_reason, self.get_error_descriptions(), manual_state_rows.get_error_descriptions(),
                       previous_state_rows.get_error_descriptions())
            ok = False
        else:
            message = "<b>Sorry, the analyzer does not know this kind of error :,-( Actual errorlist is:</b> %s" \
                      "<b>known errorlist is:</b> %s <b>previous errorlist is:</b> %s" % (self.get_error_descriptions(),
                                                                              manual_state_rows.get_error_descriptions(),
                                                                              previous_state_rows.get_error_descriptions())
            ok = False

        if good_crop_curr_num > 0:
            message += "- Also %s crops considered not detections (or empty) were ignored." % good_crop_curr_num
        return message, ok, saved_error, saved_error_comment

    def compare_three_states_failure(self, manual_state_rows, message, previous_state_rows):
        #first of all, I check for failure. If there is a failure I don't check results
        ok = True
        saved_error = False
        #if current run failed
        if self.is_rite_failed():
            if manual_state_rows.is_rite_failed():
                message = "<b>All OK! Actual state is: RITE_FAILED, known state is: RITE_FAILED (known fail comment is: %s)</b>" \
                          "<b>(previous_state was failed: %s)</b>" % (manual_state_rows.get_manual_comment(), previous_state_rows.is_rite_failed())
                ok = False
                saved_error = True
            else:
                message = "<b>New RITE Failure! Actual state is: RITE_FAILED, known state is: RITE_NOT_FAILED (previous_state was " \
                          "failed: %s)</b>" % previous_state_rows.is_rite_failed()
                ok = False
        #in case saved state is failed and current is not
        elif manual_state_rows.is_rite_failed():
            message = "<b>Anomaly! Actual state is RITE NOT FAILED, but known state is RITE_FAILED (known fail comment is: %s)</b> " \
                      "<b>(previous_state was failed: %s)</b>" % (manual_state_rows.get_manual_comment(), previous_state_rows.is_rite_failed())
            ok = False

        # print "Fail analysis:", message
        return message, ok, saved_error

    def compare_current_to_manual(self, manual_state_rows):

        cur_err = self.get_error_rows_count()
        man_err = manual_state_rows.get_error_rows_count()

        #checks if there are a different number of commands
        if cur_err > man_err:
            return False, "<b>Occurred more errors than known errors!</b>"
        else:
            different_commands = []
            different_results = []
            different_logs = []

            known_skipped = 0
            for x in range(cur_err):
                #check if there are different command names (es: BUILD vs SCREENSHOT)
                print 'comparing %s to %s' % (self.get_error_rows()[x].command, manual_state_rows.get_error_rows()[x+known_skipped].command)

                #while the comparison fails but we can skip the command, then skip
                while (not self.compare_single_current_to_manual(self.get_error_rows()[x], manual_state_rows.get_error_rows()[x+known_skipped]) and
                manual_state_rows.get_error_rows()[x+known_skipped].manual_optional and len(manual_state_rows.get_error_rows()) - 1 > x + known_skipped):
                    known_skipped += 1

                #if i am here, or the command are equal or different and cannot skip anymore
                #if are equal, I do nothing and go on
                #if not equal, add errors!
                if not self.compare_single_current_to_manual(self.get_error_rows()[x], manual_state_rows.get_error_rows()[x+known_skipped]):
                    self.compare_single_current_to_manual_get_reason(self.get_error_rows()[x], manual_state_rows.get_error_rows()[x+known_skipped],
                                                                     different_commands, different_results, different_logs)


            if len(different_results) > 0:
                return False, "Command sequence is different: %s" % different_commands
            elif len(different_results) > 0:
                return False, "Commands results are different: %s" % different_results
            elif len(different_logs) > 0:
                return False, "Commands logs patterns didn't match: %s" % different_logs
            else:
                return True, "Same execution results and logs (%s known optional errors skipped)" % + known_skipped

    def compare_single_current_to_manual(self, curr_row, manual_row):
        if curr_row.command != manual_row.command:
            return False

        #check if there are different command results (es FAILED vs NO SYNC)
        elif curr_row.parsed_result[1] != manual_row.parsed_result[1]:
            return False
            # different_results.append("Current:%s=%s, Manual:%s=%s" % (curr_row.command,
            #                                                           curr_row.parsed_result[0],
            #                                                           manual_row.command,
            #                                                           manual_row.parsed_result[0]))

        #check if there are different error logs
        #REGEXP VERSION
        elif not re.match(manual_row.rite_result_log, curr_row.rite_result_log):
            return False
            # different_logs.append("Current:%s=%s(%s), Manual:%s=%s(%s)" % (curr_row.command,
            #                                                                curr_row.parsed_result[0],
            #                                                                curr_row.rite_result_log,
            #                                                                manual_row.command,
            #                                                                manual_row.parsed_result[0],
            #                                                                manual_row.rite_result_log))
        else:
            return True

    def compare_single_current_to_manual_get_reason(self, curr_row, manual_row, different_commands, different_results, different_logs):
        if curr_row.command != manual_row.command:
            different_commands.append("Current:%s, Manual:%s" % (curr_row.command, manual_row.command))

        #check if there are different command results (es FAILED vs NO SYNC)
        elif curr_row.parsed_result[1] != manual_row.parsed_result[1]:
            different_results.append("Current:%s=%s, Manual:%s=%s" % (curr_row.command,
                                                                      curr_row.parsed_result[0],
                                                                      manual_row.command,
                                                                      manual_row.parsed_result[0]))

        #check if there are different error logs
        #REGEXP VERSION
        elif not re.match(manual_row.rite_result_log, curr_row.rite_result_log):
            different_logs.append("Current:%s=%s(%s), Manual:%s=%s(%s)" % (curr_row.command,
                                                                           curr_row.parsed_result[0],
                                                                           curr_row.rite_result_log,
                                                                           manual_row.command,
                                                                           manual_row.parsed_result[0],
                                                                           manual_row.rite_result_log))

    def get_manual_save_string(self):
        string_out = ""
        for summ in self.get_error_rows():
            #before re.escape(summ.rite_result_log) was used instead of error_type
            #"DBReport.error_types['%s'][0]" % summ.get_error_type(),
            tup = summ.test_name, summ.vm, summ.command, summ.prg, summ.parsed_result[0], summ.rite_failed, summ.rite_fail_log
            string_out += "self.insert_summary_manual_error(" + repr(tup) + ", \'" + summ.get_error_type() + "\', False, \"--INSERT-COMMENT-HERE--\")<br>"

        return string_out

    def get_causes(self):
        text = ""
        for i in self.rows:
                    text += i.get_cause(False) + "<br>"
        return text