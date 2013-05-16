
import sys
import os
import xdm
from classes import *
from classes import __all__ as allClasses
from xdm import common, tasks
from logger import *
from plugins.pm import PluginManager
from updater import CoreUpdater
from xdm.plugins.repository import RepoManager


def preDB(app_path, datadir):
    #paths
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
    """
    xdm.IMAGEPATH = os.path.join(xdm.DATADIR, xdm.IMAGEDIR)
    if not os.path.exists(xdm.IMAGEPATH):
        os.mkdir(xdm.IMAGEPATH)
    xdm.IMAGEPATH_RELATIVE = os.path.relpath(xdm.IMAGEPATH, xdm.APP_PATH)

    xdm.TEMPPATH = os.path.join(xdm.DATADIR, xdm.TEMPDIR)
    if not os.path.exists(xdm.TEMPPATH):
        os.mkdir(xdm.TEMPPATH)
    xdm.TEMPPATH_RELATIVE = os.path.relpath(xdm.TEMPPATH, xdm.APP_PATH)

    xdm.TEMPPATH = os.path.join(xdm.DATADIR, xdm.TEMPDIR)
    if not os.path.exists(xdm.TEMPPATH):
        os.mkdir(xdm.TEMPPATH)
    xdm.TEMPPATH_RELATIVE = os.path.relpath(xdm.TEMPPATH, xdm.APP_PATH)"""

    xdm.DATABASE_PATH = os.path.join(xdm.DATADIR, xdm.DATABASE_NAME)
    xdm.CONFIG_DATABASE_PATH = os.path.join(xdm.DATADIR, xdm.CONFIG_DATABASE_NAME)
    xdm.HISTORY_DATABASE_PATH = os.path.join(xdm.DATADIR, xdm.HISTORY_DATABASE_NAME)
    #databases
    xdm.DATABASE.init(xdm.DATABASE_PATH)
    xdm.CONFIG_DATABASE.init(xdm.CONFIG_DATABASE_PATH)
    xdm.HISTORY_DATABASE.init(xdm.HISTORY_DATABASE_PATH)


def db():
    classes = []
    for cur_c_name in allClasses: # see import: classes import __all__ as allClasses
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

    _checkDefaults(migration_was_done)
    if not common.WANTED:
        raise Exception('init went wrong the commons where not set to instances of the db obj')


def postDB():
    """mostly plugin and common init"""

    common.PM = PluginManager()
    common.PM.cache(debug=common.STARTOPTIONS.pluginImportDebug, systemOnly=True,)
    common.SYSTEM = common.PM.getSystems('Default')[0] # yeah SYSTEM is a plugin
    if os.path.isdir(common.SYSTEM.c.extra_plugin_path):
        log('Adding eyternal plugin path %s to the python path' % common.SYSTEM.c.extra_plugin_path)
        sys.path.append(common.SYSTEM.c.extra_plugin_path)
    common.PM.updatePlugins()
    common.PM.cache(debug=common.STARTOPTIONS.pluginImportDebug)
    common.SYSTEM = common.PM.getSystems('Default')[0] # yeah SYSTEM is a plugin

    # lets init all plugins once
    for plugin in common.PM.getAll():
        log("Plugin %s loaded successfully" % plugin.name)

    # updater
    common.UPDATER = CoreUpdater()
    common.REPOMANAGER = RepoManager(Repo.select())


def runTasks():
    """tasks to run on boot"""
    t = tasks.TaskThread(tasks.removeTempElements)
    t.start()


def _checkDefaults(resave=False):

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

    default_repos = [{'name': 'XDM demo', 'url': 'https://raw.github.com/lad1337/XDM-plugin-de.lad1337.demopackage/master/meta.json'}]

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
            new = True
            if new:
                r.save(True) # the save function is overwritten to do nothing but when we create it we send a overwrite

