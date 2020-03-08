# -*- coding: utf-8 -*-
import os
import sys
import time
import subprocess
from signal import SIGTERM


def daemonize(stdin='/dev/null', stdout='/dev/null', stderr='/dev/null'):

    # Do first fork.
    try:
        pid = os.fork()
        if pid > 0:
            sys.exit(0)  # Exit first parent.
    except OSError as e:
        sys.stderr.write('fork #1 failed: (%d) %s\n' % (e.errno, e.strerror))
        sys.exit(1)

    # Decouple from parent environment.
    os.chdir(os.sep)
    os.umask(0)
    os.setsid()

    # Do second fork.
    try:
        pid = os.fork()
        if pid > 0:
            sys.exit(0)  # Exit second parent.
    except OSError as e:
        sys.stderr.write('fork #2 failed: (%d) %s\n' % (e.errno, e.strerror))
        sys.exit(1)

    # Now I am a daemon!

    # Redirect standard file descriptors.
    si = file(stdin, 'r')
    so = file(stdout, 'a+')
    se = file(stderr, 'a+', 0)

    sys.stdout.flush()
    sys.stderr.flush()

    os.close(sys.stdin.fileno())
    os.close(sys.stdout.fileno())
    os.close(sys.stderr.fileno())

    os.dup2(si.fileno(), sys.stdin.fileno())
    os.dup2(so.fileno(), sys.stdout.fileno())
    os.dup2(se.fileno(), sys.stderr.fileno())


class LaunchApp(object):
    def __init__(self, command, thelog):
        super(LaunchApp, self).__init__()
        # assign any overrides to self
        self.stdout = '/dev/null'
        self.stderr = self.stdout
        self.stdin = '/dev/null'

        self.command = command
        self.thelog = thelog

    def start(self):

        daemonize(stdin=self.stdin, stdout=self.stdout, stderr=self.stderr)
        p = subprocess.Popen(self.command,
                             stdout=self.thelog,
                             stderr=self.thelog,
                             close_fds=True)
        if p.wait() != 0:

            return False

        return True
