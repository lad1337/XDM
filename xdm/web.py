import cherrypy
import os
from jinja2 import Environment, FileSystemLoader
from classes import *
from xdm.fileBrowser import WebFileBrowser
from xdm import common, tasks, helper
from xdm.logger import *
from xdm import actionManager
import traceback
import inspect
import json
import time


class WebRoot:
    appPath = ''

    def __init__(self, app_path):
        WebRoot.appPath = app_path
        self.env = Environment(loader=FileSystemLoader(os.path.join('html', 'templates')))
        self.env.filters['idSafe'] = helper.replace_some


    def _globals(self):
        return {'mtms': common.PM.MTM, 's': Status.select(), 'system': common.SYSTEM, 'PM': common.PM, 'common': common}

    @cherrypy.expose
    def index(self, status_message='', version=''):
        template = self.env.get_template('index.html')
        return template.render(**self._globals())

    @cherrypy.expose
    def completed(self, status_message='', version=''):
        template = self.env.get_template('completed.html')
        return template.render(**self._globals())

    @cherrypy.expose
    def settings(self):
        template = self.env.get_template('settings.html')
        return template.render(plugins=common.PM.getAll(True), **self._globals())

    @cherrypy.expose
    def forcesearch(self, id):
        element = Element.get(Element.id == id)
        newStatus = tasks.searchElement(element)
        element.save()
        raise cherrypy.HTTPRedirect('/')

    @cherrypy.expose
    def results(self, search_query=''):
        template = self.env.get_template('results.html')
        templateGlobals = self._globals()
        searchers = templateGlobals['mtms']

        if search_query.startswith('All: '):
            search_query = search_query.replace('All: ', '')
        else:
            for mtm in templateGlobals['mtms']:
                if search_query.startswith( '%s: ' % mtm.type) :
                    search_query = search_query.replace('%s: ' % mtm.type, '')
                    searchers = [mtm]
                    break
        return template.render(searchers=searchers, search_query=search_query, **templateGlobals)

    @cherrypy.expose
    def ajaxSearch(self, mt, search_query):
        mtm = common.PM.getMediaTypeManager(mt)
        oldS = None
        for s in Element.select().where(Element.status == common.TEMP, Element.type == mtm.s['root']):
            if s.getField('term') == search_query:
                oldS = s
                break
        else:
            return mtm.paint(mtm.search(search_query))
        return mtm.paint(oldS)

    @cherrypy.expose
    def ajaxDeleteElement(self, id):
        element = Element.get(Element.id == id)
        name = element.getName()
        element.deleteWithChildren()
        return json.dumps({'result': True, 'data': {}, 'msg': 'Deleted %s' % name})

    @cherrypy.expose
    def getPaint(self, id):
        e = Element.get(Element.id == id)
        return e.manager.paint(e)

    @cherrypy.expose
    def ajaxGetDownloadsFrame(self, id):
        ele = Element.get(Element.id == id)
        template = self.env.get_template('downloadsFrame.html')
        return template.render(downloads=ele.downloads, **self._globals())

    @cherrypy.expose
    def ajaxGetEventsFrame(self, id):
        template = self.env.get_template('eventsFrame.html')
        events = History.select().where(History.obj_id == id).order_by(History.time)
        return template.render(events=events, **self._globals())


    @cherrypy.expose
    def saveSettings(self, **kwargs):
        redirect_to = '/settings/'
        if 'saveOn' in kwargs:
            redirect_to += "#%s" % kwargs['saveOn']
            del kwargs['saveOn']
        self.ajaxSave(**kwargs)
        raise cherrypy.HTTPRedirect(redirect_to)

    @cherrypy.expose
    def ajaxSave(self, **kwargs):
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

        # this is slow !!
        # because i create each plugin for each config value that is for that plugin
        # because i need the config_meta from the class to create the action list
        # but i can use the plugins own c obj for saving the value
        for k, v in kwargs.items():
            log("config K:%s V:%s" % (k, v))
            parts = k.split('-')
            # parts[0] plugin class name
            # parts[1] plugin instance name
            # parts[2] config name
            # v value for config -> parts[2]
            class_name = parts[0]
            instance_name = parts[1]
            config_name = parts[2]
            plugin = common.PM.getInstanceByName(class_name, instance_name)
            if plugin:
                log("We have a plugin: %s (%s)" % (class_name, instance_name))
                old_value = getattr(plugin.c, config_name)
                new_value = convertV(v)
                if old_value == new_value:
                    continue
                setattr(plugin.c, config_name, convertV(v)) # saving value
                if plugin.config_meta[config_name]: # this returns none
                    if 'on_change_actions' in plugin.config_meta[config_name] and old_value != new_value:
                        actions[plugin] = plugin.config_meta[config_name]['on_change_actions'] # this is a list of actions
                    if 'actions' in plugin.config_meta[config_name]:
                        actions[plugin] = plugin.config_meta[config_name]['actions'] # this is a list of actions
                    if 'on_enable' in plugin.config_meta[config_name] and new_value:
                        actions[plugin] = plugin.config_meta[config_name]['on_enable'] # this is a list of actions

                continue
            else: # no plugin with that class_name or instance found
                log("We don't have a plugin: %s (%s)" % (class_name, instance_name))
                continue

        #actions = list(set(actions))
        common.PM.cache()
        final_actions = {}
        for cur_class_name, cur_actions in actions.items():
            for cur_action in cur_actions:
                if not cur_action in final_actions:
                    final_actions[cur_action] = []
                final_actions[cur_action].append(cur_class_name)
        for action, plugins_that_called_it  in final_actions.items():
            actionManager.executeAction(action, plugins_that_called_it)
        common.SYSTEM = common.PM.getSystems('Default') # yeah SYSTEM is a plugin
        return json.dumps({'result': True, 'data': {}, 'msg': 'Configuration saved.'})

    @cherrypy.expose
    def createInstance(self, plugin, instance):
        c = None
        for cur_plugin in common.PM.getAll(True):
            if cur_plugin.type == plugin and not cur_plugin.single:
                c = cur_plugin.__class__(instance=instance)
                break
        common.PM.cache()
        url = '/settings/'
        if c:
            url = '/settings/#%s' % c.name.replace(' ', '_').replace('(', '').replace(')', '')
        raise cherrypy.HTTPRedirect(url)

    @cherrypy.expose
    def removeInstance(self, plugin, instance):
        for cur_plugin in common.PM.getAll(True):
            if cur_plugin.type == plugin and cur_plugin.instance == instance:
                c = cur_plugin.deleteInstance()
                break
        common.PM.cache()
        raise cherrypy.HTTPRedirect('/settings/')

    @cherrypy.expose
    def refreshinfo(self, id):
        log("init update")
        tasks.updateElement(Element.get(Element.id == id))
        raise cherrypy.HTTPRedirect('/')

    @cherrypy.expose
    def delete(self, id):
        e = Element.get(Element.id == id)
        e.deleteWithChildren()
        raise cherrypy.HTTPRedirect('/')

    @cherrypy.expose
    def setStatus(self, id, s):
        ele = Element.get(Element.id == id)
        ele.status = common.getStatusByID(int(s))
        ele.save()
        if ele.status == common.WANTED:
            tasks.searchElement(ele)
        raise cherrypy.HTTPRedirect('/')

    @cherrypy.expose
    def getDownload(self, id):
        download = Download.get(Download.id == id)
        tasks.snatchOne(download.element, [download])
        raise cherrypy.HTTPRedirect('/')

    @cherrypy.expose
    def makePermanent(self, id):
        element = Element.get(Element.id == id)
        element.manager.makeReal(element)
        time.sleep(1)
        t = tasks.TaskThread(tasks.searchElement, element)
        t.start()
        raise cherrypy.HTTPRedirect('/')

    @cherrypy.expose
    def addElement(self, mt, providerTag, pID):
        mtm = common.PM.getMediaTypeManager(mt)
        log("adding %s %s %s" % (mt, providerTag, pID))
        for p in common.PM.P:
            if not (p.runFor(mtm) and p.tag == providerTag):
                continue
            new_e = p.getElement(pID)
            if new_e:
                new_e.save()
                new_e.downloadImages()
        raise cherrypy.HTTPRedirect('/')

    @cherrypy.expose
    def ajaxSearchProgress(self, mt, search_query):
        mtm = common.PM.getMediaTypeManager(mt)
        if mtm.searcher is not None:
            progress = mtm.searcher.progress
            #print progress.count, progress.total, progress.percent
            return json.dumps({'count': progress.count, 'percent': progress.percent, 'total': progress.total})
        return json.dumps({'count': 0, 'percent': 0, 'total': 0})

    @cherrypy.expose
    def clearSearches(self):
        tasks.removeTempElements()
        raise cherrypy.HTTPRedirect('/')

    @cherrypy.expose
    def pluginAjaxCall(self, **kwargs):
        p_type = kwargs['p_type']
        p_instance = kwargs['p_instance']
        action = kwargs['action']
        p = common.PM.getInstanceByName(p_type, p_instance)
        p_function = getattr(p, action)
        fn_args = []
        for name in inspect.getargspec(p_function).args:
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
    def reboot(self):
        actionManager.executeAction('hardReboot', 'Webgui')
        raise cherrypy.HTTPRedirect("/")

    @cherrypy.expose
    def startDownloadChecker(self):
        tasks.runChecker()
        raise cherrypy.HTTPRedirect("/")

    browser = WebFileBrowser()
