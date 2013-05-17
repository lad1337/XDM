# Author: Dennis Lutter <lad1337@gmail.com>
# URL: https://github.com/lad1337/XDM
#
# This file is part of XDM: Xtentable Download Manager.
#
#XDM: Xtentable Download Manager. Plugin based media collection manager.
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

import traceback
import inspect
import json
import time
import sys
import platform
import cherrypy
import os
from fileBrowser import WebFileBrowser
from ajax import AjaxCalls
from jinja2 import Environment, FileSystemLoader
from xdm.classes import *
from xdm import common, tasks, helper
from xdm.logger import *
from xdm import actionManager
import datetime


class WebRoot:
    appPath = ''

    env = Environment(loader=FileSystemLoader(os.path.join('html', 'templates')))
    env.filters['idSafe'] = helper.replace_some
    env.filters['statusLabelClass'] = helper.statusLabelClass
    env.filters['vars'] = helper.webVars

    def __init__(self, app_path):
        WebRoot.appPath = app_path

    def _globals(self):
        return {'mtms': common.PM.MTM, 's': Status.select(), 'system': common.SYSTEM, 'PM': common.PM, 'common': common}

    browser = WebFileBrowser()
    ajax = AjaxCalls(env)

    @cherrypy.expose
    def index(self, status_message='', version=''):
        template = self.env.get_template('index.html')
        return template.render(**self._globals())

    @cherrypy.expose
    def shutdown(self):
        cherrypy.engine.exit()

    @cherrypy.expose
    def about(self):
        template = self.env.get_template('about.html')
        return template.render(platform=platform, originalArgs=sys.argv, **self._globals())

    @cherrypy.expose
    def plugins(self, recache=''):
        now = datetime.datetime.now()
        if common.REPOMANAGER.last_cache is not None:
            last_cache = common.REPOMANAGER.last_cache
        else:
            last_cache = now - datetime.timedelta(hours=25)
        delta = datetime.timedelta(hours=24)
        if not common.REPOMANAGER.cached or recache or (now - last_cache > delta):
            t = tasks.TaskThread(tasks.cacheRepos)
            t.start()
        if recache:
            return ''

        template = self.env.get_template('plugins.html')
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
    def getPaint(self, id):
        e = Element.get(Element.id == id)
        return e.manager.paint(e)

    @cherrypy.expose
    def getChildrensPaint(self, id):
        e = Element.get(Element.id == id)
        return e.manager.paintChildrenOf(e)

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
        mtm = common.PM.getMediaTypeManager(mt)[0]
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
    def clearSearches(self):
        tasks.removeTempElements()
        raise cherrypy.HTTPRedirect('/')

    @cherrypy.expose
    def reboot(self):
        actionManager.executeAction('hardReboot', 'Webgui')
        raise cherrypy.HTTPRedirect("/")

    @cherrypy.expose
    def startDownloadChecker(self):
        tasks.runChecker()
        raise cherrypy.HTTPRedirect("/")


    @cherrypy.expose
    def saveSettings(self, **kwargs):
        redirect_to = '/settings/'
        if 'saveOn' in kwargs:
            redirect_to += "#%s" % kwargs['saveOn']
            del kwargs['saveOn']
        self.ajax.save(**kwargs)
        raise cherrypy.HTTPRedirect(redirect_to)


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
        common.SYSTEM = common.PM.getSystems('Default')[0] # yeah SYSTEM is a plugin
        return json.dumps({'result': True, 'data': {}, 'msg': 'Configuration saved.'})

