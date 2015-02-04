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
            if i.parsed_result[0] not in ['PASSED', 'NONE'] or i.rite_failed:
                error_rows.append(i)
        return error_rows

    def get_error_rows_count(self):
        error_num = 0
        for i in self.rows:
            if i.parsed_result[0] not in ['PASSED', 'NONE'] or i.rite_failed:
                error_num += 1
        return error_num

    def get_not_to_test(self):
        for i in self.rows:
            if i.parsed_result[0] in ['NOT_TO_TEST']:
                return True, i.rite_result_log
        return False, "Have to be tested"

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

    def state_rows_to_string_short(self):
        return self.state_rows_to_string_full(full=False)

    def state_rows_to_string_full(self, full=True):
        if len(self.rows) == 0:
            return "Nothing was executed - 0 rows"
        output = "{"
        for row in self.rows:
            # if full: prints "RITE FAILED" if rite failed, else the result
            # if NOT full: prints "RITE FAILED" if rite failed, else the result, but only if it's a failed result (omits success)

            # rite failed
            if row.rite_failed:
                output += "["+row.command+"=RITE FAILED!("+row.rite_fail_log+")]"
            # test failed
            elif row.parsed_result[0].strip() not in ['PASSED', 'NONE'] or full:
                output += "["+row.command+"="+row.parsed_result[0]+"("+row.rite_result_log+")]"
        output += "}"
        if output == "{}" and not full:
            return "All ok - 0 error rows"
        return output

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

        if cur_err == 0 and prev_err == 0 and man_err == 0:
            message = "All OK! Actual state is: PASSED, previous state was: PASSED, (known state is: PASSED)"

        elif cur_err == 0 and prev_err > 0 and man_err == 0:
            message = "All Ok! Actual state is PASSED, we recovered from previous errorlist: %s" % previous_state_rows.state_rows_to_string_short()

        elif cur_err > 0 and prev_err == 0 and man_err == 0:
            message = "New error! Actual errorlist is: %s, previous state was: PASSED, (known state is: PASSED)" % self.state_rows_to_string_short()
            ok = False
        elif cur_err > 0 and prev_err > 0 and man_err == 0:
            message = "New recurrent error! Actual errorlist is: %s, previous errorlist is: %s:, (known state is: PASSED)" % (
                self.state_rows_to_string_short(), previous_state_rows.state_rows_to_string_short())
            ok = False
        elif cur_err == 0 and man_err > 0:
            message = "Anomaly! Actual state is PASSED, known errorlist is: %s" % manual_state_rows.state_rows_to_string_short()
            ok = False
        #compare_current_to_manual is true if commands are equal
        elif cur_err > 0 and self.compare_current_to_manual(manual_state_rows):
            message = "OK, but known errors occurred (known error comment is: %s). Actual errorlist and known errorlist are %s " \
                      "(previous errorlist is: %s)" % (manual_state_rows.get_manual_comment(), self.state_rows_to_string_short(),
                                                       previous_state_rows.state_rows_to_string_short())
            ok = False
            saved_error = True
            saved_error_comment = manual_state_rows.get_manual_comment()
        elif cur_err > 0 and self.compare_current_to_manual(manual_state_rows):
            x, differ_reason = self.compare_current_to_manual(manual_state_rows)
            message = "Anomaly! Actual errors differs from saved errors (reason: %s). Actual errorlist is: %s, known errorlist is: %s " \
                      "(previous errorlist is: %s)" %\
                      (differ_reason, self.state_rows_to_string_short(), manual_state_rows.state_rows_to_string_short(),
                       previous_state_rows.state_rows_to_string_short())
            ok = False
        else:
            message = "Sorry, the analyzer does not know this kind of error :,-( Actual errorlist is: %s," \
                      "known errorlist is: %s (previous errorlist is: %s)" % (self.state_rows_to_string_short(),
                                                                              manual_state_rows.state_rows_to_string_short(),
                                                                              previous_state_rows.state_rows_to_string_short())
            ok = False
        return message, ok, saved_error, saved_error_comment

    def compare_three_states_failure(self, manual_state_rows, message, previous_state_rows):
        #first of all, I check for failure. If there is a failure I don't check results
        ok = True
        saved_error = False
        #if current run failed
        if self.is_rite_failed():
            if manual_state_rows.is_rite_failed():
                message = "All OK! Actual state is: RITE_FAILED, known state is: RITE_FAILED (known fail comment is: %s)" \
                          "(previous_state was failed: %s)" % (manual_state_rows.get_manual_comment(), previous_state_rows.is_rite_failed())
                ok = False
                saved_error = True
            else:
                message = "New RITE Failure! Actual state is: RITE_FAILED, known state is: RITE_NOT_FAILED (previous_state was " \
                          "failed: %s)" % previous_state_rows.is_rite_failed()
                ok = False
        #in case saved state is failed and current is not
        elif manual_state_rows.is_rite_failed():
            message = "Anomaly! Actual state is RITE NOT FAILED, but known state is RITE_FAILED (known fail comment is: %s) " \
                      "(previous_state was failed: %s)" % (manual_state_rows.get_manual_comment(), previous_state_rows.is_rite_failed())
            ok = False

        # print "Fail analysis:", message
        return message, ok, saved_error

    def compare_current_to_manual(self, manual_state_rows):

        cur_err = self.get_error_rows_count()
        man_err = manual_state_rows.get_error_rows_count()

        #checks if there are a different number of commands
        if cur_err != man_err:
            return False, "Different number of commands"
        else:
            different_results = []
            different_logs = []

            for x in range(cur_err):
                #check if there are different command names (es: BUILD vs SCREENSHOT)
                if self.get_error_rows()[x].command != manual_state_rows.get_error_rows()[x].command:
                    return False, "Commands sequence is different"
                #check if there are different command results (es FAILED vs NO SYNC)
                elif self.get_error_rows()[x].parsed_result[1] != manual_state_rows.get_error_rows()[x].parsed_result[1]:
                    different_results.append("Current:%s=%s, Manual:%s=%s" % (self.get_error_rows()[x].command,
                                                                              self.get_error_rows()[x].parsed_result[0],
                                                                              manual_state_rows.get_error_rows()[x].command,
                                                                              manual_state_rows.get_error_rows()[x].parsed_result[0]))
                #check if there are different error logs
                #REGEXP VERSION
                elif re.match(manual_state_rows.get_error_rows()[x].rite_result_log, self.get_error_rows()[x].rite_result_log):
                #NON REGEXP VERSION (EXACT MATCH)
                #elif manual_state_rows.get_error_rows()[x].rite_result_log == self.get_error_rows()[x].rite_result_log:
                    different_logs.append("Current:%s=%s(%s), Manual:%s=%s(%s)" % (self.get_error_rows()[x].command,
                                                                                   self.get_error_rows()[x].parsed_result[0],
                                                                                   self.get_error_rows()[x].rite_result_log,
                                                                                   manual_state_rows.get_error_rows()[x].command,
                                                                                   manual_state_rows.get_error_rows()[x].parsed_result[0],
                                                                                   manual_state_rows.get_error_rows()[x].rite_result_log))
            if len(different_results) > 0:
                return False, "Commands results are different: %s" % different_results
            elif len(different_logs) > 0:
                return False, "Commands logs patterns didn't match: %s" % different_logs
            else:
                return True, "Same execution results and logs"

    def get_manual_save_string(self):
        string_out = ""
        for summ in self.get_error_rows():
            tup = summ.test_name, summ.vm, summ.command, summ.prg, re.escape(summ.rite_result_log), summ.parsed_result[0], summ.rite_failed, summ.rite_fail_log
            string_out += "self.insert_summary_manual_error(" + repr(tup) + ", \"--INSERT-COMMENT-HERE--\")\n"

        return string_out

    def get_causes(self):
        text = ""
        for i in self.rows:
                    text += i.get_cause(False) + "<br>"
        return text