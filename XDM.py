#!/usr/bin/env python
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

import sys
import os
# Fix for correct path
if hasattr(sys, 'frozen'):
    app_path = os.path.abspath(os.path.join(os.path.abspath(sys.executable), '..', '..', 'Resources'))
    sys.path.insert(1, os.path.join(app_path, 'rootLibs'))
    sys.path.insert(1, app_path)
else:
    app_path = os.path.dirname(os.path.abspath(__file__))
os.chdir(app_path)
sys.path.append(os.path.join(app_path, 'rootLibs'))


import argparse
import cherrypy
import threading
import cherrypy.process.plugins
from cherrypy.process.plugins import PIDFile
from cherrypy import server
import cherrypy.lib.auth_basic
import logging # get the debug log level
import xdm
from xdm import init, helper, actionManager
from xdm import common
from xdm import logger # need this to set the log level
from xdm import tasks
from xdm.logger import *
from xdm.web import WebRoot
from xdm.helper import launchBrowser, daemonize


class RunApp():

    def __init__(self):

        p = argparse.ArgumentParser(prog='XDM')
        p.add_argument('-d', '--daemonize', action="store_true", dest='daemonize', help="Run the server as a daemon.")
        p.add_argument('-v', '--version', action="store_true", dest='version', help="Print Version and exit.")
        p.add_argument('-D', '--debug', action="store_true", dest='debug', help="Print debug log to screen.")
        p.add_argument('-p', '--pidfile', dest='pidfile', default=None, help="Store the process id in the given file.")
        p.add_argument('-P', '--port', dest='port', default=None, help="Force webinterface to listen on this port.")
        p.add_argument('-n', '--nolaunch', action="store_true", dest='nolaunch', help="Don't start the browser.")
        p.add_argument('-b', '--datadir', dest='datadir', default=None, help="Set the directory for the database.")
        p.add_argument('-c', '--config', dest='config', default=None, help="Path to config file")
        p.add_argument('--pluginImportDebug', action="store_true", dest='pluginImportDebug', help="Extra verbosy debug during plugin import is printed.")
        p.add_argument('--profile', dest='profile', nargs='*', default=None, help="Wrap a decorated(!) function in a profiler. By default all decorated functions are profiled. Decorate your function with @profileMeMaybe")

        options = p.parse_args()
        common.STARTOPTIONS = options

        if options.version:
            print common.getVersionHuman()
            exit()
        log.info('Starting XDM %s' % common.getVersionHuman())

        #Set the Paths
        if options.datadir:
            datadir = options.datadir
            if not os.path.isdir(datadir):
                os.makedirs(datadir)
        elif hasattr(sys, 'frozen'):
            datadir = helper.getSystemDataDir(app_path)
            if not os.path.isdir(datadir):
                os.makedirs(datadir)
        else:
            datadir = app_path
        datadir = os.path.abspath(datadir)

        if not os.access(datadir, os.W_OK):
            raise SystemExit("Data dir must be writeable '" + datadir + "'")

        # setup file logger with datadir
        hdlr = logging.handlers.RotatingFileHandler(os.path.join(datadir, 'xdm.log'), maxBytes=10 * 1024 * 1024, backupCount=5)
        xdm.logger.fLogger.addHandler(hdlr)


        #TODO: rewrite for the config.db
        """if options.config:
            config_path = options.config
        else:
            config_path = os.path.join(datadir, 'Gamez.ini')"""

        # Daemonize
        if options.daemonize:
            if sys.platform == 'win32':
                print "Daemonize not supported under Windows, starting normally"
            else:
                print "------------------- Preparing to run in daemon mode (screen logging is now OFF) -------------------"
                log.info("Preparing to run in daemon mode")
                logger.cLogger.setLevel(logging.CRITICAL)
                daemonize()

        # Debug
        if options.debug:
            print "------------------- XDM Debug Messages ON -------------------"
            logger.cLogger.setLevel(logging.DEBUG)
            log.info('XDM Debug mode ON')
        # Profile
        if options.profile is not None:
            print "------------------- XDM Profiling ON -------------------"
            log.info('XDM profiling mode ON')
            common.RUNPROFILER = True
            print common.RUNPROFILER

        init.preDB(app_path, datadir)
        init.db()
        init.postDB()
        init.runTasks()

        self.pluginResPaths = {}
        for pType, path in common.PM.path_cache.items():
            self.pluginResPaths['/' + pType] = {'tools.staticdir.on': True, 'tools.staticdir.dir': os.path.abspath(path)}

        # Set port
        if options.port:
            print "------------------- Port manual set to " + options.port + " -------------------"
            port = int(options.port)
            server.socket_port = port
        else:
            port = common.SYSTEM.c.port
            server.socket_port = port

        # PIDfile
        if options.pidfile:
            print "------------------- Set PIDfile to " + options.pidfile + " -------------------"
            PIDFile(cherrypy.engine, options.pidfile).subscribe()

        # from couchpotato
        host = common.SYSTEM.c.socket_host
        https = False
        try:
            if not (options.nolaunch or common.SYSTEM.c.dont_open_browser):
                print "------------------- launch Browser ( " + str(host) + ":" + str(port) + ") -------------------"
                timer = threading.Timer(2, launchBrowser, [host, port, https])
                timer.start()
            return
        except:
            pass

        # update config for cherrypy
        cherrypy.config.update({'global': {'server.socket_port': port}
                                })

    def RunWebServer(self):
        log.info("Generating CherryPy configuration")
        #cherrypy.config.update(gamez.CONFIG_PATH)

        # Set Webinterface Path
        css_path = os.path.join(app_path, 'html', 'css')

        images_path = os.path.join(app_path, 'html', 'img')
        js_path = os.path.join(app_path, 'html', 'js')
        bootstrap_path = os.path.join(app_path, 'html', 'bootstrap')
        images = xdm.IMAGEPATH

        username = common.SYSTEM.c.login_user
        password = common.SYSTEM.c.login_password

        useAuth = False
        if username and password:
            useAuth = True
        userPassDict = {username: password}
        checkpassword = cherrypy.lib.auth_basic.checkpassword_dict(userPassDict)
        conf = {'/': {'tools.auth_basic.on': useAuth, 'tools.auth_basic.realm': 'Gamez', 'tools.auth_basic.checkpassword': checkpassword},
                '/api': {'tools.auth_basic.on': False},
                '/css': {'tools.staticdir.on': True, 'tools.staticdir.dir': css_path},
                '/js': {'tools.staticdir.on': True, 'tools.staticdir.dir': js_path},
                '/bootstrap': {'tools.staticdir.on': True, 'tools.staticdir.dir': bootstrap_path},
                '/images': {'tools.staticdir.on': True, 'tools.staticdir.dir': images},
                '/img': {'tools.staticdir.on': True, 'tools.staticdir.dir': images_path},
                '/favicon.ico': {'tools.staticfile.on': True, 'tools.staticfile.filename': os.path.join(images_path, 'favicon.ico')}
               }
        conf.update(self.pluginResPaths)

        #TODO HTTPS support look at sb cp sab and others
        # Workoround for OSX. It seems have problem wit the autoreload engine
        if sys.platform.startswith('darwin') or sys.platform.startswith('win'):
            cherrypy.config.update({'engine.autoreload.on': False})

        rate = common.SYSTEM.c.interval_core_update * 60
        log.info("Setting up core update scheduler every %s seconds" % rate)
        if rate:
            coreUpdateScheduler = cherrypy.process.plugins.Monitor(cherrypy.engine, runCoreUpdater, rate, 'Core Updater Searcher')
            coreUpdateScheduler.subscribe()

        # fixed search rate because noobs will set it to something noobish
        rate = 12 * 60 * 60 # this should be 12h
        log.info("Setting up search scheduler every %s seconds" % rate)
        singleSearchScheduler = cherrypy.process.plugins.Monitor(cherrypy.engine, runSearcher, rate, 'Element Searcher')
        singleSearchScheduler.subscribe()

        rate = common.SYSTEM.c.interval_update * 60
        log.info("Setting up element list update scheduler every %s seconds" % rate)
        gameListUpdaterScheduler = cherrypy.process.plugins.Monitor(cherrypy.engine, runUpdater, rate, 'Element Updater')
        gameListUpdaterScheduler.subscribe()
        rate = common.SYSTEM.c.interval_check * 60
        log.info("Setting up download status checker scheduler every %s seconds" % rate)
        folderProcessingScheduler = cherrypy.process.plugins.Monitor(cherrypy.engine, runChecker, rate, 'Check Downloads')
        folderProcessingScheduler.subscribe()
        rate = common.SYSTEM.c.interval_mediaadder * 60
        log.info("Setting up mediaadder scheduler every %s seconds" % rate)
        folderProcessingScheduler = cherrypy.process.plugins.Monitor(cherrypy.engine, runMediaAdder, rate, 'Check for Media')
        folderProcessingScheduler.subscribe()

        log.info("Starting the XDM web server")
        cherrypy.tree.mount(WebRoot(app_path), config=conf)
        cherrypy.server.socket_host = common.SYSTEM.c.socket_host
        try:
            cherrypy.log.screen = False
            cherrypy.engine.start()
            log.info("XDM web server running")
            common.SM.setNewMessage("Up and running.")
            common.SM.setNewMessage("Done!")
            cherrypy.engine.block()
        except KeyboardInterrupt:
            actionManager.executeAction('shutdown', 'KeyboardInterrupt')


def runUpdater():
    tasks.updateGames()


def runCoreUpdater():
    tasks.coreUpdateCheck()


def runSearcher():
    tasks.runSearcher()


def runChecker():
    tasks.runChecker()


def runMediaAdder():
    tasks.runMediaAdder()

if __name__ == '__main__':
    RunApp().RunWebServer()
