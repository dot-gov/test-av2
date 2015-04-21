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
            self.conn.execute('INSERT INTO SUMMARY VALUES (?,?,?,?,?,?,?,?,?,?,?)', (summary.start_timestamp, summary.test_name, summary.vm, summary.prg,
                                                                                 summary.command, summary.parsed_result[0], str(summary.rite_result_log),
                                                                                 summary.rite_failed, summary.rite_fail_log,
                                                                                 summary.manual, summary.manual_comment))
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

        #kis 15
            # STATIC
        self.insert_summary_manual_error((u'VM_STATIC_SRV', u'kis15', u'BUILD_SRV', 38, u'\\[\\"\\+\\ FAILED\\ CHECK\\_STATIC\\.\\ SIGNATURE\\ DETECTION\\:\\ \\[\\\'build\\/blackberry.*\\]\\"\\,\\ \\"\\+\\ FAILED\\ SCOUT\\ BUILD\\.\\ SIGNATURE\\ DETECTION\\:\\ \\[.*\\]\\"\\]', 'FAILED', 0, u''), "KIS15 STATIC IOS + BB")
        self.insert_summary_manual_error((u'VM_STATIC_SRV', u'kis15', u'BUILD_SRV', 48, u'\\[\\"\\+\\ FAILED\\ CHECK\\_STATIC\\.\\ SIGNATURE\\ DETECTION\\:\\ \\[\\\'build\\/ios.*\\]\\"\\,\\ \\"\\+\\ FAILED\\ SCOUT\\ BUILD\\.\\ SIGNATURE\\ DETECTION\\:\\ \\[.*\\]\\"\\]', 'FAILED', 0, u''), "KIS15 STATIC IOS + BB")
            #exploit
        self.insert_summary_manual_error((u'VM_EXPLOIT_SRV', u'kis15', u'POPUP', 41, u"\\[.*\\]", 'POPUP', 0, u''), "KIS15 exploit selfdel")

        #kis 14
            #Static (regexp static)
        #OLD self.insert_summary_manual_error((u'VM_STATIC_SRV', u'kis14', u'BUILD_SRV', 39, u'\\[\\"\\+\\ FAILED\\ CHECK\\_STATIC\\.\\ SIGNATURE\\ DETECTION\\:\\ \\[\\\'build\\/blackberry\\\\\\\\\\\\\\\\install\\.bat\\\'\\,\\ \\\'build\\/blackberry\\\\\\\\\\\\\\\\res\\/inst\\_helper\\.exe\\\'\\,\\ \\\'build\\/blackberry\\\\\\\\\\\\\\\\res\\/facebook\\-1\\_4\\.5\\.cod\\\'\\,\\ \\\'build\\/blackberry\\\\\\\\\\\\\\\\res\\/facebook\\_4\\.5\\.cod\\\'\\]\\"\\,\\ \\"\\+\\ FAILED\\ SCOUT\\ BUILD\\.\\ SIGNATURE\\ DETECTION\\:\\ \\[\\\'build\\/blackberry\\\\\\\\\\\\\\\\install\\.bat\\\'\\,\\ \\\'build\\/blackberry\\\\\\\\\\\\\\\\res\\/inst\\_helper\\.exe\\\'\\,\\ \\\'build\\/blackberry\\\\\\\\\\\\\\\\res\\/facebook\\-1\\_4\\.5\\.cod\\\'\\,\\ \\\'build\\/blackberry\\\\\\\\\\\\\\\\res\\/facebook\\_4\\.5\\.cod\\\'\\]\\"\\,\\ \\\'\\+\\ ERROR\\:\\ Signature\\ detection\\\'\\]', 'FAILED', 0, u''), "KIS14 STATIC IOS + BB")
        #OLD self.insert_summary_manual_error((u'VM_STATIC_SRV', u'kis14', u'BUILD_SRV', 48, u'\\[\\"\\+\\ ERROR\\:\\ \\[Errno\\ 13\\]\\ Permission\\ denied\\:\\ \\\'build\\/ios\\\\\\\\\\\\\\\\win\\/install\\.exe\\\'\\"\\]', 'FAILED', 0, u''), "KIS14 STATIC IOS + BB")
        self.insert_summary_manual_error((u'VM_STATIC_SRV', u'kis14', u'BUILD_SRV', 38, u'\\[\\"\\+\\ FAILED\\ CHECK\\_STATIC\\.\\ SIGNATURE\\ DETECTION\\:\\ \\[\\\'build\\/blackberry.*\\]\\"\\,\\ \\"\\+\\ FAILED\\ SCOUT\\ BUILD\\.\\ SIGNATURE\\ DETECTION\\:\\ \\[.*\\]\\"\\]', 'FAILED', 0, u''), "KIS14 STATIC IOS + BB")
        self.insert_summary_manual_error((u'VM_STATIC_SRV', u'kis14', u'BUILD_SRV', 48, u'\\[\\"\\+\\ FAILED\\ CHECK\\_STATIC\\.\\ SIGNATURE\\ DETECTION\\:\\ \\[\\\'build\\/ios.*\\]\\"\\,\\ \\"\\+\\ FAILED\\ SCOUT\\ BUILD\\.\\ SIGNATURE\\ DETECTION\\:\\ \\[.*\\]\\"\\]', 'FAILED', 0, u''), "KIS14 STATIC IOS + BB")
            #Exploit
        self.insert_summary_manual_error((u'VM_EXPLOIT_SRV', u'kis14', u'CHECK_INFECTION', 26, u'VM\\ is\\ INFECTED', 'FAILED', 0, u''), "KIS 14 EXPLOIT")

        #eset soldier (is elite)
        self.insert_summary_manual_error((u'VM_SOLDIER_SRV', u'eset', u'BUILD_SRV', 26, u"\\[.*\\]", 'FAILED', 0, u''), "ESET Soldier (is an elite)")
        self.insert_summary_manual_error((u'VM_SOLDIER_SRV', u'eset', u'CHECK_INFECTION', 30, u'VM\\ is\\ INFECTED', 'FAILED', 0, u''), "ESET Soldier (is an elite)")

        #eset7 soldier (popup regexp)
        self.insert_summary_manual_error((u'VM_SOLDIER_SRV', u'eset7', u'BUILD_SRV', 27, u"\\[\\'\\+\\ SUCCESS\\ UPGRADED\\ SYNC\\'\\,\\ \\'\\+\\ ERROR\\:\\ \\[Error\\ 193\\]\\ \\%1\\ is\\ not\\ a\\ valid\\ Win32\\ application\\'\\]", 'FAILED', 0, u''),  "ESET 7 Soldier (is an elite)")
        self.insert_summary_manual_error((u'VM_SOLDIER_SRV', u'eset7', u'POPUP', 28, u"\\[.*\\]", 'POPUP', 0, u''), "ESET 7 Soldier (is an elite)")
        self.insert_summary_manual_error((u'VM_SOLDIER_SRV', u'eset7', u'CHECK_INFECTION', 31, u'VM\\ is\\ INFECTED', 'FAILED', 0, u''),  "ESET 7 Soldier (is an elite)")

        #fsecure exploit
        self.insert_summary_manual_error((u'VM_EXPLOIT_SRV', u'fsecure', u'BUILD_SRV', 21, u'\\[\\"\\+\\ SUCCESS\\ CHECK\\_STATIC\\:\\ \\[\\\'build\\/exploit\\_pdf\\\\\\\\\\\\\\\\example\\.exe\\\'\\]\\"\\,\\ \\\'\\+\\ SUCCESS\\ SCOUT\\ BUILD\\ \\(no\\ signature\\ detection\\)\\\'\\,\\ \\\'\\+\\ SUCCESS\\ SCOUT\\ EXECUTE\\\'\\,\\ \\\'\\+\\ ERROR\\:\\ \\[Error\\ 5\\]\\ Access\\ is\\ denied\\\'\\]', 'FAILED', 0, u''), "FSECURE EXPLOIT")

        #adaware exploit
        self.insert_summary_manual_error((u'VM_EXPLOIT_SRV', u'adaware', u'BUILD_SRV', 31, u'\\[\\"\\+\\ SUCCESS\\ CHECK\\_STATIC\\:\\ \\[\\\'build\\/exploit\\_pdf.*\\]', 'FAILED', 0, u''), "ADAWARE EXPLOIT")

        #bitdef
            # exploit
        self.insert_summary_manual_error((u'VM_EXPLOIT_SRV', u'bitdef', u'BUILD_SRV', 31, u'\\[\\"\\+\\ SUCCESS\\ CHECK\\_STATIC\\:\\ \\[\\\'build\\/exploit\\_pdf.*\\]', 'FAILED', 0, u''), "BITDEF EXPLOIT")
            # Static Android
        # self.insert_summary_manual_error((u'VM_STATIC_SRV', u'bitdef', u'BUILD_SRV', 45, u'\\[\\"\\+\\ FAILED\\ CHECK\\_STATIC\\.\\ SIGNATURE\\ DETECTION\\:\\ \\[\\\'build\\/android\\\\\\\\\\\\\\\\install\\.default\\.apk\\\'\\]\\"\\,\\ \\"\\+\\ FAILED\\ SCOUT\\ BUILD\\.\\ SIGNATURE\\ DETECTION\\:\\ \\[\\\'build\\/android\\\\\\\\\\\\\\\\install\\.default\\.apk\\\'\\]\\"\\,\\ \\\'\\+\\ ERROR\\:\\ Signature\\ detection\\\'\\]', 'FAILED', 0, u''), "BITDEF Android static detection")
        # # old discontinued test
        # # self.insert_summary_manual_error((u'VM_STATIC_SRV', u'bitdef', u'CHECK_STATIC', 59, u"\\[\\[\\'AVAgent\\/assets\\/tmp\\/install\\.m\\.apk\\'\\]\\,\\ \\[\\]\\,\\ \\[\\'AVAgent\\/assets\\/tmp\\/installer\\.v2\\.apk\\'\\]\\]", 'FAILED', 0, u''), "BITDEF Android static detection")

        #bitdef 15
             # soldier CROP NB THIS MANUAL ERROR USES THE REGEXP (SO ANY IMAGE ID IN CROP WILL MATCH)
        self.insert_summary_manual_error((u'VM_SOLDIER_SRV', u'bitdef15', u'CROP', 28, u'\[.*\]', 'CROP', 0, u''), "BITDEFENDER produces a FP crop with Elite and Soldier. From time to time is better to check manually known crops.")
             # elite CROP
        self.insert_summary_manual_error((u'VM_ELITE_FAST_SRV', u'bitdef15', u'CROP', 25, u'\[.*\]', 'CROP', 0, u''), "BITDEFENDER produces a FP crop with Elite and Soldier. From time to time is better to check manually known crops.")
            # exploit pdf
        self.insert_summary_manual_error((u'VM_EXPLOIT_SRV', u'bitdef15', u'BUILD_SRV', 35, u'\\[\\"\\+\\ SUCCESS\\ CHECK\\_STATIC\\:\\ \\[\\\'build\\/exploit\\_pdf.*\\]', 'FAILED', 0, u''), "BITDEF15 EXPLOIT PDF")


            # Static Android THIS MANUAL ERROR USES THE REGEXP (SO ANY IMAGE ID IN CROP WILL MATCH)
        # self.insert_summary_manual_error((u'VM_STATIC_SRV', u'bitdef15', u'BUILD_SRV', 45, u'\\[\\"\\+\\ FAILED\\ CHECK\\_STATIC\\.\\ SIGNATURE\\ DETECTION\\:\\ \\[\\\'build\\/android\\\\\\\\\\\\\\\\install\\.default\\.apk\\\'\\]\\"\\,\\ \\"\\+\\ FAILED\\ SCOUT\\ BUILD\\.\\ SIGNATURE\\ DETECTION\\:\\ \\[\\\'build\\/android\\\\\\\\\\\\\\\\install\\.default\\.apk\\\'\\]\\"\\,\\ \\\'\\+\\ ERROR\\:\\ Signature\\ detection\\\'\\]', 'FAILED', 0, u''), "BITDEF 15 Android static detection")
        # # old discontinued test
        # # self.insert_summary_manual_error((u'VM_STATIC_SRV', u'bitdef15', u'CHECK_STATIC', 59, u"\\[\\[\\'AVAgent\\/assets\\/tmp\\/install\\.m\\.apk\\'\\]\\,\\ \\[\\]\\,\\ \\[\\'AVAgent\\/assets\\/tmp\\/installer\\.v2\\.apk\\'\\]\\]", 'FAILED', 0, u''), "BITDEF 15 Android static detection")
        # self.insert_summary_manual_error((u'VM_STATIC_SRV', u'bitdef15', u'CROP', 70, u'\\[.*\\]', 'CROP', 0, u''), "BITDEF 15 Android static detection")

        #gdata
            # exploit
        self.insert_summary_manual_error((u'VM_EXPLOIT_SRV', u'gdata', u'BUILD_SRV', 31, u'\\[\\"\\+\\ SUCCESS\\ CHECK\\_STATIC\\:\\ \\[\\\'build\\/exploit\\_pdf.*\\]', 'FAILED', 0, u''), "GDATA EXPLOIT")
            #melt UTO
        # REMOVED because it does not detect it! self.insert_summary_manual_error((u'VM_MELT_SRV_UTO', u'gdata', u'CHECK_INFECTION', 18, u'VM\\ is\\ INFECTED', 'FAILED', 0, u''), "GDATA MELT UTO, GDATA recognize utorrent as a OpenCandy - because of its adv banners")

        #RISING
        #not checked
        self.insert_summary_manual_error((u'VM_EXPLOIT_SRV', u'risint', u'BUILD_SRV', 21, u'\\[\\"\\+\\ SUCCESS\\ CHECK\\_STATIC\\:\\ \\[\\\'build\\/exploit\\_pdf\\\\\\\\\\\\\\\\example\\.exe\\\'\\]\\"\\,\\ \\\'\\+\\ SUCCESS\\ SCOUT\\ BUILD\\ \\(no\\ signature\\ detection\\)\\\'\\,\\ \\\'\\+\\ SUCCESS\\ SCOUT\\ EXECUTE\\\'\\,\\ \\\'\\+\\ ERROR\\:\\ \\[Error\\ 1\\]\\ Incorrect\\ function\\\'\\]', 'FAILED', 0, u''), "RISING (fails mostly every test)")
        self.insert_summary_manual_error((u'VM_ELITE_FAST_SCOUTDEMO_SRV', u'risint', u'BUILD_SRV', 129, u"\\[\\'TRIGGER\\ FAILED.*FAILED\\ ELITE\\ INSTALL\\'\\]", 'FAILED', 0, u''),  "RISING (fails mostly every test)")
        self.insert_summary_manual_error((u'VM_MELT_SRV_AIR', u'risint', u'BUILD_SRV', 15, u'\\[\\"\\+\\ FAILED\\ CHECK\\_STATIC\\.\\ SIGNATURE\\ DETECTION\\:\\ \\[\\\'build\\/windows\\_melt\\_air\\\\\\\\\\\\\\\\exp\\_rite\\.exe\\.copy\\.com\\\'\\,\\ \\\'build\\/windows\\_melt\\_air\\\\\\\\\\\\\\\\agent\\.exe\\\'\\,\\ \\\'build\\/windows\\_melt\\_air\\\\\\\\\\\\\\\\exp\\_rite\\.exe\\.copy\\.bat\\\'\\,\\ \\\'build\\/windows\\_melt\\_air\\\\\\\\\\\\\\\\exp\\_rite\\.exe\\.copy\\.exe\\\'\\,\\ \\\'build\\/windows\\_melt\\_air\\\\\\\\\\\\\\\\exp\\_rite\\.exe\\.copy\\.dll\\\'\\,\\ \\\'build\\/windows\\_melt\\_air\\\\\\\\\\\\\\\\exp\\_rite\\.exe\\\'\\]\\"\\,\\ \\"\\+\\ FAILED\\ SCOUT\\ BUILD\\.\\ SIGNATURE\\ DETECTION\\:\\ \\[\\\'build\\/windows\\_melt\\_air\\\\\\\\\\\\\\\\exp\\_rite\\.exe\\.copy\\.com\\\'\\,\\ \\\'build\\/windows\\_melt\\_air\\\\\\\\\\\\\\\\agent\\.exe\\\'\\,\\ \\\'build\\/windows\\_melt\\_air\\\\\\\\\\\\\\\\exp\\_rite\\.exe\\.copy\\.bat\\\'\\,\\ \\\'build\\/windows\\_melt\\_air\\\\\\\\\\\\\\\\exp\\_rite\\.exe\\.copy\\.exe\\\'\\,\\ \\\'build\\/windows\\_melt\\_air\\\\\\\\\\\\\\\\exp\\_rite\\.exe\\.copy\\.dll\\\'\\,\\ \\\'build\\/windows\\_melt\\_air\\\\\\\\\\\\\\\\exp\\_rite\\.exe\\\'\\]\\"\\]', 'FAILED', 0, u''), "RISING (fails mostly every test)")
        self.insert_summary_manual_error((u'VM_SOLDIER_SRV', u'risint', u'BUILD_SRV', 134, u"\\[\\'TRIGGER\\ FAILED.*FAILED\\ SOLDIER\\ INSTALL\\'\\]", 'FAILED', 0, u''), "RISING (fails mostly every test)")
        self.insert_summary_manual_error((u'VM_ELITE_FAST_SRV', u'risint', u'BUILD_SRV', 134, u"\\[\\'TRIGGER\\ FAILED.*FAILED\\ ELITE\\ INSTALL\\'\\]", 'FAILED', 0, u''), "RISING (fails mostly every test)")

        #CMCAV
        #not checked
            #static (blacklisted the scout exits) (fails every test) (CROP REGEXP NB)
        self.insert_summary_manual_error((u'VM_STATIC_SRV', u'cmcav', u'BUILD_SRV', 50, u'\\[\\"\\+\\ FAILED\\ CHECK\\_STATIC\\.\\ SIGNATURE\\ DETECTION\\:\\ \\[\\\'build\\/ios\\\\\\\\\\\\\\\\win\\/install\\.exe\\\'\\]\\"\\,\\ \\"\\+\\ FAILED\\ SCOUT\\ BUILD\\.\\ SIGNATURE\\ DETECTION\\:\\ \\[\\\'build\\/ios\\\\\\\\\\\\\\\\win\\/install\\.exe\\\'\\]\\"\\,\\ \\\'\\+\\ ERROR\\:\\ Signature\\ detection\\\'\\]', 'FAILED', 0, u''), "CMCAV STATIC IOS")
        self.insert_summary_manual_error((u'VM_STATIC_SRV', u'cmcav', u'CROP', 71, u'\\[.*\\]', 'CROP', 0, u''), "CMCAV IOS")
            #elite
        #OLD self.insert_summary_manual_error((u'VM_ELITE_FAST_SRV', u'cmcav', u'BUILD_SRV', 13, u'\\[\\"\\+\\ FAILED\\ CHECK\\_STATIC\\.\\ SIGNATURE\\ DETECTION\\:\\ \\[\\\'build\\/windows\\\\\\\\\\\\\\\\agent\\.exe\\\'\\]\\"\\,\\ \\"\\+\\ FAILED\\ SCOUT\\ BUILD\\.\\ SIGNATURE\\ DETECTION\\:\\ \\[\\\'build\\/windows\\\\\\\\\\\\\\\\agent\\.exe\\\'\\]\\"\\,\\ \\\'\\+\\ ERROR\\:\\ Signature\\ detection\\\'\\]', 'FAILED', 0, u''), "CMCAV (blacklisted av)")
        self.insert_summary_manual_error((u'VM_ELITE_FAST_SRV', u'cmcav', u'CHECK_INFECTION', 30, u'VM\\ is\\ INFECTED', 'FAILED', 0, u''), "CMCAV (blacklisted av)")
            #MELT
        #disabled self.insert_summary_manual_error((u'VM_MELT_SRV_AIR', u'cmcav', u'CHECK_INFECTION', 19, u'VM\\ is\\ INFECTED', 'FAILED', 0, u''), "CMCAV MELT (blacklisted av, the scout exits)")
        self.insert_summary_manual_error((u'VM_MELT_SRV_FIF', u'cmcav', u'CHECK_INFECTION', 20, u'VM\\ is\\ INFECTED', 'FAILED', 0, u''), "CMCAV MELT (blacklisted av, the scout exits)")
        self.insert_summary_manual_error((u'VM_MELT_SRV_FIF', u'cmcav', u'CHECK_INFECTION', 20, u'VM\\ is\\ INFECTED', 'FAILED', 0, u''), "CMCAV MELT (blacklisted av, the scout exits)")
            #exploit
        self.insert_summary_manual_error((u'VM_EXPLOIT_SRV', u'cmcav', u'CHECK_INFECTION', 25, u'VM\\ is\\ INFECTED', 'FAILED', 0, u''), "CMCAV EXPLOIT (blacklisted av, the scout exits)")
            #elite scoutdemo (uses regexp for STATIC)
        self.insert_summary_manual_error((u'VM_ELITE_FAST_SCOUTDEMO_SRV', u'cmcav', u'BUILD_SRV', 12, u'\\[\\"\\+\\ FAILED\\ CHECK\\_STATIC\\.\\ SIGNATURE\\ DETECTION\\:\\ \\[.*\\]\\"\\,\\ \\"\\+\\ FAILED\\ SCOUT\\ BUILD\\.\\ SIGNATURE\\ DETECTION\\:\\ \\[.*\\]\\"\\]', 'FAILED', 0, u''), "CMCAV Elite ScoutDemo (blacklisted av, the scout exits)")
            #soldier
        self.insert_summary_manual_error((u'VM_SOLDIER_SRV', u'cmcav', u'BUILD_SRV', 26, u"\\[\\'\\+\\ FAILED\\ NO\\ INSTANCE\\_ID\\'\\]", 'FAILED', 0, u''), "CMCAV SOLDIER (blacklisted av, the scout exits)")
        self.insert_summary_manual_error((u'VM_SOLDIER_SRV', u'cmcav', u'CHECK_INFECTION', 30, u'VM\\ is\\ INFECTED', 'FAILED', 0, u''), "CMCAV SOLDIER (blacklisted av, the scout exits)")


        #norton soldier (is elite)
        self.insert_summary_manual_error((u'VM_SOLDIER_SRV', u'norton', u'BUILD_SRV', 26, u"\\[\\'\\+\\ SUCCESS\\ UPGRADED\\ SYNC\\'\\,\\ \\'\\+\\ FAILED\\ UPGRADE\\ SOLDIER\\'\\]", 'FAILED', 0, u''), "NORTON SOLDIER (Norton is Elite)")
        self.insert_summary_manual_error((u'VM_SOLDIER_SRV', u'norton', u'CHECK_INFECTION', 30, u'VM\\ is\\ INFECTED', 'FAILED', 0, u''), "NORTON SOLDIER (Norton is Elite)")
            #UTO
        #norton 15
            # soldier (is elite) NB crop regexp
        self.insert_summary_manual_error((u'VM_SOLDIER_SRV', u'norton15', u'BUILD_SRV', 31, u"\\[\\'\\+\\ SUCCESS\\ UPGRADED\\ SYNC\\'\\,\\ \\'\\+\\ FAILED\\ UPGRADE\\ SOLDIER\\'\\]", 'FAILED', 0, u''), "NORTON SOLDIER 15 (Norton is Elite)")
        self.insert_summary_manual_error((u'VM_SOLDIER_SRV', u'norton15', u'CHECK_INFECTION', 35, u'VM\\ is\\ INFECTED', 'FAILED', 0, u''), "NORTON SOLDIER 15 (Norton is Elite)")

            # melt air
        # self.insert_summary_manual_error((u'VM_MELT_SRV_AIR', u'norton15', u'BUILD_SRV', 26, u'\\[\\"\\+\\ SUCCESS\\ CHECK\\_STATIC\\:\\ \\[\\\'build\\/windows\\_melt\\_air\\\\\\\\\\\\\\\\exp\\_rite\\.exe\\.copy\\.com\\\'\\,\\ \\\'build\\/windows\\_melt\\_air\\\\\\\\\\\\\\\\agent\\.exe\\\'\\,\\ \\\'build\\/windows\\_melt\\_air\\\\\\\\\\\\\\\\exp\\_rite\\.exe\\.copy\\.bat\\\'\\,\\ \\\'build\\/windows\\_melt\\_air\\\\\\\\\\\\\\\\exp\\_rite\\.exe\\.copy\\.exe\\\'\\,\\ \\\'build\\/windows\\_melt\\_air\\\\\\\\\\\\\\\\exp\\_rite\\.exe\\.copy\\.dll\\\'\\,\\ \\\'build\\/windows\\_melt\\_air\\\\\\\\\\\\\\\\exp\\_rite\\.exe\\\'\\,\\ \\\'build\\/windows\\_melt\\_air\\\\\\\\\\\\\\\\exp\\_rite\\.exe\\.move\\.com\\\'\\,\\ \\\'build\\/windows\\_melt\\_air\\\\\\\\\\\\\\\\exp\\_rite\\.exe\\.move\\.bat\\\'\\,\\ \\\'build\\/windows\\_melt\\_air\\\\\\\\\\\\\\\\exp\\_rite\\.exe\\.move\\.exe\\\'\\,\\ \\\'build\\/windows\\_melt\\_air\\\\\\\\\\\\\\\\exp\\_rite\\.exe\\.move\\.dll\\\'\\,\\ \\\'build\\/windows\\_melt\\_air\\\\\\\\\\\\\\\\exp\\_rite\\.exe\\.move\\.com\\\'\\,\\ \\\'build\\/windows\\_melt\\_air\\\\\\\\\\\\\\\\exp\\_rite\\.exe\\.move\\.bat\\\'\\,\\ \\\'build\\/windows\\_melt\\_air\\\\\\\\\\\\\\\\exp\\_rite\\.exe\\.move\\.exe\\\'\\,\\ \\\'build\\/windows\\_melt\\_air\\\\\\\\\\\\\\\\exp\\_rite\\.exe\\.move\\.dll\\\'\\]\\"\\,\\ \\\'\\+\\ SUCCESS\\ SCOUT\\ BUILD\\ \\(no\\ signature\\ detection\\)\\\'\\,\\ \\\'\\+\\ SUCCESS\\ SCOUT\\ EXECUTE\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ FAILED\\ SCOUT\\ SYNC\\\'\\]', 'FAILED', 0, u''), "NORTON 15 MELT AIR")

        #comodo
            #soldier
        #OLD self.insert_summary_manual_error((u'VM_SOLDIER_SRV', u'comodo', u'BUILD_SRV', 33, u"\\[\\'\\+\\ NOT\\ YET\\ UPGRADED\\ SYNC\\:\\ scout\\'\\,\\ \\'\\+\\ NOT\\ YET\\ UPGRADED\\ SYNC\\:\\ scout\\'\\,\\ \\'\\+\\ NOT\\ YET\\ UPGRADED\\ SYNC\\:\\ scout\\'\\,\\ \\'\\+\\ NOT\\ YET\\ UPGRADED\\ SYNC\\:\\ scout\\'\\,\\ \\'\\+\\ NOT\\ YET\\ UPGRADED\\ SYNC\\:\\ scout\\'\\,\\ \\'\\+\\ NOT\\ YET\\ UPGRADED\\ SYNC\\:\\ scout\\'\\,\\ \\'\\+\\ NOT\\ YET\\ UPGRADED\\ SYNC\\:\\ scout\\'\\,\\ \\'\\+\\ NOT\\ YET\\ UPGRADED\\ SYNC\\:\\ scout\\'\\,\\ \\'\\+\\ NOT\\ YET\\ UPGRADED\\ SYNC\\:\\ scout\\'\\,\\ \\'\\+\\ FAILED\\ SOLDIER\\ INSTALL\\'\\]", 'FAILED', 0, u''), "COMODO (fails mostly every test due to sandbox and firewall)")
        #OLD self.insert_summary_manual_error((u'VM_SOLDIER_SRV', u'comodo', u'CROP', 34, u'\\[173\\,\\ 174\\]', 'CROP', 0, u''), "COMODO (fails mostly every test due to sandbox and firewall)")
        #OLD self.insert_summary_manual_error((u'VM_SOLDIER_SRV', u'comodo', u'CHECK_INFECTION', 37, u'VM\\ is\\ INFECTED', 'FAILED', 0, u''), "COMODO (fails mostly every test due to sandbox and firewall)")
        self.insert_summary_manual_error((u'VM_SOLDIER_SRV', u'comodo', u'BUILD_SRV', 35, u"\\[\\'\\+\\ NOT\\ YET\\ UPGRADED\\ SYNC\\:\\ scout\\'\\,\\ \\'\\+\\ NOT\\ YET\\ UPGRADED\\ SYNC\\:\\ scout\\'\\,\\ \\'\\+\\ NOT\\ YET\\ UPGRADED\\ SYNC\\:\\ scout\\'\\,\\ \\'\\+\\ NOT\\ YET\\ UPGRADED\\ SYNC\\:\\ scout\\'\\,\\ \\'\\+\\ NOT\\ YET\\ UPGRADED\\ SYNC\\:\\ scout\\'\\,\\ \\'\\+\\ NOT\\ YET\\ UPGRADED\\ SYNC\\:\\ scout\\'\\,\\ \\'\\+\\ NOT\\ YET\\ UPGRADED\\ SYNC\\:\\ scout\\'\\,\\ \\'\\+\\ NOT\\ YET\\ UPGRADED\\ SYNC\\:\\ scout\\'\\,\\ \\'\\+\\ NOT\\ YET\\ UPGRADED\\ SYNC\\:\\ scout\\'\\,\\ \\'\\+\\ FAILED\\ SOLDIER\\ INSTALL\\'\\]", 'FAILED', 0, u''), "COMODO (fails mostly every test due to sandbox and firewall)")
        self.insert_summary_manual_error((u'VM_SOLDIER_SRV', u'comodo', u'CHECK_INFECTION', 39, u'VM\\ is\\ INFECTED', 'FAILED', 0, u''), "COMODO (fails mostly every test due to sandbox and firewall)")
            #elite (popup regexp)
        #OLD self.insert_summary_manual_error((u'VM_ELITE_FAST_SRV', u'comodo', u'CROP', 26, u'\\[.*\\]', 'CROP', 0, u''), "COMODO (fails mostly every test due to sandbox and firewall)")
        #OLD self.insert_summary_manual_error((u'VM_ELITE_FAST_SRV', u'comodo', u'CHECK_INFECTION', 28, u'VM\\ is\\ INFECTED', 'FAILED', 0, u''), "COMODO (fails mostly every test due to sandbox and firewall)")
        self.insert_summary_manual_error((u'VM_ELITE_FAST_SRV', u'comodo', u'POPUP', 27, u"\\[.*\\]", 'POPUP', 0, u''), "COMODO (fails mostly every test due to sandbox and firewall)")
        self.insert_summary_manual_error((u'VM_ELITE_FAST_SRV', u'comodo', u'CHECK_INFECTION', 29, u'VM\\ is\\ INFECTED', 'FAILED', 0, u''), "COMODO (fails mostly every test due to sandbox and firewall)")

            #elite demo
        self.insert_summary_manual_error((u'VM_ELITE_FAST_SCOUTDEMO_SRV', u'comodo', u'CHECK_INFECTION', 24, u'VM\\ is\\ INFECTED', 'FAILED', 0, u''), "COMODO (fails mostly every test due to sandbox and firewall)")
            #melt
        # self.insert_summary_manual_error((u'VM_MELT_SRV_AIR', u'comodo', u'CHECK_INFECTION', 18, u'VM\\ is\\ INFECTED', 'FAILED', 0, u''), "COMODO melt air (fails mostly every test due to sandbox and firewall)")

        #comodo7
            #elitedemo
        self.insert_summary_manual_error((u'VM_ELITE_FAST_SCOUTDEMO_SRV', u'comodo7', u'CHECK_INFECTION', 24, u'VM\\ is\\ INFECTED', 'FAILED', 0, u''), "COMODO7 elitedemo (fails mostly every test due to sandbox and firewall)")
            #soldier
        self.insert_summary_manual_error((u'VM_SOLDIER_SRV', u'comodo7', u'BUILD_SRV', 27, u"\\[.*\\]", 'FAILED', 0, u''), "COMODO7 soldier (fails mostly every test due to sandbox and firewall)")
        self.insert_summary_manual_error((u'VM_SOLDIER_SRV', u'comodo7', u'CHECK_INFECTION', 31, u'VM\\ is\\ INFECTED', 'FAILED', 0, u''), "COMODO7 soldier (fails mostly every test due to sandbox and firewall)")

            #elite
        self.insert_summary_manual_error((u'VM_ELITE_FAST_SRV', u'comodo7', u'CHECK_INFECTION', 29, u'VM\\ is\\ INFECTED', 'FAILED', 0, u''), "COMODO elite (fails mostly every test due to sandbox and firewall)")

        #avast
            #SOLDIER (BUT IS ELITE)
        self.insert_summary_manual_error((u'VM_SOLDIER_SRV', u'avast', u'CHECK_INFECTION', 31, u'VM\\ is\\ INFECTED', 'FAILED', 0, u''), "AVAST SOLDIER FAILS UNINSTALLATION (Avast is Elite)")
            #(static ios and static exploit)

            #OLD    # self.insert_summary_manual_error((u'VM_STATIC_SRV', u'avast', u'BUILD_SRV', 50, u'\\[\\"\\+\\ FAILED\\ CHECK\\_STATIC\\.\\ SIGNATURE\\ DETECTION\\:\\ \\[\\\'build\\/ios\\\\\\\\\\\\\\\\win\\/install\\.exe\\\'\\]\\"\\,\\ \\"\\+\\ FAILED\\ SCOUT\\ BUILD\\.\\ SIGNATURE\\ DETECTION\\:\\ \\[\\\'build\\/ios\\\\\\\\\\\\\\\\win\\/install\\.exe\\\'\\]\\"\\,\\ \\\'\\+\\ ERROR\\:\\ Signature\\ detection\\\'\\]', 'FAILED', 0, u''), "AVAST DETECTS IOS INSTALLER")

        self.insert_summary_manual_error((u'VM_STATIC_SRV', u'avast', u'BUILD_SRV', 49, u'\\[\\"\\+\\ FAILED\\ CHECK\\_STATIC\\.\\ SIGNATURE\\ DETECTION\\:\\ \\[\\\'build\\/ios\\\\\\\\\\\\\\\\win\\/install\\.exe\\.copy\\.bat\\\'\\,\\ \\\'build\\/ios\\\\\\\\\\\\\\\\win\\/install\\.exe\\.copy\\.dll\\\'\\,\\ \\\'build\\/ios\\\\\\\\\\\\\\\\win\\/install\\.exe\\\'\\,\\ \\\'build\\/ios\\\\\\\\\\\\\\\\win\\/install\\.exe\\.copy\\.com\\\'\\,\\ \\\'build\\/ios\\\\\\\\\\\\\\\\win\\/install\\.exe\\.copy\\.exe\\\'\\]\\"\\,\\ \\"\\+\\ FAILED\\ SCOUT\\ BUILD\\.\\ SIGNATURE\\ DETECTION\\:\\ \\[\\\'build\\/ios\\\\\\\\\\\\\\\\win\\/install\\.exe\\.copy\\.bat\\\'\\,\\ \\\'build\\/ios\\\\\\\\\\\\\\\\win\\/install\\.exe\\.copy\\.dll\\\'\\,\\ \\\'build\\/ios\\\\\\\\\\\\\\\\win\\/install\\.exe\\\'\\,\\ \\\'build\\/ios\\\\\\\\\\\\\\\\win\\/install\\.exe\\.copy\\.com\\\'\\,\\ \\\'build\\/ios\\\\\\\\\\\\\\\\win\\/install\\.exe\\.copy\\.exe\\\'\\]\\"\\]', 'FAILED', 0, u''), "--TESTME--")
        self.insert_summary_manual_error((u'VM_STATIC_SRV', u'avast', u'BUILD_SRV', 63, u'\\[\\"\\+\\ FAILED\\ CHECK\\_STATIC\\.\\ SIGNATURE\\ DETECTION\\:\\ \\[\\\'build\\/exploit\\\\\\\\\\\\\\\\example\\.exe\\.copy\\.bat\\\'\\,\\ \\\'build\\/exploit\\\\\\\\\\\\\\\\example\\.exe\\\'\\,\\ \\\'build\\/exploit\\\\\\\\\\\\\\\\example\\.exe\\.copy\\.com\\\'\\,\\ \\\'build\\/exploit\\\\\\\\\\\\\\\\example\\.exe\\.copy\\.dll\\\'\\,\\ \\\'build\\/exploit\\\\\\\\\\\\\\\\example\\.exe\\.copy\\.exe\\\'\\]\\"\\,\\ \\"\\+\\ FAILED\\ SCOUT\\ BUILD\\.\\ SIGNATURE\\ DETECTION\\:\\ \\[\\\'build\\/exploit\\\\\\\\\\\\\\\\example\\.exe\\.copy\\.bat\\\'\\,\\ \\\'build\\/exploit\\\\\\\\\\\\\\\\example\\.exe\\\'\\,\\ \\\'build\\/exploit\\\\\\\\\\\\\\\\example\\.exe\\.copy\\.com\\\'\\,\\ \\\'build\\/exploit\\\\\\\\\\\\\\\\example\\.exe\\.copy\\.dll\\\'\\,\\ \\\'build\\/exploit\\\\\\\\\\\\\\\\example\\.exe\\.copy\\.exe\\\'\\]\\"\\]', 'FAILED', 0, u''), "--TESTME--")
        self.insert_summary_manual_error((u'VM_STATIC_SRV', u'avast', u'POPUP', 65, u"^\\[.*\\]$", 'POPUP', 0, u''), "--TESTME--")

        #kis 32 (blacklisted the scout exits)
            # static bb + ios
        self.insert_summary_manual_error((u'VM_STATIC_SRV', u'kis32', u'BUILD_SRV', 37, u'\\[\\"\\+\\ ERROR\\:\\ \\[Errno\\ 13\\]\\ Permission\\ denied\\:\\ \\\'build\\/blackberry\\\\\\\\\\\\\\\\install\\.bat\\\'\\"\\]', 'FAILED', 0, u''),  "KIS 32 STATIC BB+IOS")
        self.insert_summary_manual_error((u'VM_STATIC_SRV', u'kis32', u'BUILD_SRV', 47, u'\\[\\"\\+\\ FAILED\\ CHECK\\_STATIC\\.\\ SIGNATURE\\ DETECTION\\:\\ \\[\\\'build\\/ios\\\\\\\\\\\\\\\\win\\/install\\.exe\\\'\\,\\ \\\'build\\/ios\\\\\\\\\\\\\\\\win\\\\\\\\\\\\\\\\agent\\.exe\\\'\\]\\"\\,\\ \\"\\+\\ FAILED\\ SCOUT\\ BUILD\\.\\ SIGNATURE\\ DETECTION\\:\\ \\[\\\'build\\/ios\\\\\\\\\\\\\\\\win\\/install\\.exe\\\'\\,\\ \\\'build\\/ios\\\\\\\\\\\\\\\\win\\\\\\\\\\\\\\\\agent\\.exe\\\'\\]\\"\\]', 'FAILED', 0, u''), "KIS 32 STATIC BB+IOS")
        self.insert_summary_manual_error((u'VM_STATIC_SRV', u'kis32', u'POPUP', 63, u"\\[.*\\]", 'POPUP', 0, u''), "KIS 32 STATIC BB+IOS")
            #soldier
        self.insert_summary_manual_error((u'VM_SOLDIER_SRV', u'kis32', u'BUILD_SRV', 25, u'\\[\\"\\+\\ SUCCESS\\ CHECK\\_STATIC\\:\\ \\[\\\'build\\/windows\\\\\\\\\\\\\\\\agent\\.exe\\.copy\\.dll\\\'\\,\\ \\\'build\\/windows\\\\\\\\\\\\\\\\agent\\.exe\\.copy\\.bat\\\'\\,\\ \\\'build\\/windows\\\\\\\\\\\\\\\\agent\\.exe\\\'\\,\\ \\\'build\\/windows\\\\\\\\\\\\\\\\agent\\.exe\\.copy\\.com\\\'\\,\\ \\\'build\\/windows\\\\\\\\\\\\\\\\agent\\.exe\\.copy\\.exe\\\'\\,\\ \\\'build\\/windows\\\\\\\\\\\\\\\\agent\\.exe\\.move\\.dll\\\'\\,\\ \\\'build\\/windows\\\\\\\\\\\\\\\\agent\\.exe\\.move\\.bat\\\'\\,\\ \\\'build\\/windows\\\\\\\\\\\\\\\\agent\\.exe\\.move\\.com\\\'\\,\\ \\\'build\\/windows\\\\\\\\\\\\\\\\agent\\.exe\\.move\\.exe\\\'\\,\\ \\\'build\\/windows\\\\\\\\\\\\\\\\agent\\.exe\\.move\\.dll\\\'\\,\\ \\\'build\\/windows\\\\\\\\\\\\\\\\agent\\.exe\\.move\\.bat\\\'\\,\\ \\\'build\\/windows\\\\\\\\\\\\\\\\agent\\.exe\\.move\\.com\\\'\\,\\ \\\'build\\/windows\\\\\\\\\\\\\\\\agent\\.exe\\.move\\.exe\\\'\\]\\"\\,\\ \\\'\\+\\ SUCCESS\\ SCOUT\\ BUILD\\ \\(no\\ signature\\ detection\\)\\\'\\,\\ \\\'\\+\\ SUCCESS\\ SCOUT\\ EXECUTE\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ FAILED\\ SCOUT\\ SYNC\\\'\\]', 'FAILED', 0, u''), "KIS 32 SOLDIER (IS BLACKLISTED)")
        self.insert_summary_manual_error((u'VM_SOLDIER_SRV', u'kis32', u'BUILD_SRV', 34, u"\\[\\'\\+\\ FAILED\\ NO\\ INSTANCE\\_ID\\'\\]", 'FAILED', 0, u''), "KIS 32 SOLDIER (IS BLACKLISTED)")
            #elite
        self.insert_summary_manual_error((u'VM_ELITE_FAST_SRV', u'kis32', u'BUILD_SRV', 25, u'\\[\\"\\+\\ SUCCESS\\ CHECK\\_STATIC\\:\\ \\[\\\'build\\/windows\\\\\\\\\\\\\\\\agent\\.exe\\.copy\\.dll\\\'\\,\\ \\\'build\\/windows\\\\\\\\\\\\\\\\agent\\.exe\\.copy\\.bat\\\'\\,\\ \\\'build\\/windows\\\\\\\\\\\\\\\\agent\\.exe\\\'\\,\\ \\\'build\\/windows\\\\\\\\\\\\\\\\agent\\.exe\\.copy\\.com\\\'\\,\\ \\\'build\\/windows\\\\\\\\\\\\\\\\agent\\.exe\\.copy\\.exe\\\'\\,\\ \\\'build\\/windows\\\\\\\\\\\\\\\\agent\\.exe\\.move\\.dll\\\'\\,\\ \\\'build\\/windows\\\\\\\\\\\\\\\\agent\\.exe\\.move\\.bat\\\'\\,\\ \\\'build\\/windows\\\\\\\\\\\\\\\\agent\\.exe\\.move\\.com\\\'\\,\\ \\\'build\\/windows\\\\\\\\\\\\\\\\agent\\.exe\\.move\\.exe\\\'\\,\\ \\\'build\\/windows\\\\\\\\\\\\\\\\agent\\.exe\\.move\\.dll\\\'\\,\\ \\\'build\\/windows\\\\\\\\\\\\\\\\agent\\.exe\\.move\\.bat\\\'\\,\\ \\\'build\\/windows\\\\\\\\\\\\\\\\agent\\.exe\\.move\\.com\\\'\\,\\ \\\'build\\/windows\\\\\\\\\\\\\\\\agent\\.exe\\.move\\.exe\\\'\\]\\"\\,\\ \\\'\\+\\ SUCCESS\\ SCOUT\\ BUILD\\ \\(no\\ signature\\ detection\\)\\\'\\,\\ \\\'\\+\\ SUCCESS\\ SCOUT\\ EXECUTE\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ FAILED\\ SCOUT\\ SYNC\\\'\\]', 'FAILED', 0, u''), "KIS 32 ELITE (IS BLACKLISTED)")
        self.insert_summary_manual_error((u'VM_ELITE_FAST_SRV', u'kis32', u'POPUP', 28, u"\\[\\[\\'BAD\\'\\,\\ \\'\\/home\\/avmonitor\\/Rite\\/logs\\/popup\\_thumbs\\/kis32\\/NOK\\/150415\\-013609\\_direct\\_class\\-AVPProduct\\_Notification\\_thumb\\.jpg\\'\\,\\ \\'action\\'\\]\\]", 'POPUP', 0, u''), "KIS 32 ELITE (IS BLACKLISTED)")
        self.insert_summary_manual_error((u'VM_ELITE_FAST_SRV', u'kis32', u'BUILD_SRV', 34, u"\\[\\'\\+\\ FAILED\\ NO\\ INSTANCE\\_ID\\'\\]", 'FAILED', 0, u''), "KIS 32 ELITE (IS BLACKLISTED)")
            #elite demo
        self.insert_summary_manual_error((u'VM_ELITE_FAST_SCOUTDEMO_SRV', u'kis32', u'BUILD_SRV', 11, u"\\[.*\\]", 'FAILED', 0, u''), "KIS 32 ELITE DEMO (IS BLACKLISTED)")
            #exploit
        self.insert_summary_manual_error((u'VM_EXPLOIT_SRV', u'kis32', u'BUILD_SRV', 30, u'\\[\\"\\+\\ SUCCESS\\ CHECK\\_STATIC\\:\\ \\[\\\'build\\/exploit\\_pdf.*\\]', 'FAILED', 0, u''), "KIS 32 EXPLOIT (IS BLACKLISTED)")
            #melt FIF, AIR, UTO, VUZ
        #old self.insert_summary_manual_error((u'VM_MELT_SRV_FIF', u'kis32', u'BUILD_SRV', 24, u'\\[\\"\\+\\ SUCCESS\\ CHECK\\_STATIC\\:\\ \\[\\\'build\\/windows\\_melt\\_fif\\\\\\\\\\\\\\\\exp\\_rite\\.exe\\\'\\]\\"\\,\\ \\\'\\+\\ SUCCESS\\ SCOUT\\ BUILD\\ \\(no\\ signature\\ detection\\)\\\'\\,\\ \\\'\\+\\ SUCCESS\\ SCOUT\\ EXECUTE\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ FAILED\\ SCOUT\\ SYNC\\\'\\]', 'FAILED', 0, u''), "KIS 32 MELT (IS BLACKLISTED)")
        self.insert_summary_manual_error((u'VM_MELT_SRV_FIF', u'kis32', u'BUILD_SRV', 27, u'\\[\\"\\+\\ SUCCESS\\ CHECK\\_STATIC\\:\\ \\[\\\'build\\/windows\\_melt\\_fif\\\\\\\\\\\\\\\\exp\\_rite\\.exe\\.copy\\.com\\\'\\,\\ \\\'build\\/windows\\_melt\\_fif\\\\\\\\\\\\\\\\exp\\_rite\\.exe\\\'\\,\\ \\\'build\\/windows\\_melt\\_fif\\\\\\\\\\\\\\\\agent\\.exe\\\'\\,\\ \\\'build\\/windows\\_melt\\_fif\\\\\\\\\\\\\\\\exp\\_rite\\.exe\\.copy\\.exe\\\'\\,\\ \\\'build\\/windows\\_melt\\_fif\\\\\\\\\\\\\\\\exp\\_rite\\.exe\\.copy\\.dll\\\'\\,\\ \\\'build\\/windows\\_melt\\_fif\\\\\\\\\\\\\\\\exp\\_rite\\.exe\\.copy\\.bat\\\'\\,\\ \\\'build\\/windows\\_melt\\_fif\\\\\\\\\\\\\\\\exp\\_rite\\.exe\\.move\\.com\\\'\\,\\ \\\'build\\/windows\\_melt\\_fif\\\\\\\\\\\\\\\\exp\\_rite\\.exe\\.move\\.exe\\\'\\,\\ \\\'build\\/windows\\_melt\\_fif\\\\\\\\\\\\\\\\exp\\_rite\\.exe\\.move\\.dll\\\'\\,\\ \\\'build\\/windows\\_melt\\_fif\\\\\\\\\\\\\\\\exp\\_rite\\.exe\\.move\\.bat\\\'\\]\\"\\,\\ \\\'\\+\\ SUCCESS\\ SCOUT\\ BUILD\\ \\(no\\ signature\\ detection\\)\\\'\\,\\ \\\'\\+\\ SUCCESS\\ SCOUT\\ EXECUTE\\\'\\,\\ \\\'\\+\\ WARN\\ did\\ not\\ drop\\ startup\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ FAILED\\ SCOUT\\ SYNC\\\'\\]', 'FAILED', 0, u''), "KIS 32 MELT (IS BLACKLISTED)")
        self.insert_summary_manual_error((u'VM_MELT_SRV_FIF', u'kis32', u'POPUP', 28, u"\\[\\[\\'BAD\\'\\,\\ \\'\\/home\\/avmonitor\\/Rite\\/logs\\/popup\\_thumbs\\/kis32\\/NOK\\/150416\\-115246\\_printscr\\_class\\-AVPAlertDialog\\_thumb\\.jpg\\'\\,\\ \\'Block\\'\\]\\,\\ \\[\\'BAD\\'\\,\\ \\'\\/home\\/avmonitor\\/Rite\\/logs\\/popup\\_thumbs\\/kis32\\/NOK\\/150416\\-115304\\_printscr\\_class\\-AVPAlertDialog\\_thumb\\.jpg\\'\\,\\ \\'Block\\'\\]\\,\\ \\[\\'BAD\\'\\,\\ \\'\\/home\\/avmonitor\\/Rite\\/logs\\/popup\\_thumbs\\/kis32\\/NOK\\/150416\\-125146\\_printscr\\_class\\-AVPAlertDialog\\_thumb\\.jpg\\'\\,\\ \\'action\\'\\]\\,\\ \\[\\'BAD\\'\\,\\ \\'\\/home\\/avmonitor\\/Rite\\/logs\\/popup\\_thumbs\\/kis32\\/NOK\\/150416\\-125200\\_printscr\\_class\\-AVPAlertDialog\\_thumb\\.jpg\\'\\,\\ \\'worm\\'\\]\\]", 'POPUP', 0, u''), "KIS 32 MELT (IS BLACKLISTED)")

        self.insert_summary_manual_error((u'VM_MELT_SRV_AIR', u'kis32', u'BUILD_SRV', 14, u"\\[\\'\\+\\ FAILED\\ SCOUT\\ BUILD\\.\\ CANNOT\\ FIND\\ ZIP\\ FILE\\ C\\:\\\\\\\\AVTest\\\\\\\\AVAgent\\\\\\\\build\\_windows\\_melt\\_air\\_scout\\_melt\\_melt\\.zip\\ TO\\ UNZIP\\ IT\\'\\]", 'FAILED', 0, u''), "KIS 32 MELT (IS BLACKLISTED)")
        self.insert_summary_manual_error((u'VM_MELT_SRV_UTO', u'kis32', u'BUILD_SRV', 24, u'\\[\\"\\+\\ SUCCESS\\ CHECK\\_STATIC\\:\\ \\[\\\'build\\/windows\\_melt\\_uto\\\\\\\\\\\\\\\\exp\\_rite\\.exe\\\'\\]\\"\\,\\ \\\'\\+\\ SUCCESS\\ SCOUT\\ BUILD\\ \\(no\\ signature\\ detection\\)\\\'\\,\\ \\\'\\+\\ SUCCESS\\ SCOUT\\ EXECUTE\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ FAILED\\ SCOUT\\ SYNC\\\'\\]', 'FAILED', 0, u''), "KIS 32 MELT (IS BLACKLISTED)")
        self.insert_summary_manual_error((u'VM_MELT_SRV_VUZ', u'kis32', u'BUILD_SRV', 25, u'\\[\\"\\+\\ SUCCESS\\ CHECK\\_STATIC\\:\\ \\[\\\'build\\/windows\\_melt\\_vuz\\\\\\\\\\\\\\\\exp\\_rite\\.exe\\\'\\]\\"\\,\\ \\\'\\+\\ SUCCESS\\ SCOUT\\ BUILD\\ \\(no\\ signature\\ detection\\)\\\'\\,\\ \\\'\\+\\ SUCCESS\\ SCOUT\\ EXECUTE\\\'\\,\\ \\\'\\+\\ WARN\\ did\\ not\\ drop\\ startup\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ FAILED\\ SCOUT\\ SYNC\\\'\\]', 'FAILED', 0, u''), "KIS 32 MELT (IS BLACKLISTED)")

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
        self.insert_summary_manual_error((u'VM_ELITE_FAST_SRV', u'avast32', u'CROP', 27, u'\\[.*\\]', 'CROP', 0, u''), "AVAST32 SAVES A CROP IN ELITE, DUE TO A rundll32 ERROR (probably caused by avast)")

        #avg
            # melt air (uses regexp for static check)
        self.insert_summary_manual_error((u'VM_MELT_SRV_AIR', u'avg', u'BUILD_SRV', 26, u'\\[\\"\\+\\ SUCCESS\\ CHECK\\_STATIC\\:\\ \\[.*\\]\\"\\,\\ \\\'\\+\\ SUCCESS\\ SCOUT\\ BUILD\\ \\(no\\ signature\\ detection\\)\\\'\\,\\ \\\'\\+\\ SUCCESS\\ SCOUT\\ EXECUTE\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ FAILED\\ SCOUT\\ SYNC\\\'\\]', 'FAILED', 0, u''), "AVG MELT AIR")
        self.insert_summary_manual_error((u'VM_MELT_SRV_AIR', u'avg', u'CHECK_INFECTION', 29, u'VM\\ is\\ INFECTED', 'FAILED', 0, u''), "AVG MELT AIR")
            #melt fif
        self.insert_summary_manual_error((u'VM_MELT_SRV_FIF', u'avg', u'BUILD_SRV', 26, u'\\[\\"\\+\\ SUCCESS\\ CHECK\\_STATIC\\:\\ \\[\\\'build\\/windows\\_melt\\_fif\\\\\\\\\\\\\\\\exp\\_rite\\.exe\\.copy\\.com\\\'\\,\\ \\\'build\\/windows\\_melt\\_fif\\\\\\\\\\\\\\\\exp\\_rite\\.exe\\\'\\,\\ \\\'build\\/windows\\_melt\\_fif\\\\\\\\\\\\\\\\agent\\.exe\\\'\\,\\ \\\'build\\/windows\\_melt\\_fif\\\\\\\\\\\\\\\\exp\\_rite\\.exe\\.copy\\.exe\\\'\\,\\ \\\'build\\/windows\\_melt\\_fif\\\\\\\\\\\\\\\\exp\\_rite\\.exe\\.copy\\.dll\\\'\\,\\ \\\'build\\/windows\\_melt\\_fif\\\\\\\\\\\\\\\\exp\\_rite\\.exe\\.copy\\.bat\\\'\\,\\ \\\'build\\/windows\\_melt\\_fif\\\\\\\\\\\\\\\\exp\\_rite\\.exe\\.move\\.com\\\'\\,\\ \\\'build\\/windows\\_melt\\_fif\\\\\\\\\\\\\\\\exp\\_rite\\.exe\\.move\\.exe\\\'\\,\\ \\\'build\\/windows\\_melt\\_fif\\\\\\\\\\\\\\\\exp\\_rite\\.exe\\.move\\.dll\\\'\\,\\ \\\'build\\/windows\\_melt\\_fif\\\\\\\\\\\\\\\\exp\\_rite\\.exe\\.move\\.bat\\\'\\]\\"\\,\\ \\\'\\+\\ SUCCESS\\ SCOUT\\ BUILD\\ \\(no\\ signature\\ detection\\)\\\'\\,\\ \\\'\\+\\ SUCCESS\\ SCOUT\\ EXECUTE\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ FAILED\\ SCOUT\\ SYNC\\\'\\]', 'FAILED', 0, u''), "AVG MELT Firefox")
        self.insert_summary_manual_error((u'VM_MELT_SRV_FIF', u'avg', u'CHECK_INFECTION', 29, u'VM\\ is\\ INFECTED', 'FAILED', 0, u''), "AVG MELT Firefox")
            #melt uto
        self.insert_summary_manual_error((u'VM_MELT_SRV_UTO', u'avg', u'BUILD_SRV', 26, u'\\[\\"\\+\\ SUCCESS\\ CHECK\\_STATIC\\:\\ \\[\\\'build\\/windows\\_melt\\_uto\\\\\\\\\\\\\\\\exp\\_rite\\.exe\\\'\\,\\ \\\'build\\/windows\\_melt\\_uto\\\\\\\\\\\\\\\\exp\\_rite\\.exe\\.copy\\.exe\\\'\\,\\ \\\'build\\/windows\\_melt\\_uto\\\\\\\\\\\\\\\\exp\\_rite\\.exe\\.copy\\.com\\\'\\,\\ \\\'build\\/windows\\_melt\\_uto\\\\\\\\\\\\\\\\exp\\_rite\\.exe\\.copy\\.dll\\\'\\,\\ \\\'build\\/windows\\_melt\\_uto\\\\\\\\\\\\\\\\exp\\_rite\\.exe\\.copy\\.bat\\\'\\,\\ \\\'build\\/windows\\_melt\\_uto\\\\\\\\\\\\\\\\agent\\.exe\\\'\\,\\ \\\'build\\/windows\\_melt\\_uto\\\\\\\\\\\\\\\\exp\\_rite\\.exe\\.move\\.exe\\\'\\,\\ \\\'build\\/windows\\_melt\\_uto\\\\\\\\\\\\\\\\exp\\_rite\\.exe\\.move\\.com\\\'\\,\\ \\\'build\\/windows\\_melt\\_uto\\\\\\\\\\\\\\\\exp\\_rite\\.exe\\.move\\.dll\\\'\\,\\ \\\'build\\/windows\\_melt\\_uto\\\\\\\\\\\\\\\\exp\\_rite\\.exe\\.move\\.bat\\\'\\]\\"\\,\\ \\\'\\+\\ SUCCESS\\ SCOUT\\ BUILD\\ \\(no\\ signature\\ detection\\)\\\'\\,\\ \\\'\\+\\ SUCCESS\\ SCOUT\\ EXECUTE\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ NO\\ SCOUT\\ SYNC\\\'\\,\\ \\\'\\+\\ FAILED\\ SCOUT\\ SYNC\\\'\\]', 'FAILED', 0, u''), "AVG MELT uTorrent")
        self.insert_summary_manual_error((u'VM_MELT_SRV_UTO', u'avg', u'CHECK_INFECTION', 29, u'VM\\ is\\ INFECTED', 'FAILED', 0, u''), "AVG MELT uTorrent")

        #avira15 melt air
        self.insert_summary_manual_error((u'VM_MELT_SRV_AIR', u'avira15', u'BUILD_SRV', 15, u'\\[\\"\\+\\ FAILED\\ CHECK\\_STATIC\\.\\ SIGNATURE\\ DETECTION\\:\\ \\[\\\'build\\/windows\\_melt\\_air\\\\\\\\\\\\\\\\agent\\.exe\\\'\\]\\"\\,\\ \\"\\+\\ FAILED\\ SCOUT\\ BUILD\\.\\ SIGNATURE\\ DETECTION\\:\\ \\[\\\'build\\/windows\\_melt\\_air\\\\\\\\\\\\\\\\agent\\.exe\\\'\\]\\"\\]', 'FAILED', 0, u''), "AVIRA 2015 MELT AIR")
        self.insert_summary_manual_error((u'VM_MELT_SRV_AIR', u'avira15', u'POPUP', 16, u"\\[.*\\]", 'POPUP', 0, u''), "AVIRA 2015 MELT AIR")

        #avira15f full melt air
        self.insert_summary_manual_error((u'VM_MELT_SRV_AIR', u'avira15f', u'BUILD_SRV', 12, u'\\[\\"\\+\\ ERROR\\:\\ \\[Errno\\ 13\\]\\ Permission\\ denied\\:\\ \\\'build\\/windows\\_melt\\_air\\\\\\\\\\\\\\\\exp\\_rite\\.exe\\\'\\"\\]', 'FAILED', 0, u''), "AVIRA 2015 full MELT AIR")

        #avira melt air (uses regexp for POPUP)
        self.insert_summary_manual_error((u'VM_MELT_SRV_AIR', u'avira', u'BUILD_SRV', 14, u'\\[\\"\\+\\ ERROR\\:\\ \\[Errno\\ 13\\]\\ Permission\\ denied\\:\\ \\\'build\\/windows\\_melt\\_air\\\\\\\\\\\\\\\\exp\\_rite\\.exe\\\'\\"\\]', 'FAILED', 0, u''), "AVIRA MELT AIR")
        self.insert_summary_manual_error((u'VM_MELT_SRV_AIR', u'avira', u'POPUP', 15, u"\\[.*\\]", 'POPUP', 0, u''), "AVIRA MELT AIR")

        #360ts static ios
        self.insert_summary_manual_error((u'VM_STATIC_SRV', u'360ts', u'BUILD_SRV', 49, u'\\[\\"\\+\\ FAILED\\ CHECK\\_STATIC\\.\\ SIGNATURE\\ DETECTION\\:\\ \\[\\\'build\\/ios.*\\]', 'FAILED', 0, u''), "360 Total Security static ios")

        #zoneal static ios+bb (regexp)
        self.insert_summary_manual_error((u'VM_STATIC_SRV', u'zoneal', u'BUILD_SRV', 37, u'\\[\\"\\+\\ ERROR\\:\\ \\[Errno\\ 13\\]\\ Permission\\ denied\\:\\ \\\'build\\/blackberry\\\\\\\\\\\\\\\\install\\.bat\\\'\\"\\]', 'FAILED', 0, u''), "zoneal static BB + IOS")
        self.insert_summary_manual_error((u'VM_STATIC_SRV', u'zoneal', u'BUILD_SRV', 46, u'\\[\\"\\+\\ ERROR\\:\\ \\[Errno\\ 13\\]\\ Permission\\ denied\\:\\ \\\'build\\/ios.*\\]', 'FAILED', 0, u''), "zoneal static BB + IOS")
        self.insert_summary_manual_error((u'VM_STATIC_SRV', u'zoneal', u'POPUP', 62, u"\\[.*\\]", 'POPUP', 0, u''), "zoneal static BB + IOS")

        #zoneal7 static bb (regexp)
        self.insert_summary_manual_error((u'VM_STATIC_SRV', u'zoneal7', u'BUILD_SRV', 37, u'\\[\\"\\+\\ ERROR\\:\\ \\[Errno\\ 13\\]\\ Permission\\ denied\\:\\ \\\'build\\/blackberry\\\\\\\\\\\\\\\\install\\.bat\\\'\\"\\]', 'FAILED', 0, u''), "zoneal7 static BB")

        #Norman Exploit
        self.insert_summary_manual_error((u'VM_EXPLOIT_SRV', u'norman', u'BUILD_SRV', 35, u'\\[\\"\\+\\ SUCCESS\\ CHECK\\_STATIC\\:\\ \\[\\\'build\\/exploit\\_pdf.*\\]', 'FAILED', 0, u''), "Norman Exploit PDF")

        ######ANDROID APK
        #norman
        self.insert_summary_manual_error((u'VM_STATIC_SRV', u'norman', u'BUILD_SRV', 44, u'\\[\\"\\+\\ FAILED\\ CHECK\\_STATIC\\.\\ SIGNATURE\\ DETECTION\\:\\ \\[\\\'build\\/android\\\\\\\\\\\\\\\\install\\.default\\.apk\\.copy\\.bat\\\'\\,\\ \\\'build\\/android\\\\\\\\\\\\\\\\install\\.default\\.apk\\.copy\\.exe\\\'\\,\\ \\\'build\\/android\\\\\\\\\\\\\\\\install\\.default\\.apk\\\'\\,\\ \\\'build\\/android\\\\\\\\\\\\\\\\install\\.default\\.apk\\.copy\\.com\\\'\\,\\ \\\'build\\/android\\\\\\\\\\\\\\\\install\\.default\\.apk\\.copy\\.dll\\\'\\]\\"\\,\\ \\"\\+\\ FAILED\\ SCOUT\\ BUILD\\.\\ SIGNATURE\\ DETECTION\\:\\ \\[\\\'build\\/android\\\\\\\\\\\\\\\\install\\.default\\.apk\\.copy\\.bat\\\'\\,\\ \\\'build\\/android\\\\\\\\\\\\\\\\install\\.default\\.apk\\.copy\\.exe\\\'\\,\\ \\\'build\\/android\\\\\\\\\\\\\\\\install\\.default\\.apk\\\'\\,\\ \\\'build\\/android\\\\\\\\\\\\\\\\install\\.default\\.apk\\.copy\\.com\\\'\\,\\ \\\'build\\/android\\\\\\\\\\\\\\\\install\\.default\\.apk\\.copy\\.dll\\\'\\]\\"\\]', 'FAILED', 0, u''), "Norman Static Android APK")
        self.insert_summary_manual_error((u'VM_STATIC_SRV', u'norman', u'POPUP', 65, u"\\[.*\\]", 'POPUP', 0, u''), "Norman Static Android APK")
        #fsecure
        self.insert_summary_manual_error((u'VM_STATIC_SRV', u'fsecure', u'BUILD_SRV', 44, u'\\[\\"\\+\\ FAILED\\ CHECK\\_STATIC\\.\\ SIGNATURE\\ DETECTION\\:\\ \\[\\\'build\\/android\\\\\\\\\\\\\\\\install\\.default\\.apk\\.copy\\.bat\\\'\\,\\ \\\'build\\/android\\\\\\\\\\\\\\\\install\\.default\\.apk\\.copy\\.exe\\\'\\,\\ \\\'build\\/android\\\\\\\\\\\\\\\\install\\.default\\.apk\\\'\\,\\ \\\'build\\/android\\\\\\\\\\\\\\\\install\\.default\\.apk\\.copy\\.com\\\'\\,\\ \\\'build\\/android\\\\\\\\\\\\\\\\install\\.default\\.apk\\.copy\\.dll\\\'\\]\\"\\,\\ \\"\\+\\ FAILED\\ SCOUT\\ BUILD\\.\\ SIGNATURE\\ DETECTION\\:\\ \\[\\\'build\\/android\\\\\\\\\\\\\\\\install\\.default\\.apk\\.copy\\.bat\\\'\\,\\ \\\'build\\/android\\\\\\\\\\\\\\\\install\\.default\\.apk\\.copy\\.exe\\\'\\,\\ \\\'build\\/android\\\\\\\\\\\\\\\\install\\.default\\.apk\\\'\\,\\ \\\'build\\/android\\\\\\\\\\\\\\\\install\\.default\\.apk\\.copy\\.com\\\'\\,\\ \\\'build\\/android\\\\\\\\\\\\\\\\install\\.default\\.apk\\.copy\\.dll\\\'\\]\\"\\]', 'FAILED', 0, u''), "Fsecure Static Android APK")
        #drweb
        self.insert_summary_manual_error((u'VM_STATIC_SRV', u'drweb', u'BUILD_SRV', 44, u'\\[\\"\\+\\ FAILED\\ CHECK\\_STATIC\\.\\ SIGNATURE\\ DETECTION\\:\\ \\[\\\'build\\/android\\\\\\\\\\\\\\\\install\\.default\\.apk\\.copy\\.bat\\\'\\,\\ \\\'build\\/android\\\\\\\\\\\\\\\\install\\.v2\\.apk\\.copy\\.bat\\\'\\,\\ \\\'build\\/android\\\\\\\\\\\\\\\\install\\.v2\\.apk\\.copy\\.dll\\\'\\,\\ \\\'build\\/android\\\\\\\\\\\\\\\\install\\.default\\.apk\\.copy\\.exe\\\'\\,\\ \\\'build\\/android\\\\\\\\\\\\\\\\install\\.default\\.apk\\\'\\,\\ \\\'build\\/android\\\\\\\\\\\\\\\\install\\.default\\.apk\\.copy\\.com\\\'\\,\\ \\\'build\\/android\\\\\\\\\\\\\\\\install\\.default\\.apk\\.copy\\.dll\\\'\\,\\ \\\'build\\/android\\\\\\\\\\\\\\\\install\\.v2\\.apk\\\'\\,\\ \\\'build\\/android\\\\\\\\\\\\\\\\install\\.v2\\.apk\\.copy\\.exe\\\'\\,\\ \\\'build\\/android\\\\\\\\\\\\\\\\install\\.v2\\.apk\\.copy\\.com\\\'\\]\\"\\,\\ \\"\\+\\ FAILED\\ SCOUT\\ BUILD\\.\\ SIGNATURE\\ DETECTION\\:\\ \\[\\\'build\\/android\\\\\\\\\\\\\\\\install\\.default\\.apk\\.copy\\.bat\\\'\\,\\ \\\'build\\/android\\\\\\\\\\\\\\\\install\\.v2\\.apk\\.copy\\.bat\\\'\\,\\ \\\'build\\/android\\\\\\\\\\\\\\\\install\\.v2\\.apk\\.copy\\.dll\\\'\\,\\ \\\'build\\/android\\\\\\\\\\\\\\\\install\\.default\\.apk\\.copy\\.exe\\\'\\,\\ \\\'build\\/android\\\\\\\\\\\\\\\\install\\.default\\.apk\\\'\\,\\ \\\'build\\/android\\\\\\\\\\\\\\\\install\\.default\\.apk\\.copy\\.com\\\'\\,\\ \\\'build\\/android\\\\\\\\\\\\\\\\install\\.default\\.apk\\.copy\\.dll\\\'\\,\\ \\\'build\\/android\\\\\\\\\\\\\\\\install\\.v2\\.apk\\\'\\,\\ \\\'build\\/android\\\\\\\\\\\\\\\\install\\.v2\\.apk\\.copy\\.exe\\\'\\,\\ \\\'build\\/android\\\\\\\\\\\\\\\\install\\.v2\\.apk\\.copy\\.com\\\'\\]\\"\\]', 'FAILED', 0, u''), "DrWeb Static Android APK")
        #bitdef15
        self.insert_summary_manual_error((u'VM_STATIC_SRV', u'bitdef15', u'BUILD_SRV', 44, u'\\[\\"\\+\\ FAILED\\ CHECK\\_STATIC\\.\\ SIGNATURE\\ DETECTION\\:\\ \\[\\\'build\\/android\\\\\\\\\\\\\\\\install\\.default\\.apk\\.copy\\.bat\\\'\\,\\ \\\'build\\/android\\\\\\\\\\\\\\\\install\\.default\\.apk\\.copy\\.exe\\\'\\,\\ \\\'build\\/android\\\\\\\\\\\\\\\\install\\.default\\.apk\\\'\\,\\ \\\'build\\/android\\\\\\\\\\\\\\\\install\\.default\\.apk\\.copy\\.com\\\'\\,\\ \\\'build\\/android\\\\\\\\\\\\\\\\install\\.default\\.apk\\.copy\\.dll\\\'\\]\\"\\,\\ \\"\\+\\ FAILED\\ SCOUT\\ BUILD\\.\\ SIGNATURE\\ DETECTION\\:\\ \\[\\\'build\\/android\\\\\\\\\\\\\\\\install\\.default\\.apk\\.copy\\.bat\\\'\\,\\ \\\'build\\/android\\\\\\\\\\\\\\\\install\\.default\\.apk\\.copy\\.exe\\\'\\,\\ \\\'build\\/android\\\\\\\\\\\\\\\\install\\.default\\.apk\\\'\\,\\ \\\'build\\/android\\\\\\\\\\\\\\\\install\\.default\\.apk\\.copy\\.com\\\'\\,\\ \\\'build\\/android\\\\\\\\\\\\\\\\install\\.default\\.apk\\.copy\\.dll\\\'\\]\\"\\]', 'FAILED', 0, u''), "bitdef15 Static Android APK")
        #bitdef
        self.insert_summary_manual_error((u'VM_STATIC_SRV', u'bitdef', u'BUILD_SRV', 44, u'\\[\\"\\+\\ FAILED\\ CHECK\\_STATIC\\.\\ SIGNATURE\\ DETECTION\\:\\ \\[\\\'build\\/android\\\\\\\\\\\\\\\\install\\.default\\.apk\\.copy\\.bat\\\'\\,\\ \\\'build\\/android\\\\\\\\\\\\\\\\install\\.default\\.apk\\.copy\\.exe\\\'\\,\\ \\\'build\\/android\\\\\\\\\\\\\\\\install\\.default\\.apk\\\'\\,\\ \\\'build\\/android\\\\\\\\\\\\\\\\install\\.default\\.apk\\.copy\\.com\\\'\\,\\ \\\'build\\/android\\\\\\\\\\\\\\\\install\\.default\\.apk\\.copy\\.dll\\\'\\]\\"\\,\\ \\"\\+\\ FAILED\\ SCOUT\\ BUILD\\.\\ SIGNATURE\\ DETECTION\\:\\ \\[\\\'build\\/android\\\\\\\\\\\\\\\\install\\.default\\.apk\\.copy\\.bat\\\'\\,\\ \\\'build\\/android\\\\\\\\\\\\\\\\install\\.default\\.apk\\.copy\\.exe\\\'\\,\\ \\\'build\\/android\\\\\\\\\\\\\\\\install\\.default\\.apk\\\'\\,\\ \\\'build\\/android\\\\\\\\\\\\\\\\install\\.default\\.apk\\.copy\\.com\\\'\\,\\ \\\'build\\/android\\\\\\\\\\\\\\\\install\\.default\\.apk\\.copy\\.dll\\\'\\]\\"\\]', 'FAILED', 0, u''), "bitdef Static Android APK")
        #adaware
        self.insert_summary_manual_error((u'VM_STATIC_SRV', u'adaware', u'BUILD_SRV', 44, u'\\[\\"\\+\\ FAILED\\ CHECK\\_STATIC\\.\\ SIGNATURE\\ DETECTION\\:\\ \\[\\\'build\\/android\\\\\\\\\\\\\\\\install\\.default\\.apk\\.copy\\.bat\\\'\\,\\ \\\'build\\/android\\\\\\\\\\\\\\\\install\\.default\\.apk\\.copy\\.exe\\\'\\,\\ \\\'build\\/android\\\\\\\\\\\\\\\\install\\.default\\.apk\\\'\\,\\ \\\'build\\/android\\\\\\\\\\\\\\\\install\\.default\\.apk\\.copy\\.com\\\'\\,\\ \\\'build\\/android\\\\\\\\\\\\\\\\install\\.default\\.apk\\.copy\\.dll\\\'\\]\\"\\,\\ \\"\\+\\ FAILED\\ SCOUT\\ BUILD\\.\\ SIGNATURE\\ DETECTION\\:\\ \\[\\\'build\\/android\\\\\\\\\\\\\\\\install\\.default\\.apk\\.copy\\.bat\\\'\\,\\ \\\'build\\/android\\\\\\\\\\\\\\\\install\\.default\\.apk\\.copy\\.exe\\\'\\,\\ \\\'build\\/android\\\\\\\\\\\\\\\\install\\.default\\.apk\\\'\\,\\ \\\'build\\/android\\\\\\\\\\\\\\\\install\\.default\\.apk\\.copy\\.com\\\'\\,\\ \\\'build\\/android\\\\\\\\\\\\\\\\install\\.default\\.apk\\.copy\\.dll\\\'\\]\\"\\]', 'FAILED', 0, u''), "Adaware Static Android APK")
        self.insert_summary_manual_error((u'VM_STATIC_SRV', u'adaware', u'POPUP', 65, u"\\[\\[.*\\]", 'POPUP', 0, u''), "Adaware Static Android APK")

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