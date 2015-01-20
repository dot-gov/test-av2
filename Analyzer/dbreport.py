import sqlite3
from summarydata import SummaryData
from resultstates import ResultStates
sqlite_file = "results.db"


class DBReport(object):
    conn = None

    def __enter__(self):
        if not self.conn:
            self.conn = sqlite3.connect(sqlite_file)
        # Create table
        #timestamp is integer

        self.conn.execute('''CREATE TABLE IF NOT EXISTS RESULTS( timestamp integer, start_timestamp integer, test_name text, vm text, command text, args text,
                        rite_result text, parsed_result text, rite_failed text, rite_fail_log text, side text )''')

        self.conn.execute('''CREATE TABLE IF NOT EXISTS SUMMARY( start_timestamp integer, test_name text, vm text, prg integer, command text,
                        parsed_result text, log text, rite_failed text, rite_fail_log text, manual text, manual_comment text,
                        PRIMARY KEY (start_timestamp, test_name, vm, prg, manual) )''')

        #since sometime I make table modifications I prefer to recreate the views
        self.conn.execute('''DROP VIEW IF EXISTS SUMMARY_LATEST''')
        self.conn.execute('''DROP VIEW IF EXISTS SUMMARY_MANUAL''')

        self.conn.execute('''CREATE VIEW SUMMARY_LATEST AS
                                SELECT S.*
                                FROM SUMMARY S
                                WHERE MANUAL <> 1 AND
                                       START_TIMESTAMP = (
                                                       SELECT MIN(START_TIMESTAMP)
                                                         FROM SUMMARY X
                                                        WHERE S.VM = X.VM AND
                                                              S.TEST_NAME = X.TEST_NAME AND
                                                              MANUAL <> 1

                                                   );''')

        self.conn.execute('''CREATE VIEW SUMMARY_MANUAL AS
                                SELECT S.*
                                  FROM SUMMARY S
                                 WHERE MANUAL = 1 AND
                                       START_TIMESTAMP = (
                                                       SELECT MIN(START_TIMESTAMP)
                                                         FROM SUMMARY X
                                                        WHERE S.VM = X.VM AND
                                                              S.TEST_NAME = X.TEST_NAME AND
                                                              MANUAL = 1
                                                   );''')

        #debug
        self.annichilate_summary_table()

        self.apply_known_errors()

        return self

    def __exit__(self, typez, value, traceback):
        self.conn.commit()
        self.conn.close()

    #def __init__(self):

    def get_conn(self):
        return self.conn

    def get_results_rows(self, vm, test_name, print_data=False):

        cursor = self.conn.cursor()

        if vm and test_name:
            cursor.execute('SELECT * FROM RESULTS WHERE vm = ? and test_name = ?', (vm, test_name))

        if vm and not test_name:
            cursor.execute('SELECT * FROM RESULTS WHERE vm = ?', [vm])

        if not vm and test_name:
            cursor.execute('SELECT * FROM RESULTS WHERE test_name = ?', [test_name])

        if not vm and not test_name:
            cursor.execute('SELECT * FROM RESULTS')

        rows = cursor.fetchall()

        if print_data:
            print " ============================================================ "
            print "Dumping RESULT Table! (vm = %s , test_name = %s )" % (vm, test_name)
            print " ============================================================ "

            for i in rows:
                print i

        return rows

    def insert_result(self, result):
        #nine params MISSING RITE LOG
        self.conn.execute('INSERT INTO RESULTS VALUES(?,?,?,?,?,?,?,?,?,?,?)', (result.timestamp, result.start_timestamp, result.test_name, result.vm,
                                                                                result.command, str(result.args), result.rite_result,
                                                                                result.parsed_result[0], result.rite_failed, result.rite_fail_log,
                                                                                result.side))

    def print_results_table(self):
        self.get_results_rows(None, None, True)

    def annichilate_result_table(self):
        print "REMOVING COMPLETELY THE RESULTS TABLE!"
        self.conn.execute('DELETE FROM RESULTS')

    def annichilate_summary_table(self):
        print "REMOVING COMPLETELY THE SUMMARY TABLE!"
        self.conn.execute('DELETE FROM SUMMARY')

    # start_timestamp integer, test_name text, vm text, prg integer, command text, parsed_result text, log text, rite_failed text, rite_failed_log text, manual text, manual_comment text
    def insert_summary(self, summary):
        try:
            self.conn.execute('INSERT INTO SUMMARY VALUES (?,?,?,?,?,?,?,?,?,?,?)', (summary.start_timestamp, summary.test_name, summary.vm, summary.prg,
                                                                                 summary.command, summary.parsed_result[0], str(summary.rite_result_log),
                                                                                 str(summary.rite_failed), summary.rite_fail_log,
                                                                                 summary.manual, summary.manual_comment))
            #print "inserted 1 row"
        except sqlite3.IntegrityError:
            print('Skipping insert, this summary already exists.')

    #this gets time-ordered (latest first) summary for a specific vm/test
    def get_latest_summary_rows(self, vm, test_name, print_data=False, strip_passed=True):
        return self.get_summary_rows(vm, test_name, 'SELECT * FROM SUMMARY_LATEST WHERE vm = ? and test_name = ? ORDER BY prg ASC', print_data,
                                     strip_passed)

    def get_known_summary_rows(self, vm, test_name, print_data=False, strip_passed=True):
        return self.get_summary_rows(vm, test_name, 'SELECT * FROM SUMMARY_MANUAL WHERE vm = ? and test_name = ? ORDER BY prg ASC', print_data,
                                     strip_passed)

    # def get_known_summary_rows(self, vm, test_name, print_data=False, strip_passed=True):
    #     return self.get_summary_rows(vm, test_name, 'SELECT * FROM SUMMARY ORDER BY ?, ?', print_data,
    #                                  strip_passed)

    def get_summary_rows(self, vm, test_name, query, print_data=False, strip_passed=True):
        cursor = self.conn.cursor()
        cursor.execute(query, (vm, test_name))
        rows = cursor.fetchall()

        if print_data:
            print " =================================================================================================== "
            print "Dumping SUMMARY Table! (vm = %s , test_name = %s )" % (vm, test_name)
            print " =================================================================================================== "
            if len(rows) == 0:
                print "<0 Rows!>"
            for i in rows:
                print i
            print " =================================================================================================== "

        summarys = []
        # from # start_timestamp integer 0 , test_name text 1, vm text 2, prg integer 3, command text 4, parsed_result text 5, log text 6,
        #                   rite_failed text 7, rite_failed_log text 8, manual text, manual_comment text
        # to timestamp, start_timestamp, test_name, vm, command, prg, manual, manual_comment, args=None, rite_result=None, rite_result_log=None,
        #                    parsed_result=ResultStates.NONE, rite_failed=False, rite_fail_log=None, side=None

        for i in rows:
                                        #start_timestamp , test_name , vm , command prg
            summarys.append(SummaryData(i[0], i[1], i[2], i[4], i[3],
                                        # manual, manual_comment,
                                        i[9], i[10],
                                        # args=None, rite_result=None, rite_result_log=None, parsed_result=ResultStates.NONE,
                                        i[6], ResultStates().get_state_from_content(i[5].strip()),
                                        # rite_failed=False, rite_fail_log=None
                                        i[7], i[8]
                                        ))

        if strip_passed:
            parsed_summarys = []
            for i in summarys:
                if i.parsed_result[0] not in ['PASSED', 'NONE'] or i.rite_failed:
                    parsed_summarys.append(i)

            return parsed_summarys
        else:
            return summarys

    def apply_known_errors(self):
        self.conn.execute('DELETE FROM SUMMARY WHERE manual <> 0')

                        # self, start_timestamp, test_name,             vm, command,      prg, manual, manual_comment,
                        # rite_result_log=None, parsed_result=ResultStates.NONE, rite_failed=False, rite_fail_log=None):

        #riattivare
        #self.insert_summary(SummaryData(0, 'VM_ELITE_FAST_DEMO_SRV', 'avira', 'BUILD_SRV', 0, '1', "Test avira falloso comment", "Failed log result", ResultStates.FAILED, False, ""))

        self.insert_summary(SummaryData(0, u'VM_MELT_SRV_UTO', u'trendm', u'REPORT_KIND_INIT', 0, '1', "TestTrendm",     u'VM_MELT_SRV_UTO', ResultStates.PASSED, False, u''))
        self.insert_summary(SummaryData(0, u'VM_MELT_SRV_UTO', u'trendm', u'CALL', 1, '1', "TestTrendm",                 u'VM_MELT_SRV_UTO', ResultStates.PASSED, False, u''))
        self.insert_summary(SummaryData(0, u'VM_MELT_SRV_UTO', u'trendm', u'ENABLE', 2, '1', "TestTrendm",               u"['tuesday', 'friday', 'sunday']", ResultStates.PASSED, False, u''))
        self.insert_summary(SummaryData(0, u'VM_MELT_SRV_UTO', u'trendm', u'CALL', 3, '1', "TestTrendm",                 u'INIT_DISPATCH', ResultStates.PASSED, False, u''))
        self.insert_summary(SummaryData(0, 'VM_MELT_SRV_UTO', 'trendm', 'BUILD', 4, '1', "TestTrendm",             'False', ResultStates.FAILED, False, ''))
        self.insert_summary(SummaryData(0, u'VM_MELT_SRV_UTO', u'trendm', u'REVERT', 5, '1', "TestTrendm",               u'[]', ResultStates.PASSED, False, u'' ))
        self.insert_summary(SummaryData(0, u'VM_MELT_SRV_UTO', u'trendm', u'START_VM', 6, '1', "TestTrendm",             u'AV_AGENT', ResultStates.PASSED, False, u'' ))
        self.insert_summary(SummaryData(0, u'VM_MELT_SRV_UTO', u'trendm', u'SLEEP', 7, '1', "TestTrendm",                u'60', ResultStates.PASSED, False, u'' ))
        self.insert_summary(SummaryData(0, u'VM_MELT_SRV_UTO', u'trendm', u'END_CALL', 8, '1', "TestTrendm",             u'INIT_DISPATCH', ResultStates.PASSED, False, u''))
        self.insert_summary(SummaryData(0, u'VM_MELT_SRV_UTO', u'trendm', u'BUILD_SRV', 9, '1', "TestTrendm",            u"['scout', 'windows_melt_uto', 'melt', 'melt', 'avmaster', (u'54982ebb7263731198b4f102', u'54b8cf1972637306707b7500', u'RCS_0000222569'), 'C:\\\\AVTest\\\\AVAgent\\\\build_windows_melt_uto_scout_melt_melt.zip']", ResultStates.FAILED, False, u''))
        self.insert_summary(SummaryData(0, u'VM_MELT_SRV_UTO', u'trendm', u'REPORT_KIND_END', 10, '1', "TestTrendm",      u"['VM_MELT_SRV_UTO', []]", ResultStates.PASSED, False, u''))
        #this to test failing of VM
        self.insert_summary(SummaryData(0, u'VM_MELT_SRV_UTO', u'avira', u'REPORT_KIND_INIT', 0, '1', "No report Test Manual avira",      u"['VM_MELT_SRV_UTO', []]", ResultStates.PASSED, True, "Failed because fail fail fail"))

        # self.insert_summary(0, 'VM_ELITE_FAST_DEMO_SRV', 'avira', '0', 'BUILD_SRV', 'FAILED', 'logblabla', False, 1)
        # self.insert_summary(0, 'VM_ELITE_FAST_DEMO_SRV', 'avira', '1', 'BUILD_SRV', 'FAILED', 'logblabla', False, 1)
        # self.insert_summary(0, 'VM_ELITE_FAST_DEMO_SRV', 'norton', '0', 'CROP', 'CROP', '*', False, 1)
        # self.insert_summary(0, 'VM_SOLDIER_SRV', 'eset', '0', 'BUILD_SRV', 'FAILED', 'logblabla', False, 1)
        # self.insert_summary(0, 'VM_SOLDIER_SRV', 'eset', '1', 'TEST_CMD', 'FAILED', 'logblabla', False, 1)
        # self.insert_summary(0, 'VM_SOLDIER_SRV', 'eset', '2', 'CHECK_INFECTION', 'FAILED', 'logblabla', False, 1)




# def parse_known_error_row(original_row):
#         if original_row:
#             print "dc", original_row
#             row = list(original_row)
#             if row[3]:
#                 errorlist = eval(row[3])
#             else:
#                 errorlist = None
#             return row[0], row[1], row[2], errorlist, row[4], row[5]
#         else:
#             return None