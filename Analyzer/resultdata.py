__author__ = 'mlosito'

from resultstates import ResultStates

failing_commands = ["BUILD", "BUILD_SRV", "CHECK_INFECTION"]
cropping_commands = ["CROP"]
always_passed_commands = ["REPORT_KIND_END", "REPORT_KIND_INIT", "ENABLE"]


class ResultData(object):

    def __init__(self, timestamp, start_timestamp, test_name, vm, command, args=None, rite_result=None, rite_result_log=None, parsed_result=ResultStates.NONE, rite_failed=False, rite_fail_log=None, side=None):

        assert vm
        assert command
        assert test_name
        self.timestamp = str(timestamp).split('.')[0]   # removes milliseconds
        self.start_timestamp = start_timestamp
        self.test_name = test_name
        self.vm = vm
        self.command = command
        self.args = args
        self.rite_result = rite_result
        self.rite_result_log = rite_result_log
        self.parsed_result = parsed_result
        self.rite_failed = rite_failed
        self.rite_fail_log = rite_fail_log
        self.side = side
        if parsed_result == ResultStates.NONE:
            self.parse_result()

    def print_me(self):
        print "-----------------"
        print "VM: ", self.vm
        print "Test: ", self.test_name
        print "Timestamp: ", self.timestamp
        print "Start Timestamp: ", self.start_timestamp
        print "Command: ", self.command
        print "Arguments: ", self.args
        print "Result from Rite: ", self.rite_result
        print "Result log from Rite: ", self.rite_result_log
        print "Parsed result: ", self.parsed_result
        print "Rite Failed: ", self.rite_failed
        print "Rite fail log: ", self.rite_fail_log
        print "Command side: ", self.side

    def print_short(self):
        print "-----------------"
        print "VM: ", self.vm
        print "Test: ", self.test_name
        print "Command: ", self.command
        print "Result from Rite: ", self.rite_result
        print "Parsed result: ", self.parsed_result
        print "Rite Failed: ", self.rite_failed

    def get_cause(self, print_data=False):
        x = "%s(%s) | %s | vm: %s | %s | Comm: %s | Logs: %s" % (self.parsed_result[0], self.parsed_result[1], self.test_name, self.vm, self.timestamp, self.command.ljust(15), self.rite_result_log)
        if print_data:
            print x
        return x

    def get_value(self):
        if self.parsed_result:
            return self.parsed_result[1]
        else:
            return None

    #this contains all the intelligence to parse the rite Output
    def parse_result(self):
        # passed case
        if self.rite_result is True:
            self.parsed_result = ResultStates.PASSED

        # some commands never fails (REPORT_KIND_END)
        if self.command in always_passed_commands:
            self.parsed_result = ResultStates.PASSED

        #crop case
        if self.command in cropping_commands and self.rite_result is False:
            self.parsed_result = ResultStates.CROP

        #fail and no sync case
        if self.command in failing_commands and self.rite_result is False:
            #and "FAILED" in self.rite_result_log
            if "NO SCOUT SYNC" in self.rite_result_log:
                self.parsed_result = ResultStates.NO_SYNC
            else:
                self.parsed_result = ResultStates.FAILED

        #debug
        # print "# Parsed result %s for cmd %s -> %s" % (self.rite_result, self.command, self.parsed_result[0])