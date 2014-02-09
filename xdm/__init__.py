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

import version
from peewee import *
from os.path import join
from profilehooks import profile as profileHookFunction
from functools import partial, update_wrapper, wraps
from xdm.message import MessageManager, SystemMessageManager
from xdm.news import NewsManager
import sched
import time
from xdm.scheduler import Scheduler
import xdm
import datetime
from Queue import Queue

HOME_PATH = ""
APP_PATH = ""
DATADIR = ""
CONFIG_PATH = ""
PROGDIR = ""

IMAGEDIR = "images"
IMAGEPATH = ""
IMAGEPATH_RELATIVE = ""

TEMPDIR = 'temp'
TEMPPATH = ''
TEMPPATH_RELATIVE = ''

PLUGININSTALLDIR = 'plugins'
PLUGININSTALLPATH = ''
PLUGININSTALLPATH_RELATIVE = ''

LOGPATH = ''
LOGFILE = 'xdm.log'

DATABASE_NAME = "data.db"
DATABASE_PATH = "./"
DATABASE = SqliteDatabase(None, threadlocals=True, autocommit=True)
CONFIG_DATABASE_NAME = "config.db"
CONFIG_DATABASE_PATH = "./"
CONFIG_DATABASE = SqliteDatabase(None, threadlocals=True, autocommit=True)
HISTORY_DATABASE_NAME = "history.db"
HISTORY_DATABASE_PATH = "./"
HISTORY_DATABASE = SqliteDatabase(None, threadlocals=True, autocommit=True)

major_names = {0: 'Zim',
               1: 'Gir',
               2: 'Dib',
               3: 'Gaz'}

xdm_states = {0: 'booting',
              1: 'migrating',
              2: 'running',
              3: 'updating',
              4: 'plugin_install',
              5: 'searching',
              6: 'cleaning',
              7: 'wizard'}


class Common(object):
    """A class that conveniently holds references to common objects and variables
    *@DynamicAttrs*
    """
    # trying to remove the import errors for all the None objects but it does no seam to work (its a different case here)
    # http://pydev.org/manual_adv_code_analysis.html see Passing info to code-analysis

    STARTOPTIONS = None # the argparse.Namespace object

    PM = None # PluginManager hold the plugins
    SYSTEM = None # system holds the config and maybe later more
    UPDATER = None # CoreUpdater instance
    REPOMANAGER = None # RepoManager() instance

    # will be set to the obj during initDB()
    UNKNOWN = None
    WANTED = None # default status
    SNATCHED = None # well snatched and the downloader is getting it ... so we hope
    DOWNLOADING = None # its currently downloading woohhooo
    DOWNLOADED = None # no status thingy
    COMPLETED = None # downloaded and pp_success
    FAILED = None # download failed
    PP_FAIL = None # post processing failed
    DELETED = None # marked as deleted
    IGNORE = None # ignore this item
    TEMP = None # ignore this item

    def _getApiKey(self):
        return self.SYSTEM.c.api_key

    def _setApiKey(self, new_key):
        self.SYSTEM.c.api_key = new_key

    APIKEY = property(_getApiKey, _setApiKey)

    STATES = [xdm_states[0]]

    def _running(self):
        return xdm_states[2] in self.STATES
    RUNNING = property(_running)

    # pp stop connditions
    STOPPPONSUCCESS = 1
    STOPPPONFAILURE = 2
    STOPPPALWAYS = 3
    DONTSTOPPP = 4

    RUNPROFILER = False

    PUBLIC_PATHS = []
    CHERRYPY_APP = None

    MM = MessageManager()
    SM = SystemMessageManager()
    NM = NewsManager()
    SCHEDULER = Scheduler()
    Q = Queue()

    FAKEDATE = datetime.datetime(1987, 5, 24, 13, 37, 6)

    CONFIGOVERWRITE = {}

    def getLocale(self):
        """get the current local string
        e.g. en_US
        e.g. de

        this is either the system language / locale or the user set language or the fallback to en_US
        """
        return self.SYSTEM._locale

    def addState(self, num):
        self.STATES.append(xdm_states[num])
        self.STATES = list(set(self.STATES))

    def removeState(self, num):
        if xdm_states[num] in self.STATES:
            del self.STATES[self.STATES.index(xdm_states[num])]
        xdm.logger.log('Removing state "%s". STATES are now %s' % (xdm_states[num], self.STATES))

    def getAllStatus(self):
        """get all available status instances"""
        return [self.UNKNOWN, self.WANTED, self.SNATCHED, self.DOWNLOADING,
                self.DOWNLOADED, self.COMPLETED, self.FAILED, self.PP_FAIL,
                self.DELETED, self.IGNORE, self.TEMP]

    def getEveryStatusBut(self, notWantedStatuses):
        """get all available status instances except statuses in the list `notWantedStatuses`"""
        filtered = self.getAllStatus()
        for notWantedStatus in notWantedStatuses:
            filtered = [ x for x in filtered if x is not notWantedStatus ]
        return filtered

    def getHomeStatuses(self):
        """get statuses that are shown on the home/index page"""
        return self.getEveryStatusBut(self.getCompletedStatuses() + [self.TEMP])

    def getCompletedStatuses(self):
        """get statuses that are shown on the completed page"""
        return [self.DELETED, self.COMPLETED, self.DOWNLOADED, self.PP_FAIL]

    def getStatusByID(self, id):
        """get a status be the database id"""
        for s in self.getAllStatus():
            if s.id == id:
                return s
        raise ValueError("There is no status with the id %s" % id)

    def getDownloadTypeExtension(self, downloadTypeIdentifier):
        """get the (file) of the DownloadType defined by `downloadTypeIdentifier` if none is found will return `txt`"""
        for dt in self.PM.DT:
            if dt.identifier == downloadTypeIdentifier:
                return dt.extension
        else:
            # log.warning("Download type with identifier %s was not found" % downloadTypeIdentifier)
            return 'txt'

    def isThisVersionNewer(self, major, minor, revision, build):
        """return bool weather the running version is OLDER then the one build by the params"""
        return (major, minor, revision, build) > self.getVersionTuple()

    def getVersionTuple(self, noBuild=False):
        """return a tuple of the current version"""
        if not noBuild:
            return (version.major, version.minor, version.revision, version.build)
        else:
            return (version.major, version.minor, version.revision)

    def getVersionString(self):
        if version.build:
            return '%s.%s.%s.%s' % (version.major, version.minor, version.revision, version.build)
        return '%s.%s.%s' % (version.major, version.minor, version.revision)

    def getVersionHuman(self):
        return self.makeVersionHuman(version.major, version.minor, version.revision, version.build)

    def makeVersionHuman(self, major, minor, revision, build=0):
        if version.build:
            return "%s %s.%s.%s.%s" % (major_names[major], major, minor, revision, build)
        return "%s %s.%s.%s" % (major_names[major], major, minor, revision)

    _provider_tags_cache = []

    def getProviderTags(self):
        if self._provider_tags_cache:
            return self._provider_tags_cache
        self._provider_tags_cache = [p.tag for p in self.PM.P]
        return self._provider_tags_cache

    def updateConfigOverwrite(self, config):
        self.CONFIGOVERWRITE.update(config)

    def getConfigOverWriteForPlugin(self, plugin):
        if plugin.identifier in self.CONFIGOVERWRITE and plugin.instance in self.CONFIGOVERWRITE[plugin.identifier]:
            return self.CONFIGOVERWRITE[plugin.identifier][plugin.instance]
        else:
            return {}


common = Common()


# maybe move this some place else
class profileMeMaybe(object):

    def __init__(self, target):
        self.target = target
        # and we expect it to be the wrapped function name
        self.__name__ = self.target.__name__

    # http://stackoverflow.com/questions/8856164/class-decorator-decorating-method-in-python
    def __get__(self, obj, type=None):
        self.obj = obj
        return self

    def __call__(self, *args, **kwargs):

        @wraps(self.target)
        def wrapper(*args, **kwargs):
            if not common.STARTOPTIONS.profile or self.target.__name__ in common.STARTOPTIONS.profile:
                print 'Profiling function "%s" with arguments %s and keyword arguments %s' % (self.target.__name__, args, kwargs)
                return profileHookFunction(self.target, immediate=True)(*args, **kwargs)
            else:
                return self.target(*args, **kwargs)

        if common.RUNPROFILER:
            return wrapper(self.obj, *args, **kwargs)
        return self.target(self.obj, *args, **kwargs)

