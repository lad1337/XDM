# Author: Dennis Lutter <lad1337@gmail.com>
# URL: https://github.com/lad1337/XDM
#
# This file is part of XDM: Xtentable Download Manager.
#
#XDM: Xtentable Download Manager. Plugin based media collection manager.
#Copyright (C) 2013  Dennis Lutter
#
#XDM is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.
#
#XDM is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.
#
#You should have received a copy of the GNU General Public License
#along with this program.  If not, see http://www.gnu.org/licenses/.

import os
import sys
import cherrypy
import traceback
from xdm.logger import *
from xdm import common
import xdm
import re
import subprocess
import time

ACTIONS = ['reboot', 'hardReboot', 'recachePlugins']


def executeAction(action, callers):
    #print type(action).__name__ == 'function'
    if not action in ACTIONS and not type(action).__name__ == 'function':
        log.warning("There is no action %s. Called from %s" % (action, callers))
        return False

    log.info("Executing actions '%s'. Called from %s" % (action, callers))
    if action == 'reboot':
        cherrypy.engine.restart()
    elif action == 'hardReboot':
        hardReboot()
    elif action == 'recachePlugins':
        common.PM.cache()
    else:
        for caller in callers:
            _callMethod(caller, action)


def _callMethod(o, function):
    try:
        getattr(o, function.__name__)()
    except Exception as ex:
        tb = traceback.format_exc()
        log.error("Error during action call %s of %s \nError: %s\n\n%s" % (o.name, function.__name__, ex, tb))


def oldhardReboot():
    # this should not be here ... because its very strong and should not be in the plugin manager
    # how will it react to a .exe ?
    # how will it to an .app ?
    """Restarts the current program.
    Note: this function does not return. Any cleanup action (like
    saving data) must be done before calling this function."""
    log.info("Doing a hard REBOOT!!")
    python = sys.executable
    os.execl(python, python, * sys.argv)


def hardReboot():
    log("Determining restart method...")
    common.SM.setNewMessage("Determining restart method...")
    install_type = common.UPDATER.install_type

    popen_list = []

    if install_type in (xdm.updater.install_type_git, xdm.updater.install_type_source):
        popen_list = [sys.executable, os.path.normpath(os.path.abspath(sys.argv[0]))]
    elif install_type == xdm.updater.install_type_exe:
        if hasattr(sys, 'frozen'):
            # c:\dir\to\updater.exe 12345 c:\dir\to\sickbeard.exe
            popen_list = [os.path.join(xdm.APP_PATH, 'updater.exe'), str(os.getpid()), sys.executable]
        else:
            log(u"Unknown XDM launch method, please file a bug report about this")
    elif install_type == xdm.updater.install_type_mac:
        m = re.search(r'(^.+?)/Contents', xdm.APP_PATH)
        executablePath = os.path.join(m.group(0), "MacOS", "XDM")
        popen_list = [executablePath]

    time.sleep(1)
    if popen_list:
        popen_list += sys.argv[1:]
        if '--nolaunch' not in popen_list:
            popen_list += ['--nolaunch']
        log(u"Restarting XDM with " + str(popen_list))
        common.SM.setNewMessage("Restarting XDM with %s" % popen_list)
        subprocess.Popen(popen_list, cwd=os.getcwd())
    else:
        log(u"not able to restart")
    common.SM.setNewMessage("Exiting out of this one. Bye bye and good luck!")
    common.SM.setNewMessage("Please wait...")
    time.sleep(2)
    os._exit(0)

