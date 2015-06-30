from ConfigParser import ConfigParser, NoOptionError
import os
import subprocess
import yaml
from Analyzer import dbreport

__author__ = 'mlosito'

import smtplib
import socket
import datetime
import cgi
import sys

import tesserhackt
from ocrdict import OcrDict

sys.path.append("./Rite/")

from email.mime.text import MIMEText
from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage

from AVCommon.commands.meta import VM_ALL


class MailSender(object):

    invert_result_tests = ["VM_PUSH_VIRUS"]

    #important_tests = ['VM_ELITE_FAST_SCOUTDEMO_SRV', 'VM_ELITE_FAST_SRV', 'VM_EXPLOIT_SRV', 'VM_SOLDIER_SRV', 'VM_STATIC_SRV']
    important_tests = ['VM_STATIC_SRV', 'VM_ELITE_FAST_SRV', 'VM_SOLDIER_SRV']

    enabled = {'VM_ELITE_FAST_DEMO_SRV': ['sunday'],
               'VM_EXPLOIT_SRV': ['sunday'],
               'VM_MELT_SRV_AIR': ['wednesday', 'saturday'],
               'VM_MELT_SRV_FIF': ['monday', 'thursday'],
               'VM_MELT_SRV_UTO': ['tuesday', 'friday'],
               'VM_MELT_SRV_VUZ': ['sunday']}

    retestlist = ""

    class ResultTypes(object):
        RITE_FAILS = "RITE NEW FAILS"
        RITE_KNOWN_FAILS = "RITE KNOWN FAILS"
        NEW_ERRORS = "NEW ERRORS"
        KNOWN_ERRORS = "KNOWN ERRORS"
        KNOWN_ERRORS_BUT_PASSED = "KNOWN ERRORS BUT PASSED"
        OK = "OK"
        NOT_RUN = "NO RUN"

    #all datas on tests
    all_results = {}

    #stats
    total_tests_num = 0
    sanity_percentage = 0
    rite_errors_percentage = 0
    rite_fails_percentage = 0
    not_run_percentage = 0
    #stats dicts
    stats_by_test = {}
    stats_by_result_type = {}
    stats_by_vm = {}
    times_by_vm = {}
    #stat vm/test matrix (which is an av-indexed dictionary)
    expected_table = {}

    #for footer
    yaml_analyzed = []
    known_error_reports = None

    # (ordered) list of the results every test should return
    results_to_receive = []

    default_yaml = None
    vms_cfg = None

    # , "f.cornelli@hackingteam.com", "m.oliva@hackingteam.com"
    def send_mail(self, mail_recipients=["m.losito@hackingteam.com", "f.cornelli@hackingteam.com", "m.oliva@hackingteam.com"], mail_server="mail.hackingteam.com"):
        # Create a text/plain message

        header_charset = 'ISO-8859-1'
        body_charset = 'ISO-8859-1'

        sender_name = str(Header(unicode("avtest@hackingteam.com"), header_charset))

        msg_root = MIMEMultipart('related')
        msg = MIMEMultipart('alternative')
        msg_root.attach(msg)

        message = self.generate_text(msg_root)

        htmlpart = MIMEText(message.encode(body_charset), 'html', body_charset)

        # According to RFC 2046, the last part of a multipart message, in this case the HTML message, is best and preferred (here we have just html).
        msg.attach(htmlpart)

        hostname = socket.gethostname()
        if self.rite_errors_percentage == 0.0:
            subject = 'RiteAnalyzer - FLAWLESS VICTORY!!! - Fails=%s%%+%s%%' % (self.rite_fails_percentage, self.not_run_percentage)
        else:
            subject = 'RiteAnalyzer - Sanity=%s%% - Errors=%s%% - Fails=%s%%+%s%%' % (self.sanity_percentage, self.rite_errors_percentage, self.rite_fails_percentage, self.not_run_percentage)

        # for recipient in mail_recipients:
        #     # Make sure email addresses do not contain non-ASCII characters
        #     recipient = recipient.encode('ascii')
        #     msg_root.Message.add_header('To', recipient)

        # recipient = recipient.encode('ascii')
        msg_root['Subject'] = Header(unicode(subject), header_charset)
        msg_root['From'] = sender_name
        msg_root['To'] = ", ".join(mail_recipients)

        print "Mail enabled. Msg to: %s to be sent. Mail size: %s" % (msg_root['To'], len(msg_root.as_string()))
        # Send the message via our own SMTP server, but don't include the
        # envelope header.
        s = smtplib.SMTP(mail_server)

        # reci[pients as list [msg_root['To']]
        s.sendmail(msg_root['From'], mail_recipients, msg_root.as_string())
        s.quit()

    def add_result(self, vm, test, result_types, message, details=None, save_strings=None, saved_error_comment=None, crop_filenames=None,
                   popup_results=None, time=0):
        if not vm in self.all_results:
            self.all_results[vm] = {}
        if not test in self.all_results[vm]:
            self.all_results[vm][test] = {}
        self.all_results[vm][test]['result_type'] = result_types
        self.all_results[vm][test]['message'] = message
        self.all_results[vm][test]['details'] = details
        self.all_results[vm][test]['save_string'] = save_strings
        self.all_results[vm][test]['saved_error_comment'] = saved_error_comment
        self.all_results[vm][test]['crop_filenames'] = crop_filenames
        self.all_results[vm][test]['popup_results'] = popup_results
        self.all_results[vm][test]['time'] = time

    #we pass msg that is the "root" multipart. We have to attach to it the images.
    def generate_text(self, msg):

        self.load_default_yaml('Rite/AVAgent/default.yaml')
        self.load_vms_cfg('Rite/AVMaster/conf/vms-rite.cfg')

        #css styles
        mail_message = self.get_html_header()
        mail_message += self.generate_stats(msg)

        mail_message += self.get_html_retests()

        mail_message += self.get_html_avtest_table()

        mail_message += self.get_html_body(msg)

        mail_message += self.get_html_footer()
        return mail_message

    def get_html_retests(self):
        mail_message = '<br><a id="retests"><div class="boldback" style="color: black">Retests to be run</div></a><br>'
        mail_message += '<div class="cleancontainer">'
        mail_message += self.retestlist
        mail_message += '</div>'
        return mail_message

    def get_html_header(self):
        return '''
        <!DOCTYPE html>
        <html>
        <head>
        <style>
            div.title   {
                        /*font-weight: bold;*/
                        background-color: lightgray;
                        text-align: center;
                        padding: 8px;
                        }
            div.testcontainer {
                        background-color: #e0e0e0;
                        margin-left: auto;
                        margin-right: auto;
                        margin-top: 4px;
                        margin-bottom: 4px;
                        border: 2px solid #707070;
                        border-radius: 5px;
                        box-shadow: 3px 3px 2px #888888;
                        padding: 4px;

                        max-width: 700px;
                        }
            div.cleancontainer {
                        border: 1px solid #707070;
                        border-radius: 7px;
                        box-shadow: 2px 3px 2px #A0A0A0;
                        padding: 4px;
                        }
            div.test    {
                        font-weight: normal;
                        text-align: center;
                        }
            div.bold {font-weight: bold}
            span.bold {font-weight: bold}
            summary.bold {font-weight: bold;
                          padding-left:6em}
            div.boldback   {font-weight: bold;
                          background-color: #b0b0b0;
                          color: white;
                          text-align: center;
                          padding: 4px;}
            p.tab    {padding-left:3em}
            div.doubletab    {padding-left:6em}
            ol.doubletab   {padding-left:2em}
            img.tab  {padding-left:9em}
            img.logo  {
                       width: 25%;
                       display: block;
                       margin-left: auto;
                       margin-right: auto;
                      }
            img.icon {
                        height: 16px;
                        width: 16px;
                      }
            .percentbar {   background: red;
                            border:1px solid #000000;
                            height:10px; width:200px;
                            margin-left: auto;
                            margin-right: auto;
                            box-shadow: 3px 3px 2px #888888;
                        }
            .percentbar div { background: green ;
                                height: 10px;
                                float: left;
                                }

            th {
                border-collapse: collapse;
                /* border: 1px solid black;*/
                color: black;
                background-color: white;
                vertical-align: bottom;
                }
            table, td, th {
                -webkit-border-radius: 4px;
                -moz-border-radius:    4px;
                border-radius:         4px;
                }
            table {
                   margin-left: auto;
                   margin-right: auto;
                  }
            td.av {
                border-collapse: collapse;
                background-color: white;
                color: black;
                text-align: right;
                font-weight: bold;
                }
            td.green {
                background-color: green;
                color: white;
                }
            td.red {
                background-color: red;
                color: white;
                }
            td.darkred {
                background-color: darkred;
                color: white;
                }
            td.white {
                background-color: white;
                color: black;
                }
            td.gray {
                background-color: gray;
                color: black;
                }
            /* All link in the table should be white!*/
            table a {
                color: white;
                }
        </style>
        </head>
        <body>
        '''

    def get_html_footer(self):
        return '''<br>
                  <br>
                    Files analyzed: %s
                  </body>
                  </html>''' % str(self.yaml_analyzed)

    def get_result_type_section_html(self, result_type, ocrd, mime_msg, error_details=False):
        attachment_number = 0
        mail_message = '<div class="cleancontainer">'
        for vm in sorted(self.all_results):
            #if it hase some results of this type I put the header and
            found = False
            for test in self.all_results[vm]:
                # print test
                # print result_type
                #checks if there is a test of this result type to add the vm
                #but if the test is disabled today, I should not add it to KNOWN BUT PASSED (otherwise we fill that section of garbage)
                if self.all_results[vm][test]['result_type'] == result_type and not (result_type == self.ResultTypes.KNOWN_ERRORS_BUT_PASSED and self.disabled_today(test)):
                    found = True

            if found:
                mail_message += '<details close><summary style="display:inline">Analyzed VM: %s</summary><p><br>' % self.decorate_vm(vm)
                for test in self.all_results[vm]:
                    if self.all_results[vm][test]['result_type'] == result_type:
                        #if the test is disabled today, I should not add it to KNOWN BUT PASSED (otherwise we fill that section of garbage)
                        if result_type == self.ResultTypes.KNOWN_ERRORS_BUT_PASSED and self.disabled_today(test):
                            continue
                        mail_message += '<p class="tab">Test: %s, Execution time in minutes: %s</p><br>' % (self.decorate_test(test, vm), self.all_results[vm][test]['time'])
                        if self.all_results[vm][test]['saved_error_comment']:
                            mail_message += '<div class="doubletab" style="color: red;">Comment: %s</div><br>' % cgi.escape(self.all_results[vm][test]['saved_error_comment'])
                        mail_message += '<div class="doubletab">%s</div><br>' % self.all_results[vm][test]['message']  # before here was used cgi.escape(
                        #details for errors
                        if error_details:
                            mail_message += '<details close><summary class="bold">ERROR LOG</summary><div class="doubletab">'
                            mail_message += self.all_results[vm][test]['details']
                            mail_message += "</div></details>"
                            mail_message += '<details close><summary class="bold">HELPER FOR MANUAL</summary><div class="doubletab">'
                            mail_message += self.all_results[vm][test]['save_string']
                            mail_message += "</div></details>"

                        #in error details I dont's show crops
                        if result_type != self.ResultTypes.NEW_ERRORS or not error_details:
                            if self.all_results[vm][test]['crop_filenames']:
                            #crops
                            #here I re-analyze every crop, for 2 reasons: 1: i do not have to bring all the values to this level; 2 to check consistency
                                for crop in self.all_results[vm][test]['crop_filenames']:
                                    result, word, thumb_filename = tesserhackt.process(av=vm, num=crop, ocrd=ocrd)
                                    #good case:
                                    if thumb_filename == "":
                                        mail_message += '<div class="doubletab">%s - <b>%s</b> - got word: %s - [image omitted] </div><br>' % (str(crop), result, word)
                                    #not good:
                                    else:
                                        mail_message += '<div class="doubletab">%s - <b>%s</b> - got word: %s - filename: %s </div><br>' % (str(crop), result, word, thumb_filename)
                                        img_fp = open(thumb_filename, 'rb')
                                        img_data = img_fp.read()
                                        # Now create the MIME container for the image
                                        cid = vm+"-"+str(crop)
                                        img = MIMEImage(img_data)  # , 'jpeg'

                                        img.add_header('Content-Id', '<%s>' % cid)  # angle brackets are important
                                        #not necessary
                                        # img.add_header("Content-Disposition", "inline", filename=thumb_filename)  # David Hess recommended this edit
                                        mime_msg.attach(img)
                                        img_fp.close()
                                        attachment_number += 1
                                        mail_message += '<img class="tab" src="cid:%s">' % cid
                            elif self.all_results[vm][test]['popup_results']:
                                for result_list in self.all_results[vm][test]['popup_results'][0:11]:
                                    result, thumb_filename, word = result_list
                                    mail_message += '<div class="doubletab"><b>%s</b> - got word: %s - filename: %s </div><br>' % (result, word, thumb_filename)
                                    if os.path.exists(thumb_filename):
                                        img_fp = open(thumb_filename, 'rb')
                                        img_data = img_fp.read()
                                        # Now create the MIME container for the image
                                        cid = vm+"-"+str(thumb_filename)
                                        img = MIMEImage(img_data)  # , 'jpeg'

                                        img.add_header('Content-Id', '<%s>' % cid)  # angle brackets are important
                                        #not necessary
                                        # img.add_header("Content-Disposition", "inline", filename=thumb_filename)  # David Hess recommended this edit
                                        mime_msg.attach(img)
                                        img_fp.close()
                                        attachment_number += 1
                                        mail_message += '<img class="tab" src="cid:%s">' % cid
                                    else:
                                        mail_message += '<div class="doubletab"><b>ERROR: filename %s not found on server! IMAGE OMITTED!</b></div>' % thumb_filename
                                if len(self.all_results[vm][test]['popup_results']) > 7:
                                    mail_message += '<div class="doubletab"><b>TOO MANY POPUPS. %i IMAGES OMITTED!</b></div>' % (len(self.all_results[vm][test]['popup_results']) - 8)
                mail_message += "</p></details><hr>"
        mail_message += '</div>'
        if result_type == self.ResultTypes.NEW_ERRORS and attachment_number == 0 and not error_details:
            print "WARNING: NEW ERRORS HAVE NO ATTACHMENTS. CHECK popup_thumbs dir and permissions!"
        else:
            print "Number of attachments in section %s: %s" % (result_type, attachment_number)
        return mail_message

    def get_html_body(self, mime_msg):

        self.attach_images(mime_msg)

        ocrd = OcrDict()

        mail_message = '<br><a id="rite_fails"><div class="boldback" style="background-color:darkred">RITE NEW FAILS - these are the tests in which the test system (rite) failed</div></a><br>'
        mail_message += self.get_result_type_section_html(self.ResultTypes.RITE_FAILS, ocrd, mime_msg, error_details=True)

        mail_message += '<br><a id="rite_known_fails"><div class="boldback" style="background-color:green">RITE KNOWN FAILS - these are the tests in which the test system (rite) failed but we previously aknowledged that</div></a><br>'
        mail_message += self.get_result_type_section_html(self.ResultTypes.RITE_KNOWN_FAILS, ocrd, mime_msg)

        mail_message += '<br><a id="errors"><div class="boldback" style="background-color:red">NEW ERRORS - these are the tests in which the test FAILED</div></a><br>'
        mail_message += self.get_result_type_section_html(self.ResultTypes.NEW_ERRORS, ocrd, mime_msg)

        mail_message += '<br><a id="known_errors"><div class="boldback" style="background-color:green">KNOWN ERRORS - these are the tests in which the test failed, but we previously aknowledged that</div></a><br>'
        mail_message += self.get_result_type_section_html(self.ResultTypes.KNOWN_ERRORS, ocrd, mime_msg)

        mail_message += '<br><a id="known_errors"><div class="boldback" style="background-color:green">KNOWN ERRORS BUT PASSED - these are the tests in which the test passed, but we previously aknowledged an error. Some are not enabled tests.</div></a><br>'
        mail_message += self.get_result_type_section_html(self.ResultTypes.KNOWN_ERRORS_BUT_PASSED, ocrd, mime_msg)

        mail_message += '<br><a id="ok"><div class="boldback" style="background-color:green">OK - Passed tests</div></a><br>'
        mail_message += self.get_result_type_section_html(self.ResultTypes.OK, ocrd, mime_msg)

        mail_message += '<br><a id="errorsdetails"><div class="boldback" style="background-color:red">ERROR DETAILS - log of every operation and python code to acknowledge the error (crops are not shown here)</div></a><br>'
        mail_message += self.get_result_type_section_html(self.ResultTypes.NEW_ERRORS, ocrd, mime_msg, error_details=True)

        mail_message += '<br><a id="errorsdetails"><div class="boldback" style="background-color:blue">KNOWN ERRORS FRIENDLY REPORT - All the errors we known about</div></a><br>'
        mail_message += self.get_known_errors_report()

        return mail_message

    def get_known_errors_report(self):
        mail_message = '<div class="cleancontainer">'
        for vm in self.known_error_reports:
            mail_message += '<details close><summary style="display:inline">Analyzed VM: %s</summary><p><br>' % self.decorate_vm(vm)
            for test in self.known_error_reports[vm]:
                mail_message += '<p class="tab"><b>Test: ' + test + '</b> - Comment: <b>' + self.known_error_reports[vm][test][0][3] + '</b></p>'
                for res in self.known_error_reports[vm][test]:
                    vm, test, type_comment, manual_comment, manual_optional = res
                    mail_message += '<div class="doubletab">ERROR: %s - Occurs only some times: %s<br>' % (type_comment, manual_optional) + '</div>' #"%s - %s - %s - %s - manual_optional= %s <br>" %
            mail_message += '</details><hr>'
        mail_message += '</div>'
        return mail_message

    def generate_stats(self, mime_msg):

        self.calculate_stats()

        self.attach_image('logo', mime_msg)

        stat_text = '<div class="title">'
        # stat_text += '<img class="logo" src="cid:logo">'
        stat_text += '<div style="font-size: 200%; font-weight: lighter; background-color: white;padding: 5px; font-family: calibri"><img class="logo" src="cid:logo"><b>]</b>Rite<b>Analyzer</b>[</div>'
        stat_text += '<div class="testcontainer" style="font-weight: bold;">'
        #if sanity is a number, displays percentage bar
        if not self.sanity_percentage == "Unknown":
            stat_text += "Global Sanity: %s%% - New Errors:%s%% (Rite fails: %s%% - Not run: %s%%)" % (self.sanity_percentage, self.rite_errors_percentage, self.rite_fails_percentage, self.not_run_percentage)
            stat_text += '''
                <div class="percentbar">
                    <div style="width:%spx;"></div>
                    <div style="width:%spx;background:white;"></div>
                    <div style="width:%spx;background:darkred;"></div>
                </div>
                </br>
                ''' % (self.sanity_percentage*2, self.not_run_percentage*2, self.rite_fails_percentage*2)
        else:
            stat_text += "Unknown Sanity (0 test runs reported from Rite)<br>"

        stat_text += '<a href="#rite_fails">Rite new fails: %s</a><br>' % self.stats_by_result_type[self.ResultTypes.RITE_FAILS]
        stat_text += '<a href="#rite_known_fails">Rite known fails: %s</a><br>' % self.stats_by_result_type[self.ResultTypes.RITE_KNOWN_FAILS]
        stat_text += '<a href="#errors">New Errors: %s</a><br>' % self.stats_by_result_type[self.ResultTypes.NEW_ERRORS]
        stat_text += '<a href="#errorsdetails">Error details link</a><br>'
        stat_text += '<a href="#known_errors">Known Errors: %s<br></a>' % self.stats_by_result_type[self.ResultTypes.KNOWN_ERRORS]
        # stat_text += '<a href="#crop">Crops<br></a>'
        stat_text += '<a href="#ok">OK: %s<br></a>' % str(self.stats_by_result_type[self.ResultTypes.OK] + self.stats_by_result_type[self.ResultTypes.KNOWN_ERRORS_BUT_PASSED])
        #not implemented
        #stat_text += '<a href="#not_enabled">Not Enabled: %s<br></a>' % self.not_enabled_num
        stat_text += "TOTAL: %s<br>" % self.total_tests_num
        stat_text += '<p style="font-weight: normal;">Always remember that the "Known Errors" are very very important because they are the problems we known we have. Every known error have a comment.</p>'
        stat_text += '</div>'
        stat_text += '<br><a id="retests"><div class="boldback" style="color: black; font-size: 125%;">Stats by test</div></a><br>'
        stat_text += '<div class="testcontainer">'
        for test in sorted(self.stats_by_test):
            test_sane = self.stats_by_test[test][self.ResultTypes.OK] + self.stats_by_test[test][self.ResultTypes.KNOWN_ERRORS_BUT_PASSED] +\
                self.stats_by_test[test][self.ResultTypes.KNOWN_ERRORS] + self.stats_by_test[test][self.ResultTypes.RITE_KNOWN_FAILS]
            test_sanity = round(((test_sane*100.0)/(self.stats_by_test[test]['total']*100.0))*100, 2)
            test_no_run = round(((self.stats_by_test[test][self.ResultTypes.NOT_RUN]*100.0)/(self.stats_by_test[test]['total']*100.0))*100, 2)
            test_rite_fails = round(((self.stats_by_test[test][self.ResultTypes.RITE_FAILS]*100.0)/(self.stats_by_test[test]['total']*100.0))*100, 2)

            stat_text += '''
            <div class="test"> Test: %s (Sane: %s%%, Not run: %s%%, Rite fails: %s%%)
                <div class="percentbar">

                    <div style="width:%spx;"></div>
                    <div style="width:%spx;background:white;"></div>
                    <div style="width:%spx;background:darkred;"></div>

                </div>
            </div>
            </br><hr>
            ''' % (self.decorate_test(test), test_sanity, test_no_run, test_rite_fails, test_sanity*2, test_no_run*2, test_rite_fails*2)

        #end testcontainer
        stat_text += '</div>'
        #end title
        stat_text += '</div>'
        return stat_text

    def get_html_avtest_table(self):
        table_text = '<br><div class="boldback" style="background-color:lightgray; color: black">Result matrix</div><br>'
        table_text += '<div class="testcontainer">'
        table_text += "<table><tr>"
        table_text += '<th style="background-color:#e0e0e0;border: none;"></th>'
        # here I search for the expected results
        for test in self.results_to_receive:
        #for test in sorted(self.stats_by_test):
            test_title = ""
            for letter in test:
                test_title += letter + '<br>'
            #if disabled, text is gray
            if self.disabled_today(test):
                table_text += '<th><span style="color: darkgray;" title="%s">%s</span></th>' % (test, test_title)
            else:
                table_text += '<th><span title="%s">%s</span></th>' % (test, test_title)
        for vm in sorted(self.expected_table):
            table_text += '<tr>'
            table_text += '<td class="av">%s</td>' % self.decorate_vm(vm, icons=True)
            for test in self.results_to_receive:
                table_text += self.decorate_result(self.expected_table[vm][test], vm, test, self.all_results[vm][test]['time'])
            table_text += '</tr>'
        table_text += "</table>"

        # calculate occupied space on /
        df = subprocess.Popen(["sh", "-c", "df", "/"], stdout=subprocess.PIPE)
        output = df.communicate()[0]
        device, size, used, available, percent, mountpoint = output.split("\n")[1].split()

        percent_available = (float(available)/(float(used)+float(available)) * 100)

        table_text += '<div style="margin-left:auto;margin-right:auto;">RF=Rite new Fails, RK=Rite Known fails, NE=New Error, KE=Known Error, KP=Known error but Passed, OK=OK, NT=Not enabled Today, NR=Not run, probably caused by previous error(s)</div><hr>'
        table_text += '<div style="margin-left:auto;margin-right:auto;">Temporarily deactivated vms: <b>%s</b><br><hr>' % VM_ALL.vm_deactivated_temp
        table_text += '<img class="icon" src="cid:ok">= Silent ok (Elite or Soldier is evaluated, depending on soldierlist)<br>'
        table_text += '<img class="icon" src="cid:error">= Silent new error (Elite or Soldier is evaluated, depending on soldierlist)<br>'
        table_text += '<img class="icon" src="cid:fix">= VM to fix (only Elite or Soldier test is evaluated)<br>'
        table_text += '<img class="icon" src="cid:soldier">= In SoldierList (Soldier test is evaluated)<br>'
        table_text += '<img class="icon" src="cid:blacklist">= In Blacklist (No test is evaluated)<br>'
        table_text += '<img class="icon" src="cid:save">= Saved error or saved fail (for Elite or Soldier)<br><hr>'
        table_text += 'Available space on Rite mountpoint "%s" is: %.2f%%' % (mountpoint, percent_available)
        if percent_available < 20:
            table_text += '<b> WARNING LOW DISK FREE ON RITE!</b> (Check /tmp/tmp*)<br>'
        table_text += '</div>'

        table_text += "</div>"
        return table_text

    def calculate_stats(self):

        #detect NOT RUN
        for vm in self.all_results:
            for test in self.results_to_receive:
                if test not in self.all_results[vm]:
                    self.add_result(vm, test, self.ResultTypes.NOT_RUN, "No Message")

        #initialize structures:
        self.stats_by_result_type[self.ResultTypes.RITE_FAILS] = 0
        self.stats_by_result_type[self.ResultTypes.RITE_KNOWN_FAILS] = 0
        self.stats_by_result_type[self.ResultTypes.OK] = 0
        self.stats_by_result_type[self.ResultTypes.NEW_ERRORS] = 0
        self.stats_by_result_type[self.ResultTypes.KNOWN_ERRORS] = 0
        self.stats_by_result_type[self.ResultTypes.KNOWN_ERRORS_BUT_PASSED] = 0
        self.stats_by_result_type[self.ResultTypes.NOT_RUN] = 0

        for vm in self.all_results:
            self.times_by_vm[vm] = 0
            for test in self.all_results[vm]:
                #adds to total
                self.total_tests_num += 1
                #adds result by test
                if not test in self.stats_by_test:
                    self.stats_by_test[test] = {}
                    self.stats_by_test[test][self.ResultTypes.RITE_FAILS] = 0
                    self.stats_by_test[test][self.ResultTypes.RITE_KNOWN_FAILS] = 0
                    self.stats_by_test[test][self.ResultTypes.OK] = 0
                    self.stats_by_test[test][self.ResultTypes.NEW_ERRORS] = 0
                    self.stats_by_test[test][self.ResultTypes.KNOWN_ERRORS] = 0
                    self.stats_by_test[test][self.ResultTypes.KNOWN_ERRORS_BUT_PASSED] = 0
                    self.stats_by_test[test][self.ResultTypes.NOT_RUN] = 0
                if not self.all_results[vm][test]['result_type'] in self.stats_by_test[test]:
                    self.stats_by_test[test][self.all_results[vm][test]['result_type']] = 1
                else:
                    self.stats_by_test[test][self.all_results[vm][test]['result_type']] += 1
                if not 'total' in self.stats_by_test[test]:
                    self.stats_by_test[test]['total'] = 1
                else:
                    self.stats_by_test[test]['total'] += 1

                # adds stats by result_type
                if not self.all_results[vm][test]['result_type'] in self.stats_by_result_type:
                    self.stats_by_result_type[self.all_results[vm][test]['result_type']] = 1
                else:
                    self.stats_by_result_type[self.all_results[vm][test]['result_type']] += 1

                #calculating silent invisibility for av
                if test == 'VM_SOLDIER_SRV' and vm in self.default_yaml['soldierlist']:
                    self.stats_by_vm[vm] = self.all_results[vm][test]['result_type']
                elif test == 'VM_ELITE_FAST_SRV' and vm not in self.default_yaml['blacklist'] and vm not in self.default_yaml['soldierlist']:
                    self.stats_by_vm[vm] = self.all_results[vm][test]['result_type']

                self.times_by_vm[vm] += self.all_results[vm][test]['time']

        if self.total_tests_num > 0:

            self.sanity_percentage = round((((self.stats_by_result_type[self.ResultTypes.OK] +
                                              self.stats_by_result_type[self.ResultTypes.KNOWN_ERRORS] +
                                              self.stats_by_result_type[self.ResultTypes.RITE_KNOWN_FAILS] +
                                              self.stats_by_result_type[self.ResultTypes.KNOWN_ERRORS_BUT_PASSED])*100.0) /
                                            (self.total_tests_num*100.0))*100, 2)
            self.rite_errors_percentage = round(((self.stats_by_result_type[self.ResultTypes.NEW_ERRORS]*100.0)/(self.total_tests_num*100.0))*100, 2)
            self.rite_fails_percentage = round(((self.stats_by_result_type[self.ResultTypes.RITE_FAILS]*100.0)/(self.total_tests_num*100.0))*100, 2)
            self.not_run_percentage = round(((self.stats_by_result_type[self.ResultTypes.NOT_RUN]*100.0)/(self.total_tests_num*100.0))*100, 2)
        else:
            self.sanity_percentage = "Unknown"

        #calculate test/vm matrix
        for vm in self.all_results:
            self.expected_table[vm] = {}
            #here I searche for tehe expected results
            for test in self.results_to_receive:
                # if test in self.all_results[vm]:
                self.expected_table[vm][test] = self.all_results[vm][test]['result_type']
                # else:
                #     self.expected_table[vm][test] = self.ResultTypes.NOT_RUN

    def decorate_test(self, test, vm=None):
        if vm:
            decorated_test = '<a id="res_%s_%s">%s</a>' % (vm, test, test)
        else:
            decorated_test = test

        if test in self.important_tests:
            decorated_test = '<span class="bold" style="text-decoration: underline;">%s</span>' % decorated_test

        if test in self.invert_result_tests:
            decorated_test = '<span class="bold">Inverted: %s</span>' % decorated_test

        if self.disabled_today(test):
            decorated_test = '<span style="color: darkgray; text-decoration: line-through;">Disabled today: %s</span>' % decorated_test

        return decorated_test

    def decorate_result(self, result, vm, test, time):
        time_string = "[" + str(time) + "]"  # .zfill(3)
        #function to create a link

        def create_link(text, vm, test, css_class):
            border = ''
            if test == 'VM_SOLDIER_SRV' and vm in self.default_yaml['soldierlist']:
                border = 'style="border: 3px solid black;"'
            elif test == 'VM_ELITE_FAST_SRV' and vm not in self.default_yaml['blacklist'] and vm not in self.default_yaml['soldierlist']:
                border = 'style="border: 3px solid black;"'
            return '<td class="%s" %s><a href="#res_%s_%s">%s<sup>%s</sup></td>' % (css_class, border, vm, test, text, time_string)

        if result == self.ResultTypes.RITE_FAILS:
            return create_link("RF", vm, test, "darkred")

        elif result == self.ResultTypes.NEW_ERRORS:
            return create_link("NE", vm, test, "red")

        elif result == self.ResultTypes.NOT_RUN:
            return '<td class="white">NR</td>'

        #I see if there is an error before using the "Not Today" Option
        if self.disabled_today(test):
            return create_link("NT", vm, test, "gray")

        elif result == self.ResultTypes.RITE_KNOWN_FAILS:
            return create_link("RK", vm, test, "green")

        elif result == self.ResultTypes.KNOWN_ERRORS:
            return create_link("KE", vm, test, "green")

        elif result == self.ResultTypes.KNOWN_ERRORS_BUT_PASSED:
            return create_link("KP", vm, test, "green")

        elif result == self.ResultTypes.OK:
            return create_link("OK", vm, test, "green")

        else:
            return '<td class="white">??</td>'

    #icons are showed only in header where icons=True
    def decorate_vm(self, vm, icons=False):
        vm_txt = vm
        #adds level icon
        if vm in self.default_yaml['soldierlist']:
            #vm_txt += '<sub style="color: red;">[soldier]</sub>'
            vm_txt += '<img class="icon" src="cid:soldier">'
        if vm in self.default_yaml['blacklist']:
            #vm_txt += '<sub style="color: black;">[blacklist]</sub>'
            vm_txt += '<img class="icon" src="cid:blacklist">'
        #adds virtual machine name
        vm_txt += "<sup>" + self.get_vm_name(vm) + "</sup>"

        #writes total time for vm (only in header)
        if icons:
            if self.times_by_vm[vm]:
                vm_txt += "<sup>[" + str(self.times_by_vm[vm]) + "]</sup>"

        #adds result icon(s)
        if vm in self.stats_by_vm and icons:
            #errors
            if self.stats_by_vm[vm] == self.ResultTypes.NEW_ERRORS:
                vm_txt += '<img class="icon" src="cid:error">'
            #ok
            elif self.stats_by_vm[vm] in [self.ResultTypes.OK, self.ResultTypes.KNOWN_ERRORS, self.ResultTypes.KNOWN_ERRORS_BUT_PASSED, self.ResultTypes.RITE_KNOWN_FAILS]:
                vm_txt += '<img class="icon" src="cid:ok">'
            # vm to fix
            elif self.stats_by_vm[vm] in [self.ResultTypes.RITE_FAILS, self.ResultTypes.NOT_RUN]:
                vm_txt += '<img class="icon" src="cid:fix">'
            #if saved error
            if self.stats_by_vm[vm] in [self.ResultTypes.KNOWN_ERRORS, self.ResultTypes.KNOWN_ERRORS_BUT_PASSED, self.ResultTypes.RITE_KNOWN_FAILS]:
                vm_txt += '<img class="icon" src="cid:save">'

        if vm in VM_ALL.vm_first_rite:
            return '<div style="color: red;font-weight: bold; display:inline;">%s</div>' % vm_txt
        else:
            return vm_txt

    def disabled_today(self, test):
        week = ['monday',
                'tuesday',
                'wednesday',
                'thursday',
                'friday',
                'saturday',
                'sunday', ]
        today = datetime.datetime.today().weekday()
        today_week = week[today]
        #if the test is one enabled only on single days
        if test in self.enabled:
            # and if not enabled today
            if today_week not in self.enabled[test]:
                return True

        return False

    def load_default_yaml(self, def_file):
        stream = file(def_file, 'r')
        self.default_yaml = y = yaml.load(stream)

    def load_vms_cfg(self, def_file):
        # stream = file(def_file, 'r')
        # self.vms_yaml = y = yaml.load(stream)
        #
        self.vms_cfg = ConfigParser()
        self.vms_cfg.read(def_file)

    def get_vm_name(self, vm):
        try:
            path = self.vms_cfg.get("vms", vm)
        except NoOptionError:
            return vm + "(vm path not found)"
        path = path.replace(".vmx", "")
        #example: [VMFuzz] Win7-Zoneal/Win7-Zoneal.vmx
        vm_name = path.split("/")[1]
        storage_name = (path.split("]")[0]).split("[")[1]
        return vm_name + "(" + storage_name + ")"

    def attach_images(self, mime_msg):
        self.attach_image('logo', mime_msg)
        self.attach_image('soldier', mime_msg)
        self.attach_image('blacklist', mime_msg)
        self.attach_image('ok', mime_msg)
        self.attach_image('error', mime_msg)
        self.attach_image('fix', mime_msg)
        self.attach_image('save', mime_msg)

    def attach_image(self, name, mime_msg):
            cid = name
            # if name not in self.attached_images:
            img_fp = open('./Rite/Analyzer/img/%s.png' % name, 'rb')
            img_data = img_fp.read()
            # Now create the MIME container for the image
            img = MIMEImage(img_data)

            img.add_header('Content-Id', '<%s>' % name)  # angle brackets are important
            mime_msg.attach(img)
            img_fp.close()
                # self.attached_images.append(name)

            return cid
