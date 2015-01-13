__author__ = 'mlosito'
import smtplib
import socket
# Import the email modules we'll need
from email.mime.text import MIMEText


def analyzer_mail(test_name, vms, message, mail_recipients=["m.losito@hackingteam.com"], mail_server="mail.hackingteam.com"):
    # Create a text/plain message
    for recipient in mail_recipients:
        msg = MIMEText(message)
        hostname = socket.gethostname()

        msg['Subject'] = '%s@%s - %s' % (test_name, hostname, vms)
        msg['From'] = "avtest@hackingteam.com"
        msg['To'] = recipient

        print "Msg to: %s to be sent" % msg['To']
        # Send the message via our own SMTP server, but don't include the
        # envelope header.
        s = smtplib.SMTP(mail_server)
        s.sendmail(msg['From'], [msg['To']], msg.as_string())
        s.quit()
