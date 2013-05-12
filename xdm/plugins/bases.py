import os
import xdm
import re
import types
from xdm import common, helper
from xdm.classes import *
from xdm.logger import *
from meta import *
from xdm.helper import replace_all


"""plugins should not set the status of an element !!! it will be done in the loops that call / use the plugins"""


class Plugin(object):
    """plugin base class. loads the config on init
    "self.c" is reserved!!! thats how you get the config
    "self.type" is reserved!!! its the class name
    "self._type" is reserved!!! its the plugin type name e.g. Downloader
    "self.instance" is reserved!!! its the instance name
    "self.name" is reserved!!! its the class name and instance name
    "self.single" is reserved!!! set this if you only want to allow one instance of your plugin !
    """
    _type = 'Plugin'
    single = False # if True the gui will not give the option for more configurations. but there is no logic to stop you do it anyways
    _config = {}
    config_meta = {}
    version = "0.1"
    useConfigsForElementsAs = 'Category'
    addMediaTypeOptions = True
    screenName = ''

    elementConfig = {}
    elementConfig_meta = {}

    def __init__(self, instance='Default'):
        """returns a new instance of the Plugin with the config loaded get the configuration as self.c.<name_of_config>"""
        #setup names
        if not self.screenName:
            self.screenName = self.__class__.__name__
        self.name = "%s (%s)" % (self.screenName, instance)
        self.type = self.__class__.__name__
        self.instance = instance.replace('.', '_')
        # log message
        if self._type != 'DownloadType':
            log("Creating new plugin %s" % self.name)
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
                if self.type == 'SystemConfig':
                    print 'init system config k:%s v:%s' % (k, v)
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

            if cur_c.element is not None and cur_c.type == 'element_config':
                # element configs ae only loade on the fly,
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
            self.config_meta[name] = {'human': 'Run for %s' % mtm.name, 'type': 'enabled', 'mediaType': mtm.mt}
            if self.addMediaTypeOptions == 'runFor':
                continue

            #log('Creating multi config fields on %s from %s' % (self.__class__, mtm.__class__))
            for configType in [x.__name__ for x in mtm.elementConfigsFor]:
                for element in Element.select().where(Element.type == configType):
                    prefix = self.useConfigsForElementsAs
                    sufix = element.getName()
                    h_name = '%s for %s (%s)' % (prefix, sufix, mtm.identifier)
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
            if curConfig.element is None:
                continue
            if curConfig.mediaType == element.mediaType and\
                self.useConfigsForElementsAs.lower() == curConfig.type and\
                curConfig.element.isAncestorOf(element): # is the config elemtn "above" the element in question

                return curConfig.value
        return None

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

class DownloadType(Plugin):
    _type = 'DownloadType'
    single = True
    addMediaTypeOptions = False
    extension = ''
    identifier = ''


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


class Downloader(DownloadTyped):
    """Plugins of this class send Downloads to another Program or directly download stuff"""
    _type = 'Downloader'
    types = [] # types the downloader can handle ... e.g. blackhole can handle both

    def addDownload(self, download):
        """Add nzb to downloader"""
        return False

    def getElementStaus(self, element):
        """return tuple of Status and a path (str)"""
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

    def _findGamezID(self, s):
        return self._findIDs(s)[0]

    def _findDownloadID(self, s):
        return self._findIDs(s)[1]


class Indexer(DownloadTyped):
    """Plugins of this class create elemnts based on mediaType structures"""
    _type = 'Indexer'
    types = [] # types this indexer will give back
    name = "Does Noting"

    def __init__(self, instance='Default'):
        # wrap function
        def searchForElement(*args, **kwargs):
            res = self._searchForElement(*args, **kwargs)
            for i, d in enumerate(res):
                # default stuff
                d.indexer = self.type
                d.indexer_instance = self.instance
                d.status = common.UNKNOWN
                res[i]
            return res
        self._searchForElement = self.searchForElement
        self.searchForElement = searchForElement
        DownloadTyped.__init__(self, instance=instance)

    def _getCategory(self, e):
        for cur_c in self.c.configs:
            if cur_c.type == 'category' and e.mediaType == cur_c.mediaType and cur_c.element in e.ancestors:
                return cur_c.value

    def getLatestRss(self):
        """return list of Gamez"""
        return []

    def searchForElement(self, element):
        """return list of Download()"""
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
    """get game information"""
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

    """creating more providers is definety more complicatedn then other things since
    the platform identification is kinda based on the the id of thegamesdb
    and the Game only has one field... but if one will take on this task please dont create just another field for the game
    instead create a new class that holds the information
    """

    def searchForElement(self, term=''):
        """return always a list of games even if id is given, list might be empty or only contain 1 item"""
        return Element()

    def getElement(self, id):
        return False

    def _getSupportedManagers(self):
        out = []
        for mtm in common.PM.MTM:
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


class Filter(Plugin):
    _type = 'Filter'
    name = 'Does Nothing'

    class FilterResult(object):
        def __init__(self, result=False, reason=''):
            self.result = result
            self.reason = reason

    def __init__(self, instance='Default'):
        self._config['run_on_hook_select'] = ''
        self.config_meta['run_on_hook_select'] = {'human': 'Run on stage'}
        #self._config['positive'] = True
        #self.config_meta['positive'] = {'human': 'Keep the the matches'}

        Plugin.__init__(self, instance=instance)

    def _run_on_hook_select(self):
        return {common.SEARCHTERMS: 'Search Term',
                common.FOUNDDOWNLOADS: 'Found Downloads'}

    def compare(self, element=None, download=None, string=None):
        # return a tuple if the string was accepted and the new string

        # for downloads only the bool is used
        # False -> reject download
        # True -> accept download

        #TODO implement
        # for search terms
        # False and '' -> reject
        # False and 'something' -> replaced
        # True and 'same as original' -> pass
        # True and 'something new' -> add the new string
        return (True, string)


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
    _type = 'MediaTypeManager'
    name = "Does Noting"
    identifier = ''
    order = ()
    download = None
    addConfig = {}
    elementConfigsFor = ()
    defaultElements = {}

    def __init__(self, instance):
        self.single = True

        self.config_meta['enable'] = {'on_enable': 'recachePlugins'}
        self._config['default_new_status_select'] = common.WANTED.id
        self.config_meta['default_new_status_select'] = {'human': 'Status for newly added %s' % self.__class__.__name__}
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
        else:
            return None

    def getManagedTypes(self):
        return [self.type] + [classType.__name__ for classType in self.order]

    def getOrderField(self, eType):
        if eType in self.s and '_orderBy' in self.s[eType]['class'].__dict__:
            return self.s[eType]['class'].__dict__['_orderBy']
        else:
            return ''

    def getAttrs(self, eType):
        return self.s[eType]['attr']

    def headInject(self):
        return ''

    def paint(self, root=None, status=None):
        if status is None:
            status = common.getHomeStatuses()

        if root is None:
            log('init paint on default root %s %s' % (self.root, self.root.id))
            return self.root.paint(status=status)
        else:
            log('init paint on given root %s %s' % (root, root.id))
            return root.paint(search=True)

    def search(self, search_query):
        log.info('Init search on %s for %s' % (self, search_query))
        self.searcher = None
        #xdm.DATABASE.set_autocommit(False)
        out = None
        for provider in common.PM.P:
            if not provider.runFor(self) or self.identifier not in provider.types:
                continue
            self.searcher = provider
            out = provider.searchForElement(term=search_query)
        #xdm.DATABASE.commit()
        #xdm.DATABASE.set_autocommit(True)
        self.searcher = None
        return out

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
        return {common.UNKNOWN.id: common.UNKNOWN.name,
                common.WANTED.id: common.WANTED.name,
                common.IGNORE.id: common.IGNORE.name}

__all__ = ['System', 'PostProcessor', 'Provider', 'Indexer', 'Notifier', 'Downloader', 'MediaTypeManager', 'Element', 'DownloadType', 'Filter', 'MediaAdder']
