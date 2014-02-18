# Author: Dennis Lutter <lad1337@gmail.com>
# URL: https://github.com/lad1337/XDM
#
# This file is part of XDM: eXtentable Download Manager.
#
# XDM: eXtentable Download Manager. Plugin based media collection manager.
# Copyright (C) 2013  Dennis Lutter
#
# XDM is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# XDM is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see http://www.gnu.org/licenses/.

import sys
import sqlite3
import os
import xdm
from classes import *
from classes import __all__ as allClasses
from xdm import common, tasks, helper
from logger import *
from plugins.pluginManager import PluginManager
from updater import CoreUpdater
from xdm.plugins.repository import RepoManager
from xdm.garbage_collector import soFreshAndSoClean


def preDB(app_path, datadir):
    # paths
    xdm.APP_PATH = app_path
    xdm.DATADIR = datadir
    xdm.HOME_PATH = os.path.expanduser("~")

    for cur_path in ('IMAGE', 'TEMP', 'PLUGININSTALL'):
        dirname = '%sDIR' % cur_path
        thedir = getattr(xdm, dirname)
        pathname = '%sPATH' % cur_path
        relativepathname = '%sPATH_RELATIVE' % cur_path
        setattr(xdm, pathname, os.path.join(xdm.DATADIR, thedir))
        if not os.path.exists(getattr(xdm, pathname)):
            os.mkdir(getattr(xdm, pathname))
        setattr(xdm, relativepathname, os.path.relpath(getattr(xdm, pathname), xdm.DATADIR))
        log('Set %s to %s' % (pathname, getattr(xdm, pathname)))
        log('Set %s to %s' % (relativepathname, getattr(xdm, relativepathname)))

    # config db
    if common.STARTOPTIONS.config_db is not None:
        xdm.CONFIG_DATABASE_PATH = common.STARTOPTIONS.config_db
    else:
        xdm.CONFIG_DATABASE_PATH = os.path.join(xdm.DATADIR, xdm.CONFIG_DATABASE_NAME)
    log('Set CONFIG_DATABASE_PATH to %s' % xdm.CONFIG_DATABASE_PATH)

    # data db
    if common.STARTOPTIONS.data_db is not None:
        xdm.DATABASE_PATH = common.STARTOPTIONS.data_db
    else:
        xdm.DATABASE_PATH = os.path.join(xdm.DATADIR, xdm.DATABASE_NAME)
    log('Set DATABASE_PATH to %s' % xdm.DATABASE_PATH)

    # history db
    if common.STARTOPTIONS.history_db is not None:
        xdm.HISTORY_DATABASE_PATH = common.STARTOPTIONS.history_db
    else:
        xdm.HISTORY_DATABASE_PATH = os.path.join(xdm.DATADIR, xdm.HISTORY_DATABASE_NAME)
    log('Set HISTORY_DATABASE_PATH to %s' % xdm.HISTORY_DATABASE_PATH)


    # databases FILE init
    xdm.DATABASE.init(xdm.DATABASE_PATH)
    xdm.CONFIG_DATABASE.init(xdm.CONFIG_DATABASE_PATH)
    xdm.HISTORY_DATABASE.init(xdm.HISTORY_DATABASE_PATH)

    # set pylint environment variable this should fix issue #99
    os.environ['PYLINTHOME'] = xdm.DATADIR


def db():
    classes = []
    for cur_c_name in allClasses: # see import: classes import __all__ as allClasses
        cur_c = globals()[cur_c_name]
        log("Checking %s table" % cur_c.__name__)
        cur_c.create_table(True)
        classes.append(cur_c)

    migration_was_done = False
    for cur_c in classes:
        try:
            if cur_c.updateTable():
                migration_was_done = True
        except sqlite3.DatabaseError:
            log.critical("@!&%&*$% ... *sigh* i am sorry but the database %s is broken!" % cur_c.Meta.database)
        log("Selecting all of %s" % cur_c.__name__)
        try:
            cur_c.select().execute()
        except: # the database structure does not match the classstructure
            log.exception("\n\nFATAL ERROR:\nThe database structure does not match the class structure.\nCheck log.\nOr assume no migration was implemented and you will have to delete your db database file :(")
            exit(1)

    _checkDefaults(migration_was_done)
    if not common.WANTED:
        raise Exception('init went wrong the commons where not set to instances of the db obj')


def postDB():
    """mostly plugin and common init"""
    common.PM = PluginManager()
    common.PM.cache(debug=common.STARTOPTIONS.pluginImportDebug, systemOnly=True,)
    # load system config !
    common.SYSTEM = common.PM.getPluginByIdentifier(common.STARTOPTIONS.systemIdentifer, 'Default') # yeah SYSTEM is a plugin, identifier permits to be sure to get the right plugin.
    # system config loaded

    # init i18n
    common.SYSTEM._switchLanguage()

    # init updater
    common.UPDATER = CoreUpdater()
    common.REPOMANAGER = RepoManager(Repo.select())

    if not os.path.isabs(common.SYSTEM.c.https_cert_filepath):
        common.SYSTEM.c.https_cert_filepath = os.path.join(xdm.DATADIR, common.SYSTEM.c.https_cert_filepath)

    if not os.path.isabs(common.SYSTEM.c.https_key_filepath):
        common.SYSTEM.c.https_key_filepath = os.path.join(xdm.DATADIR, common.SYSTEM.c.https_key_filepath)

    # prepare to load other plugins
    if not common.SYSTEM.c.extra_plugin_path or common.STARTOPTIONS.datadir is not None:
        log.info('Setting extra plugin path to %s' % xdm.PLUGININSTALLPATH)
        common.SYSTEM.c.extra_plugin_path = xdm.PLUGININSTALLPATH

    if os.path.isdir(common.SYSTEM.c.extra_plugin_path):
        log('Adding eyternal plugin path %s to the python path' % common.SYSTEM.c.extra_plugin_path)
        sys.path.append(common.SYSTEM.c.extra_plugin_path)
    common.PM.cache(debug=common.STARTOPTIONS.pluginImportDebug)
    common.SYSTEM = common.PM.getPluginByIdentifier(common.STARTOPTIONS.systemIdentifer, 'Default') # yeah SYSTEM is a plugin, identifier permits to be sure to get the right plugin.

    # generate api key if api is aktive
    if common.SYSTEM.c.api_active and not common.SYSTEM.c.api_key:
        log.info('Generating your first API key for XDM')
        common.SYSTEM.c.api_key = helper.generateApiKey()

    # lets init all plugins once
    for plugin in common.PM.getAll():
        log("Plugin %s loaded successfully" % plugin.name)

    # migrate core
    t = tasks.TaskThread(common.UPDATER.migrate)
    t.start()


def schedule():
    common.SCHEDULER.stopAllTasks()
    # download status checker schedule
    rate = common.SYSTEM.c.interval_check * 60
    log.info("Setting up download status checker scheduler every %s seconds" % rate)
    common.SCHEDULER.addTask(tasks.runChecker, rate, rate, 'download status')

    # fixed search rate because noobs will set it to something noobish
    rate = 12 * 60 * 60 # this should be 12h
    log.info("Setting up search scheduler every %s seconds" % rate)
    common.SCHEDULER.addTask(tasks.runSearcher, rate, rate, 'searcher')

    # element updater
    # TODO: implement a all Element updater

    rate = 60 * 60 * 24 # one day!
    common.SCHEDULER.addTask(tasks.updateAllElements, rate, rate / 2, 'Element Updater')


    # queue worker
    common.SCHEDULER.addTask(tasks.checkQ, 2, 10, 'queue worker')

    # media adder schedule
    rate = common.SYSTEM.c.interval_mediaadder * 60
    log.info("Setting up mediaadder scheduler every %s seconds" % rate)
    common.SCHEDULER.addTask(tasks.runMediaAdder, rate, rate,
        'media adder', "Add media from from external sources")

    # news feed schedule
    if common.SYSTEM.c.show_feed:
        rate = 60 * 60 * 6 # six hours
        log.info("Setting up news feed scheduler every %s seconds" % rate)
        common.SCHEDULER.addTask(common.NM.cache, rate, 15, 'news feed')

    # plugin repo cacher
    rate = 60 * 60 * 12 # 12 hours
    log.info("Setting up plugin repo / plugin update scheduler every %s seconds" % rate)
    common.SCHEDULER.addTask(common.REPOMANAGER.autoCache, rate, 10, 'repository cache')

    # garbage collector
    rate = common.SYSTEM.c.interval_clean * 60
    log.info("Setting up garbage collector scheduler every %s seconds" % rate)
    common.SCHEDULER.addTask(soFreshAndSoClean, rate, 20 * 60, 'garbage collector')

    # core update schedule
    rate = common.SYSTEM.c.interval_core_update * 60
    if rate:
        log.info("Setting up core update scheduler every %s seconds" % rate)
        common.SCHEDULER.addTask(tasks.coreUpdateCheck, rate, 5, 'core updater') # 5 = run in 10s for the first time
    else:
        log.info("Core update scheduler should never run on its own, because interval is set to 0")

    common.SCHEDULER.startAllTasks()


def _checkDefaults(resave=False):

    default_statuss = [ {'setter': 'WANTED', 'name': 'Wanted', 'hidden': False},
                        {'setter': 'SNATCHED', 'name': 'Snatched', 'hidden': False},
                        {'setter': 'DOWNLOADED', 'name': 'Downloaded', 'hidden': False},
                        {'setter': 'COMPLETED', 'name': 'Completed', 'hidden': True},
                        {'setter': 'FAILED', 'name': 'Failed', 'hidden': True},
                        {'setter': 'PP_FAIL', 'name': 'Post Processing Fail', 'hidden': True},
                        {'setter': 'UNKNOWN', 'name': 'Unknown', 'hidden': True},
                        {'setter': 'DELETED', 'name': 'Deleted', 'hidden': True},
                        {'setter': 'IGNORE', 'name': 'Ignore', 'hidden': False},
                        {'setter': 'TEMP', 'name': 'Temp', 'hidden': True},
                        {'setter': 'DOWNLOADING', 'name': 'Downloading', 'hidden': True}
                      ]
    _('Wanted')
    _('Snatched')
    _('Downloaded')
    _('Completed')
    _('Post Processing Fail')
    _('Unknown')
    _('Deleted')
    _('Ignore')
    _('Downloading')

    default_repos = [{'name': 'XDM demo',
                      'url': 'https://raw.github.com/lad1337/XDM-main-plugin-repo/master/meta.json',
                      'info_url': 'https://github.com/lad1337/XDM-main-plugin-repo/'}]

    # create default Status
    for cur_s in default_statuss:
        new = False
        try:
            s = Status.get(Status.name == cur_s['name'])
            setattr(common, cur_s['setter'], s)
            if not resave:
                continue
        except Status.DoesNotExist:
            s = Status()
            new = True

        s.name = cur_s['name']
        s.hidden = cur_s['hidden']
        if new:
            s.save(True) # the save function is overwritten to do nothing but when we create it we send a overwrite
        setattr(common, cur_s['setter'], s)

    for repo in default_repos:
        new = False
        try:
            s = Repo.get(Repo.url == repo['url'])
            if not resave:
                continue
        except Repo.DoesNotExist:
            r = Repo()
            r.name = repo['name']
            r.url = repo['url']
            r.info_url = repo['info_url']
            new = True
            if new:
                r.save(True) # the save function is overwritten to do nothing but when we create it we send a overwrite

