from lib.peewee import *
from os.path import join
from lib.profilehooks import profile as profileHookFunction
from functools import wraps


DATADIR = ""
CONFIG_PATH = ""
PROGDIR = ""
CACHEDIR = "images"
CACHEPATH = ""
DATABASE_NAME = "data.db"
DATABASE_PATH = "./"
DATABASE = SqliteDatabase(None, threadlocals=True, autocommit=True)
CONFIG_DATABASE_NAME = "config.db"
CONFIG_DATABASE_PATH = "./"
CONFIG_DATABASE = SqliteDatabase(None, threadlocals=True, autocommit=True)
HISTORY_DATABASE_NAME = "history.db"
HISTORY_DATABASE_PATH = "./"
HISTORY_DATABASE = SqliteDatabase(None, threadlocals=True, autocommit=True)

ENCRYPTION_FILENAME = 'xdm_encryption_key.txt'


class Common(object):

    STARTOPTIONS = None # the argparse.Namespace object

    PM = None # PluginManager hold the plugins
    SYSTEM = None # system holds the config and maybe later more

    # will be set to the obj during initDB()
    UNKNOWN = None
    WANTED = None  # default status
    SNATCHED = None # well snatched and the downloader is getting it ... so we hope
    DOWNLOADED = None # no status thingy
    COMPLETED = None # downloaded and pp_success
    FAILED = None # download failed
    PP_FAIL = None # post processing failed
    DELETED = None # marked as deleted
    IGNORE = None # ignore this item
    TEMP = None # ignore this item

    LOGTOSCREEN = True
    LOGDEBUGTOSCREEN = False

    #Hooks
    SEARCHTERMS = 1
    FOUNDDOWNLOADS = 2

    #pp stop connditions
    STOPPPONSUCCESS = 1
    STOPPPONFAILURE = 2
    STOPPPALWAYS = 3
    DONTSTOPPP = 4

    HOMEDIR = None
    RUNPROFILER = False

    def getAllStatus(self):
        return [self.UNKNOWN, self.WANTED, self.SNATCHED, self.DOWNLOADED,
                  self.COMPLETED, self.FAILED, self.PP_FAIL, self.DELETED,
                  self.IGNORE, self.TEMP]

    def getEveryStatusBut(self, notWantedStatuses):
        filtered = self.getAllStatus()
        for notWantedStatus in notWantedStatuses:
            filtered = [ x for x in filtered if x is not notWantedStatus ]
        return filtered

    def getHomeStatuses(self):
        return self.getEveryStatusBut(self.getCompletedStatuses() + [self.TEMP])

    def getCompletedStatuses(self):
        return [self.DELETED, self.COMPLETED, self.DOWNLOADED, self.PP_FAIL]

    def getStatusByID(self, id):
        for s in self.getAllStatus():
            if s.id == id:
                return s
        raise ValueError("There is no status with the id %s" % id)

    def getDownloadTypeExtension(self, downloadTypeIdentifier):
        for dt in self.PM.DT:
            if dt.identifier == downloadTypeIdentifier:
                return dt.extension
        else:
            #log.warning("Download type with identifier %s was not found" % downloadTypeIdentifier)
            return 'txt'

common = Common()


#maybe move this some place else
def profileMeMaybe(target):
    @wraps(target)
    def wrapper(*args, **kwargs):
        if common.RUNPROFILER:
            if not common.STARTOPTIONS.profile: # empty list profile all
                print 'Profiling function "%s" with arguments %s and keyword arguments %s' % (target.__name__, args, kwargs)
                return profileHookFunction(target, immediate=True)(*args, **kwargs)
            elif target.__name__ in common.STARTOPTIONS.profile: # a list with function names
                print 'Profiling function "%s" with arguments %s and keyword arguments %s' % (target.__name__, args, kwargs)
                return profileHookFunction(target, immediate=True)(*args, **kwargs)
        # fallback normal call
        return target(*args, **kwargs)

    return wrapper


