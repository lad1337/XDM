
import xdm
from classes import *
from classes import __all__ as allClasses
from xdm import common
from xdm.logger import *
import os


def initCheck():
    common.HOMEDIR = os.path.expanduser("~")


def initDB():
    xdm.DATABASE.init(xdm.DATABASE_PATH)

    #classes = (Game, Platform, Status, Config, Download)
    classes = []
    for cur_c_name in allClasses:
        cur_c = globals()[cur_c_name]
        log("Checking %s table" % cur_c.__name__)
        cur_c.create_table(True)
        classes.append(cur_c)

    migration_was_done = False
    for cur_c in classes:
        if cur_c.updateTable():
            migration_was_done = True
        log("Selecting all of %s" % cur_c.__name__)
        try:
            cur_c.select().execute()
        except: # the database structure does not match the classstructure
            log.error("\n\nFATAL ERROR:\nThe database structure does not match the class structure.\nCheck log.\nOr assume no migration was implemented and you will have to delete your GameZZ.db database file :(")
            exit(1)

    checkDefaults(migration_was_done)
    if not common.WANTED:
        raise Exception('init went wrong the commons where not set to instances of the db obj')


def checkDefaults(resave=False):

    default_statuss = [ {'setter': 'WANTED',      'name': 'Wanted',               'hidden': False},
                        {'setter': 'SNATCHED',    'name': 'Snatched',             'hidden': False},
                        {'setter': 'DOWNLOADED',  'name': 'Downloaded',           'hidden': False},
                        {'setter': 'COMPLETED',   'name': 'Completed',            'hidden': True},
                        {'setter': 'FAILED',      'name': 'Failed',               'hidden': True},
                        {'setter': 'PP_FAIL',     'name': 'Post Processing Fail', 'hidden': True},
                        {'setter': 'UNKNOWN',     'name': 'Unknown',              'hidden': True},
                        {'setter': 'DELETED',     'name': 'Deleted',              'hidden': True},
                        {'setter': 'IGNORE',      'name': 'Ignore',               'hidden': False},
                        {'setter': 'TEMP',        'name': 'Temp',                 'hidden': True}
                      ]

    #create default Status
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
