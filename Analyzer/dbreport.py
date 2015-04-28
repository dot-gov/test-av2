import sqlite3
import time
from datetime import date, timedelta, datetime
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

        self.conn.execute('''CREATE TABLE IF NOT EXISTS SUMMARY( start_timestamp integer, end_timestamp integer, test_name text, vm text, prg integer, command text,
                        parsed_result text, log text, rite_failed integer, rite_fail_log text, manual integer, manual_optional integer, manual_comment text,
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

    # def get_results_rows(self, vm, test_name, print_data=False):
    #
    #     cursor = self.conn.cursor()
    #
    #     if vm and test_name:
    #         cursor.execute('SELECT * FROM RESULTS WHERE vm = ? and test_name = ?', (vm, test_name))
    #
    #     if vm and not test_name:
    #         cursor.execute('SELECT * FROM RESULTS WHERE vm = ?', [vm])
    #
    #     if not vm and test_name:
    #         cursor.execute('SELECT * FROM RESULTS WHERE test_name = ?', [test_name])
    #
    #     if not vm and not test_name:
    #         cursor.execute('SELECT * FROM RESULTS')
    #
    #     rows = cursor.fetchall()
    #
    #     cursor.close()
    #
    #     if print_data:
    #         print "................................................................. "
    #         print "Dumping RESULT Table! (vm = %s , test_name = %s )" % (vm, test_name)
    #         print "................................................................. "
    #
    #         for i in rows:
    #             print i
    #
    #     return rows

    def insert_result(self, result):
        #nine params MISSING RITE LOG
        self.conn.execute('INSERT INTO RESULTS VALUES(?,?,?,?,?,?,?,?,?,?,?)', (result.timestamp, result.start_timestamp, result.test_name, result.vm,
                                                                                result.command, str(result.args), result.rite_result,
                                                                                result.parsed_result[0], result.rite_failed, result.rite_fail_log,
                                                                                result.side))

    # def print_results_table(self):
    #     self.get_results_rows(None, None, True)

    def annichilate_result_table(self):
        print "REMOVING COMPLETELY THE RESULTS TABLE!"
        self.conn.execute('DELETE FROM RESULTS')

    def annichilate_summary_table(self):
        print "REMOVING COMPLETELY THE SUMMARY TABLE!"
        self.conn.execute('DELETE FROM SUMMARY')

    # start_timestamp integer, test_name text, vm text, prg integer, command text, parsed_result text, log text, rite_failed text, rite_failed_log text, manual text, manual_comment text
    def insert_summary(self, summary):
        try:
            self.conn.execute('INSERT INTO SUMMARY VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)', (summary.start_timestamp, summary.end_timestamp, summary.test_name, summary.vm, summary.prg,
                                                                                 summary.command, summary.parsed_result[0], str(summary.rite_result_log),
                                                                                 summary.rite_failed, summary.rite_fail_log,
                                                                                 summary.manual, summary.manual_optional, summary.manual_comment))
            return True
            #print "inserted 1 row"
        except sqlite3.IntegrityError:
            #print('Skipping insert, this summary already exists.')
            return False

    #this gets time-ordered (latest first) summary for a specific vm/test
    def get_latest_summary_rows(self, vm, test_name, print_data=False):
        return self.get_summary_rows(vm, test_name, 'SELECT * FROM SUMMARY_LATEST WHERE vm = ? and test_name = ? ORDER BY prg ASC', print_data)

    def get_known_summary_rows(self, vm, test_name, print_data=False):
        return self.get_summary_rows(vm, test_name, 'SELECT * FROM SUMMARY_MANUAL WHERE vm = ? and test_name = ? ORDER BY prg ASC', print_data)

    #gets previous summarys going back x DAYS
    def get_previous_summary_rows(self, vm, test_name, days, print_data=False):
        datenow = date.today()
        dateback = datenow - timedelta(days=days)
        timestamp_day = datetime.combine(dateback, datetime.min.time())
        #strips away fraction of seconds
        timestamp_day = str(timestamp_day.strftime("%s")).split('.')[0]
        print timestamp_day
        query = '''SELECT S.* FROM SUMMARY S
                    WHERE MANUAL <> 1 AND
                        START_TIMESTAMP < %s AND
                           START_TIMESTAMP = (
                                           SELECT MAX(START_TIMESTAMP)
                                            FROM SUMMARY X
                                            WHERE S.VM = X.VM AND
                                                  S.TEST_NAME = X.TEST_NAME AND
                                                  MANUAL <> 1 AND
                                                  START_TIMESTAMP < %s

                                       )
                            AND vm = ?
                            AND test_name = ?
                            ORDER BY prg ASC
                            ;''' % (timestamp_day, timestamp_day)
        return self.get_summary_rows(vm, test_name, query, True)

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

# DB
# ( start_timestamp integer, end_timestamp integer, test_name text, vm text, prg integer, command text,
#                         parsed_result text, log text, rite_failed integer, rite_fail_log text, manual integer, manual_optional integer, manual_comment text,
#
# SummasryData
# start_timestamp, end_timestamp, test_name, vm, command, prg, manual, manual_optional=False, manual_comment="", rite_result_log=None,
#                  parsed_result=ResultStates.NONE, rite_failed=False, rite_fail_log=None):

        for i in rows:
                                        #start_timestamp , test_name , vm , command prg
            summarys.append(SummaryData(i[0], i[1], i[2], i[3], i[5], i[4],
                                        # manual, manual_comment,
                                        i[10], i[11], i[12],
                                        # args=None, rite_result=None, rite_result_log=None, parsed_result=ResultStates.NONE,
                                        i[7], ResultStates().get_state_from_content(i[6].strip()),
                                        # rite_failed=False, rite_fail_log=None
                                        i[8], i[9]
                                        ))
        return SummaryDataColl(summarys)

    def apply_known_errors(self):
        self.conn.execute('DELETE FROM SUMMARY WHERE manual <> 0')

        error_types = {'popup': [u"\\[.*\\]", "Popup may occur"],
                       'infected': [u'VM\\ is\\ INFECTED', "Vm is infected after instance close. Usual if the agent cant sync"],
                       'no_instance_id': [u"\\[\\'\\+\\ FAILED\\ NO\\ INSTANCE\\_ID\\'\\]", "Cannot sync"],
                       'trigger': [u"\\[\\'TRIGGER\\ FAILED.*", "Cannot trigger sync with mouse emulation"],
                       '193': [u"\\[\\'\\+\\ SUCCESS\\ UPGRADED\\ SYNC\\'\\,\\ \\'\\+\\ ERROR\\:\\ \\[Error\\ 193\\]\\ \\%1\\ is\\ not\\ a\\ valid\\ Win32\\ application\\'\\]", "Misterious error in which the scout is called but cannot execute AFTER soldier upgrade"],
                       #statics
                       'android_apk_static': [u'\\[\\"\\+\\ FAILED\\ CHECK\\_STATIC\\.\\ SIGNATURE\\ DETECTION\\:\\ \\[\\\'build\\/android\\\\\\\\\\\\\\\\install\\.default\\.apk.*\\]', "Android apk are detected (static)"],
                       'blackberry': [u'\\[\\"\\+\\ ERROR\\:\\ \\[Errno\\ 13\\]\\ Permission\\ denied\\:\\ \\\'build\\/blackberry\\\\\\\\\\\\\\\\install\\.bat\\\'\\"\\]', "Blackberry static detection (Permission denied)"],
                       'blackberry_static': [u'\\[\\"\\+\\ FAILED\\ CHECK\\_STATIC\\.\\ SIGNATURE\\ DETECTION\\:\\ \\[\\\'build\\/blackberry.*', "Blackberry static detection (Failed static check)"],
                       'ios': [u'\\[\\"\\+\\ ERROR\\:\\ \\[Errno\\ 13\\]\\ Permission\\ denied\\:\\ \\\'build\\/ios.*\\]', "iOS static detection (Permission Denied)"],
                       'ios_static': [u'\\[\\"\\+\\ FAILED\\ CHECK\\_STATIC\\.\\ SIGNATURE\\ DETECTION\\:\\ \\[\\\'build\\/ios.*', "iOS static detection (Failed Static check)"],
                       'exploit_pdf': [u'\\[\\"\\+\\ FAILED\\ CHECK\\_STATIC\\.\\ SIGNATURE\\ DETECTION\\:\\ \\[\\\'build\\/exploit\\\\\\\\\\\\\\\\example\\.exe\\\'\\]\\"\\]', "Exploit Pdf passes static check but is detected"],
                       #exploits
                       'exploit_pdf_run': [u'\\[\\"\\+\\ SUCCESS\\ CHECK\\_STATIC\\:\\ \\[\\\'build\\/exploit\\_pdf.*\\]', "Exploit Pdf passes static check but is detected"],
                       #melt
                       'air_perm_denied': [u'\\[\\"\\+\\ ERROR\\:\\ \\[Errno\\ 13\\]\\ Permission\\ denied\\:\\ \\\'build\\/windows\\_melt\\_air\\\\\\\\\\\\\\\\exp\\_rite\\.exe\\\'\\"\\]', "Static detection of Melt with Adobe Air"],
                       'air_signature': [u'\\[\\"\\+\\ FAILED\\ CHECK\\_STATIC\\.\\ SIGNATURE\\ DETECTION\\:\\ \\[\\\'build\\/windows\\_melt\\_air\\\\\\\\\\\\\\\\agent\\.exe\\\'\\]\\"\\,\\ \\"\\+\\ FAILED\\ SCOUT\\ BUILD\\.\\ SIGNATURE\\ DETECTION\\:\\ \\[\\\'build\\/windows\\_melt\\_air\\\\\\\\\\\\\\\\agent\\.exe\\\'\\]\\"\\]', "Static detection of Melt with Adobe Air"],
                       'air_signature_zip': [u"\\[\\'\\+\\ FAILED\\ SCOUT\\ BUILD\\.\\ CANNOT\\ FIND\\ ZIP\\ FILE\\ C\\:\\\\\\\\AVTest\\\\\\\\AVAgent\\\\\\\\build\\_windows\\_melt\\_air\\_scout\\_melt\\_melt\\.zip\\ TO\\ UNZIP\\ IT\\'\\]", "Static detection of Melt with Adobe Air (zip file)"],
                       'air_no_sync': [u'\\[\\"\\+\\ SUCCESS\\ CHECK\\_STATIC\\:\\ \\[.*\\]\\"\\,\\ \\\'\\+\\ SUCCESS\\ SCOUT\\ BUILD\\ \\(no\\ signature\\ detection\\)\\\'\\,\\ \\\'\\+\\ SUCCESS\\ SCOUT\\ EXECUTE\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ FAILED\\ SCOUT\\ SYNC\\\'\\]', "Melt with Adobe Air fails to sync"],
                       'fif_no_sync': [u'\\[\\"\\+\\ SUCCESS\\ CHECK\\_STATIC\\:\\ \\[\\\'build\\/windows\\_melt\\_fif\\\\\\\\\\\\\\\\exp\\_rite\\.exe\\\'\\]\\"\\,\\ \\\'\\+\\ SUCCESS\\ SCOUT\\ BUILD\\ \\(no\\ signature\\ detection\\)\\\'\\,\\ \\\'\\+\\ SUCCESS\\ SCOUT\\ EXECUTE\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ FAILED\\ SCOUT\\ SYNC\\\'\\]', "Melt with Firefox fails to sync"],
                       'uto_no_sync': [u'\\[\\"\\+\\ SUCCESS\\ CHECK\\_STATIC\\:\\ \\[\\\'build\\/windows\\_melt\\_uto\\\\\\\\\\\\\\\\exp\\_rite\\.exe\\\'\\]\\"\\,\\ \\\'\\+\\ SUCCESS\\ SCOUT\\ BUILD\\ \\(no\\ signature\\ detection\\)\\\'\\,\\ \\\'\\+\\ SUCCESS\\ SCOUT\\ EXECUTE\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ FAILED\\ SCOUT\\ SYNC\\\'\\]', "Melt with uTorrent fails to sync"],
                       'vuz_no_sync': [u'\\[\\"\\+\\ SUCCESS\\ CHECK\\_STATIC\\:\\ \\[\\\'build\\/windows\\_melt\\_vuz\\\\\\\\\\\\\\\\exp\\_rite\\.exe\\\'\\]\\"\\,\\ \\\'\\+\\ SUCCESS\\ SCOUT\\ BUILD\\ \\(no\\ signature\\ detection\\)\\\'\\,\\ \\\'\\+\\ SUCCESS\\ SCOUT\\ EXECUTE\\\'\\,\\ \\\'\\+\\ WARN\\ did\\ not\\ drop\\ startup\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ FAILED\\ SCOUT\\ SYNC\\\'\\]', "Melt with Vuze fails to sync"],
                       #soldier, elite, scout
                       'scout_no_sync': [u'\\[\\"\\+\\ SUCCESS\\ CHECK\\_STATIC\\:\\ \\[\\\'build\\/windows\\\\\\\\\\\\\\\\agent\\.exe.*SUCCESS\\ SCOUT.*FAILED\\ SCOUT\\ SYNC\\\'\\]', "Windows agent no sync"],
                       'elite_demo_no_sync': [u'\\[\\"\\+\\ SUCCESS\\ CHECK\\_STATIC\\:\\ \\[\\\'build\\/windows\\_demo\\\\\\\\\\\\\\\\agent\\.exe\\\'\\]\\"\\,\\ \\\'\\+\\ SUCCESS\\ SCOUT\\ BUILD\\ \\(no\\ signature\\ detection\\)\\\'\\,\\ \\\'\\+\\ SUCCESS\\ SCOUT\\ EXECUTE\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ FAILED\\ SCOUT\\ SYNC\\\'\\]', "Elite Scout Demo fails to sync"],
                       'no_soldier_upgrade': [u"\\[\\'\\+\\ NOT\\ YET\\ UPGRADED\\ SYNC\\:\\ scout\\'\\,\\ \\'\\+\\ NOT\\ YET\\ UPGRADED\\ SYNC\\:\\ scout\\'\\,\\ \\'\\+\\ NOT\\ YET\\ UPGRADED\\ SYNC\\:\\ scout\\'\\,\\ \\'\\+\\ NOT\\ YET\\ UPGRADED\\ SYNC\\:\\ scout\\'\\,\\ \\'\\+\\ NOT\\ YET\\ UPGRADED\\ SYNC\\:\\ scout\\'\\,\\ \\'\\+\\ NOT\\ YET\\ UPGRADED\\ SYNC\\:\\ scout\\'\\,\\ \\'\\+\\ NOT\\ YET\\ UPGRADED\\ SYNC\\:\\ scout\\'\\,\\ \\'\\+\\ NOT\\ YET\\ UPGRADED\\ SYNC\\:\\ scout\\'\\,\\ \\'\\+\\ NOT\\ YET\\ UPGRADED\\ SYNC\\:\\ scout\\'\\,\\ \\'\\+\\ FAILED\\ SOLDIER\\ INSTALL\\'\\]", "Impossibile to upgrade to soldier"],
                       'failed_soldier_upgrade': [u"\\[\\'\\+\\ SUCCESS\\ UPGRADED\\ SYNC\\'\\,\\ \\'\\+\\ FAILED\\ UPGRADE\\ SOLDIER\\'\\]", "Impossibile to upgrade to soldier"],
                       }

        #kis 15
            # STATIC
        self.insert_summary_manual_error((u'VM_STATIC_SRV', u'kis15', u'BUILD_SRV', 38, error_types['blackberry_static'][0], 'FAILED', 0, u''), False, "KIS15 STATIC IOS + BB")
        self.insert_summary_manual_error((u'VM_STATIC_SRV', u'kis15', u'BUILD_SRV', 48, error_types['ios_static'][0], 'FAILED', 0, u''), False, "KIS15 STATIC IOS + BB")
            #exploit
        self.insert_summary_manual_error((u'VM_EXPLOIT_SRV', u'kis15', u'POPUP', 41, error_types['popup'][0], 'POPUP', 0, u''), False, "KIS15 exploit selfdel")

        #kis 14
            #Static (regexp static)
        self.insert_summary_manual_error((u'VM_STATIC_SRV', u'kis14', u'BUILD_SRV', 38, error_types['blackberry_static'][0], 'FAILED', 0, u''), False, "KIS14 STATIC IOS + BB")
        self.insert_summary_manual_error((u'VM_STATIC_SRV', u'kis14', u'BUILD_SRV', 48, error_types['ios_static'][0], 'FAILED', 0, u''), False, "KIS14 STATIC IOS + BB")
            #Exploit
        self.insert_summary_manual_error((u'VM_EXPLOIT_SRV', u'kis14', u'CHECK_INFECTION', 26, error_types['infected'][0], 'FAILED', 0, u''), False, "KIS 14 EXPLOIT")

        #eset soldier (is elite)
        self.insert_summary_manual_error((u'VM_SOLDIER_SRV', u'eset', u'BUILD_SRV', 26, u"\\[.*\\]", 'FAILED', 0, u''), False, "ESET Soldier (is an elite)")
        self.insert_summary_manual_error((u'VM_SOLDIER_SRV', u'eset', u'CHECK_INFECTION', 30, error_types['infected'][0], 'FAILED', 0, u''), False, "ESET Soldier (is an elite)")

        #eset7 soldier (popup regexp)
        self.insert_summary_manual_error((u'VM_SOLDIER_SRV', u'eset7', u'BUILD_SRV', 27, error_types['193'][0], 'FAILED', 0, u''),  False, "ESET 7 Soldier (is an elite)")
        self.insert_summary_manual_error((u'VM_SOLDIER_SRV', u'eset7', u'POPUP', 28, error_types['popup'][0], 'POPUP', 0, u''), False, "ESET 7 Soldier (is an elite)")
        self.insert_summary_manual_error((u'VM_SOLDIER_SRV', u'eset7', u'CHECK_INFECTION', 31, error_types['infected'][0], 'FAILED', 0, u''),  False, "ESET 7 Soldier (is an elite)")

        #fsecure exploit
        self.insert_summary_manual_error((u'VM_EXPLOIT_SRV', u'fsecure', u'BUILD_SRV', 21,  error_types['exploit_pdf_run'][0], 'FAILED', 0, u''), False, "FSECURE EXPLOIT")

        #adaware exploit
        self.insert_summary_manual_error((u'VM_EXPLOIT_SRV', u'adaware', u'BUILD_SRV', 31,  error_types['exploit_pdf_run'][0], 'FAILED', 0, u''), False, "ADAWARE EXPLOIT")

        #bitdef
            # exploit
        self.insert_summary_manual_error((u'VM_EXPLOIT_SRV', u'bitdef', u'BUILD_SRV', 31,  error_types['exploit_pdf_run'][0], 'FAILED', 0, u''), False, "BITDEF EXPLOIT")

        #bitdef 15
            # exploit pdf
        self.insert_summary_manual_error((u'VM_EXPLOIT_SRV', u'bitdef15', u'BUILD_SRV', 35,  error_types['exploit_pdf_run'][0], 'FAILED', 0, u''), False, "BITDEF15 EXPLOIT PDF")

        #gdata
            # exploit
        self.insert_summary_manual_error((u'VM_EXPLOIT_SRV', u'gdata', u'BUILD_SRV', 31,  error_types['exploit_pdf_run'][0], 'FAILED', 0, u''), False, "GDATA EXPLOIT")
            #melt UTO

        #RISING
        #not checked
        self.insert_summary_manual_error((u'VM_EXPLOIT_SRV', u'risint', u'BUILD_SRV', 21, error_types['exploit_pdf_run'][0], 'FAILED', 0, u''), False, "RISING (fails mostly every test)")
        self.insert_summary_manual_error((u'VM_ELITE_FAST_SCOUTDEMO_SRV', u'risint', u'BUILD_SRV', 129, error_types['trigger'][0], 'FAILED', 0, u''),  False, "RISING (fails mostly every test)")
        self.insert_summary_manual_error((u'VM_MELT_SRV_AIR', u'risint', u'BUILD_SRV', 15,  error_types['air_signature'][0], 'FAILED', 0, u''), False, "RISING (fails mostly every test)")
        self.insert_summary_manual_error((u'VM_SOLDIER_SRV', u'risint', u'BUILD_SRV', 134, error_types['trigger'][0], 'FAILED', 0, u''), False, "RISING (fails mostly every test)")
        self.insert_summary_manual_error((u'VM_ELITE_FAST_SRV', u'risint', u'BUILD_SRV', 26, error_types['no_instance_id'][0], 'FAILED', 0, u''), False, "RISING (fails mostly every test)")
        self.insert_summary_manual_error((u'VM_ELITE_FAST_SRV', u'risint', u'CHECK_INFECTION', 29, error_types['infected'][0], 'FAILED', 0, u''), False, "RISING (fails mostly every test)")





        #CMCAV
            #elite
        self.insert_summary_manual_error((u'VM_ELITE_FAST_SRV', u'cmcav', u'CHECK_INFECTION', 30, error_types['infected'][0], 'FAILED', 0, u''), False, "CMCAV (blacklisted av)")
            #MELT
        self.insert_summary_manual_error((u'VM_MELT_SRV_FIF', u'cmcav', u'CHECK_INFECTION', 20, error_types['infected'][0], 'FAILED', 0, u''), False, "CMCAV MELT (blacklisted av, the scout exits)")
        self.insert_summary_manual_error((u'VM_MELT_SRV_FIF', u'cmcav', u'CHECK_INFECTION', 20, error_types['infected'][0], 'FAILED', 0, u''), False, "CMCAV MELT (blacklisted av, the scout exits)")
            #exploit
        self.insert_summary_manual_error((u'VM_EXPLOIT_SRV', u'cmcav', u'CHECK_INFECTION', 25, error_types['infected'][0], 'FAILED', 0, u''), False, "CMCAV EXPLOIT (blacklisted av, the scout exits)")
            #elite scoutdemo (uses regexp for STATIC)
        #.* self.insert_summary_manual_error((u'VM_ELITE_FAST_SCOUTDEMO_SRV', u'cmcav', u'BUILD_SRV', 12, u'\\[\\"\\+\\ FAILED\\ CHECK\\_STATIC\\.\\ SIGNATURE\\ DETECTION\\:\\ \\[.*\\]\\"\\,\\ \\"\\+\\ FAILED\\ SCOUT\\ BUILD\\.\\ SIGNATURE\\ DETECTION\\:\\ \\[.*\\]\\"\\]', 'FAILED', 0, u''), False, "CMCAV Elite ScoutDemo (blacklisted av, the scout exits)")
            #soldier
        self.insert_summary_manual_error((u'VM_SOLDIER_SRV', u'cmcav', u'BUILD_SRV', 26, error_types['no_instance_id'][0], 'FAILED', 0, u''), False, "CMCAV SOLDIER (blacklisted av, the scout exits)")
        self.insert_summary_manual_error((u'VM_SOLDIER_SRV', u'cmcav', u'CHECK_INFECTION', 30, error_types['infected'][0], 'FAILED', 0, u''), False, "CMCAV SOLDIER (blacklisted av, the scout exits)")


        #norton soldier (is elite)
        self.insert_summary_manual_error((u'VM_SOLDIER_SRV', u'norton', u'BUILD_SRV', 26, error_types['failed_soldier_upgrade'][0], 'FAILED', 0, u''), False, "NORTON SOLDIER (Norton is Elite)")
        self.insert_summary_manual_error((u'VM_SOLDIER_SRV', u'norton', u'CHECK_INFECTION', 30, error_types['infected'][0], 'FAILED', 0, u''), False, "NORTON SOLDIER (Norton is Elite)")
            #UTO
        #norton 15
            # soldier (is elite) NB crop regexp
        self.insert_summary_manual_error((u'VM_SOLDIER_SRV', u'norton15', u'BUILD_SRV', 31, error_types['failed_soldier_upgrade'][0], 'FAILED', 0, u''), False, "NORTON SOLDIER 15 (Norton is Elite)")
        self.insert_summary_manual_error((u'VM_SOLDIER_SRV', u'norton15', u'CHECK_INFECTION', 35, error_types['infected'][0], 'FAILED', 0, u''), False, "NORTON SOLDIER 15 (Norton is Elite)")

        #comodo
            #soldier

        self.insert_summary_manual_error((u'VM_SOLDIER_SRV', u'comodo', u'BUILD_SRV', 35, error_types['no_soldier_upgrade'][0], 'FAILED', 0, u''), False, "COMODO (fails mostly every test due to sandbox and firewall)")
        self.insert_summary_manual_error((u'VM_SOLDIER_SRV', u'comodo', u'CHECK_INFECTION', 39, error_types['infected'][0], 'FAILED', 0, u''), False, "COMODO (fails mostly every test due to sandbox and firewall)")
            #elite (popup regexp)
        self.insert_summary_manual_error((u'VM_ELITE_FAST_SRV', u'comodo', u'POPUP', 27, error_types['popup'][0], 'POPUP', 0, u''), False, "COMODO (fails mostly every test due to sandbox and firewall)")
        self.insert_summary_manual_error((u'VM_ELITE_FAST_SRV', u'comodo', u'CHECK_INFECTION', 29, error_types['infected'][0], 'FAILED', 0, u''), False, "COMODO (fails mostly every test due to sandbox and firewall)")

            #elite demo
        self.insert_summary_manual_error((u'VM_ELITE_FAST_SCOUTDEMO_SRV', u'comodo', u'CHECK_INFECTION', 24, error_types['infected'][0], 'FAILED', 0, u''), False, "COMODO (fails mostly every test due to sandbox and firewall)")


        #comodo7
            #elitedemo
        self.insert_summary_manual_error((u'VM_ELITE_FAST_SCOUTDEMO_SRV', u'comodo7', u'CHECK_INFECTION', 24, error_types['infected'][0], 'FAILED', 0, u''), False, "COMODO7 elitedemo (fails mostly every test due to sandbox and firewall)")
            #soldier
        #.*  self.insert_summary_manual_error((u'VM_SOLDIER_SRV', u'comodo7', u'BUILD_SRV', 27, u"\\[.*\\]", 'FAILED', 0, u''), False, "COMODO7 soldier (fails mostly every test due to sandbox and firewall)")
        # self.insert_summary_manual_error((u'VM_SOLDIER_SRV', u'comodo7', u'CHECK_INFECTION', 31, error_types['infected'][0], 'FAILED', 0, u''), False, "COMODO7 soldier (fails mostly every test due to sandbox and firewall)")

        self.insert_summary_manual_error((u'VM_SOLDIER_SRV', u'comodo7', u'BUILD_SRV', 36, error_types['no_soldier_upgrade'][0] , 'FAILED', 0, u''), False, "COMODO7 soldier (fails mostly every test due to sandbox and firewall)")
        self.insert_summary_manual_error((u'VM_SOLDIER_SRV', u'comodo7', u'CHECK_INFECTION', 40, error_types['infected'][0], 'FAILED', 0, u''), False, "COMODO7 soldier (fails mostly every test due to sandbox and firewall)")


            #elite
        self.insert_summary_manual_error((u'VM_ELITE_FAST_SRV', u'comodo7', u'CHECK_INFECTION', 29, error_types['infected'][0], 'FAILED', 0, u''), False, "COMODO elite (fails mostly every test due to sandbox and firewall)")

        #avast
            #SOLDIER (BUT IS ELITE)
        self.insert_summary_manual_error((u'VM_SOLDIER_SRV', u'avast', u'CHECK_INFECTION', 31, error_types['infected'][0], 'FAILED', 0, u''), False, "AVAST SOLDIER FAILS UNINSTALLATION (Avast is Elite)")
            #(static ios and static exploit)
        self.insert_summary_manual_error((u'VM_STATIC_SRV', u'avast', u'BUILD_SRV', 49, error_types['ios_static'][0], 'FAILED', 0, u''), False, "--TESTME--")
        self.insert_summary_manual_error((u'VM_STATIC_SRV', u'avast', u'BUILD_SRV', 63, error_types['exploit_pdf'][0], 'FAILED', 0, u''), True, "--TESTME--")
        self.insert_summary_manual_error((u'VM_STATIC_SRV', u'avast', u'POPUP', 65, error_types['popup'][0], 'POPUP', 0, u''), False, "--TESTME--")

        #kis 32 (blacklisted the scout exits)
            # static bb + ios
        self.insert_summary_manual_error((u'VM_STATIC_SRV', u'kis32', u'BUILD_SRV', 37, error_types['blackberry'][0], 'FAILED', 0, u''),  False, "KIS 32 STATIC BB+IOS")
        self.insert_summary_manual_error((u'VM_STATIC_SRV', u'kis32', u'BUILD_SRV', 47, error_types['ios_static'][0], 'FAILED', 0, u''), False, "KIS 32 STATIC BB+IOS")
        self.insert_summary_manual_error((u'VM_STATIC_SRV', u'kis32', u'POPUP', 63, error_types['popup'][0], 'POPUP', 0, u''), False, "KIS 32 STATIC BB+IOS")

            #soldier
        self.insert_summary_manual_error((u'VM_SOLDIER_SRV', u'kis32', u'BUILD_SRV', 25, error_types['scout_no_sync'][0], 'FAILED', 0, u''), False, "KIS 32 SOLDIER (IS BLACKLISTED)")
        self.insert_summary_manual_error((u'VM_SOLDIER_SRV', u'kis32', u'BUILD_SRV', 34, error_types['no_instance_id'][0], 'FAILED', 0, u''), False, "KIS 32 SOLDIER (IS BLACKLISTED)")

            #elite
        # self.insert_summary_manual_error((u'VM_ELITE_FAST_SRV', u'kis32', u'BUILD_SRV', 25, error_types['scout_no_sync'][0], 'FAILED', 0, u''), False, "KIS 32 ELITE (IS BLACKLISTED)")
        # self.insert_summary_manual_error((u'VM_ELITE_FAST_SRV', u'kis32', u'POPUP', 28, error_types['popup'][0], 'POPUP', 0, u''), False, "KIS 32 ELITE (IS BLACKLISTED)")
        # self.insert_summary_manual_error((u'VM_ELITE_FAST_SRV', u'kis32', u'BUILD_SRV', 34, error_types['no_instance_id'][0], 'FAILED', 0, u''), False, "KIS 32 ELITE (IS BLACKLISTED)")

        self.insert_summary_manual_error((u'VM_ELITE_FAST_SRV', u'kis32', u'BUILD_SRV', 25, error_types['scout_no_sync'][0], 'FAILED', 0, u''), False, "KIS 32 ELITE (IS BLACKLISTED)")
        self.insert_summary_manual_error((u'VM_ELITE_FAST_SRV', u'kis32', u'POPUP', 28, error_types['popup'][0], 'POPUP', 0, u''), True, "KIS 32 ELITE (IS BLACKLISTED)")
        self.insert_summary_manual_error((u'VM_ELITE_FAST_SRV', u'kis32', u'BUILD_SRV', 34, error_types['no_instance_id'][0], 'FAILED', 0, u''), False, "KIS 32 ELITE (IS BLACKLISTED)")



            #elite demo
        self.insert_summary_manual_error((u'VM_ELITE_FAST_SCOUTDEMO_SRV', u'kis32', u'BUILD_SRV', 23, error_types['elite_demo_no_sync'][0], 'FAILED', 0, u''), False, "KIS 32 ELITE DEMO (IS BLACKLISTED)")
            #exploit
        self.insert_summary_manual_error((u'VM_EXPLOIT_SRV', u'kis32', u'BUILD_SRV', 30, error_types['exploit_pdf_run'][0], 'FAILED', 0, u''), False, "KIS 32 EXPLOIT (IS BLACKLISTED)")
            #melt FIF, AIR, UTO, VUZ
        self.insert_summary_manual_error((u'VM_MELT_SRV_FIF', u'kis32', u'BUILD_SRV', 27, error_types['fif_no_sync'][0], 'FAILED', 0, u''), False, "KIS 32 MELT (IS BLACKLISTED)")
        self.insert_summary_manual_error((u'VM_MELT_SRV_FIF', u'kis32', u'POPUP', 28, error_types['popup'][0], 'POPUP', 0, u''), False, "KIS 32 MELT (IS BLACKLISTED)")
        self.insert_summary_manual_error((u'VM_MELT_SRV_AIR', u'kis32', u'BUILD_SRV', 14, error_types['air_signature_zip'][0], 'FAILED', 0, u''), False, "KIS 32 MELT (IS BLACKLISTED)")
        self.insert_summary_manual_error((u'VM_MELT_SRV_UTO', u'kis32', u'BUILD_SRV', 26, error_types['uto_no_sync'][0], 'FAILED', 0, u''), False, "KIS 32 MELT (IS BLACKLISTED)")
        self.insert_summary_manual_error((u'VM_MELT_SRV_UTO', u'kis32', u'CHECK_INFECTION', 29,error_types['infected'][0], 'FAILED', 0, u''), False, "KIS 32 MELT (IS BLACKLISTED)")
        self.insert_summary_manual_error((u'VM_MELT_SRV_VUZ', u'kis32', u'BUILD_SRV', 25, error_types['vuz_no_sync'][0], 'FAILED', 0, u''), False, "KIS 32 MELT (IS BLACKLISTED)")

        # #syscare failes due to mouse emulation
        #     #soldier
        # self.insert_summary_manual_error((u'VM_SOLDIER_SRV', u'syscare', u'BUILD_SRV', 23, error_types['soldier_no_sync'][0], 'FAILED', 0, u''), False, "SYSCARE TESTS FAILS DUE TO MOUSE EMULATION")
        #     #elite
        # self.insert_summary_manual_error((u'VM_ELITE_FAST_SRV', u'syscare', u'BUILD_SRV', 23, , 'FAILED', 0, u''), False, "SYSCARE TESTS FAILS DUE TO MOUSE EMULATION")
        #     #elite demo
        # self.insert_summary_manual_error((u'VM_ELITE_FAST_SCOUTDEMO_SRV', u'syscare', u'BUILD_SRV', 23, , 'FAILED', 0, u''), False, "SYSCARE TESTS FAILS DUE TO MOUSE EMULATION")
        #     #exploit
        # self.insert_summary_manual_error((u'VM_EXPLOIT_SRV', u'syscare', u'CHECK_INFECTION', 38, u'VM\\ is\\ INFECTED', 'FAILED', 0, u''), False, "SYSCARE TESTS FAILS DUE TO MOUSE EMULATION")

        #mbytes exploit
        self.insert_summary_manual_error((u'VM_EXPLOIT_SRV', u'mbytes', u'CHECK_INFECTION', 25, error_types['infected'][0], 'FAILED', 0, u''), False, "MBYTES DETECTS EXPLOIT DURING UNINSTALL (or uninstall fails in some way)")

        #avast32
            # soldier uninstall
        self.insert_summary_manual_error((u'VM_SOLDIER_SRV', u'avast32', u'CHECK_INFECTION', 31, error_types['infected'][0], 'FAILED', 0, u''), False, "AVAST32 FAILS SOLDIER UNINSTALLATION, BUT IS ELITE ")

        #avg
            # melt air (uses regexp for static check)
        self.insert_summary_manual_error((u'VM_MELT_SRV_AIR', u'avg', u'BUILD_SRV', 26, error_types['air_no_sync'][0], 'FAILED', 0, u''), False, "AVG MELT AIR")
        self.insert_summary_manual_error((u'VM_MELT_SRV_AIR', u'avg', u'CHECK_INFECTION', 29, error_types['infected'][0], 'FAILED', 0, u''), False, "AVG MELT AIR")
            #melt fif
        self.insert_summary_manual_error((u'VM_MELT_SRV_FIF', u'avg', u'BUILD_SRV', 26, error_types['fif_no_sync'][0], 'FAILED', 0, u''), False, "AVG MELT Firefox")
        self.insert_summary_manual_error((u'VM_MELT_SRV_FIF', u'avg', u'CHECK_INFECTION', 29, error_types['infected'][0], 'FAILED', 0, u''), False, "AVG MELT Firefox")
            #melt uto
        self.insert_summary_manual_error((u'VM_MELT_SRV_UTO', u'avg', u'BUILD_SRV', 26, error_types['uto_no_sync'][0], 'FAILED', 0, u''), False, "AVG MELT uTorrent")
        self.insert_summary_manual_error((u'VM_MELT_SRV_UTO', u'avg', u'CHECK_INFECTION', 29, error_types['infected'][0], 'FAILED', 0, u''), False, "AVG MELT uTorrent")

        #avira15 melt air
        self.insert_summary_manual_error((u'VM_MELT_SRV_AIR', u'avira15', u'BUILD_SRV', 15, error_types['air_signature'][0], 'FAILED', 0, u''), False, "AVIRA 2015 MELT AIR")
        self.insert_summary_manual_error((u'VM_MELT_SRV_AIR', u'avira15', u'POPUP', 16, error_types['popup'][0], 'POPUP', 0, u''), False, "AVIRA 2015 MELT AIR")

        #avira15f full melt air
        self.insert_summary_manual_error((u'VM_MELT_SRV_AIR', u'avira15f', u'BUILD_SRV', 12, error_types['air_perm_denied'][0], 'FAILED', 0, u''), False, "AVIRA 2015 full MELT AIR")

        #avira melt air (uses regexp for POPUP)
        self.insert_summary_manual_error((u'VM_MELT_SRV_AIR', u'avira', u'BUILD_SRV', 14, error_types['air_perm_denied'][0], 'FAILED', 0, u''), False, "AVIRA MELT AIR")
        self.insert_summary_manual_error((u'VM_MELT_SRV_AIR', u'avira', u'POPUP', 15, error_types['popup'][0], 'POPUP', 0, u''), False, "AVIRA MELT AIR")

        #360ts static ios
        self.insert_summary_manual_error((u'VM_STATIC_SRV', u'360ts', u'BUILD_SRV', 49, error_types['ios_static'][0], 'FAILED', 0, u''), False, "360 Total Security static ios")

        #zoneal static ios+bb (regexp)
        self.insert_summary_manual_error((u'VM_STATIC_SRV', u'zoneal', u'BUILD_SRV', 37, error_types['blackberry'][0], 'FAILED', 0, u''), False, "zoneal static BB + IOS")
        self.insert_summary_manual_error((u'VM_STATIC_SRV', u'zoneal', u'BUILD_SRV', 46, error_types['ios'][0], 'FAILED', 0, u''), False, "zoneal static BB + IOS")
        self.insert_summary_manual_error((u'VM_STATIC_SRV', u'zoneal', u'POPUP', 62, error_types['popup'][0], 'POPUP', 0, u''), False, "zoneal static BB + IOS")

        #zoneal7 static bb (regexp)
        self.insert_summary_manual_error((u'VM_STATIC_SRV', u'zoneal7', u'BUILD_SRV', 37, error_types['blackberry'][0], 'FAILED', 0, u''), False, "zoneal7 static BB")
        self.insert_summary_manual_error((u'VM_STATIC_SRV', u'zoneal7', u'BUILD_SRV', 38, error_types['ios'][0], 'FAILED', 0, u''), False, "zoneal7 static BB")

        #Norman Exploit
        self.insert_summary_manual_error((u'VM_EXPLOIT_SRV', u'norman', u'BUILD_SRV', 35, error_types['exploit_pdf_run'][0], 'FAILED', 0, u''), False, "Norman Exploit PDF")

        ######ANDROID APK
        #norman
        self.insert_summary_manual_error((u'VM_STATIC_SRV', u'norman', u'BUILD_SRV', 44, error_types['android_apk_static'][0], 'FAILED', 0, u''), False, "Norman Static Android APK")
        self.insert_summary_manual_error((u'VM_STATIC_SRV', u'norman', u'POPUP', 65, error_types['popup'][0], 'POPUP', 0, u''), False, "Norman Static Android APK")
        #fsecure
        self.insert_summary_manual_error((u'VM_STATIC_SRV', u'fsecure', u'BUILD_SRV', 44, error_types['android_apk_static'][0], 'FAILED', 0, u''), False, "Fsecure Static Android APK")
        #drweb
        self.insert_summary_manual_error((u'VM_STATIC_SRV', u'drweb', u'BUILD_SRV', 44, error_types['android_apk_static'][0], 'FAILED', 0, u''), False, "DrWeb Static Android APK")
        #bitdef15
        self.insert_summary_manual_error((u'VM_STATIC_SRV', u'bitdef15', u'BUILD_SRV', 44, error_types['android_apk_static'][0], 'FAILED', 0, u''), False, "bitdef15 Static Android APK")
        #bitdef
        self.insert_summary_manual_error((u'VM_STATIC_SRV', u'bitdef', u'BUILD_SRV', 44, error_types['android_apk_static'][0], 'FAILED', 0, u''), False,  "bitdef Static Android APK")
        #adaware
        self.insert_summary_manual_error((u'VM_STATIC_SRV', u'adaware', u'BUILD_SRV', 44, error_types['android_apk_static'][0], 'FAILED', 0, u''), False, "Adaware Static Android APK")
        self.insert_summary_manual_error((u'VM_STATIC_SRV', u'adaware', u'POPUP', 65, u"\\[.*\\]", 'POPUP', 0, u''), False, "Adaware Static Android APK")



    def insert_summary_manual_error(self, txt_tuple, manual_optional, manual_comment):
        test, vm, command, prg, log, result_state, rite_failed, rite_fail_log = txt_tuple
        #start_timestamp and end_timestamp are 0
        # SYNTAX: self.insert_summary(SummaryData(0, u'VM_MELT_SRV_UTO', u'trendm', u'REPORT_KIND_INIT', 0, True, "TestTrendm",     u'VM_MELT_SRV_UTO', ResultStates.PASSED, False, u''))
        self.insert_summary(SummaryData(0, 0, test, vm, command, prg, True, manual_optional, manual_comment, log, ResultStates().get_state_from_content(result_state), rite_failed, rite_fail_log))


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