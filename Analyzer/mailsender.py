__author__ = 'mlosito'
import smtplib
import socket
from email.mime.text import MIMEText
from email.header import Header
from email.mime.multipart import MIMEMultipart
import cgi


class MailSender(object):

    retestlist = ""

    rite_fails = {}
    rite_known_fails = {}
    errors = {}
    known_errors = {}
    known_errors_but_test_passed = {}
    ok = {}
    not_enabled = {}

    rite_fails_num = 0
    rite_known_fails_num = 0
    errors_num = 0
    known_errors_num = 0
    ok_num = 0
    not_enabled_num = 0

    total_tests_num = 0

    sanity = 0

    #contains a list with the values: total, sane, rite_failed
    stats_by_test = {}

    yaml_analyzed = ""

    # , "f.cornelli@hackingteam.com", "m.oliva@hackingteam.com"
    def send_mail(self, mail_recipients=["m.losito@hackingteam.com", "f.cornelli@hackingteam.com", "m.oliva@hackingteam.com"], mail_server="mail.hackingteam.com"):
        # Create a text/plain message

        header_charset = 'ISO-8859-1'
        body_charset = 'ISO-8859-1'

        sender_name = str(Header(unicode("avtest@hackingteam.com"), header_charset))

        for recipient in mail_recipients:

            message = self.generate_text()
            msg = MIMEMultipart('alternative')

            #part1 = MIMEText(text, 'plain')
            htmlpart = MIMEText(message.encode(body_charset), 'html', body_charset)

            # According to RFC 2046, the last part of a multipart message, in this case the HTML message, is best and preferred.
            msg.attach(htmlpart)

            # msg = MIMEText(message)
            hostname = socket.gethostname()

            subject = 'ANALYZER_REPORT@%s - Sanity=%s%%' % (hostname, self.sanity)

            # Make sure email addresses do not contain non-ASCII characters

            recipient = recipient.encode('ascii')

            msg['Subject'] = Header(unicode(subject), header_charset)
            msg['From'] = sender_name
            msg['To'] = recipient

            print "Mail enabled. Msg to: %s to be sent" % msg['To']
            # Send the message via our own SMTP server, but don't include the
            # envelope header.
            s = smtplib.SMTP(mail_server)

            s.sendmail(msg['From'], [msg['To']], msg.as_string())
            s.quit()

    def rite_fails_add(self, vm, test, message):
        if not vm in self.rite_fails:
            self.rite_fails[vm] = {}
        self.rite_fails[vm][test] = message
        self.total_tests_num += 1
        self.rite_fails_num += 1
        if not test in self.stats_by_test:
            self.stats_by_test[test] = [0, 0, 0]
        self.stats_by_test[test][0] += 1  # adds total
        self.stats_by_test[test][2] += 1  # adds RITE_FAIL

    def rite_known_fails_add(self, vm, test, message):
        if not vm in self.rite_known_fails:
            self.rite_known_fails[vm] = {}
        self.rite_known_fails[vm][test] = message
        self.total_tests_num += 1
        self.rite_known_fails_num += 1
        if not test in self.stats_by_test:
            self.stats_by_test[test] = [0, 0, 0]
        self.stats_by_test[test][0] += 1  # adds total
        self.stats_by_test[test][1] += 1  # adds sane

    def errors_add(self, vm, test, message, details, save_strings):
        if not vm in self.errors:
            self.errors[vm] = {}
        self.errors[vm][test] = message, details, save_strings
        self.total_tests_num += 1
        self.errors_num += 1
        if not test in self.stats_by_test:
            self.stats_by_test[test] = [0, 0, 0]
        self.stats_by_test[test][0] += 1  # adds total

    def known_errors_add(self, vm, test, message, saved_error_comment):
        if not vm in self.known_errors:
            self.known_errors[vm] = {}
        self.known_errors[vm][test] = message, saved_error_comment
        self.total_tests_num += 1
        self.known_errors_num += 1
        if not test in self.stats_by_test:
            self.stats_by_test[test] = [0, 0, 0]
        self.stats_by_test[test][0] += 1  # adds total
        self.stats_by_test[test][1] += 1  # adds sane

    def known_errors_but_test_passed_add(self, vm, test, message, saved_error_comment):
        if not vm in self.known_errors_but_test_passed:
            self.known_errors_but_test_passed[vm] = {}
        self.known_errors_but_test_passed[vm][test] = message, saved_error_comment
        self.total_tests_num += 1
        self.ok_num += 1
        if not test in self.stats_by_test:
            self.stats_by_test[test] = [0, 0, 0]
        self.stats_by_test[test][0] += 1  # adds total
        self.stats_by_test[test][1] += 1  # adds sane

    def ok_add(self, vm, test, message):
        if not vm in self.ok:
            self.ok[vm] = {}
        self.ok[vm][test] = message
        self.total_tests_num += 1
        self.ok_num += 1
        if not test in self.stats_by_test:
            self.stats_by_test[test] = [0, 0, 0]
        self.stats_by_test[test][0] += 1  # adds total
        self.stats_by_test[test][1] += 1  # adds sane

    def rite_not_enabled_add(self, vm, test, message):
        if not vm in self.not_enabled:
            self.not_enabled[vm] = {}
        self.not_enabled[vm][test] = message
        self.total_tests_num += 1
        self.not_enabled_num += 1
        if not test in self.stats_by_test:
            self.stats_by_test[test] = [0, 0, 0]
        self.stats_by_test[test][0] += 1  # adds total
        self.stats_by_test[test][1] += 1  # adds sane

    def generate_text(self):

        #css styles
        mail_message = self.get_html_header()
        mail_message += self.generate_stats()

        mail_message += '<br><a id="retests"><div class="boldback" style="color: black">Retests to be run</div></a><br>'
        mail_message += self.retestlist

        mail_message += '<br><a id="rite_fails"><div class="boldback" style="background-color:darkred">RITE NEW FAILS - these are the tests in which the test system (rite) failed</div></a><br>'
        for vm in sorted(self.rite_fails):
            mail_message += "<details close><summary>Analyzed VM: %s</summary><p><br>" % vm
            for test in self.rite_fails[vm]:
                mail_message += '<span class="tab">Test: %s</p><br>' % test
                mail_message += '<span class="doubletab">%s</p><br>' % cgi.escape(self.rite_fails[vm][test])
            mail_message += "</p></details><hr>"
        mail_message += '<br><a id="rite_known_fails"><div class="boldback" style="background-color:green">RITE KNOWN FAILS - these are the tests in which the test system (rite) failed but we previously aknowledged that</div></a><br>'
        for vm in sorted(self.rite_known_fails):
            mail_message += "<details close><summary>Analyzed VM: %s</summary><p><br>" % vm
            for test in self.rite_known_fails[vm]:
                mail_message += '<span class="tab">Test: %s</p><br>' % test
                mail_message += '<span class="doubletab">%s</p><br>' % cgi.escape(self.rite_known_fails[vm][test])
            mail_message += "</p></details><hr>"
        mail_message += '<br><a id="errors"><div class="boldback" style="background-color:red">NEW ERRORS - these are the tests in which the test FAILED</div></a><br>'
        for vm in sorted(self.errors):
            mail_message += "<details close><summary>Analyzed VM: %s</summary><p><br>" % vm
            for test in self.errors[vm]:
                mail_message += '<p class="tab">Test: %s</p><br>' % test
                mail_message += '<p class="doubletab">%s</p><br>' % cgi.escape(self.errors[vm][test][0])  # gets only the message
            mail_message += "\n</p></details><hr>"
        mail_message += '<br><a id="known_errors"><div class="boldback" style="background-color:green">KNOWN ERRORS - these are the tests in which the test failed, but we previously aknowledged that</div></a><br>'
        for vm in sorted(self.known_errors):
            mail_message += "<details close><summary>Analyzed VM: %s</summary><p><br>" % vm
            for test in self.known_errors[vm]:
                mail_message += '<p class="tab">Test: %s</p><br>' % test
                mail_message += '<p class="doubletab" style="color: red;">Comment: %s</p><br>' % cgi.escape(self.known_errors[vm][test][1])
                mail_message += '<p class="doubletab">%s</p><br>' % cgi.escape(self.known_errors[vm][test][0])
            mail_message += "</p></details><hr>"
        mail_message += '<br><a id="known_errors"><div class="boldback" style="background-color:green">KNOWN ERRORS BUT PASSED - these are the tests in which the test passed, but we previously aknowledged an error. Some are not enabled tests.</div></a><br>'
        for vm in sorted(self.known_errors_but_test_passed):
            mail_message += "<details close><summary>Analyzed VM: %s</summary><p><br>" % vm
            for test in self.known_errors_but_test_passed[vm]:
                mail_message += '<p class="tab">Test: %s</p><br>' % test
                mail_message += '<p class="doubletab" style="color: red;">Comment: %s</p><br>' % cgi.escape(self.known_errors_but_test_passed[vm][test][1])
                mail_message += '<p class="doubletab">%s</p><br>' % cgi.escape(self.known_errors_but_test_passed[vm][test][0])
            mail_message += "</p></details><hr>"
        mail_message += '<br><a id="ok"><div class="boldback" style="background-color:green">OK - Passed tests</div></a><br>'
        for vm in sorted(self.ok):
            mail_message += "<details close><summary>Analyzed VM: %s</summary><p><br>" % vm
            tmp = ""
            for test in self.ok[vm]:
                mail_message += '<p class="tab">Test: %s</p><br>' % test
                mail_message += '<p class="doubletab">%s</p><br>' % cgi.escape(self.ok[vm][test])
            mail_message += "</p></details><hr>"
        #not implemented
        # mail_message += '<br><a id="not_enabled"><div class="boldback" style="background-color:gray">Not Enabled - Tests which are not enabled in this run</div></a><br>'
        # for vm in sorted(self.not_enabled):
        #     mail_message += "<details close><summary>Analyzed VM: %s</summary><p><br>" % vm
        #     tmp = ""
        #     for test in self.not_enabled[vm]:
        #         mail_message += '<p class="tab">Test: %s</p><br>' % test
        #         mail_message += '<p class="doubletab">%s</p><br>' % cgi.escape(self.not_enabled[vm][test])
        #     mail_message += "</p></details><hr>"
        mail_message += '<br><a id="errorsdetails"><div class="boldback" style="background-color:red">ERROR DETAILS - log of every operation and python code to acknowledge the error</div></a><br>'
        for vm in sorted(self.errors):
            mail_message += "<details close><summary>Analyzed VM: %s</summary><p><br>" % vm
            for test in self.errors[vm]:
                mail_message += '<p class="tab">Test: %s</p><br>' % test
                mail_message += '<p class="doubletab">%s</p><br>' % self.errors[vm][test][0]
                # mail_message += "<hr>"
                mail_message += '<details close><summary class="bold">ERROR LOG</summary><p class="doubletab">'
                # mail_message += "<hr>"
                mail_message += self.errors[vm][test][1]
                mail_message += "</p></details>"
                mail_message += '<details close><summary class="bold">HELPER FOR MANUAL</summary><p class="doubletab">'
                mail_message += self.errors[vm][test][2]
                mail_message += "</p></details>"
            mail_message += "</p></details><hr>"

        mail_message += self.get_html_footer()
        return mail_message

    def get_html_header(self):
        return '''
        <html>
        <head>
        <style>
            div.title   {font-weight: bold;
                        background-color: lightgray;
                        text-align: center;}
            div.test    {font-weight: normal;
                        background-color: #e0e0e0;
                        margin-left: auto;
                        margin-right: auto;
                        text-align: center;
                        border: 2px solid #707070;
                        border-radius: 5px;
                        box-shadow: 3px 3px 2px #888888;
                        padding: 4px;
                        width:55%;}
            div.bold {font-weight: bold}
            summary.bold {font-weight: bold;
                          padding-left:6em}
            div.boldback   {font-weight: bold;
                          background-color: #b0b0b0;
                          color: white;
                          text-align: center;}
            p.tab    {padding-left:3em}
            p.doubletab    {padding-left:6em}
            .percentbar { background: red; border:1px solid #000000; height:10px; margin-left: auto;
                          margin-right: auto; box-shadow: 3px 3px 2px #888888; }
            .percentbar div { background: green; height: 10px; }
        </style>
        </head>
        <body>
        '''

    def get_html_footer(self):
        return '''<br>
                  <br>
                    File analyzed: %s
                  </body>
                  </html>''' % self.yaml_analyzed

    def generate_stats(self):
        #calculate sanity  - test success percentage, higher is better
        rite_fails = 0
        if self.total_tests_num > 0:

            self.sanity = round((((self.ok_num+self.known_errors_num+self.rite_known_fails_num+self.not_enabled_num)*100.0)/(self.total_tests_num*100.0))*100, 2)
            rite_fails = round(((self.rite_fails_num*100.0)/(self.total_tests_num*100.0))*100, 2)
        else:
            self.sanity = "Unknown"

        stat_text = '<div class="title">'
        stat_text += '<div style="font-size: 140%;background-color: #b0b0b0;">Analyzer Report RITE</div>'
        #if sanity is a numner, displays percentage bar
        if not self.sanity == "Unknown":
            stat_text += "Sanity: %s%% (Rite fails: %s%%)" % (self.sanity, rite_fails)
            stat_text += '''
                <div class="percentbar" style="width:200px;">
                    <div style="width:%spx;"></div>
                    <div style="width:%spx;background:darkred;float: right"></div>
                </div>
                </br>
                ''' % (self.sanity*2, rite_fails*2)
        else:
            stat_text += "Unknown Sanity (0 test runs reported from Rite)<br>"

        stat_text += '<a href="#rite_fails">Rite new fails: %s</a><br>' % self.rite_fails_num
        stat_text += '<a href="#rite_known_fails">Rite known fails: %s</a><br>' % self.rite_known_fails_num
        stat_text += '<a href="#errors">New Errors: %s</a><br>' % self.errors_num
        stat_text += '<a href="#errorsdetails">Error details link</a><br>'
        stat_text += '<a href="#known_errors">Known Errors: %s<br></a>' % self.known_errors_num
        stat_text += '<a href="#ok">OK: %s<br></a>' % self.ok_num
        #not implemented
        #stat_text += '<a href="#not_enabled">Not Enabled: %s<br></a>' % self.not_enabled_num
        stat_text += "TOTAL: %s<br>" % self.total_tests_num
        stat_text += '<p style="font-weight: normal;">Always remember that th "Known Errors" are very very important because they are the problems we known we have. Every known error have a comment.</p><br>'
        stat_text += '<br><a id="retests"><div class="boldback" style="color: black; font-size: 125%;">Stats by test</div></a><br>'

        for test in sorted(self.stats_by_test):
            test_sanity = round((((self.stats_by_test[test][1])*100.0)/(self.stats_by_test[test][0]*100.0))*100, 2)
            test_rite_fails = round(((self.stats_by_test[test][2]*100.0)/(self.stats_by_test[test][0]*100.0))*100, 2)
            stat_text += '''
            <div class="test"> Test: %s (Sane: %s%%, Rite fails: %s%%)
                <div class="percentbar" style="width:200px;">

                    <div style="width:%spx;"></div>
                    <div style="width:%spx;background:darkred;float: right"></div>

                </div>
            </div>
            </br>
            ''' % (test, test_sanity, rite_fails, test_sanity*2, rite_fails*2)

        stat_text += '</div>'
        return stat_text