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

import bases as plugins
import os
import traceback
from xdm.classes import *
from xdm.logger import *
from xdm import common
import threading
from cStringIO import StringIO
from pylint import lint
import sys


class PluginManager(object):
    """Class that manages/provides and finds plugins"""

    _cache = {}
    _mt_cache = {}
    path_cache = {}
    pylintScoreWarning = 7
    """send a warning when score is bellow or equal this"""
    pylintScoreError = 4
    """send an error when score is bellow or equal this"""

    def __init__(self, path='plugins'):
        self._caching = threading.Semaphore()
        self.path = path
        self.clearCache()
        self._score_cache = {}
        self.crashed_on_init_cache = {}

    def _getPylintScore(self, path):
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        sys.stdout = mystdout = StringIO()
        sys.stderr = mystderr = StringIO()
        try:
            r = lint.Run(['--disable=W0704,C0301,C0302,C0111,R0903,R0902,R0201,W0614,W0602,C0103,W0603,C0321,F0401,W0603,W0602,C0301,C0111,C0321,C0103,W0401,W0614,E0202', path], exit=False)
            s = eval(r.linter.config.evaluation, {}, r.linter.stats)
        except:
            log.error('Chrash during pylint scoring. TODO: get traceback and stuff')
            s = 0
        sys.stdout = old_stdout
        sys.stderr = old_stderr

        logFilepath = '%s.pylintOutput.txt' % path
        if s and s <= self.pylintScoreWarning or os.path.isfile(logFilepath):
            try:
                logFile = open(logFilepath, 'w')
                try:
                    logFile.write(mystdout.getvalue())
                finally:
                    logFile.close()
            except IOError as exe:
                print exe
                log.error("Error during writing of the pylint output")
        return s

    def clearCache(self):
        self.path_cache = {}
        self._mt_cache = {}
        self._cache = {}

    def cache(self, reloadModules=False, debug=False, systemOnly=False, clearUnsedConfgs=False, calculateScore=True):
        """collects available plugins and saved it in self._cache

        systemOnly
            only look for System plugins

        debug
            bool prints extra messages during plugin search (defautl: False)

        """
        if systemOnly:
            log.info('Loading/searching system plugins')
        else:
            log.info('Loading/searching all plugins')

        with self._caching:
            self.clearCache()
            if systemOnly:
                classes = (plugins.System,)
            else:
                classes = (plugins.System, plugins.Notifier, plugins.MediaTypeManager,
                           plugins.Downloader, plugins.DownloadFilter, plugins.SearchTermFilter,
                           plugins.MediaAdder, plugins.Indexer, plugins.Provider,
                           plugins.PostProcessor, plugins.DownloadType)
            for cur_plugin_type in classes: #for plugin types
                cur_plugin_type_name = cur_plugin_type.__name__
                cur_classes = self.find_subclasses(cur_plugin_type, reloadModules, debug=debug)
                if not systemOnly and os.path.isdir(common.SYSTEM.c.extra_plugin_path):
                    extra_plugin_path = common.SYSTEM.c.extra_plugin_path
                    if debug:
                        print '###### extra path %s #######' % extra_plugin_path
                    cur_classes.extend(self.find_subclasses(cur_plugin_type, reloadModules, debug=debug, path=extra_plugin_path))

                if cur_classes:
                    log("I found %s %s: %s" % (len(cur_classes), cur_plugin_type_name, [x[0].__name__ for x in cur_classes]))
                else:
                    log("I found ZERO %s" % cur_plugin_type_name)
                for cur_class, cur_path in cur_classes: # for classes of that type
                    if cur_plugin_type not in self._score_cache:
                        if calculateScore:
                            score = self._getPylintScore(cur_path)
                            if score <= self.pylintScoreError:
                                log.error('Pylint Score for %s is only %.2f' % (cur_class.__name__, score))
                            elif score <= self.pylintScoreWarning:
                                log.warning('Pylint Score for %s is only %.2f' % (cur_class.__name__, score))
                            else:
                                log.info('Pylint Score for %s is %.2f' % (cur_class.__name__, score))
                        else:
                            score = 0
                        self._score_cache[cur_class] = score
                    if not cur_plugin_type in self._cache:
                        self._cache[cur_plugin_type] = {}
                    if cur_plugin_type is not plugins.MediaTypeManager:
                        instances = []
                        configs = Config.select().where(Config.section == cur_class.__name__).execute()
                        for config in configs: # for instances of that class of tht type
                            instances.append(config.instance)
                        instances.append('Default') # add default instance for everything, this is only needed for the first init after that the instance names will be found in the db
                        instances = list(set(instances))
                        final_instances = []
                        for instance in instances:
                            try:
                                #log("Creating %s (%s)" % (cur_class, instance))
                                i = cur_class(instance)
                            except Exception as ex:
                                tb = traceback.format_exc()
                                log.error("%s (%s) crashed on init i am not going to remember this one !! \nError: %s\n\n%s" % (cur_class.__name__, instance, ex, tb))
                                if cur_class not in self.crashed_on_init_cache:
                                    self.crashed_on_init_cache[cur_class] = {}
                                self.crashed_on_init_cache[cur_class] = instance
                                continue
                            if clearUnsedConfgs:
                                i.cleanUnusedConfigs()
                            testResult, testMessage = i.testMe()
                            if not testResult:
                                log.warning("%s said it can not run: %s" % (i, testMessage))
                                i.c.enable = False
                            final_instances.append(instance)
                    else:
                        final_instances = [cur_class.identifier.replace('.', '_')]
                    self._cache[cur_plugin_type][cur_class] = final_instances
                    self.path_cache[cur_class.__name__] = os.path.dirname(cur_path)
                    log("I found %s instances for %s(v%s): %s" % (len(final_instances), cur_class.__name__, cur_class.version, self._cache[cur_plugin_type][cur_class]))
            #log("Final plugin cache %s" % self._cache)

   
    def getPluginScore(self, plugin):
        if plugin.__class__ in self._score_cache:
            return self._score_cache[plugin.__class__]
        return 0

    def _getAny(self, cls, wanted_i='', returnAll=False, runFor=''):
        """may return a list with instances or just one instance if wanted_i is given
        only gives back enabeld plugins by default set returnAll to True to get all
        WARNING: "disabeld" plugins are still instantiated
        """
        plugin_instances = []
        if not cls in self._cache:
            return plugin_instances

        wanted_i = wanted_i.replace('_', '.')
        for cur_c, instances in self._cache[cls].items():
            for cur_instance in instances:
                cur_instance = cur_instance.replace('_', '.')
                #log("Will create new instance (%s) from %s" % (cur_instance, cur_c.__name__))
                if cls == plugins.MediaTypeManager:
                    if cur_c not in self._mt_cache:
                        log('Creating and caching instance from %s' % cur_c)
                        new = cur_c(cur_instance.replace('_', '.'))
                        self._mt_cache[cur_c] = new
                    else:
                        #log('Using cached instance from %s' % cur_c)
                        new = self._mt_cache[cur_c]
                else:
                    new = cur_c(cur_instance)
                if wanted_i:
                    if wanted_i == cur_instance or (cls == plugins.MediaTypeManager and wanted_i == 'Default'):
                        plugin_instances.append(new)
                        continue
                    elif cls == plugins.MediaTypeManager and wanted_i == cur_instance:
                        return [new]
                elif new.enabled or returnAll:
                    plugin_instances.append(new)
                else:
                    pass
                    #log("%s is disabled" % cur_c.__name__)
        #print cls, wanted_i, returnAll, plugin_instances, sorted(plugin_instances, key=lambda x: x.c.plugin_order, reverse=False)
        return sorted(plugin_instances, key=lambda x: x.c.plugin_order, reverse=False)

    def _getTyped(self, plugins, types=[]):
        if not types:
            return plugins
        filtered = []
        for cur_cls in plugins:
            for cur_type in types:
                if cur_type in cur_cls.types:
                    filtered.append(cur_cls)
        return filtered

    def _getRunners(self, plugins, mediaTypeManager=None):
        if mediaTypeManager is None:
            return plugins
        filtered = []
        for cur_cls in plugins:
            if cur_cls.runFor(mediaTypeManager):
                filtered.append(cur_cls)
        return filtered

    # typed and runner checked
    def getDownloaders(self, i='', returnAll=False, types=[], runFor=None):
        return self._getRunners(self._getTyped(self._getAny(plugins.Downloader, i, returnAll), types), runFor)
    D = property(getDownloaders)

    def getIndexers(self, i='', returnAll=False, types=[], runFor=None):
        return self._getRunners(self._getTyped(self._getAny(plugins.Indexer, i, returnAll), types), runFor)
    I = property(getIndexers)

    def getPostProcessors(self, i='', returnAll=False, types=[], runFor=None):
        return self._getRunners(self._getTyped(self._getAny(plugins.PostProcessor, i, returnAll), types), runFor)
    PP = property(getPostProcessors)

    # runner checked
    def getProvider(self, i='', returnAll=False, runFor=None):
        return self._getRunners(self._getAny(plugins.Provider, i, returnAll), runFor)
    P = property(getProvider)

    def getDownloadFilters(self, i='', returnAll=False, runFor=None):
        return self._getRunners(self._getAny(plugins.DownloadFilter, i, returnAll), runFor)
    DF = property(getDownloadFilters)

    def getSearchTermFilters(self, i='', returnAll=False, runFor=None):
        return self._getRunners(self._getAny(plugins.SearchTermFilter, i, returnAll), runFor)
    SF = property(getSearchTermFilters)

    # none filtered
    def getDownloaderTypes(self, i='', returnAll=False):
        return self._getAny(plugins.DownloadType, i, returnAll)
    DT = property(getDownloaderTypes)

    def getNotifiers(self, i='', returnAll=False):
        return self._getAny(plugins.Notifier, i, returnAll)
    N = property(getNotifiers)

    def getSystems(self, i='', returnAll=False):
        return self._getAny(plugins.System, i, returnAll)
    S = property(getSystems)

    def getMediaTypeManager(self, i='', returnAll=False):
        return self._getAny(plugins.MediaTypeManager, i, returnAll)
    MTM = property(getMediaTypeManager)

    def getMediaAdder(self, i='', returnAll=False):
        return self._getAny(plugins.MediaAdder, i, returnAll)
    MA = property(getMediaAdder)

    def getAll(self, returnAll=False, instance=""):
        return self.getSystems(returnAll=returnAll, i=instance) +\
                self.getIndexers(returnAll=returnAll, i=instance) +\
                self.getDownloaders(returnAll=returnAll, i=instance) +\
                self.getDownloadFilters(returnAll=returnAll, i=instance) +\
                self.getSearchTermFilters(returnAll=returnAll, i=instance) +\
                self.getPostProcessors(returnAll=returnAll, i=instance) +\
                self.getMediaAdder(returnAll=returnAll, i=instance) +\
                self.getNotifiers(returnAll=returnAll, i=instance) +\
                self.getProvider(returnAll=returnAll, i=instance) +\
                self.getDownloaderTypes(returnAll=returnAll, i=instance) +\
                self.getMediaTypeManager(returnAll=returnAll, i=instance)

    # this is ugly ... :(
    def getInstanceByName(self, class_name, instance):
        for pType in self._cache:
            for pClass in self._cache[pType]:
                if class_name == pClass.__name__:
                    for cur_instance in self._cache[pType][pClass]:
                        if instance == cur_instance:
                            return pClass(instance)
        return None

    def clearAllUnsedConfgs(self):
        amount = 0
        for p in self.getAll(True):
            amount += p.cleanUnusedConfigs()
        return amount

    def find_subclasses(self, cls, reloadModule=False, debug=False, path=''):
        """
        Find all subclass of cls in py files located below path
        (does look in sub directories)

        @param path: the path to the top level folder to walk
        @type path: str
        @param cls: the base class that all subclasses should inherit from
        @type cls: class
        @rtype: list
        @return: a list if classes that are subclasses of cls
        """
        externalPath = True
        if not path:
            path = self.path
            externalPath = False

        if debug:
            print "searching for subclasses of", cls, cls.__name__, 'in', path
        org_cls = cls
        subclasses = []

        def look_for_subclass(modulename, cur_path):
            if debug:
                print("searching %s in path %s" % (modulename, cur_path))

            try:
                module = __import__(modulename)
            except Exception as ex:# catch everything we dont know what kind of error a plugin might have
                tb = traceback.format_exc()
                log.error("Error during importing of %s \nError: %s\n\n%s" % (modulename, ex, tb), traceback=tb, exception=ex)
                return

            #walk the dictionaries to get to the last one
            d = module.__dict__
            for m in modulename.split('.')[1:]:
                d = d[m].__dict__

            #look through this dictionary for things
            #that are subclass of Job
            #but are not Job itself
            for key, entry in d.items():
                if key == cls.__name__:
                    continue

                try:
                    if issubclass(entry, cls):
                        if debug:
                            print("Found subclass: " + key)
                        if reloadModule: # this is donw to many times !!
                            log("Reloading module %s" % module)
                            reload(module)
                        subclasses.append((entry, cur_path))
                except TypeError:
                    #this happens when a non-type is passed in to issubclass. We
                    #don't care as it can't be a subclass of Job if it isn't a
                    #type
                    continue

        followlinks = common.STARTOPTIONS.dev
        for root, dirs, files in os.walk(path, followlinks=followlinks):
            if 'pluginRootLibarys' in root or '__old__' in root:
                continue
            if debug:
                print dirs
                print files
            if 'pluginRootLibarys' in dirs:
                extra_root_path = os.path.join(root, 'pluginRootLibarys')
                if extra_root_path not in sys.path:
                    log.info('Adding -->%s<-- to the python path... ohhh boy' % extra_root_path)
                    sys.path.append(extra_root_path)
            for name in files:
                if name.endswith(".py") and not name.startswith("__"):
                    cur_path = os.path.join(root, name)
                    if externalPath:
                        modulename = cur_path.rsplit('.', 1)[0].replace('%s%s' % (common.SYSTEM.c.extra_plugin_path, os.sep), '').replace(os.sep, '.').replace('pluginRootLibarys.', '')
                    else:
                        modulename = cur_path.rsplit('.', 1)[0].replace(os.sep, '.').replace('pluginRootLibarys.', '')
                    look_for_subclass(modulename, cur_path)

        if debug:
            print "final subclasses for", org_cls, subclasses

        return subclasses


