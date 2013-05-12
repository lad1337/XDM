#!/usr/bin/env python

import sys
import os
# Fix for correct path
if hasattr(sys, 'frozen'):
    app_path = os.path.dirname(os.path.abspath(sys.executable))
else:
    app_path = os.path.dirname(os.path.abspath(__file__))
os.chdir(app_path)
sys.path.append(os.path.join(app_path, 'rootLibs'))


import cherrypy
import threading
import cherrypy.process.plugins
from cherrypy.process.plugins import PIDFile
from cherrypy import server
from xdm.web import WebRoot
from xdm.helper import launchBrowser, daemonize
import cherrypy.lib.auth_basic
import xdm
import logging
from xdm.init import initDB
from xdm.plugins import PluginManager

from xdm import common
from xdm import logger
from xdm.logger import *

from optparse import OptionParser

from xdm import tasks


xdm.PROGDIR = app_path
xdm.CACHEPATH = os.path.join(app_path, xdm.CACHEDIR)
if not os.path.exists(xdm.CACHEDIR):
    os.mkdir(xdm.CACHEDIR)


class RunApp():
    
    
    def __init__(self):
        usage = "usage: %prog [-options] [arg]"
        p = OptionParser(usage=usage)
        p.add_option('-d', '--daemonize', action = "store_true",
                     dest = 'daemonize', help = "Run the server as a daemon")
        p.add_option('-D', '--debug', action = "store_true",
                     dest = 'debug', help = "Debug Log to screen")
        p.add_option('', '--pluginImportDebug', action = "store_true",
                     dest = 'pluginImportDebug', help = "Extra verbosy Debug during plugin import")
        p.add_option('-p', '--pidfile',
                     dest = 'pidfile', default = None,
                     help = "Store the process id in the given file")
        p.add_option('-P', '--port',
                     dest = 'port', default = None,
                     help = "Force webinterface to listen on this port")
        p.add_option('-n', '--nolaunch', action = "store_true",
                     dest = 'nolaunch', help="Don't start browser")
        p.add_option('-b', '--datadir', default = None,
                     dest = 'datadir', help="Set the directory for the database")
        p.add_option('-c', '--config', default = None,
                     dest = 'config', help="Path to configfile")

        options, args = p.parse_args()

        #Set the Paths
        if options.datadir:
            datadir = options.datadir
            if not os.path.isdir(datadir):
                os.makedirs(datadir)
        else:
            datadir = app_path
        datadir = os.path.abspath(datadir)

        if not os.access(datadir, os.W_OK):
            raise SystemExit("Data dir must be writeable '" + datadir + "'")

        if options.config:
            config_path = options.config
        else:
            config_path = os.path.join(datadir, 'Gamez.ini')

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

        #Set global variables
        xdm.CONFIG_PATH = config_path
        xdm.DATADIR = datadir
        xdm.DATABASE_PATH = os.path.join(xdm.DATADIR, xdm.DATABASE_NAME)
        xdm.CONFIG_DATABASE_PATH = os.path.join(xdm.DATADIR, xdm.CONFIG_DATABASE_NAME)
        xdm.HISTORY_DATABASE_PATH = os.path.join(xdm.DATADIR, xdm.HISTORY_DATABASE_NAME)

        xdm.DATABASE.init(xdm.DATABASE_PATH)
        xdm.CONFIG_DATABASE.init(xdm.CONFIG_DATABASE_PATH)
        xdm.HISTORY_DATABASE.init(xdm.HISTORY_DATABASE_PATH)

        initDB()

        sys.path.append(os.path.join(app_path, 'rootLibs'))
        common.PM = PluginManager()
        common.PM.cache(debug=options.pluginImportDebug, systemOnly=True,)
        common.SYSTEM = common.PM.getSystems('Default') # yeah SYSTEM is a plugin
        if os.path.isdir(common.SYSTEM.c.extra_plugin_path):
            log('Adding eyternal plugin path %s to the python path' % common.SYSTEM.c.extra_plugin_path)
            sys.path.append(common.SYSTEM.c.extra_plugin_path)
        common.PM.updatePlugins()
        common.PM.cache(debug=options.pluginImportDebug)
        common.SYSTEM = common.PM.getSystems('Default') # yeah SYSTEM is a plugin

        # lets init all plugins once
        for plugin in common.PM.getAll():
            log("Plugin %s loaded successfully" % plugin.name)

        tasks.removeTempElements()

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
            if not options.nolaunch:
                print "------------------- launch Browser ( " + str(host) + ":" + str(port) + ") -------------------"
                timer = threading.Timer(5, launchBrowser, [host, port, https])
                timer.start()
            return
        except:
            pass

        # update config for cherrypy
        cherrypy.config.update({
                                    'global': {
                                               'server.socket_port': port
                                              }
                                })

    def RunWebServer(self):
        log.info("Generating CherryPy configuration")
        #cherrypy.config.update(gamez.CONFIG_PATH)

        # Set Webinterface Path
        css_path = os.path.join(app_path, 'html', 'css')

        images_path = os.path.join(app_path, 'html', 'img')
        js_path = os.path.join(app_path, 'html', 'js')
        bootstrap_path = os.path.join(app_path, 'html', 'bootstrap')
        images = xdm.CACHEPATH

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
                '/favicon.ico': {'tools.staticfile.on': True, 'tools.staticfile.filename': os.path.join(images_path, 'favicon.ico')},
               }
        conf.update(self.pluginResPaths)

        #TODO HTTPS support look at sb cp sab and others
        # Workoround for OSX. It seems have problem wit the autoreload engine
        if sys.platform.startswith('darwin') or sys.platform.startswith('win'):
            cherrypy.config.update({'engine.autoreload.on': False})

        rate = common.SYSTEM.c.interval_search * 60
        log.info("Setting up download scheduler every %s seconds" % rate)
        gameTasksScheduler = cherrypy.process.plugins.Monitor(cherrypy.engine, runSearcher, rate, 'Element Searcher')
        gameTasksScheduler.subscribe()
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
            cherrypy.engine.block()
        except KeyboardInterrupt:
            log.info("Shutting down XDM")
            sys.exit()


def runUpdater():
    tasks.updateGames()


def runSearcher():
    tasks.runSearcher()


def runChecker():
    tasks.runChecker()


def runMediaAdder():
    tasks.runMediaAdder()

if __name__ == '__main__':
    RunApp().RunWebServer()
