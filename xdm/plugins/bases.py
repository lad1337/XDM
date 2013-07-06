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

import os
import xdm
import re
import types
from xdm import common, helper
from xdm.classes import *
from xdm.logger import *
from meta import *
from xdm.helper import replace_all
import json
import collections
from babel.dates import format_timedelta
import datetime


"""plugins should not set the status of an element !!! it will be done in the loops that call / use the plugins"""


class Plugin(object):
    """Plugin base class. loads the config on init"""
    _type = 'Plugin'
    """The plugin type name e.g. Downloader"""
    single = False
    """if True the gui will not give the option for more configurations. but there is no logic to stop you do it anyways"""
    _config = {}
    """The configuration defining dict""" 
    config_meta = {}
    """Meta information on the the config keys"""
    version = "0.1"
    """version string. may only have a major and a minor version number"""
    useConfigsForElementsAs = 'Category'
    """MediaTypeManager can add configurations for elements.
    this defines how this configuration is used.
    This string will be used for:

    - It will be added to the configurations name.
    - A function will be created named ``get<useConfigsForElementsAs_value>()`` e.g. getCategory()
    """
    addMediaTypeOptions = True
    """Defines if options defined by a MediaType should be added to the plugin.

    .. note::

        This is ignored for plugins of the type MediaTypeManager_ and System_ since it's **never** done for them.

    .. _MediaTypeManager: MediaTypeManager.html
    .. System: System.html

    bool
        - ``True``: this will add all configurations defined by a MediaType
        - ``False``: No configurations are added

    list
        a list of MediaType identifiers e.g. ``['de.lad1337.music', 'de.lad1337.games']``, this will add only options from the MediaType with the given identifier

    str
        only str value allowed is ``runFor``, this will only add runFor options to the plugin.
    """
    xdm_version = (0, 0, 0)
    """this is the greater or equal XDM version this plugin needs to function

    .. note::

        By default this is (0, 0, 0) but the json builder will return the current version of XDM if it is not specifically set.

    """

    screenName = ''
    identifier = ''

    elementConfig = {}
    elementConfig_meta = {}
    
    _hidden_config = {}
    _hidden_config_meta = {}

    def __init__(self, instance='Default'):
        """returns a new instance of the Plugin with the config loaded get the configuration as self.c.<name_of_config>"""
        #setup names
        if not self.screenName:
            self.screenName = self.__class__.__name__
        self.name = "%s (%s)" % (self.screenName, instance)
        self.type = self.__class__.__name__
        self.instance = instance.replace('.', '_')

        #setup other config options from mediatypes
        if self.addMediaTypeOptions:
            self._create_media_type_configs() #this adds the configs for media types

        self._claimed_configs = []
        # plugin configs
        self.c = ConfigWrapper(self, self._config)
        self.config_meta = ConfigMeta(self.config_meta)
        if not ('enabled' in self._config and self._config['enabled']):
            self._config['enabled'] = False
        self._config['plugin_order'] = 0
        self._collect_plugin_configs()

        # element configs
        self.e = ConfigWrapper(self, self.elementConfig)
        self.elementConfig_meta = ConfigMeta(self.elementConfig_meta)
        self._collect_element_configs()

        # hidden configs
        self.hc = ConfigWrapper(self, self._hidden_config)
        self._hidden_config_meta = ConfigMeta(self._hidden_config_meta)
        self._collect_hidden_configs()

        # method wrapping
        methodList = [method for method in dir(self) if isinstance(getattr(self, method), (types.FunctionType, types.BuiltinFunctionType, types.MethodType, types.BuiltinMethodType, types.UnboundMethodType)) \
                      and not method.startswith('_')]
        for method_name in methodList:
            alternative = getattr(super(self.__class__, self), method_name)
            method = getattr(self, method_name)
            setattr(self, method_name, pluginMethodWrapper(self.name, method, alternative))

    def _get_enabled(self):
        return self.c.enabled

    def _set_enabled(self, value):
        self.c.enabled = value

    # shortcut to the enabled config option
    enabled = property(_get_enabled, _set_enabled)

    def _collect_plugin_configs(self):
        enabled_obj = None
        for k, v in self._config.items():
            #print "looking for", self.__class__.__name__, 'Plugin', k, instance
            try:
                cur_c = Config.get(Config.section == self.__class__.__name__,
                                  Config.module == 'Plugin',
                                  Config.name == k,
                                  Config.instance == self.instance)
            except Config.DoesNotExist:
                cur_c = Config()
                cur_c.module = 'Plugin'
                cur_c.section = self.__class__.__name__
                cur_c.instance = self.instance
                cur_c.name = k
                cur_c.value = v
                if cur_c.name in self.config_meta and self.config_meta[cur_c.name]:
                    for field in ('type', 'element', 'mediaType'):
                        if field in self.config_meta[cur_c.name] is not None:
                            if self.config_meta[cur_c.name][field] is not None:
                                log('Setting %s for %s to %s' % (cur_c.name, field, self.config_meta[cur_c.name][field]))
                                setattr(cur_c, field, self.config_meta[cur_c.name][field])
                cur_c.save()

            if cur_c.type == 'element_config':
                continue
            self._claimed_configs.append(cur_c.get_id())
            if k == 'enabled':
                enabled_obj = cur_c
            self.c.addConfig(cur_c)
        self.c.finalSort(enabled_obj)

    def _collect_element_configs(self):
        for k, v in self.elementConfig.items():
            cur_configs = Config.select().where(Config.section == self.__class__.__name__,
                                          Config.module == 'Plugin',
                                          Config.name == k,
                                          Config.instance == self.instance,
                                          Config.type == 'element_config')
            cur_configs = list(cur_configs)
            if len(cur_configs):
                for c in cur_configs:
                    self.e.addConfig(c)
                    self._claimed_configs.append(c.get_id())
        self.e.finalSort()

    def _collect_hidden_configs(self):
        for k, v in self._hidden_config.items():
            #print "looking for", self.__class__.__name__, 'Plugin', k, instance
            try:
                cur_c = Config.get(Config.section == self.__class__.__name__,
                                  Config.module == 'Plugin',
                                  Config.name == k,
                                  Config.instance == self.instance,
                                  Config.type == 'hidden')
            except Config.DoesNotExist:
                cur_c = Config()
                cur_c.module = 'Plugin'
                cur_c.section = self.__class__.__name__
                cur_c.instance = self.instance
                cur_c.type = 'hidden'
                cur_c.name = k
                cur_c.value = v
                if cur_c.name in self._hidden_config_meta and self._hidden_config_meta[cur_c.name]:
                    for field in ('type', 'element', 'mediaType'):
                        if field in self._hidden_config_meta[cur_c.name] is not None:
                            if self._hidden_config_meta[cur_c.name][field] is not None:
                                log('Setting %s for %s to %s' % (cur_c.name, field, self._hidden_config_meta[cur_c.name][field]))
                                setattr(cur_c, field, self._hidden_config_meta[cur_c.name][field])
                cur_c.save()

            self._claimed_configs.append(cur_c.get_id())
            self.hc.addConfig(cur_c)
        self.hc.finalSort()

    def deleteInstance(self):
        for c in self.c.configs:
            log("Deleting config %s from %s" % (c, self))
            c.delete_instance()
        for c in self.e.configs:
            log("Deleting config %s from %s" % (c, self))
            c.delete_instance()

    def cleanUnusedConfigs(self):
        amount = 0
        configs = list(Config.select().where(Config.section == self.__class__.__name__,
                                  Config.module == 'Plugin',
                                  Config.instance == self.instance))
        for cur_c in configs:

            try:
                _e = cur_c.element
            except Element.DoesNotExist:
                log('Element for the config was not found, probably because the MediaType is not installed any more: %s' % cur_c)
                log('Deleting config with missing element %s(%s) in %s' % (cur_c, cur_c.get_id(), self))
                cur_c.delete_instance()
                amount += 1
                continue
            else:
                if cur_c.element is not None and cur_c.type == 'element_config':
                    # element configs are only loade on the fly,
                    # to register them we get them all if the current config has an element attached
                    self.e.getConfigsFor(cur_c.element)
            if cur_c in self.c.configs or cur_c in self.e.configs:
                continue
            else:
                log('Deleting unclaimed config %s(%s) in %s' % (cur_c, cur_c.get_id(), self))
                cur_c.delete_instance()
                amount += 1
        return amount

    def __str__(self):
        return self.name

    def _get_plugin_file_path(self):
        return os.path.abspath(__file__)

    def get_plugin_isntall_path(self):
        if self.identifier:
            return common.PM.path_cache[self.identifier]
        else:
            return common.PM.path_cache[self.__class__.__name__]

    def _create_media_type_configs(self):
        if self._type in (MediaTypeManager.__name__, System.__name__):
            return

        for mtm in common.PM.getMediaTypeManager():
            if type(self.addMediaTypeOptions) is list and mtm.identifier not in self.addMediaTypeOptions:
                continue

            #enable options for mediatype on this plugin
            #log('Creating runFor field on %s from %s' % (self.__class__, mtm.__class__))
            name = helper.replace_some('%s_runfor' % mtm.name)
            self._config[name] = False
            self.config_meta[name] = {'human': 'Run for %s' % mtm.type, 'type': 'enabled', 'mediaType': mtm.mt}
            if self.addMediaTypeOptions == 'runFor':
                continue

            #log('Creating multi config fields on %s from %s' % (self.__class__, mtm.__class__))
            for configType in [x.__name__ for x in mtm.elementConfigsFor]:
                for element in Element.select().where(Element.type == configType):
                    prefix = self.useConfigsForElementsAs
                    sufix = element.getName()
                    h_name = '%s for %s' % (prefix, sufix)
                    c_name = helper.replace_some('%s %s %s' % (mtm.name, prefix.lower(), sufix))
                    self._config[c_name] = None
                    self.config_meta[c_name] = {'human': h_name, 'type': self.useConfigsForElementsAs.lower(), 'mediaType': mtm.mt, 'element': element}

            # add costum options
            if self.__class__.__bases__[0] in mtm.addConfig:
                for config in mtm.addConfig[self.__class__.__bases__[0]]:
                    if 'forcePrefix' in config and config['forcePrefix']:
                        prefix = config['prefix']
                        h_name = '%s %s' % (prefix, config['sufix'])
                        c_type = config['type']
                    else:
                        prefix = self.useConfigsForElementsAs.lower()
                        h_name = '%s for %s' % (self.useConfigsForElementsAs, config['sufix'])
                        c_type = prefix.lower()
                    c_name = helper.replace_some('%s %s %s' % (mtm.name, prefix, config['sufix']))
                    self._config[c_name] = config['default']
                    element = mtm.root
                    self.config_meta[c_name] = {'human': h_name, 'type': c_type.lower(), 'mediaType': mtm.mt, 'element': element}

    def __getattribute__(self, name):
        useAs = object.__getattribute__(self, 'useConfigsForElementsAs')
        if name == '_get%s' % useAs:
            return object.__getattribute__(self, '_getUseConfigsForElementsAsWrapper')
        return object.__getattribute__(self, name)

    def _getUseConfigsForElementsAsWrapper(self, element):
        """Gets the the config value for given element"""
        possibleConfigs = []
        for curConfig in self.c.configs:
            """print '\n#####################'
            print '--', 'config:',curConfig
            print '--', 'config value:',curConfig.value
            print '--', 'element:', element
            print '--', 'config.element:', curConfig.element
            if curConfig.element is None:
                print '__', 'no config.element'
            else:
                print '--', curConfig.type, 'vs', self.useConfigsForElementsAs.lower()
                print '--', curConfig.mediaType, 'vs', element.mediaType
                print '--', 'isAncestorOf', curConfig.element.isAncestorOf(element)
            """
            try:
                _e = curConfig.element
            except Element.DoesNotExist:
                continue

            try:
                _mt = curConfig.mediaType
            except MediaType.DoesNotExist:
                log.warning('A config(%s) assumed a MediaType but was not found. This can happend when an old config database is used.' % curConfig.id)
                continue

            if curConfig.element is None:
                continue
            if curConfig.mediaType == element.mediaType and\
                self.useConfigsForElementsAs.lower() == curConfig.type and\
                curConfig.element.isAncestorOf(element): # is the config elemtn "above" the element in question
                # we have to add this to a list
                # because we can have multiple successful finds e.g. games: global games category but closer platform categories
                possibleConfigs.append(curConfig)

        # if only one result cool we use that
        if len(possibleConfigs) == 1:
            return possibleConfigs[0].value
        if not possibleConfigs: # no possibeConfigs okay just return None
            return None

        # lets find the closest related config for element
        relationDegree = None
        closestRelatedConfig = None
        for curConfig in possibleConfigs:
            cur_RelationDegree = curConfig.element.decendants.index(element) # the index resembles the relation degree
            if relationDegree is None: # on first iteration
                relationDegree = cur_RelationDegree
                closestRelatedConfig = curConfig
            elif cur_RelationDegree < relationDegree:
                relationDegree = cur_RelationDegree
                closestRelatedConfig = curConfig
        # closestRelatedConfig can not be None after at least one iteration and we would only do this if we had two or more
        return closestRelatedConfig.value

    def runFor(self, mtm):
        try:
            return getattr(self.c, helper.replace_some('%s_runfor' % mtm.name))
        except AttributeError: # this might be a type check
            if hasattr(self, 'types') and mtm.identifier in self.types:
                return True
        return False

    def getMyScore(self):
        return common.PM.getPluginScore(self)

    def testMe(self):
        return (True, 'Everything fine')

    def getConfigHtml(self):
        return ''

    def _get_minor_version(self):
        return int(self.version.split('.')[1])
    minor_version = property(_get_minor_version)

    def _get_major_version(self):
        return int(self.version.split('.')[0])
    major_version = property(_get_major_version)

    def createRepoJSON(self, notJSON=False):
        desc = "Please write a description for me in config_meta['plugin_desc']"
        if 'plugin_desc' in self.config_meta:
            desc = self.config_meta['plugin_desc']
        if not sum(self.xdm_version):
            xdm_version = common.getVersionTuple()
        else:
            xdm_version = self.xdm_version
        #http://stackoverflow.com/a/4402799/729059
        data = collections.OrderedDict([("major_version", self.major_version),
                                        ("minor_version", self.minor_version),
                                        ("name", self.screenName),
                                        ("type", self._type),
                                        ("format", 'zip'),
                                        ("desc", desc),
                                        ("xdm_version", (xdm_version[0], xdm_version[1], xdm_version[2])), # buildnumber is not taken into account for version comparison on plugins
                                        ("download_url", "##enter the url to the zip file here !##")])

        out = {self.identifier: [data]}
        if notJSON:
            return out
        return json.dumps(out, indent=4, sort_keys=False)

    def myUrl(self):
        # NOTE: this patern is also used in heper.updateCherrypyPluginDirs()
        return "%s/%s.v%s" % (common.SYSTEM.c.webRoot, self.identifier, self.version)


class DownloadType(Plugin):
    """Simple skeleton for a "DownloadType"."""
    _type = 'DownloadType'
    single = True
    addMediaTypeOptions = False
    extension = ''
    """The file extension if a file is created for this DownloadType"""
    identifier = ''
    """A absolute unique identifier in reverse URL style e.g. de.lad1337.nzb"""


class DownloadTyped(Plugin):
    """DON'T SUBCLASS THIS IN YOUR PLUGIN"""

    def __init__(self, instance='Default'):
        if not self.types:
            for downloadType in common.PM.DT:
                self.types.append(downloadType.identifier)
        Plugin.__init__(self, instance=instance)

    def _getDownloadTypeExtension(self, downloadTypeIdentifier):
        return common.getDownloadTypeExtension(downloadTypeIdentifier)

    def getSupportedDownloadExtensions(self):
        extensions = {}
        for indentifer in self.types:
            extensions[indentifer] = '.%s' % self._getDownloadTypeExtension(indentifer)
        return extensions

    def getDownloadPercentage(self, element):
        """"this should return a int betwen 0 and 100 as the percentage"""
        return 0


class Downloader(DownloadTyped):
    """Plugins of this class send Downloads to another Program or directly download stuff"""
    _type = 'Downloader'
    types = [] # types the downloader can handle ... e.g. blackhole can handle both

    def addDownload(self, download):
        """Add/download a Download to this downloader

        Arguments:
        download -- an Download object

        return:
        bool if the adding was successful
        >>>> False
        """
        return False

    def getElementStaus(self, element):
        """Get the staus of element that it has in this downloader

        Arguments:
        element -- an Element object

        return:
        tuple of Status, Download and a path (str)
        >>>> (common.UNKNOWN, Download(), '')
        """
        return (common.UNKNOWN, Download(), '')

    def _downloadName(self, download):
        """tmplate on how to call the nzb/torrent file. nzb_name for sab"""
        return "%s (XDM.%s-%s)" % (download.element.getName(), download.element.id, download.id)

    def _findIDs(self, s):
        """find the game id and gownload id in s is based on the _downloadName()"""
        m = re.search("\((XDM.(?P<gid>\d+)-(?P<did>\d+))\)", s)
        gid, did = 0, 0
        if m and m.group('gid'):
            gid = int(m.group('gid'))
        if m and m.group('did'):
            did = int(m.group('did'))
        return (gid, did)

    def _findElementID(self, s):
        return self._findIDs(s)[0]

    def _findDownloadID(self, s):
        return self._findIDs(s)[1]


class Indexer(DownloadTyped):
    """Plugins of this class create elemnts based on mediaType structures"""
    _type = 'Indexer'
    types = [] # types this indexer will give back
    name = "Does Noting"

    def __init__(self, instance='Default'):
        #TODO: dont repeat this function make it wor with one
        # wrap function
        def downloadWrapperSingle(*args, **kwargs):
            res = self._searchForElement(*args, **kwargs)
            for i, d in enumerate(res):
                # default stuff
                d.indexer = self.type
                d.indexer_instance = self.instance
                d.status = common.UNKNOWN
                res[i]
            return res

        self._searchForElement = self.searchForElement
        self.searchForElement = downloadWrapperSingle

        def downloadWrapperRSS(*args, **kwargs):
            res = self._getLatestRss(*args, **kwargs)
            for i, d in enumerate(res):
                # default stuff
                d.indexer = self.type
                d.indexer_instance = self.instance
                d.status = common.UNKNOWN
                res[i]
            return res

        self._getLatestRss = self.getLatestRss
        self.getLatestRss = downloadWrapperRSS
        DownloadTyped.__init__(self, instance=instance)

    #TODO: implement / define / use
    def getLatestRss(self):
        """return list of Dowloads"""
        return []

    def searchForElement(self, element):
        """Returns a list of Downloads that where found for element

        For each download following attributes are set automatically after this is called
        download.indexer = self.type
        download.indexer_instance = self.instance
        download.status = common.UNKNOWN
        """
        return []

    def _getSearchNames(self, game):
        terms = []
        if game.additional_search_terms != None:
            terms = [x.strip() for x in game.additional_search_terms.split(',')]

        terms.append(re.sub('[ ]*\(\d{4}\)', '', replace_all(game.name)))
        log("Search terms for %s are %s" % (self.name, terms))
        return terms

    def commentOnDownload(self, download):
        return True


class Notifier(Plugin):
    """Plugins of this class send out notification"""
    _type = 'Notifier'
    addMediaTypeOptions = True
    name = "prints"

    def __init__(self, *args, **kwargs):
        self._config['on_snatch'] = False
        self.config_meta['on_snatch'] = {'human': 'Send on snatch'}
        self._config['on_complete'] = True # this is called after ppe
        self.config_meta['on_complete'] = {'human': 'Send on complete'}
        self._config['on_warning'] = False
        self.config_meta['on_warning'] = {'human': 'Send on warning'}
        self._config['on_error'] = False
        self.config_meta['on_error'] = {'human': 'Send on error'}
        self._config['on_update'] = False
        self.config_meta['on_update'] = {'human': 'Send notice when update is available'}
        super(Notifier, self).__init__(*args, **kwargs)

    def sendMessage(self, msg, element=None):
        return False


class Provider(Plugin):
    """Plugins of this class create elemnets based on mediaType structures.

    creating more providers is definety more complicated then other things since
    creating element structures based on the structure defined by the mediaType can be complicated
    """
    _type = 'Provider'
    _tag = 'unknown'
    addMediaTypeOptions = False

    class Progress(object):
        count = 0
        total = 0

        def reset(self):
            self.count = 0
            self.total = 0

        def addItem(self):
            self.count += 1

        def _getPercent(self):
            if self.total:
                return (self.count / float(self.total)) * 100
            else:
                return 0

        percent = property(_getPercent)

    def __init__(self, instance='Default'):
        self._config['favor'] = False
        Plugin.__init__(self, instance=instance)
        self.tag = self._tag
        if instance != 'Default':
            self.tag = instance
        self.progress = self.Progress()

    def searchForElement(self, term=''):
        """Create a MediaType structure of the type of element.mediaType
        """
        return Element()

    def getElement(self, id, element=None):
        return False

    def _getSupportedManagers(self):
        out = []
        for mtm in common.PM.getMediaTypeManager(returnAll=True):
            if mtm.identifier in self.types:
                out.append(mtm)
        return out


class PostProcessor(Plugin):
    _type = 'PostProcessor'
    types = [] # media types the downloader can handle

    def __init__(self, instance='Default'):
        self._config['stop_after_me_select'] = common.STOPPPONSUCCESS
        self.config_meta['stop_after_me_select'] = {'human': 'Stop other PostProcessors on'}
        Plugin.__init__(self, instance=instance)

    def _stop_after_me_select(self):
        return {common.STOPPPONSUCCESS: 'Success',
                common.STOPPPONFAILURE: 'Failure',
                common.STOPPPALWAYS: 'Always',
                common.DONTSTOPPP: "Don't stop others"}

    def postProcessPath(self, element, path):
        return (False, '')


class System(Plugin):
    """Is just a way to handle the config part and stuff"""
    _type = 'System'
    name = "Does Noting"

    def getBlacklistForPlatform(self, p):
        return []

    def getCheckPathForPlatform(self, p):
        return ''

    def getWhitelistForPlatform(self, p):
        return []


class DownloadFilter(Plugin):
    _type = 'DownloadFilter'
    addMediaTypeOptions = 'runFor'
    name = 'Does Nothing'

    class FilterResult(object):
        def __init__(self, result=False, reason=''):
            self.result = result
            self.reason = reason

    def compare(self, element, download):
        return self.FilterResult()


class SearchTermFilter(Plugin):
    _type = 'SearchTermFilter'
    addMediaTypeOptions = 'runFor'
    name = 'Does Nothing'

    def compare(self, element, terms):
        return terms


class MediaAdder(Plugin):
    _type = 'MediaAdder'
    name = 'Does Nothing'

    class Media(object):
        def __init__(self, mediaTypeIdentifier, externalID, providerTag, elementType, name, additionalData={}):
            self.mediaTypeIdentifier = mediaTypeIdentifier
            self.externalID = externalID
            self.providerTag = providerTag
            self.elementType = elementType
            self.name = name
            self.additionalData = additionalData

    def runShedule(self):
        return []

    def successfulAdd(self, mediaList):
        return False


class MediaTypeManager(Plugin):
    """Plugins of this type define a "MediaType" e.g. Movies
    They define a Structure of Classes simple classes that resemble Objects needed for the media that is being reflected.
    """
    _type = 'MediaTypeManager'
    name = "Does Nothing"
    identifier = ''
    """A absolute unique identifier in reverse URL style e.g. de.lad1337.nzb"""
    order = ()
    """A tubple that defines the order top to bottom / outer to inner of the classes that replect the media"""
    download = None
    """The class to download/search for"""
    addConfig = {}
    """Add configuration to otherplugins

    keys
        a plugin base class reference

    value
        list of dicts
        [{'type':'category', 'default': None, 'prefix': 'Category for', 'sufix': 'Movies'}]
        TODO: explain more

    """
    elementConfigsFor = ()
    """Tuple of classes that will have a configuration on each plugin e.g. Platform of de.lad1337.games
    TODO: link Platform
    """
    defaultElements = []
    """list of dicts Elements to create

    e.g.
        {'tgdb':{'name': 'Nintendo Wii', 'alias':'Wii', 'id': 9}}

    .. note::

        each list item is a dict that can contain multiple provider informations for one Element.
        In the above example we create the Wii with given attributes for the provider that has the tag tgdb (thegamesdb.net)
    
    """
    def __init__(self, instance):
        self.single = True

        self.config_meta['enable'] = {'on_enable': 'recachePlugins'}
        self._config['default_new_status_select'] = common.WANTED.id
        self.config_meta['default_new_status_select'] = {'human': 'Status for newly added %s' % self.__class__.__name__}

        self._config['release_threshold_select'] = 2 #default to two days see self._release_threshold_select()
        self.config_meta['release_threshold_select'] = {'human': 'Time to ignore the release date prior the release date.'}

        super(MediaTypeManager, self).__init__(instance)

        self.searcher = None
        self.s = {'root': self.__class__.__name__}
        l = list(self.order)
        for i, e in enumerate(l):
            attributes = [attr for attr in dir(e) if isinstance(getattr(e, attr), (types.IntType, types.StringType)) and not attr.startswith('_')]
            if not i:
                if len(l) > 1:
                    self.s[e.__name__] = {'parent': 'root', 'child': l[i + 1], 'class': e, 'attr': attributes}
                else:
                    self.s[e.__name__] = {'parent': 'root', 'child': None, 'class': e, 'attr': attributes}
                    self.leaf = e.__name__
            else:
                if i == len(l) - 1:
                    self.s[e.__name__] = {'parent': l[i - 1], 'child': None, 'class': e, 'attr': attributes}
                    self.leaf = e.__name__
                else:
                    self.s[e.__name__] = {'parent': l[i - 1], 'child': l[i + 1], 'class': e, 'attr': attributes}
        try:
            self.mt = MediaType.get(MediaType.identifier == self.identifier)
        except MediaType.DoesNotExist:
            self.mt = MediaType()
            self.mt.name = self.__class__.__name__
            self.mt.identifier = self.identifier
            self.mt.save()

        try:
            self.root = Element.get(Element.type == self.__class__.__name__, Element.status != common.TEMP)
        except Element.DoesNotExist:
            self.root = Element()
            self.root.type = self.__class__.__name__
            self.root.parent = None
            self.root.mediaType = self.mt
            self.root.save()

        for elementType in self.defaultElements:
            for defaultElement in self.defaultElements[elementType]:
                for providerTag, defaultAttributes in defaultElement.items():
                    try:
                        e = Element.getWhereField(self.mt, elementType.__name__, defaultAttributes, providerTag)
                    except Element.DoesNotExist:
                        log('Creating default element for %s. type:%s, attrs:%s' % (self.identifier, elementType.__name__, defaultAttributes))
                        #continue
                        e = Element()
                        e.type = elementType.__name__
                        e.mediaType = self.mt
                        e.parent = self.root
                        e.status = common.UNKNOWN
                        for name, value in defaultAttributes.items():
                            e.setField(name, value, providerTag)
                        e.save()

    def checkElementFields(self):
        for cur_class in self.order:
            for element in self.getElementsWithStatusIn(common.getEveryStatusBut([common.TEMP])):
                for attrName in self.s[cur_class.__name__]['attr']:
                    try:
                        getattr(element, attrName)
                    except AttributeError:
                        log(u"%s is missing attr: '%s'. Fixing that for you." % (element, attrName))
                        element.setField(attrName, getattr(cur_class, attrName), 'XDM')

    def getDownloadableElements(self, asList=True):
        return self.getElementsWithStatusIn(common.getHomeStatuses(), asList, [self.download.__name__])

    def getElementsWithStatusIn(self, status, asList=True, types=None):
        if types is None:
            out = Element.select().where(Element.mediaType == self.mt, Element.type == self.download.__name__, Element.status << status)
        else:
            out = Element.select().where(Element.mediaType == self.mt, Element.type == self.download.__name__, Element.status << status, Element.type << types)
        if asList:
            out = list(out)
        return out

    def isTypeLeaf(self, eType):
        return self.leaf == eType

    def getFn(self, eType, fnName):
        if eType in self.s and fnName in self.s[eType]['class'].__dict__:
            return self.s[eType]['class'].__dict__[fnName]
        elif eType == self.type and fnName in self.__class__.__dict__:
            return self.__class__.__dict__[fnName]
        else:
            return None

    def getManagedTypes(self):
        return [self.type] + [classType.__name__ for classType in self.order]

    def getOrderFields(self, eType):
        if eType in self.s and '_orderBy' in self.s[eType]['class'].__dict__:
            fields = self.s[eType]['class'].__dict__['_orderBy']
            if type(fields) is tuple:
                return fields
            else:
                return (fields,)
            return self.s[eType]['class'].__dict__['_orderBy']
        else:
            return []

    def getAttrs(self, eType):
        return self.s[eType]['attr']

    def headInject(self):
        return ''

    def _defaultHeadInject(self):
        """This will inject a script and a css style tag script.js and style.css respectively
        It is assumes that these files are in the root of the plugin.
        """
        myUrl = self.myUrl()
        return """
        <link rel="stylesheet" href="%s/style.css">
        <script src="%s/script.js"></script>
        """ % (myUrl, myUrl)

    @xdm.profileMeMaybe
    def paintChildrenOf(self, root, status=None):
        if status is None:
            status = common.getAllStatus()
        log('init paint children on given root %s %s' % (root, root.id))
        return root.paint(status=status, onlyChildren=True)

    @xdm.profileMeMaybe
    def paint(self, root=None, status=None):
        if status is None:
            status = common.getHomeStatuses()

        if root is None:
            log('init paint on default root %s' % self.root)
            return self.root.paint(status=status)
        else:
            log('init paint on given root %s' % root)
            return root.paint(search=True)

    def search(self, search_query):
        log.info('Init search on %s for %s' % (self, search_query))
        self.searcher = None
        #xdm.DATABASE.set_autocommit(False)
        rootElement = None
        for provider in common.PM.P:
            if not provider.runFor(self) or self.identifier not in provider.types:
                continue
            self.searcher = provider
            rootElement = provider.searchForElement(term=search_query)
        #xdm.DATABASE.commit()
        #xdm.DATABASE.set_autocommit(True)
        self.searcher = None
        return rootElement

    def makeReal(self, element):
        log.warning('Default makereal/save method called but the media type should have implemented this')
        return False

    def getSearches(self):
        return Element.select().where(Element.status == common.TEMP, Element.type == self.__class__.__name__)

    def getFakeRoot(self, term=''):
        root = Element()
        root.type = self.__class__.__name__
        root.parent = None
        root.mediaType = self.mt
        root.setField('term', term)
        root.saveTemp()
        return root

    def _default_new_status_select(self):
        return {common.UNKNOWN.id: common.UNKNOWN.screenName,
                common.WANTED.id: common.WANTED.screenName,
                common.IGNORE.id: common.IGNORE.screenName}

    def _release_threshold_select(self):
        return {0: "Don't ignore.",
                1: format_timedelta(helper.releaseThresholdDelta[1], locale=common.getLocale()),
                2: format_timedelta(helper.releaseThresholdDelta[2], locale=common.getLocale()),
                3: format_timedelta(helper.releaseThresholdDelta[3], locale=common.getLocale()),
                4: format_timedelta(helper.releaseThresholdDelta[4], locale=common.getLocale()),
                5: format_timedelta(helper.releaseThresholdDelta[5], locale=common.getLocale()),
                6: 'Completely ignore'}

    def getTemplate(self):
        if self.leaf:
            return helper.getLeafTpl()
        else:
            return helper.getContainerTpl()

__all__ = ['System', 'PostProcessor', 'Provider', 'Indexer', 'Notifier', 'Downloader', 'MediaTypeManager', 'Element', 'DownloadType', 'DownloadFilter', 'SearchTermFilter', 'MediaAdder']
