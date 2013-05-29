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

import cherrypy
import json
import xdm
from xdm import common, tasks, actionManager
from xdm.logger import *
from xdm.classes import *
import traceback
from xdm.plugins.repository import RepoManager


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
        p_type = kwargs['p_type']
        p_instance = kwargs['p_instance']
        action = kwargs['action']
        p = common.PM.getInstanceByName(p_type, p_instance)
        p_function = getattr(p, action)
        fn_args = []
        if hasattr(p_function, 'args'):
            for name in p_function.args:
                log('function %s needs %s' % (action, name))
                field_name = 'field_%s' % name
                if field_name in kwargs:
                    fn_args.append(kwargs[field_name])
        try:
            status, data, msg = p_function(*fn_args)
        except Exception as ex:
            tb = traceback.format_exc()
            log.error("Error during %s of %s(%s) \nError: %s\n\n%s\n" % (action, p_type, p_instance, ex, tb))
            return json.dumps({'result': False, 'data': {}, 'msg': 'Internal Error in plugin'})
        return json.dumps({'result': status, 'data': data, 'msg': msg})

    @cherrypy.expose
    def search(self, mt, search_query):
        mtm = common.PM.getMediaTypeManager(mt)[0]
        oldS = None
        for s in Element.select().where(Element.status == common.TEMP, Element.type == mtm.s['root']):
            if s.getField('term') == search_query:
                oldS = s
                break
        else:
            return mtm.paint(mtm.search(search_query))
        return mtm.paint(oldS)

    @cherrypy.expose
    def deleteElement(self, id):
        element = Element.get(Element.id == id)
        name = element.getName()
        element.deleteWithChildren()
        return json.dumps({'result': True, 'data': {}, 'msg': 'Deleted %s' % name})

    @cherrypy.expose
    def getDownloadsFrame(self, id):
        ele = Element.get(Element.id == id)
        template = self.env.get_template('modalFrames/downloadsFrame.html')
        return template.render(downloads=ele.downloads, **self._globals())

    @cherrypy.expose
    def getEventsFrame(self, id):
        template = self.env.get_template('modalFrames/eventsFrame.html')
        events = History.select().where(History.obj_id == id).order_by(History.time).order_by(History.time.desc())
        return template.render(events=events, **self._globals())

    @cherrypy.expose
    def getConfigFrame(self, id):
        ele = Element.get(Element.id == id)
        pluginWithOptions = []
        for plugin in common.PM.getAll():
            if plugin.elementConfig and plugin.runFor(ele.manager):
                pluginWithOptions.append(plugin)
        template = self.env.get_template('modalFrames/configFrame.html')
        return template.render(plugins=pluginWithOptions, element=ele, **self._globals())

    @cherrypy.expose
    def clearEvents(self, id):
        amount = History.delete().where(History.obj_id == id).execute()
        return json.dumps({'result': True, 'data': {'amount': amount}, 'msg': '%s events removed' % amount})

    @cherrypy.expose
    def searchProgress(self, mt, search_query):
        mtm = common.PM.getMediaTypeManager(mt)[0]
        if mtm.searcher is not None:
            progress = mtm.searcher.progress
            #print progress.count, progress.total, progress.percent
            return json.dumps({'count': progress.count, 'percent': progress.percent, 'total': progress.total})
        return json.dumps({'count': 0, 'percent': 0, 'total': 0})

    @cherrypy.expose
    def repo(self):
        if common.REPOMANAGER.caching or not common.REPOMANAGER.cached:
            return ''
        template = self.env.get_template('repos.html')
        return template.render(repos=common.REPOMANAGER.getRepos(), **self._globals())

    @cherrypy.expose
    def addRepo(self, url):
        r = Repo()
        r.name = 'unknown'
        r.url = url
        r.save()
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
        t = tasks.TaskThread(actionManager.executeAction, 'hardReboot', 'Webgui')
        t.start()
        return '<ul id="install-shell" class="shell"></ul>'

    @cherrypy.expose
    def getSystemMessage(self):
        return json.dumps({'result': True, 'data': common.SM.getLastMessages(), 'msg': ''})

    @cherrypy.expose
    def shutdown(self):
        common.SM.reset()
        common.SM.setNewMessage('shutdown.py -t NOW')
        t = tasks.TaskThread(actionManager.executeAction, 'shutdown', 'Webgui')
        t.start()
        return '<ul id="install-shell" class="shell"></ul>'

    @cherrypy.expose
    def coreUpdate(self):
        t = tasks.TaskThread(common.UPDATER.update)
        t.start()
        common.SM.reset()
        common.SM.setNewMessage('update.py -t NOW')
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
        if 'saveOn' in kwargs:
            del kwargs['saveOn']

        def convertV(cur_v):
            try:
                return float(cur_v)
            except TypeError: # its a list for bools / checkboxes "on" and "off"... "on" is only send when checked "off" is always send
                return True
            except ValueError:
                if cur_v in ('None', 'off'):
                    cur_v = False
                return cur_v

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
            log("config K:%s V:%s" % (k, v))
            parts = k.split('-')
            #print parts
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
                log("We have a plugin: %s (%s)" % (class_name, instance_name))
                if element is not None: # we got an element id so its an element config
                    old_value = getattr(plugin.e, config_name)
                else: # normal settings page
                    old_value = getattr(plugin.c, config_name)
                new_value = convertV(v)
                if old_value == new_value:
                    continue
                if element is not None: # we got an element id so its an element config
                    cur_c = plugin.e.getConfig(config_name, element)
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
                log("We don't have a plugin: %s (%s)" % (class_name, instance_name))
                continue

        common.PM.cache()
        final_actions = {}
        for cur_class_name, cur_actions in actions.items():
            for cur_action in cur_actions:
                if not cur_action in final_actions:
                    final_actions[cur_action] = []
                final_actions[cur_action].append(cur_class_name)
        for action, plugins_that_called_it  in final_actions.items():
            actionManager.executeAction(action, plugins_that_called_it)
        common.SYSTEM = common.PM.getSystems('Default')[0] # yeah SYSTEM is a plugin
        return json.dumps({'result': True, 'data': {}, 'msg': 'Configuration saved.'})

