__author__ = 'zeno'

import os, sys, inspect

basedir = None

if not basedir:
    cmd_folder = os.path.split(os.path.realpath(os.path.abspath(inspect.getfile(inspect.currentframe()))))[0]
    if cmd_folder not in sys.path:
        sys.path.insert(0, cmd_folder)
    parent = os.path.split(cmd_folder)[0]
    ancestor = os.path.split(parent)[0]
    if parent not in sys.path:
        sys.path.insert(0, parent)
    if ancestor not in sys.path:
        sys.path.insert(0, ancestor)
    os.chdir(cmd_folder)