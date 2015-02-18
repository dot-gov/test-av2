__author__ = 'mlosito'

from resultstates import ResultStates
from resultdata import ResultData


class SummaryData(ResultData):
    #timestamp will be equal to start_timestamp
    #side, args, rite_result are none
    def __init__(self, start_timestamp, test_name, vm, command, prg, manual, manual_comment, rite_result_log=None,
                 parsed_result=ResultStates.NONE, rite_failed=False, rite_fail_log=None):
        ResultData.__init__(self, start_timestamp, start_timestamp, test_name, vm, command, args=None, rite_result=None,
                            rite_result_log=rite_result_log,
                            parsed_result=parsed_result, rite_failed=rite_failed, rite_fail_log=rite_fail_log, side=None)
        self.prg = prg
        self.manual = manual
        self.manual_comment = manual_comment
