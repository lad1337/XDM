#!/usr/bin/env python
# Author: Dennis Lutter <lad1337@gmail.com>
# URL: https://github.com/lad1337/XDM
#
# This file is part of XDM: eXtentable Download Manager.
#
#XDM: eXtentable Download Manager. Plugin based media collection manager.
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
import time
# Fix for correct path
if hasattr(sys, 'frozen'):
    app_path = os.path.abspath(os.path.join(os.path.abspath(sys.executable), '..', '..', 'Resources'))
    sys.path.insert(1, os.path.join(app_path, 'rootLibs'))
    sys.path.insert(1, app_path)
else:
    app_path = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(1, os.path.join(app_path, 'rootLibs'))
os.chdir(app_path)

import locale
locale.setlocale(locale.LC_ALL, '')
#init _ and other i18n functions the real language set based on the config is done in init.py -> system plugin
import gettext
t = gettext.translation('messages', os.path.join(app_path, 'i18n'), languages=None, fallback=True)
t.install(1, ('gettext', 'ngettext', 'lgettext', 'lngettext'))

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
from xdm.api import JSONRPCapi
# import sub api modules
from xdm.api import system as UNUSED_api_system
from xdm.api import plugins as UNUSED_api_plugins
from xdm import core_string_for_i18n

from xdm import common
from xdm import logger # need this to set the log level
from xdm import tasks
from xdm.logger import *
from xdm.web import WebRoot
from xdm.helper import launchBrowser, daemonize


class App():

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
        p.add_argument('--dev', action="store_true", dest='dev', default=None, help="Developer mode. Disables the censoring during log and the plugin manager follows symlinks")
        p.add_argument('--noApi', action="store_true", dest='noApi', default=None, help="Disable the api")
        p.add_argument('--apiPort', dest='apiPort', default=None, help="Port the api runs on")
        p.add_argument('--noWebServer', action="store_true", dest='noWebServer', help="Port the api runs on")
        p.add_argument('--pluginImportDebug', action="store_true", dest='pluginImportDebug', help="Extra verbosy debug during plugin import is printed.")
        p.add_argument('--profile', dest='profile', nargs='*', default=None, help="Wrap a decorated(!) function in a profiler. By default all decorated functions are profiled. Decorate your function with @profileMeMaybe")

        options = p.parse_args()
        self.options = options
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
        xdm.LOGPATH = os.path.join(datadir, xdm.LOGFILE)
        hdlr = logging.handlers.RotatingFileHandler(xdm.LOGPATH, maxBytes=10 * 1024 * 1024, backupCount=5)
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

        # PIDfile
        if options.pidfile:
            print "------------------- Set PIDfile to " + options.pidfile + " -------------------"
            PIDFile(cherrypy.engine, options.pidfile).subscribe()
        if options.pidfile:
            pid = str(os.getpid())
            log(u"Writing PID %s to %s" % (pid, options.pidfile))
            file(os.path.abspath(options.pidfile), 'w').write("%s\n" % pid)

        init.preDB(app_path, datadir)
        init.db()
        init.postDB()
        init.schedule()
        init.runTasks()

        # Set port
        if options.port:
            print "------------------- Port manual set to " + options.port + " -------------------"
            port = int(options.port)
            server.socket_port = port
        else:
            port = common.SYSTEM.c.port
            server.socket_port = port
        self.port = server.socket_port
        # Set api port
        if options.apiPort:
            print "------------------- Api port manual set to " + options.apiPort + " -------------------"
            self.port_api = int(options.apiPort)
        else:
            self.port_api = common.SYSTEM.c.port_api

        # update config for cherrypy
        cherrypy.config.update({'global': {'server.socket_port': port}})

    def startWebServer(self):
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
        conf = {'/': {'tools.auth_basic.on': useAuth,
                      'tools.auth_basic.realm': 'XDM',
                      'tools.auth_basic.checkpassword': checkpassword,
                      'tools.encode.encoding': 'utf-8'},
                '/api': {'tools.auth_basic.on': False},
                '/css': {'tools.staticdir.on': True, 'tools.staticdir.dir': css_path},
                '/js': {'tools.staticdir.on': True, 'tools.staticdir.dir': js_path},
                '/bootstrap': {'tools.staticdir.on': True, 'tools.staticdir.dir': bootstrap_path},
                '/images': {'tools.staticdir.on': True, 'tools.staticdir.dir': images},
                '/img': {'tools.staticdir.on': True, 'tools.staticdir.dir': images_path},
                '/favicon.ico': {'tools.staticfile.on': True, 'tools.staticfile.filename': os.path.join(images_path, 'favicon.ico')}
               }
        common.PUBLIC_PATHS = conf.keys()

        if common.SYSTEM.c.webRoot: # if this is always set even when False then https does not work
            options_dict = {'global': {'tools.proxy.on': True}}
        else:
            options_dict = {}

        sslCert_path = common.SYSTEM.c.https_cert_filepath
        sslKey_path = common.SYSTEM.c.https_key_filepath
        if common.SYSTEM.c.https:
            # If either the HTTPS certificate or key do not exist, make some self-signed ones.
            if not (sslCert_path and os.path.exists(sslCert_path)) or not (sslKey_path and os.path.exists(sslKey_path)):
                if not helper.create_https_certificates(sslCert_path, sslKey_path):
                    log.error(u"Unable to create cert/key files, disabling HTTPS")
                    common.SYSTEM.c.https = False

            if not (os.path.exists(sslCert_path) and os.path.exists(sslKey_path)):
                log.error(u"Disabled HTTPS because of missing CERT and KEY files")
                common.SYSTEM.c.https = False

        if common.SYSTEM.c.https:
            options_dict['server.ssl_certificate'] = sslCert_path
            options_dict['server.ssl_private_key'] = sslKey_path

        # Workoround for OSX. It seems have problem wit the autoreload engine
        if sys.platform.startswith('darwin') or sys.platform.startswith('win'):
            options_dict['engine.autoreload.on'] = False

        cherrypy.config.update(options_dict)
        cherrypy.config["tools.encode.on"] = True
        cherrypy.config["tools.encode.encoding"] = "utf-8"
        cherrypy.tools.stateBlock = cherrypy._cptools.HandlerTool(xdm.web.stateCheck)

        if common.SYSTEM.c.https:
            log.info("Starting the XDM https web server")
        else:
            log.info("Starting the XDM http web server")

        common.CHERRYPY_APP = cherrypy.tree.mount(WebRoot(app_path), config=conf)
        helper.updateCherrypyPluginDirs()
        cherrypy.server.socket_host = common.SYSTEM.c.socket_host

        cherrypy.log.screen = False
        cherrypy.server.start()
        log.info("XDM web server running")
        cherrypy.server.wait()

        # from couchpotato
        host = common.SYSTEM.c.socket_host
        https = common.SYSTEM.c.https
        try:
            if not (common.STARTOPTIONS.nolaunch or common.SYSTEM.c.dont_open_browser):
                print "------------------- launch Browser ( " + str(host) + ":" + str(self.port) + ") -------------------"
                launchBrowser(host, self.port, https)
        except:
            pass


def main():
    app = App()
    if not app.options.noWebServer:
        try:
            app.startWebServer()
        except IOError:
            log.error("Unable to start web server, is something else running on port %d?" % app.port)
            os._exit(1)
    else:
        log.info('Not starting webserver because of the command line option --noWebServer')
    if not app.options.noApi and common.SYSTEM.c.api_active:
        try:
            api = JSONRPCapi(app.port_api)
        except:
            log.error('could not init jsonrpc api')
            os._exit(1)
        else:
            log('Starting api thread')
            api.start()
    else:
        log.info('Api is OFF')

    common.addState(2)
    common.removeState(0)

    common.SM.setNewMessage("Up and running.")
    common.SM.setNewMessage("Done!")

    try:
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        actionManager.executeAction('shutdown', 'KeyboardInterrupt')
    os._exit()


if __name__ == '__main__':
    main()
