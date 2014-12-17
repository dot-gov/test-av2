import zipfile
import os
import sys
import signal
import subprocess
import threading


class GenericThread(object):
    """ Threading example class

    The run() method will be started and it will run in the background
    until the application exits.
    """

    def __init__(self, cmd, interval=1):
        """ Constructor

        :type interval: int
        :param interval: Check interval, in seconds
        """
        self.cmd = cmd
        self.interval = interval
        self.run_baby = True
        print "lunching thread with cmd=%s" % cmd
        self.pro = subprocess.Popen(self.cmd, stdout=subprocess.PIPE,
                       shell=True, preexec_fn=os.setsid)
        self.thread = threading.Thread(target=self.run, args=())
        self.thread.daemon = True                            # Daemonize thread
        self.thread.start()                                  # Start the execution

    def run(self):
        """ Method that runs forever """
        while self.run_baby and not self.pro.returncode:
            out = self.pro.stdout.read(1)
            if out == '' and self.pro.poll() != None:
                break
            if out != '':
                sys.stdout.write(out)
                sys.stdout.flush()
        if not self.pro.returncode:
            print "killing command %s" % self.cmd
            self.run_baby = False
            try:
                os.killpg(self.pro.pid, signal.SIGTERM)
            except Exception, ex:
                print "no need to kill.."

    def is_alive_inner(self):
        return self.run_baby
