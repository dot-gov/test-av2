import sqlite3
from summarydata import SummaryData
from summarydatacoll import SummaryDataColl
from resultstates import ResultStates
sqlite_file = "results.db"


class DBReport(object):
    conn = None

    def __enter__(self, re_init=False):
        if not self.conn:
            self.conn = sqlite3.connect(sqlite_file)
        # Create table
        #timestamp is integer
        if re_init:
            self.recreate_database()

        return self

    def __exit__(self, typez, value, traceback):
        self.conn.commit()
        self.conn.close()

    #def __init__(self):

    def recreate_database(self, debug=False):
        self.conn.execute('''CREATE TABLE IF NOT EXISTS RESULTS( timestamp integer, start_timestamp integer, test_name text, vm text, command text, args text,
                        rite_result text, parsed_result text, rite_failed integer, rite_fail_log text, side text )''')

        self.conn.execute('''CREATE TABLE IF NOT EXISTS SUMMARY( start_timestamp integer, test_name text, vm text, prg integer, command text,
                        parsed_result text, log text, rite_failed integer, rite_fail_log text, manual integer, manual_comment text,
                        PRIMARY KEY (start_timestamp, test_name, vm, prg, manual) )''')

        #since sometime I make table modifications I prefer to recreate the views
        self.conn.execute('''DROP VIEW IF EXISTS SUMMARY_LATEST''')
        self.conn.execute('''DROP VIEW IF EXISTS SUMMARY_MANUAL''')

        self.conn.execute('''CREATE VIEW SUMMARY_LATEST AS
                                SELECT S.*
                                FROM SUMMARY S
                                WHERE MANUAL <> 1 AND
                                       START_TIMESTAMP = (
                                                       SELECT MAX(START_TIMESTAMP)
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
                                                       SELECT MAX(START_TIMESTAMP)
                                                         FROM SUMMARY X
                                                        WHERE S.VM = X.VM AND
                                                              S.TEST_NAME = X.TEST_NAME AND
                                                              MANUAL = 1
                                                   );''')

        if debug:
            self.annichilate_summary_table()

        self.apply_known_errors()

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

        cursor.close()

        if print_data:
            print "................................................................. "
            print "Dumping RESULT Table! (vm = %s , test_name = %s )" % (vm, test_name)
            print "................................................................. "

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
                                                                                 summary.rite_failed, summary.rite_fail_log,
                                                                                 summary.manual, summary.manual_comment))
            #print "inserted 1 row"
        except sqlite3.IntegrityError:
            print('Skipping insert, this summary already exists.')

    #this gets time-ordered (latest first) summary for a specific vm/test
    def get_latest_summary_rows(self, vm, test_name, print_data=False):
        return self.get_summary_rows(vm, test_name, 'SELECT * FROM SUMMARY_LATEST WHERE vm = ? and test_name = ? ORDER BY prg ASC', print_data)

    def get_known_summary_rows(self, vm, test_name, print_data=False):
        return self.get_summary_rows(vm, test_name, 'SELECT * FROM SUMMARY_MANUAL WHERE vm = ? and test_name = ? ORDER BY prg ASC', print_data)

    # def get_known_summary_rows(self, vm, test_name, print_data=False, strip_passed=True):
    #     return self.get_summary_rows(vm, test_name, 'SELECT * FROM SUMMARY ORDER BY ?, ?', print_data,
    #                                  strip_passed)

    def get_summary_rows(self, vm, test_name, query, print_data=False):
        cursor = self.conn.cursor()
        cursor.execute(query, (vm, test_name))
        rows = cursor.fetchall()
        cursor.close()

        if print_data:
            print "................................................................. "
            print "Dumping SUMMARY Table! (vm = %s , test_name = %s )" % (vm, test_name)
            print "................................................................. "
            if len(rows) == 0:
                print "<0 Rows!>"
            for i in rows:
                print i
            print "................................................................. "

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
        return SummaryDataColl(summarys)

    def apply_known_errors(self):
        self.conn.execute('DELETE FROM SUMMARY WHERE manual <> 0')

                #ANALYZER TESTS
                # self.insert_summary(SummaryData(0, u'VM_MELT_SRV_UTO', u'trendm', u'REPORT_KIND_INIT', 0, True, "TestTrendm",     u'VM_MELT_SRV_UTO', ResultStates.PASSED, False, u''))
                # self.insert_summary(SummaryData(0, u'VM_MELT_SRV_UTO', u'trendm', u'CALL', 1, True, "TestTrendm",                 u'VM_MELT_SRV_UTO', ResultStates.PASSED, False, u''))
                # self.insert_summary(SummaryData(0, u'VM_MELT_SRV_UTO', u'trendm', u'ENABLE', 2, True, "TestTrendm",               u"['tuesday', 'friday', 'sunday']", ResultStates.PASSED, False, u''))
                # self.insert_summary(SummaryData(0, u'VM_MELT_SRV_UTO', u'trendm', u'CALL', 3, True, "TestTrendm",                 u'INIT_DISPATCH', ResultStates.PASSED, False, u''))
                # self.insert_summary(SummaryData(0, 'VM_MELT_SRV_UTO', 'trendm', 'BUILD_SRV', 4, True, "TestTrendm",                   'windows_melt_uto', ResultStates.FAILED, False, ''))
                # self.insert_summary(SummaryData(0, u'VM_MELT_SRV_UTO', u'trendm', u'REVERT', 5, True, "TestTrendm",               u'[]', ResultStates.PASSED, False, u'' ))
                # self.insert_summary(SummaryData(0, u'VM_MELT_SRV_UTO', u'trendm', u'START_VM', 6, True, "TestTrendm",             u'AV_AGENT', ResultStates.PASSED, False, u'' ))
                # self.insert_summary(SummaryData(0, u'VM_MELT_SRV_UTO', u'trendm', u'SLEEP', 7, True, "TestTrendm",                u'60', ResultStates.PASSED, False, u'' ))
                # self.insert_summary(SummaryData(0, u'VM_MELT_SRV_UTO', u'trendm', u'END_CALL', 8, True, "TestTrendm",             u'INIT_DISPATCH', ResultStates.PASSED, False, u''))
                # self.insert_summary(SummaryData(0, u'VM_MELT_SRV_UTO', u'trendm', u'BUILD_SRV', 9, True, "TestTrendm",            u"['scout', 'windows_melt_uto', 'melt', 'melt', 'avmaster', (u'54982ebb7263731198b4f102', u'54b8cf1972637306707b7500', u'RCS_0000222569'), 'C:\\\\AVTest\\\\AVAgent\\\\build_windows_melt_uto_scout_melt_melt.zip']", ResultStates.PASSED, False, u''))
                # self.insert_summary(SummaryData(0, u'VM_MELT_SRV_UTO', u'trendm', u'REPORT_KIND_END', 10, True, "TestTrendm",      u"['VM_MELT_SRV_UTO', []]", ResultStates.PASSED, False, u''))
                # #this to test failing of VM
                # self.insert_summary(SummaryData(0, u'VM_MELT_SRV_UTO', u'avira', u'REPORT_KIND_INIT', 0, True, "No report FAIL MAnual Test avira",      u"['VM_MELT_SRV_UTO', []]", ResultStates.PASSED, True, "Failed because fail fail fail"))

        #kis 15 STATIC
        self.insert_summary_manual_error((u'VM_STATIC_SRV', u'kis15', u'BUILD_SRV', 39, u'\\[\\"\\+\\ FAILED\\ CHECK\\_STATIC\\.\\ SIGNATURE\\ DETECTION\\:\\ \\[\\\'build\\/blackberry\\\\\\\\\\\\\\\\install\\.bat\\\'\\,\\ \\\'build\\/blackberry\\\\\\\\\\\\\\\\res\\/inst\\_helper\\.exe\\\'\\,\\ \\\'build\\/blackberry\\\\\\\\\\\\\\\\res\\/facebook\\-1\\_4\\.5\\.cod\\\'\\,\\ \\\'build\\/blackberry\\\\\\\\\\\\\\\\res\\/facebook\\_4\\.5\\.cod\\\'\\]\\"\\,\\ \\"\\+\\ FAILED\\ SCOUT\\ BUILD\\.\\ SIGNATURE\\ DETECTION\\:\\ \\[\\\'build\\/blackberry\\\\\\\\\\\\\\\\install\\.bat\\\'\\,\\ \\\'build\\/blackberry\\\\\\\\\\\\\\\\res\\/inst\\_helper\\.exe\\\'\\,\\ \\\'build\\/blackberry\\\\\\\\\\\\\\\\res\\/facebook\\-1\\_4\\.5\\.cod\\\'\\,\\ \\\'build\\/blackberry\\\\\\\\\\\\\\\\res\\/facebook\\_4\\.5\\.cod\\\'\\]\\"\\,\\ \\\'\\+\\ ERROR\\:\\ Signature\\ detection\\\'\\]', 'FAILED', 0, u''), "KIS15 STATIC BB")
        self.insert_summary_manual_error((u'VM_STATIC_SRV', u'kis15', u'BUILD_SRV', 50, u'\\[\\"\\+\\ FAILED\\ CHECK\\_STATIC\\.\\ SIGNATURE\\ DETECTION\\:\\ \\[\\\'build\\/ios\\\\\\\\\\\\\\\\win\\/install\\.exe\\\'\\]\\"\\,\\ \\"\\+\\ FAILED\\ SCOUT\\ BUILD\\.\\ SIGNATURE\\ DETECTION\\:\\ \\[\\\'build\\/ios\\\\\\\\\\\\\\\\win\\/install\\.exe\\\'\\]\\"\\,\\ \\\'\\+\\ ERROR\\:\\ Signature\\ detection\\\'\\]', 'FAILED', 0, u''), "KIS15 STATIC IOS")

        #kis 14
            #Static
        self.insert_summary_manual_error((u'VM_STATIC_SRV', u'kis14', u'BUILD_SRV', 39, u'\\[\\"\\+\\ FAILED\\ CHECK\\_STATIC\\.\\ SIGNATURE\\ DETECTION\\:\\ \\[\\\'build\\/blackberry\\\\\\\\\\\\\\\\install\\.bat\\\'\\,\\ \\\'build\\/blackberry\\\\\\\\\\\\\\\\res\\/inst\\_helper\\.exe\\\'\\,\\ \\\'build\\/blackberry\\\\\\\\\\\\\\\\res\\/facebook\\-1\\_4\\.5\\.cod\\\'\\,\\ \\\'build\\/blackberry\\\\\\\\\\\\\\\\res\\/facebook\\_4\\.5\\.cod\\\'\\]\\"\\,\\ \\"\\+\\ FAILED\\ SCOUT\\ BUILD\\.\\ SIGNATURE\\ DETECTION\\:\\ \\[\\\'build\\/blackberry\\\\\\\\\\\\\\\\install\\.bat\\\'\\,\\ \\\'build\\/blackberry\\\\\\\\\\\\\\\\res\\/inst\\_helper\\.exe\\\'\\,\\ \\\'build\\/blackberry\\\\\\\\\\\\\\\\res\\/facebook\\-1\\_4\\.5\\.cod\\\'\\,\\ \\\'build\\/blackberry\\\\\\\\\\\\\\\\res\\/facebook\\_4\\.5\\.cod\\\'\\]\\"\\,\\ \\\'\\+\\ ERROR\\:\\ Signature\\ detection\\\'\\]', 'FAILED', 0, u''), "KIS14 STATIC BB")
        self.insert_summary_manual_error((u'VM_STATIC_SRV', u'kis14', u'BUILD_SRV', 48, u'\\[\\"\\+\\ ERROR\\:\\ \\[Errno\\ 13\\]\\ Permission\\ denied\\:\\ \\\'build\\/ios\\\\\\\\\\\\\\\\win\\/install\\.exe\\\'\\"\\]', 'FAILED', 0, u''), "KIS14 STATIC BB")
            #Exploit
        self.insert_summary_manual_error((u'VM_EXPLOIT_SRV', u'kis14', u'CHECK_INFECTION', 26, u'VM\\ is\\ INFECTED', 'FAILED', 0, u''), "KIS 14 EXPLOIT")

        #eset soldier (is elite)
        self.insert_summary_manual_error((u'VM_SOLDIER_SRV', u'eset', u'BUILD_SRV', 12, u"\\[\\'\\+\\ FAILED\\ SCOUT\\ BUILD\\.\\ CANNOT\\ FIND\\ ZIP\\ FILE\\ C\\:\\\\\\\\AVTest\\\\\\\\AVAgent\\\\\\\\build\\_windows\\_scout\\_silent\\_soldier\\_fast\\.zip\\ TO\\ UNZIP\\ IT\\'\\,\\ \\'\\+\\ ERROR\\:\\ No\\ file\\ to\\ unzip\\'\\]", 'FAILED', 0, u''), "ESET Soldier (is an elite)")

        #eset7 soldier
        self.insert_summary_manual_error((u'VM_SOLDIER_SRV', u'eset7', u'BUILD_SRV', 25, u"\\[\\'\\+\\ SUCCESS\\ UPGRADED\\ SYNC\\'\\,\\ \\'\\+\\ ERROR\\:\\ \\[Error\\ 193\\]\\ \\%1\\ is\\ not\\ a\\ valid\\ Win32\\ application\\'\\]", 'FAILED', 0, u''), "ESET 7 Soldier (is an elite)")
        self.insert_summary_manual_error((u'VM_SOLDIER_SRV', u'eset7', u'CROP', 26, u'\\[163\\,\\ 167\\,\\ 168\\]', 'CROP', 0, u''), "ESET 7 Soldier (is an elite)")
        self.insert_summary_manual_error((u'VM_SOLDIER_SRV', u'eset7', u'CHECK_INFECTION', 29, u'VM\\ is\\ INFECTED', 'FAILED', 0, u''), "ESET 7 Soldier (is an elite)")

        #fsecure exploit
        self.insert_summary_manual_error((u'VM_EXPLOIT_SRV', u'fsecure', u'BUILD_SRV', 21, u'\\[\\"\\+\\ SUCCESS\\ CHECK\\_STATIC\\:\\ \\[\\\'build\\/exploit\\_pdf\\\\\\\\\\\\\\\\example\\.exe\\\'\\]\\"\\,\\ \\\'\\+\\ SUCCESS\\ SCOUT\\ BUILD\\ \\(no\\ signature\\ detection\\)\\\'\\,\\ \\\'\\+\\ SUCCESS\\ SCOUT\\ EXECUTE\\\'\\,\\ \\\'\\+\\ ERROR\\:\\ \\[Error\\ 5\\]\\ Access\\ is\\ denied\\\'\\]', 'FAILED', 0, u''), "FSECURE EXPLOIT")

        #adaware exploit
        self.insert_summary_manual_error((u'VM_EXPLOIT_SRV', u'adaware', u'BUILD_SRV', 31, u'\\[\\"\\+\\ SUCCESS\\ CHECK\\_STATIC\\:\\ \\[\\\'build\\/exploit\\_pdf\\\\\\\\\\\\\\\\example\\.exe\\\'\\]\\"\\,\\ \\\'\\+\\ SUCCESS\\ SCOUT\\ BUILD\\ \\(no\\ signature\\ detection\\)\\\'\\,\\ \\\'\\+\\ SUCCESS\\ SCOUT\\ EXECUTE\\\'\\,\\ \\\'\\+\\ WARN\\ did\\ not\\ drop\\ startup\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ FAILED\\ SCOUT\\ SYNC\\\'\\]', 'FAILED', 0, u''), "ADAWARE EXPLOIT")

        #bitdef exploit
        self.insert_summary_manual_error((u'VM_EXPLOIT_SRV', u'bitdef', u'BUILD_SRV', 31, u'\\[\\"\\+\\ SUCCESS\\ CHECK\\_STATIC\\:\\ \\[\\\'build\\/exploit\\_pdf\\\\\\\\\\\\\\\\example\\.exe\\\'\\]\\"\\,\\ \\\'\\+\\ SUCCESS\\ SCOUT\\ BUILD\\ \\(no\\ signature\\ detection\\)\\\'\\,\\ \\\'\\+\\ SUCCESS\\ SCOUT\\ EXECUTE\\\'\\,\\ \\\'\\+\\ WARN\\ did\\ not\\ drop\\ startup\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ FAILED\\ SCOUT\\ SYNC\\\'\\]', 'FAILED', 0, u''), "BITDEF EXPLOIT")

        #bitdef
        # NB THIS MANUAL ERROR USES THE REGEXP (SO ANY IMAGE ID IN CROP WILL MATCH)
             # soldier CROP
        self.insert_summary_manual_error((u'VM_SOLDIER_SRV', u'bitdef15', u'CROP', 28, u'\\[.*\\]', 'CROP', 0, u''), "BITDEFENDER produces a FP crop with Elite and Soldier. From time to time is better to check manually known crops.")
             # elite CROP
        self.insert_summary_manual_error((u'VM_ELITE_FAST_SRV', u'bitdef15', u'CROP', 25, u'\\[.*\\]', 'CROP', 0, u''), "BITDEFENDER produces a FP crop with Elite and Soldier. From time to time is better to check manually known crops.")

        #gdata exploit
        self.insert_summary_manual_error((u'VM_EXPLOIT_SRV', u'gdata', u'BUILD_SRV', 31, u'\\[\\"\\+\\ SUCCESS\\ CHECK\\_STATIC\\:\\ \\[\\\'build\\/exploit\\_pdf\\\\\\\\\\\\\\\\example\\.exe\\\'\\]\\"\\,\\ \\\'\\+\\ SUCCESS\\ SCOUT\\ BUILD\\ \\(no\\ signature\\ detection\\)\\\'\\,\\ \\\'\\+\\ SUCCESS\\ SCOUT\\ EXECUTE\\\'\\,\\ \\\'\\+\\ WARN\\ did\\ not\\ drop\\ startup\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ FAILED\\ SCOUT\\ SYNC\\\'\\]', 'FAILED', 0, u''), "GDATA EXPLOIT")

        #RISING
        self.insert_summary_manual_error((u'VM_SOLDIER_SRV', u'risint', u'BUILD_SRV', 33, u"\\[\\'\\+\\ NOT\\ YET\\ UPGRADED\\ SYNC\\:\\ scout\\'\\,\\ \\'\\+\\ NOT\\ YET\\ UPGRADED\\ SYNC\\:\\ scout\\'\\,\\ \\'\\+\\ NOT\\ YET\\ UPGRADED\\ SYNC\\:\\ scout\\'\\,\\ \\'\\+\\ NOT\\ YET\\ UPGRADED\\ SYNC\\:\\ scout\\'\\,\\ \\'\\+\\ NOT\\ YET\\ UPGRADED\\ SYNC\\:\\ scout\\'\\,\\ \\'\\+\\ NOT\\ YET\\ UPGRADED\\ SYNC\\:\\ scout\\'\\,\\ \\'\\+\\ NOT\\ YET\\ UPGRADED\\ SYNC\\:\\ scout\\'\\,\\ \\'\\+\\ NOT\\ YET\\ UPGRADED\\ SYNC\\:\\ scout\\'\\,\\ \\'\\+\\ NOT\\ YET\\ UPGRADED\\ SYNC\\:\\ scout\\'\\,\\ \\'\\+\\ FAILED\\ SOLDIER\\ INSTALL\\'\\]", 'FAILED', 0, u''), "RISING (fails mostly every test)")
        self.insert_summary_manual_error((u'VM_ELITE_FAST_SRV', u'risint', u'BUILD_SRV', 33, u"\\[\\'\\+\\ NOT\\ YET\\ UPGRADED\\ SYNC\\:\\ scout\\'\\,\\ \\'\\+\\ NOT\\ YET\\ UPGRADED\\ SYNC\\:\\ scout\\'\\,\\ \\'\\+\\ NOT\\ YET\\ UPGRADED\\ SYNC\\:\\ scout\\'\\,\\ \\'\\+\\ NOT\\ YET\\ UPGRADED\\ SYNC\\:\\ scout\\'\\,\\ \\'\\+\\ NOT\\ YET\\ UPGRADED\\ SYNC\\:\\ scout\\'\\,\\ \\'\\+\\ NOT\\ YET\\ UPGRADED\\ SYNC\\:\\ scout\\'\\,\\ \\'\\+\\ NOT\\ YET\\ UPGRADED\\ SYNC\\:\\ scout\\'\\,\\ \\'\\+\\ NOT\\ YET\\ UPGRADED\\ SYNC\\:\\ scout\\'\\,\\ \\'\\+\\ NOT\\ YET\\ UPGRADED\\ SYNC\\:\\ scout\\'\\,\\ \\'\\+\\ FAILED\\ ELITE\\ INSTALL\\'\\]", 'FAILED', 0, u''), "RISING (fails mostly every test)")
        self.insert_summary_manual_error((u'VM_ELITE_FAST_SCOUTDEMO_SRV', u'risint', u'BUILD_SRV', 31, u"\\[\\'\\+\\ NOT\\ YET\\ UPGRADED\\ SYNC\\:\\ scout\\'\\,\\ \\'\\+\\ NOT\\ YET\\ UPGRADED\\ SYNC\\:\\ scout\\'\\,\\ \\'\\+\\ NOT\\ YET\\ UPGRADED\\ SYNC\\:\\ scout\\'\\,\\ \\'\\+\\ NOT\\ YET\\ UPGRADED\\ SYNC\\:\\ scout\\'\\,\\ \\'\\+\\ NOT\\ YET\\ UPGRADED\\ SYNC\\:\\ scout\\'\\,\\ \\'\\+\\ NOT\\ YET\\ UPGRADED\\ SYNC\\:\\ scout\\'\\,\\ \\'\\+\\ NOT\\ YET\\ UPGRADED\\ SYNC\\:\\ scout\\'\\,\\ \\'\\+\\ NOT\\ YET\\ UPGRADED\\ SYNC\\:\\ scout\\'\\,\\ \\'\\+\\ NOT\\ YET\\ UPGRADED\\ SYNC\\:\\ scout\\'\\,\\ \\'\\+\\ FAILED\\ ELITE\\ INSTALL\\'\\]", 'FAILED', 0, u''), "RISING (fails mostly every test)")
        self.insert_summary_manual_error((u'VM_MELT_SRV_AIR', u'risint', u'BUILD_SRV', 14, u'\\[\\"\\+\\ FAILED\\ CHECK\\_STATIC\\.\\ SIGNATURE\\ DETECTION\\:\\ \\[\\\'build\\/windows\\_melt\\_air\\\\\\\\\\\\\\\\exp\\_rite\\.exe\\\'\\]\\"\\,\\ \\"\\+\\ FAILED\\ SCOUT\\ BUILD\\.\\ SIGNATURE\\ DETECTION\\:\\ \\[\\\'build\\/windows\\_melt\\_air\\\\\\\\\\\\\\\\exp\\_rite\\.exe\\\'\\]\\"\\,\\ \\\'\\+\\ ERROR\\:\\ Signature\\ detection\\\'\\]', 'FAILED', 0, u''), "RISING (fails mostly every test)")
        self.insert_summary_manual_error((u'VM_EXPLOIT_SRV', u'risint', u'BUILD_SRV', 21, u'\\[\\"\\+\\ SUCCESS\\ CHECK\\_STATIC\\:\\ \\[\\\'build\\/exploit\\_pdf\\\\\\\\\\\\\\\\example\\.exe\\\'\\]\\"\\,\\ \\\'\\+\\ SUCCESS\\ SCOUT\\ BUILD\\ \\(no\\ signature\\ detection\\)\\\'\\,\\ \\\'\\+\\ SUCCESS\\ SCOUT\\ EXECUTE\\\'\\,\\ \\\'\\+\\ ERROR\\:\\ \\[Error\\ 1\\]\\ Incorrect\\ function\\\'\\]', 'FAILED', 0, u''), "RISING (fails mostly every test)")

        #CMCAV
            #static
        self.insert_summary_manual_error((u'VM_STATIC_SRV', u'cmcav', u'BUILD_SRV', 50, u'\\[\\"\\+\\ FAILED\\ CHECK\\_STATIC\\.\\ SIGNATURE\\ DETECTION\\:\\ \\[\\\'build\\/ios\\\\\\\\\\\\\\\\win\\/install\\.exe\\\'\\]\\"\\,\\ \\"\\+\\ FAILED\\ SCOUT\\ BUILD\\.\\ SIGNATURE\\ DETECTION\\:\\ \\[\\\'build\\/ios\\\\\\\\\\\\\\\\win\\/install\\.exe\\\'\\]\\"\\,\\ \\\'\\+\\ ERROR\\:\\ Signature\\ detection\\\'\\]', 'FAILED', 0, u''), "CMCAV STATIC IOS")
        self.insert_summary_manual_error((u'VM_STATIC_SRV', u'cmcav', u'CROP', 71, u'\\[761\\,\\ 766\\]', 'CROP', 0, u''), "CMCAV IOS")
            #elite
        self.insert_summary_manual_error((u'VM_ELITE_FAST_SRV', u'cmcav', u'BUILD_SRV', 13, u'\\[\\"\\+\\ FAILED\\ CHECK\\_STATIC\\.\\ SIGNATURE\\ DETECTION\\:\\ \\[\\\'build\\/windows\\\\\\\\\\\\\\\\agent\\.exe\\\'\\]\\"\\,\\ \\"\\+\\ FAILED\\ SCOUT\\ BUILD\\.\\ SIGNATURE\\ DETECTION\\:\\ \\[\\\'build\\/windows\\\\\\\\\\\\\\\\agent\\.exe\\\'\\]\\"\\,\\ \\\'\\+\\ ERROR\\:\\ Signature\\ detection\\\'\\]', 'FAILED', 0, u''), "CMCAV (blacklisted av)")
            #MELT AIR
        self.insert_summary_manual_error((u'VM_MELT_SRV_AIR', u'cmcav', u'CHECK_INFECTION', 19, u'VM\\ is\\ INFECTED', 'FAILED', 0, u''), "CMCAV MELT AIR (blacklisted av)")
            #exploit
        self.insert_summary_manual_error((u'VM_EXPLOIT_SRV', u'cmcav', u'CHECK_INFECTION', 25, u'VM\\ is\\ INFECTED', 'FAILED', 0, u''), "CMCAV EXPLOIT(blacklisted av)")

        #norton
        self.insert_summary_manual_error((u'VM_SOLDIER_SRV', u'norton', u'BUILD_SRV', 26, u"\\[\\'\\+\\ SUCCESS\\ UPGRADED\\ SYNC\\'\\,\\ \\'\\+\\ FAILED\\ UPGRADE\\ SOLDIER\\'\\]", 'FAILED', 0, u''), "NORTON SOLDIER (Norton is Elite)")
        self.insert_summary_manual_error((u'VM_SOLDIER_SRV', u'norton', u'CHECK_INFECTION', 30, u'VM\\ is\\ INFECTED', 'FAILED', 0, u''), "NORTON SOLDIER (Norton is Elite)")

        #comodo
            #soldier
        self.insert_summary_manual_error((u'VM_SOLDIER_SRV', u'comodo', u'BUILD_SRV', 33, u"\\[\\'\\+\\ NOT\\ YET\\ UPGRADED\\ SYNC\\:\\ scout\\'\\,\\ \\'\\+\\ NOT\\ YET\\ UPGRADED\\ SYNC\\:\\ scout\\'\\,\\ \\'\\+\\ NOT\\ YET\\ UPGRADED\\ SYNC\\:\\ scout\\'\\,\\ \\'\\+\\ NOT\\ YET\\ UPGRADED\\ SYNC\\:\\ scout\\'\\,\\ \\'\\+\\ NOT\\ YET\\ UPGRADED\\ SYNC\\:\\ scout\\'\\,\\ \\'\\+\\ NOT\\ YET\\ UPGRADED\\ SYNC\\:\\ scout\\'\\,\\ \\'\\+\\ NOT\\ YET\\ UPGRADED\\ SYNC\\:\\ scout\\'\\,\\ \\'\\+\\ NOT\\ YET\\ UPGRADED\\ SYNC\\:\\ scout\\'\\,\\ \\'\\+\\ NOT\\ YET\\ UPGRADED\\ SYNC\\:\\ scout\\'\\,\\ \\'\\+\\ FAILED\\ SOLDIER\\ INSTALL\\'\\]", 'FAILED', 0, u''), "COMODO (fails mostly every test due to sandbox and firewall)")
        self.insert_summary_manual_error((u'VM_SOLDIER_SRV', u'comodo', u'CROP', 34, u'\\[173\\,\\ 174\\]', 'CROP', 0, u''), "COMODO (fails mostly every test due to sandbox and firewall)")
        self.insert_summary_manual_error((u'VM_SOLDIER_SRV', u'comodo', u'CHECK_INFECTION', 37, u'VM\\ is\\ INFECTED', 'FAILED', 0, u''), "COMODO (fails mostly every test due to sandbox and firewall)")
            #elite
        self.insert_summary_manual_error((u'VM_ELITE_FAST_SRV', u'comodo', u'CROP', 26, u'\\[4\\,\\ 7\\]', 'CROP', 0, u''), "COMODO (fails mostly every test due to sandbox and firewall)")
        self.insert_summary_manual_error((u'VM_ELITE_FAST_SRV', u'comodo', u'CHECK_INFECTION', 28, u'VM\\ is\\ INFECTED', 'FAILED', 0, u''), "COMODO (fails mostly every test due to sandbox and firewall)")
            #elite demo
        self.insert_summary_manual_error((u'VM_ELITE_FAST_SCOUTDEMO_SRV', u'comodo', u'CHECK_INFECTION', 24, u'VM\\ is\\ INFECTED', 'FAILED', 0, u''), "COMODO (fails mostly every test due to sandbox and firewall)")

        #avast
        self.insert_summary_manual_error((u'VM_SOLDIER_SRV', u'avast', u'CHECK_INFECTION', 31, u'VM\\ is\\ INFECTED', 'FAILED', 0, u''), "AVAST SOLDIER FAILES UNINSTALLATION (Avast is Elite)")
        #clamav
        self.insert_summary_manual_error((u'VM_SOLDIER_SRV', u'clamav', u'CHECK_INFECTION', 31, u'VM\\ is\\ INFECTED', 'FAILED', 0, u''), "CLAMAV SOLDIER FAILES UNINSTALLATION (Clamav is Elite)")

        #kis 32 (blacklisted)
            # static bb + ios
        self.insert_summary_manual_error((u'VM_STATIC_SRV', u'kis32', u'BUILD_SRV', 37, u'\\[\\"\\+\\ ERROR\\:\\ \\[Errno\\ 13\\]\\ Permission\\ denied\\:\\ \\\'build\\/blackberry\\\\\\\\\\\\\\\\install\\.bat\\\'\\"\\]', 'FAILED', 0, u''), "KIS 32 STATIC BB+IOS")
        self.insert_summary_manual_error((u'VM_STATIC_SRV', u'kis32', u'BUILD_SRV', 46, u'\\[\\"\\+\\ ERROR\\:\\ \\[Errno\\ 13\\]\\ Permission\\ denied\\:\\ \\\'build\\/ios\\\\\\\\\\\\\\\\win\\/install\\.exe\\\'\\"\\]', 'FAILED', 0, u''), "KIS 32 STATIC BB+IOS")
            #soldier
        self.insert_summary_manual_error((u'VM_SOLDIER_SRV', u'kis32', u'BUILD_SRV', 23, u'\\[\\"\\+\\ SUCCESS\\ CHECK\\_STATIC\\:\\ \\[\\\'build\\/windows\\\\\\\\\\\\\\\\agent\\.exe\\\'\\]\\"\\,\\ \\\'\\+\\ SUCCESS\\ SCOUT\\ BUILD\\ \\(no\\ signature\\ detection\\)\\\'\\,\\ \\\'\\+\\ SUCCESS\\ SCOUT\\ EXECUTE\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ FAILED\\ SCOUT\\ SYNC\\\'\\]', 'FAILED', 0, u''), "KIS 32 SOLDIER (IS BLACKLISTED)")
            #elite
        self.insert_summary_manual_error((u'VM_ELITE_FAST_SRV', u'kis32', u'BUILD_SRV', 23, u'\\[\\"\\+\\ SUCCESS\\ CHECK\\_STATIC\\:\\ \\[\\\'build\\/windows\\\\\\\\\\\\\\\\agent\\.exe\\\'\\]\\"\\,\\ \\\'\\+\\ SUCCESS\\ SCOUT\\ BUILD\\ \\(no\\ signature\\ detection\\)\\\'\\,\\ \\\'\\+\\ SUCCESS\\ SCOUT\\ EXECUTE\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ FAILED\\ SCOUT\\ SYNC\\\'\\]', 'FAILED', 0, u''), "KIS 32 ELITE (IS BLACKLISTED)")
            #elite demo
        self.insert_summary_manual_error((u'VM_ELITE_FAST_SCOUTDEMO_SRV', u'kis32', u'BUILD_SRV', 23, u'\\[\\"\\+\\ SUCCESS\\ CHECK\\_STATIC\\:\\ \\[\\\'build\\/windows\\_demo\\\\\\\\\\\\\\\\agent\\.exe\\\'\\]\\"\\,\\ \\\'\\+\\ SUCCESS\\ SCOUT\\ BUILD\\ \\(no\\ signature\\ detection\\)\\\'\\,\\ \\\'\\+\\ SUCCESS\\ SCOUT\\ EXECUTE\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ FAILED\\ SCOUT\\ SYNC\\\'\\]', 'FAILED', 0, u''), "KIS 32 ELITE DEMO (IS BLACKLISTED)")
            #exploit
        self.insert_summary_manual_error((u'VM_EXPLOIT_SRV', u'kis32', u'BUILD_SRV', 30, u'\\[\\"\\+\\ SUCCESS\\ CHECK\\_STATIC\\:\\ \\[\\\'build\\/exploit\\_pdf\\\\\\\\\\\\\\\\example\\.exe\\\'\\]\\"\\,\\ \\\'\\+\\ SUCCESS\\ SCOUT\\ BUILD\\ \\(no\\ signature\\ detection\\)\\\'\\,\\ \\\'\\+\\ SUCCESS\\ SCOUT\\ EXECUTE\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ FAILED\\ SCOUT\\ SYNC\\\'\\]', 'FAILED', 0, u''), "KIS 32 EXPLOIT (IS BLACKLISTED)")

        #syscare failes due to mouse emulation
            #soldier
        self.insert_summary_manual_error((u'VM_SOLDIER_SRV', u'syscare', u'BUILD_SRV', 23, u'\\[\\"\\+\\ SUCCESS\\ CHECK\\_STATIC\\:\\ \\[\\\'build\\/windows\\\\\\\\\\\\\\\\agent\\.exe\\\'\\]\\"\\,\\ \\\'\\+\\ SUCCESS\\ SCOUT\\ BUILD\\ \\(no\\ signature\\ detection\\)\\\'\\,\\ \\\'\\+\\ SUCCESS\\ SCOUT\\ EXECUTE\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ FAILED\\ SCOUT\\ SYNC\\\'\\]', 'FAILED', 0, u''), "SYSCARE TESTS FAILS DUE TO MOUSE EMULATION")
            #elite
        self.insert_summary_manual_error((u'VM_ELITE_FAST_SRV', u'syscare', u'BUILD_SRV', 23, u'\\[\\"\\+\\ SUCCESS\\ CHECK\\_STATIC\\:\\ \\[\\\'build\\/windows\\\\\\\\\\\\\\\\agent\\.exe\\\'\\]\\"\\,\\ \\\'\\+\\ SUCCESS\\ SCOUT\\ BUILD\\ \\(no\\ signature\\ detection\\)\\\'\\,\\ \\\'\\+\\ SUCCESS\\ SCOUT\\ EXECUTE\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ FAILED\\ SCOUT\\ SYNC\\\'\\]', 'FAILED', 0, u''), "SYSCARE TESTS FAILS DUE TO MOUSE EMULATION")
            #elite demo
        self.insert_summary_manual_error((u'VM_ELITE_FAST_SCOUTDEMO_SRV', u'syscare', u'BUILD_SRV', 23, u'\\[\\"\\+\\ SUCCESS\\ CHECK\\_STATIC\\:\\ \\[\\\'build\\/windows\\_demo\\\\\\\\\\\\\\\\agent\\.exe\\\'\\]\\"\\,\\ \\\'\\+\\ SUCCESS\\ SCOUT\\ BUILD\\ \\(no\\ signature\\ detection\\)\\\'\\,\\ \\\'\\+\\ SUCCESS\\ SCOUT\\ EXECUTE\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ FAILED\\ SCOUT\\ SYNC\\\'\\]', 'FAILED', 0, u''), "SYSCARE TESTS FAILS DUE TO MOUSE EMULATION")
            #exploit
        self.insert_summary_manual_error((u'VM_EXPLOIT_SRV', u'syscare', u'CHECK_INFECTION', 38, u'VM\\ is\\ INFECTED', 'FAILED', 0, u''), "SYSCARE TESTS FAILS DUE TO MOUSE EMULATION")

        #mbytes exploit
        self.insert_summary_manual_error((u'VM_EXPLOIT_SRV', u'mbytes', u'CHECK_INFECTION', 25, u'VM\\ is\\ INFECTED', 'FAILED', 0, u''), "MBYTES DETECTS EXPLOIT DURING UNINSTALL (or uninstall fails in some way)")

        #avast32
            # soldier uninstall
        self.insert_summary_manual_error((u'VM_SOLDIER_SRV', u'avast32', u'CHECK_INFECTION', 31, u'VM\\ is\\ INFECTED', 'FAILED', 0, u''), "AVAST32 FAILS SOLDIER UNINSTALLATION, BUT IS ELITE ")
            #elite fp crop
        self.insert_summary_manual_error((u'VM_ELITE_FAST_SRV', u'avast32', u'CROP', 27, u'\\[152\\,\\ 154\\]', 'CROP', 0, u''), "AVAST32 SAVES A CROP IN ELITE, DUE TO A rundll32 ERROR (probably caused by avast)")

    def insert_summary_manual_error(self, txt_tuple, manual_comment):
        test, vm, command, prg, log, result_state, rite_failed, rite_fail_log = txt_tuple
        # SYNTAX: self.insert_summary(SummaryData(0, u'VM_MELT_SRV_UTO', u'trendm', u'REPORT_KIND_INIT', 0, True, "TestTrendm",     u'VM_MELT_SRV_UTO', ResultStates.PASSED, False, u''))
        self.insert_summary(SummaryData(0, test, vm, command, prg, True, manual_comment, log, ResultStates().get_state_from_content(result_state), rite_failed, rite_fail_log))


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