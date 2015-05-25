__author__ = 'mlosito'
import re
import sys

from resultstates import ResultStates
from resultdata import ResultData
sys.path.append("./Rite/")
import dbreport


class SummaryData(ResultData):
    #timestamp will be equal to start_timestamp
    #side, args, rite_result are none
    def __init__(self, start_timestamp, end_timestamp, test_name, vm, command, prg, manual, manual_optional=False, manual_comment="", rite_result_log=None,
                 parsed_result=ResultStates.NONE, rite_failed=False, rite_fail_log=None):
        ResultData.__init__(self, start_timestamp, start_timestamp, test_name, vm, command, args=None, rite_result=None,
                            rite_result_log=rite_result_log,
                            parsed_result=parsed_result, rite_failed=rite_failed, rite_fail_log=rite_fail_log, side=None)

        self.end_timestamp = end_timestamp
        self.prg = prg
        self.manual = manual
        self.manual_optional = manual_optional
        self.manual_comment = manual_comment

    def get_error_type(self):
        if self.parsed_result == ResultStates.PASSED:
            return None
        elif self.manual:
            # I know the specific manual error saved, so I use this comment
            for k, v in dbreport.DBReport.error_types.viewitems():
                if v[0] == self.rite_result_log and v[1] == self.command:
                    return k
        else:
            # I try to guess a possible manual error
            for k, v in dbreport.DBReport.error_types.viewitems():
                if v[1] == self.command and re.match(v[0], self.rite_result_log):
                    return k

            return "New type: %s" % re.escape(self.rite_result_log)

    def get_error_description(self):
        if self.parsed_result == ResultStates.PASSED:
            return ""
        elif self.manual:
            # I know the specific manual error saved, so I use this comment
            for k, v in dbreport.DBReport.error_types.viewitems():
                if v[0] == self.rite_result_log and v[1] == self.command:
                    return v[2]
        else:
            # I try to guess a possible manual error
            for k, v in dbreport.DBReport.error_types.viewitems():
                if v[1] == self.command and re.match(v[0], self.rite_result_log):
                    return v[2]

            return "This is a new unknown error. Details: %s" % self.rite_result_log

