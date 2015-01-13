import sqlite3
sqlite_file = "results.db"


class DBReport(object):
    conn = None

    def __enter__(self):
        if not self.conn:
            self.conn = sqlite3.connect(sqlite_file)
        # Create table
        #timestamp is integer

        self.conn.execute('''CREATE TABLE IF NOT EXISTS RESULTS( timestamp integer, test_name text, vm text, command text, args text,
                        rite_result text, parsed_result text, rite_failed text, rite_fail_log text, side text )''')
        self.conn.execute('''CREATE TABLE IF NOT EXISTS SUMMARY( timestamp integer, test_name text, vm text, parsed_result text,
                        rite_failed text, manual text, PRIMARY KEY (timestamp, test_name, vm, manual) )''')

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
            cursor.execute('SELECT * FROM RESULTS WHERE vm = ? and test_name = ?', ([vm], [test_name]))

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
        self.conn.execute('INSERT INTO RESULTS VALUES (?,?,?,?,?,?,?,?,?,?)', (result.timestamp, result.test_name, result.vm, result.command,
                                                                               str(result.args), result.rite_result, result.parsed_result[0],
                                                                               result.rite_failed, result.rite_fail_log, result.side))

    def print_results_table(self):
        self.get_results_rows(None, None, True)

    def annichilate_table(self):
        self.conn.execute('DELETE FROM RESULTS')

    def insert_summary(self, timestamp, test_name, vm, error_list, rite_failed, manual):
        try:
            self.conn.execute('INSERT INTO SUMMARY VALUES (?,?,?,?,?,?)', (timestamp, test_name, vm, str(error_list), rite_failed, manual))
        except sqlite3.IntegrityError:
            print('This summary already exists')

    #this gets time-ordered (latest first) summaryfor a specific vm/test
    def get_summary_rows(self, vm, test_name, print_data=False):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM SUMMARY WHERE vm = ? and test_name = ? ORDER BY timestamp DESC', (vm, test_name))
        rows = cursor.fetchall()

        if print_data:
            print " ============================================================ "
            print "Dumping SUMMARY Table! (vm = %s , test_name = %s )" % (vm, test_name)
            print " ============================================================ "

            for i in rows:
                print i

        parsed_rows = []
        for i in rows:
            parsed_rows.append(parse_known_error_row(i))
        return parsed_rows

    def get_known_error(self, vm, test_name):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM SUMMARY WHERE vm = ? and test_name = ? and manual <> "0" ORDER BY timestamp DESC', (vm, test_name))
        row = cursor.fetchone()
        return parse_known_error_row(row)

    def apply_known_errors(self):
        self.conn.execute('DELETE FROM SUMMARY WHERE manual <> 0')
        # timestamp, test_name, vm, parsed_result[0], rite_failed, manual

        testerr = ["['FAILED', 'FAILED']"]
        self.conn.execute("INSERT INTO SUMMARY VALUES (0,'VM_ELITE_FAST_DEMO_SRV','avira',? ,'',1)", testerr)
        self.conn.execute("INSERT INTO SUMMARY VALUES (0,'VM_ELITE_FAST_DEMO_SRV','norton',? ,'',1)", testerr)
        self.conn.execute("INSERT INTO SUMMARY VALUES (0,'VM_SOLDIER_SRV','norton',? ,'',1)", testerr)


def parse_known_error_row(original_row):
        if original_row:
            print "dc", original_row
            row = list(original_row)
            if row[3]:
                errorlist = eval(row[3])
            else:
                errorlist = None
            return row[0], row[1], row[2], errorlist, row[4], row[5]
        else:
            return None