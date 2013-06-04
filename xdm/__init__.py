import version
from lib.peewee import *
from os.path import join
from lib.profilehooks import profile as profileHookFunction
from functools import partial, update_wrapper, wraps
from xdm.message import MessageManager, SystemMessageManager
from xdm.news import NewsManager
import sched
import time
from xdm.scheduler import Scheduler

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

PLUGININSTALLDIR = 'extraPlugins'
PLUGININSTALLPATH = ''
PLUGININSTALLPATH_RELATIVE = ''

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


class Common(object):
    """A class that conveniently holds references to common objects and variables"""

    STARTOPTIONS = None # the argparse.Namespace object

    PM = None # PluginManager hold the plugins
    SYSTEM = None # system holds the config and maybe later more
    UPDATER = None # CoreUpdater instance
    REPOMANAGER = None # RepoManager() instance

    # will be set to the obj during initDB()
    UNKNOWN = None
    WANTED = None  # default status
    SNATCHED = None # well snatched and the downloader is getting it ... so we hope
    DOWNLOADING = None # its currently downloading woohhooo
    DOWNLOADED = None # no status thingy
    COMPLETED = None # downloaded and pp_success
    FAILED = None # download failed
    PP_FAIL = None # post processing failed
    DELETED = None # marked as deleted
    IGNORE = None # ignore this item
    TEMP = None # ignore this item

    APIKEY = ""

    #pp stop connditions
    STOPPPONSUCCESS = 1
    STOPPPONFAILURE = 2
    STOPPPALWAYS = 3
    DONTSTOPPP = 4

    RUNPROFILER = False

    MM = MessageManager()
    SM = SystemMessageManager()
    NM = NewsManager()
    SCHEDULER = Scheduler()

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
            #log.warning("Download type with identifier %s was not found" % downloadTypeIdentifier)
            return 'txt'

    def isThisVersionNewer(self, major, minor, revision, build):
        """return bool weather the running version is OLDER then the one build by the params"""
        return (major, minor, revision, build) > self.getVersionTuple()

    def getVersionTuple(self):
        """return a tuple of the current version"""
        return (version.major, version.minor, version.revision, version.build)

    def getVersionString(self):
        if version.build:
            return '%s.%s.%s.%s' % (version.major, version.minor, version.revision, version.build)
        return '%s.%s.%s' % (version.major, version.minor, version.revision)

    def getVersionHuman(self):
        return self.makeVersionHuman(version.major, version.minor, version.revision, version.build)

    def makeVersionHuman(self, major, minor, revision, build):
        if version.build:
            return "%s %s.%s.%s.%s" % (major_names[major], major, minor, revision, build)
        return "%s %s.%s.%s" % (major_names[major], major, minor, revision)


common = Common()


#maybe move this some place else
class profileMeMaybe(object):

    def __init__(self, target):
        self.target = target
        # and we expect it to be the wrapped function name
        self.__name__ = self.target.__name__

    #http://stackoverflow.com/questions/8856164/class-decorator-decorating-method-in-python
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

