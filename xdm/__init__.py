from lib.peewee import *

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


class Common(object):
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

    TYPE_NZB = 1
    TYPE_TORRENT = 2

    LOGTOSCREEN = True
    LOGDEBUGTOSCREEN = False

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
        return self.getEveryStatusBut(self.getCompletedStatuses())

    def getCompletedStatuses(self):
        return [self.DELETED, self.COMPLETED, self.DOWNLOADED, self.PP_FAIL]

    def getStatusByID(self, id):
        for s in self.getAllStatus():
            if s.id == id:
                return s
        raise ValueError("There is no status with the id %s" % id)

common = Common()

