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

import cherrypy
import json
from collections import OrderedDict
import xdm
from xdm import common, tasks, actionManager
from xdm.logger import *
from xdm.classes import *
from xdm.helper import convertV
import traceback
from xdm.plugins.repository import RepoManager
import threading
from xdm import helper


@cherrypy.popargs('state_path')
class Oauth(object):

    def __init__(self, env):
        self.env = env

    @cherrypy.expose
    def v1(self, state, oauth_token=None, oauth_verifier=None):
        plugin_identifier, instance = state.split("|")
        plugin = common.PM.getPluginByIdentifier(plugin_identifier, instance)
        if plugin.oauth.get_access_token(oauth_token, oauth_verifier):
            return "<script>try { window.opener.oauth_done(); } catch (err) {};window.close();</script>"

    @cherrypy.expose
    def v2(self, state=None, code=None):
        plugin_identifier, instance = state.split("|")
        plugin = common.PM.getPluginByIdentifier(plugin_identifier, instance)
        if plugin.oauth.get_access_token(code):
            return "<script>try { window.opener.oauth_done(); } catch (err) {};window.close();</script>"


    @cherrypy.expose
    def final(self):
        return "<script>try { window.opener.oauth_done(); } catch (err) {};window.close();</script>"



class AjaxCalls:

    def __init__(self, env):
        self.env = env

    @cherrypy.expose
    def index(self):
        return 'nothing here'

    def _globals(self):
        return {'mtms': common.PM.MTM, 's': Status.select(), 'system': common.SYSTEM, 'PM': common.PM, 'common': common}

    @cherrypy.expose
    def pluginCall(self, **kwargs):
        log("Plugin ajax call with: %s" % kwargs)
        p_type = kwargs.get('p_type')
        p_identifier = kwargs.get("p_identifier")
        p_instance = kwargs.get('p_instance')
        action = kwargs['action']
        p = None
        if p_type:
            p = common.PM.getInstanceByName(p_type, p_instance)
        elif p_identifier:
            p = common.PM.getPluginByIdentifier(p_identifier, p_instance)
        if p is None:
            return json.dumps({
                'result': False, 'data': {},
                'msg': 'Plugin not found {} {} {}'.format(p_type, p_identifier, p_instance)})

        if "." in action:
            last_attr = None
            for attr in action.split("."):
                if last_attr is None:
                    last_attr = getattr(p, attr)
                else:
                    last_attr = getattr(last_attr, attr)
            p_function = last_attr
        else:
            p_function = getattr(p, action)
        fn_args = []
        if hasattr(p_function, 'args'):
            for name in p_function.args:
                log('function %s needs %s' % (action, name))
                field_name = 'field_%s' % name
                if field_name in kwargs:
                    fn_args.append(convertV(kwargs[field_name]))
                    continue
                else:
                    log("Field '%s' not found in kwargs. tring array" % field_name)
                field_name = 'field_%s[]' % name
                if field_name in kwargs:
                    fn_args.append(convertV(kwargs[field_name]))
                else:
                    log.warning("Field %s not found in kwargs. this will probably not work out" % field_name)

        try:
            log("calling %s with %s" % (p_function, fn_args))
            status, data, msg = p_function(*fn_args)
        except Exception as ex:
            tb = traceback.format_exc()
            log.error("Error during %s of %s(%s) \nError: %s\n\n%s\n" % (action, p_type, p_instance, ex, tb))
            return json.dumps({'result': False, 'data': {}, 'msg': 'Internal Error in plugin'})
        return json.dumps({'result': status, 'data': data, 'msg': msg})

    @cherrypy.expose
    def search(self, mt, search_query, ignorePrevious=False):
        mtm = common.PM.getMediaTypeManager(mt)[0]
        oldS = None
        for s in Element.select().where(Element.status == common.TEMP, Element.type == mtm.s['root']):
            if s.getField('term') == search_query:
                oldS = s
                break
        if oldS is None or ignorePrevious:
            return mtm.paint(mtm.search(search_query))
        return mtm.paint(oldS)

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def preview(self, term='', mt=''):
        if len(term) < 3:
            return json.dumps({'result': False, 'data': [], 'msg': 'did not search'})
        term = u"%{}%".format(term.strip())
        mt = MediaType.select().where(MediaType.name == mt)
        fields = Field.select().join(Element).where(Field._value_char ** term, Element.mediaType == mt, Element.status != common.TEMP)
        results = {}
        for index, field in enumerate(fields):
            if field.element.id not in results:
                img = field.element.getAnyImage()
                results[field.element.id] = {'name': field.element.getName(),
                                             'img': unicode(img if img else ""),
                                             'type': field.element.type,
                                             'status': _(field.element.status.name)}
            if index >= 5:
                break
        return {'result': bool(results), 'data': results, 'msg': ''}

    @cherrypy.expose
    def deleteElement(self, id):
        element = Element.get(Element.id == id)
        common.Q.put(('element.delete', {'id': id}))
        return json.dumps({
            'result': True,
            'data': {},
            'msg': 'Deleted %s' % element.getName()}
        )

    @cherrypy.expose
    def addElement(self, id):
        element = Element.get(Element.id == id)
        status = common.getStatusByID(element.manager.c.default_new_status_select)
        element.manager.makeReal(element, status)
        if status == common.WANTED:
            t = tasks.TaskThread(tasks.searchElement, element)
            t.start()
        return json.dumps({'result': True, 'data': {}, 'msg': '%s added.' % element.getName()})

    @cherrypy.expose
    def getDownloadsFrame(self, id):
        ele = Element.get(Element.id == id)
        template = self.env.get_template('modalFrames/downloadsFrame.html')
        return template.render(downloads=ele.downloads, **self._globals())

    @cherrypy.expose
    def getEventsFrame(self, id, is_element=False):
        # this sis so supid -.-
        if is_element:
            if is_element == "true":
                is_element = True
            else:
                is_element = False
        template = self.env.get_template('modalFrames/eventsFrame.html')
        if is_element:
            events = History.select().where((History.obj_id == id) | (History.element == id)).order_by(History.time.desc())
        else:
            events = History.select().where(History.obj_id == id).order_by(History.time.desc())
        return template.render(events=events, **self._globals())

    @cherrypy.expose
    def getConfigFrame(self, id):
        ele = Element.get(Element.id == id)
        pluginWithOptions = []
        for plugin in common.PM.getAll():
            if plugin.elementConfig and plugin.runFor(ele.manager):
                log.debug("%s is a configureable plugin" % plugin)
                pluginWithOptions.append(plugin)
        template = self.env.get_template('modalFrames/configFrame.html')
        return template.render(plugins=pluginWithOptions, element=ele, **self._globals())

    @cherrypy.expose
    def getLocationsFrame(self, id):
        ele = Element.get(Element.id == id)
        template = self.env.get_template('modalFrames/locationsFrame.html')
        return template.render(locations=ele.locations, **self._globals())

    @cherrypy.expose
    def getDownloadDetailFrame(self, id):
        download = Download.get(Download.id == id)
        template = self.env.get_template('modalFrames/downloadDetailFrame.html')
        return template.render(download=download, **self._globals())

    @cherrypy.expose
    def clearEvents(self, id):
        amount = History.delete().where(History.obj_id == id).execute()
        return json.dumps({'result': True, 'data': {'amount': amount}, 'msg': '%s events removed' % amount})

    @cherrypy.expose
    def setStatus(self, status_id, element_id):
        status = common.getStatusByID(int(status_id))
        try:
            ele = Element.get(Element.id == element_id)
            ele.status = status
            ele.save()
        except:
            return json.dumps({'result': False, 'data': {}, 'msg': 'Could not set status.'})

        if status == common.WANTED:
            t = tasks.TaskThread(tasks.searchElement, ele)
            t.start()

        return json.dumps({'result': True, 'data': {'status_id': status.id}, 'msg': u'%s set to %s' % (ele.getName(), status)})

    @cherrypy.expose
    def getDownload(self, id):
        download = Download.get(Download.id == id)
        tasks.snatchOne(download.element, [download])
        download = Download.get(Download.id == id)
        if download.status == common.SNATCHED:
            return json.dumps({'result': True, 'data': {'element_id': download.element.id, 'status_id': download.status.id}, 'msg': u'%s was snatched' % (download.name)})
        else:
            return json.dumps({'result': False, 'data': [], 'msg': u'%s not was snatched' % (download.name)})


    @cherrypy.expose
    def forceSearch(self, id):
        element = Element.get(Element.id == id)
        newStatus = tasks.searchElement(element)
        element.save()
        if newStatus == common.SNATCHED:
            return json.dumps({'result': True, 'data': {"status_id": element.status.id}, 'msg': u'%s was snatched' % (element.getName())})
        else:
            element.status = common.WANTED
            element.save()
            return json.dumps({'result': False, 'data': {"status_id": element.status.id}, 'msg': u'No downloads found for %s' % (element.getName())})

    @cherrypy.expose
    def deleteLocation(self, id):
        l = Location.get(Location.id == id)
        l.delete_instance()
        return json.dumps({'result': True, 'data': {}, 'msg': u'Location deleted.'})

    @cherrypy.expose
    def searchProgress(self, mt, search_query):
        mtm = common.PM.getMediaTypeManager(mt)[0]
        if mtm.searcher is not None:
            progress = mtm.searcher.progress
            # print progress.count, progress.total, progress.percent
            return json.dumps({'count': progress.count, 'percent': progress.percent, 'total': progress.total})
        return json.dumps({'count': 0, 'percent': 0, 'total': 0})

    @cherrypy.expose
    def plugins_by_repo(self):
        if common.REPOMANAGER.caching or not common.REPOMANAGER.cached:
            return ''
        template = self.env.get_template('plugins_by_repo.html')
        installed_plugins = common.PM.getAll(returnAll=True, instance='Default')
        return template.render(repos=common.REPOMANAGER.getRepos(), installed_plugins=installed_plugins, **self._globals())

    @cherrypy.expose
    def plugins_by_type(self):
        if common.REPOMANAGER.caching or not common.REPOMANAGER.cached:
            return ''
        template = self.env.get_template('plugins_by_type.html')
        typed_plugins = OrderedDict()
        for repo in common.REPOMANAGER.getRepos():
            for plugin in repo.plugins:
                if plugin.type not in typed_plugins:
                    typed_plugins[plugin.type] = []
                typed_plugins[plugin.type].append(plugin)
        installed_plugins = common.PM.getAll(returnAll=True, instance='Default')
        return template.render(typed_plugins=typed_plugins, installed_plugins=installed_plugins, **self._globals())

    @cherrypy.expose
    def addRepo(self, url):
        r = Repo()
        r.name = 'unknown'
        r.info_url = ''
        r.url = url
        r.save()
        common.REPOMANAGER = RepoManager(Repo.select())
        t = tasks.TaskThread(tasks.cacheRepos)
        t.start()
        return ''

    @cherrypy.expose
    def removeRepo(self, url):
        try:
            repo = Repo.get(Repo.url == url)
        except Repo.DoesNotExist:
            return ''
        repo.delete_instance()
        common.REPOMANAGER = RepoManager(Repo.select())
        t = tasks.TaskThread(tasks.cacheRepos)
        t.start()
        return ''

    @cherrypy.expose
    def installPlugin(self, url='', identifier=''):
        t = tasks.TaskThread(tasks.installPlugin, identifier)
        t.start()
        return '<ul id="install-shell" class="shell"></ul>'

    @cherrypy.expose
    def installPlugins(self, **kwargs):
        _keys = sorted([int(x) for x in kwargs.keys()])
        _identifiers = [kwargs[str(key)] for key in _keys]

        log("Batch plugin install identifiers: %s" % _identifiers)

        def installAllPlugins(identifiers):
            for identifier in identifiers:
                common.REPOMANAGER.install(identifier, doCleanUp=False)
            common.REPOMANAGER.doCleanUp()

        t = tasks.TaskThread(installAllPlugins, _identifiers)
        t.start()
        return '<ul id="install-shell" class="shell"></ul>'

    @cherrypy.expose
    def deinstallPlugin(self, identifier=''):
        t = tasks.TaskThread(tasks.deinstallPlugin, identifier)
        t.start()
        return '<ul id="install-shell" class="shell"></ul>'

    @cherrypy.expose
    def getRepoMessage(self):
        return json.dumps({'result': True, 'data': common.REPOMANAGER.getLastInstallMessages(), 'msg':''})

    @cherrypy.expose
    def messageClose(self, uuid):
        result = common.MM.closeMessage(uuid)
        return json.dumps({'result': result, 'data':[], 'msg':''})

    @cherrypy.expose
    def messageConfirm(self, uuid):
        result = common.MM.confirmMessage(uuid)
        return json.dumps({'result': result, 'data':[], 'msg':''})

    @cherrypy.expose
    def reboot(self):
        common.SM.reset();
        common.SM.setNewMessage('reboot.py -t NOW')
        t = tasks.TaskThread(actionManager.executeAction, 'reboot', 'Webgui')
        t.start()
        return '<ul id="install-shell" class="shell"></ul>'

    @cherrypy.expose
    def getSystemMessage(self):
        return json.dumps({'result': True, 'data': common.SM.getLastMessages(), 'msg': ''})

    @cherrypy.expose
    def getLogEntries(self, entries=10):
        logEntries = []
        entryTemplate = self.env.get_template('log_entry.html')
        for _log in log.getEntries(int(entries)):
            logEntries.append(
                {'id': _log['id'],
                 'html': entryTemplate.render(log=_log),
                 'lvl': _log['data']['lvl']
                }
            )
        return json.dumps(logEntries)

    @cherrypy.expose
    def shutdown(self):
        common.SM.reset()
        common.SM.setNewMessage('shutdown.py -t NOW')
        t = tasks.TaskThread(actionManager.executeAction, 'shutdown', 'Webgui')
        threading.Timer(1, t.start).start()
        return '<ul id="install-shell" class="shell"></ul>'

    @cherrypy.expose
    def coreUpdate(self):
        common.SM.reset()
        common.SM.setNewMessage('update.py -t NOW')
        t = tasks.TaskThread(common.UPDATER.update)
        t.start()
        return '<ul id="install-shell" class="shell"></ul>'

    @cherrypy.expose
    def getDownloadBars(self, **kwargs):
        data = {}
        elements = list(Element.select().where(Element.id << kwargs.values()))
        for provider in common.PM.D:
            for element in elements:
                percentage = provider.getDownloadPercentage(element)
                if percentage and element.id not in data: # only set percentage for the element.id if we get one and only when we didn't already set on, this way we respect the order of downloaders
                    data[element.id] = percentage
        return json.dumps({'result': True, 'data': data, 'msg': ''})

    @cherrypy.expose
    def save(self, **kwargs):
        return self._save(**kwargs)

    @xdm.profileMeMaybe
    def _save(self, **kwargs):
        actions = {}
        # print kwargs
        if 'saveOn' in kwargs:
            del kwargs['saveOn']

        element = None
        if 'element_id' in kwargs:
            element = Element.get(Element.id == kwargs['element_id'])
            del kwargs['element_id']

        # this is slow !!
        # because i create each plugin for each config value that is for that plugin
        # because i need the config_meta from the class to create the action list
        # but i can use the plugins own c obj for saving the value
        _plugin_cache = {} # first try to make it faster is by using a cache for each plugin instance
        for k, v in kwargs.items():
            try:
                k = k.decode('utf-8')
            except UnicodeDecodeError:
                k = k.decode('latin-1') # for some obscure reason cherrypy (i think) encodes param key into latin-1 some times
                k = k.encode('utf-8') # but i like utf-8
            # print k, repr(k)
            # print v, repr(v)

            log(u"config K:%s V:%s" % (k, v))
            parts = k.split('-')
            # print parts
            # parts[0] plugin class name
            # parts[1] plugin instance name
            # parts[2] config name
            # v value for config -> parts[2]
            class_name = parts[0]
            instance_name = parts[1]
            config_name = parts[2]
            _cacheName = "%s %s" % (class_name, instance_name)
            if _cacheName in _plugin_cache:
                plugin = _plugin_cache[_cacheName]
            else:
                plugin = common.PM.getInstanceByName(class_name, instance_name)
                _plugin_cache[_cacheName] = plugin
            if plugin:
                log(u"We have a plugin: %s (%s)" % (class_name, instance_name))
                new_value = helper.convertV(v)
                if element is None: # normal settings page
                    old_value = getattr(plugin.c, config_name)
                    new_value = helper.convertV(v)
                    if old_value == new_value:
                        continue
                if element is not None: # we got an element id so its an element config
                    cur_c = plugin.e.getConfig(config_name, element)
                    if cur_c.value == new_value:
                        continue
                    log.debug("setting element config. %s K:%s, V:%s" % (element, config_name, new_value))
                    cur_c.element = element
                    cur_c.value = new_value
                    cur_c.save()
                else: # normal settings page
                    setattr(plugin.c, config_name, convertV(v)) # saving value

                if plugin.config_meta[config_name] and element is None: # this returns none
                    if 'on_change_actions' in plugin.config_meta[config_name] and old_value != new_value:
                        actions[plugin] = plugin.config_meta[config_name]['on_change_actions'] # this is a list of actions
                    if 'actions' in plugin.config_meta[config_name]:
                        actions[plugin] = plugin.config_meta[config_name]['actions'] # this is a list of actions
                    if 'on_enable' in plugin.config_meta[config_name] and new_value:
                        actions[plugin] = plugin.config_meta[config_name]['on_enable'] # this is a list of actions
                elif plugin.elementConfig_meta[config_name] and element is not None:
                    pass
                continue
            else: # no plugin with that class_name or instance found
                log(u"We don't have a plugin: %s (%s)" % (class_name, instance_name))
                continue

        if element is None:
            common.PM.reinstanceiate()
            # This is provate find a better place to the cache
            common._provider_tags_cache = []
        final_actions = {}
        for cur_class_name, cur_actions in actions.items():
            for cur_action in cur_actions:
                if not cur_action in final_actions:
                    final_actions[cur_action] = []
                final_actions[cur_action].append(cur_class_name)
        for action, plugins_that_called_it  in final_actions.items():
            actionManager.executeAction(action, plugins_that_called_it)

        return json.dumps({'result': True, 'data': {}, 'msg': 'Configuration saved.'})

    @cherrypy.expose
    def oauth_init(self, **body):
        plugin = common.PM.getPluginByIdentifier(
            body["identifier"], body["instance"])
        if plugin.oauth is None:
            return json.dumps({"error": "plugins does not support oauth"})
        return json.dumps(
            {"access_url": plugin.oauth.request_access_url}
        )



