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

import traceback
import inspect
import json
import time
import sys
import platform
import cherrypy
import os
import re
import datetime
import xdm
from fileBrowser import WebFileBrowser
from wizard import Wizard

from ajax import AjaxCalls
from jinja2 import Environment, FileSystemLoader
from xdm.classes import *
from xdm import common, tasks, helper
from xdm.logger import *
from xdm import actionManager
from xdm.api import WebApi
# workaround for spinxy not installing _ and ngettext
try:
    _()
except NameError:
    _ = lambda x: x
try:
    ngettext()
except NameError:
    ngettext = lambda x: x

env = Environment(loader=FileSystemLoader(os.path.join('html', 'templates')), extensions=['jinja2.ext.i18n'])
env.install_gettext_callables(_, ngettext, newstyle=True)
env.filters['idSafe'] = helper.idSafe
env.filters['statusLabelClass'] = helper.statusLabelClass
env.filters['vars'] = helper.webVars
env.filters['relativeTime'] = helper.reltime
env.filters['dereferMe'] = helper.dereferMe
env.filters['dereferMeText'] = helper.dereferMeText


def stateCheck():
    if xdm.xdm_states[7] in xdm.common.STATES:
        r = cherrypy.request
        if not r.path_info.startswith('/wizard'):
            for path in common.PUBLIC_PATHS + ['/ajax']:
                if r.path_info.startswith(path) and len(r.path_info) > 1:
                    # print 'path looks fine %s' % r.path_info
                    break
            else:
                # print "redirecting %s to %s" % (r.path_info, '%s%s' % (common.SYSTEM.c.webRoot, '/wizard/%s' % common.SYSTEM.hc.setup_wizard_step))
                raise cherrypy.HTTPRedirect('%s%s' % (common.SYSTEM.c.webRoot, '/wizard/%s' % common.SYSTEM.hc.setup_wizard_step))

    if not (xdm.xdm_states[0] in xdm.common.STATES or\
            xdm.xdm_states[1] in xdm.common.STATES or\
            xdm.xdm_states[6] in xdm.common.STATES or\
            xdm.xdm_states[3] in xdm.common.STATES):
        # allow normal handler to run
        # now check if we need tu run the wizard an redirect to it
        if xdm.xdm_states[7] not in xdm.common.STATES and common.SYSTEM.hc.setup_wizard_step < Wizard.steps:
            xdm.common.addState(7)
            raise cherrypy.HTTPRedirect('%s%s' % (common.SYSTEM.c.webRoot, '/wizard/%s' % common.SYSTEM.hc.setup_wizard_step))

        # i dont want to rewrite every header of a function just to allow pjax
        if '_pjax' in cherrypy.request.params:
            del cherrypy.request.params['_pjax']
        return False
    elif xdm.xdm_states[3] in xdm.common.STATES and cherrypy.request.path_info.startswith('/ajax'):
        # allow ajax calls during update
        return False
    else: # webserver is running but we do something that is so important that we don't want the user to interact with the gui
        messages = ""
        for msg in common.SM.system_messages:
            messages += u'%s<br>' % msg[1]
        cherrypy.response.body = "<html>" \
                                 "<head><title>Not now</title></head>" \
                                 "<body>XDM is in a state of '%s' please wait...<br>%s</body>" \
                                 "</html>" % (common.STATES, messages)
        try:
            del cherrypy.response.headers["Content-Length"]
        except KeyError:
            pass
        # suppress normal handler from running
        return True


class WebRoot:
    _cp_config = {'tools.stateBlock.on': True}
    appPath = ''

    def __init__(self, app_path):
        WebRoot.appPath = app_path

    _globals = helper.guiGlobals
    browser = WebFileBrowser()
    ajax = AjaxCalls(env)
    wizard = Wizard(env)
    api = WebApi()

    def redirect(self, abspath, *args, **KWs):
        assert abspath[0] == '/'
        raise cherrypy.HTTPRedirect('%s%s' % (common.SYSTEM.c.webRoot, abspath), *args, **KWs)

    @cherrypy.expose
    def index(self, status_message='', version=''):
        template = env.get_template('index.html')
        return template.render(**self._globals())

    @cherrypy.expose
    def status(self, runTask=None):
        if runTask is None:
            tasks.coreUpdateCheck()
        else:
            common.SCHEDULER.runTaskNow(runTask)
        template = env.get_template('about.html')
        return template.render(platform=platform, originalArgs=sys.argv, xdm=xdm, **self._globals())

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

        template = env.get_template('plugins.html')
        return template.render(**self._globals())

    @cherrypy.expose
    def completed(self):
        template = env.get_template('completed.html')
        return template.render(**self._globals())

    @cherrypy.expose
    def settings(self, **kwargs):
        plugins = []
        if kwargs:
            indexes = sorted(kwargs.keys())
            for index in indexes:
                pluginClassGetter = kwargs[index]
                plugins.extend(getattr(common.PM, pluginClassGetter)(returnAll=True))
        else:
            plugins = common.PM.getAll(True)
        template = env.get_template('settings.html')
        return template.render(plugins=plugins, **self._globals())

    @cherrypy.expose
    def settingsPluginHtml(self, **kwargs):
        plugins = []
        if kwargs:
            indexes = sorted(kwargs.keys())
            for index in indexes:
                pluginClassGetter = kwargs[index]
                try:
                    plugins.extend(getattr(common.PM, pluginClassGetter)(returnAll=True))
                except AttributeError:
                    pass
        else:
            return ""
        template = env.get_template('settingsPlugin.html')
        return template.render(plugins=plugins, **self._globals())

    @cherrypy.expose
    def forcesearch(self, id):
        element = Element.get(Element.id == id)
        newStatus = tasks.searchElement(element)
        element.save()
        self.redirect('/')

    @cherrypy.expose
    def results(self, search_query=''):
        template = env.get_template('results.html')
        templateGlobals = self._globals()
        searchers = templateGlobals['mtms']

        if search_query.startswith('All: '):
            search_query = search_query.replace('All: ', '')
        else:
            for mtm in templateGlobals['mtms']:
                if search_query.startswith('%s: ' % mtm.type) :
                    search_query = search_query.replace('%s: ' % mtm.type, '')
                    searchers = [mtm]
                    break
        return template.render(searchers=searchers, search_query=search_query, **templateGlobals)


    @cherrypy.expose
    def getMediaTypePaint(self, identifier, status=''):

        mt = common.PM.getMediaTypeManager(identifier)[0]
        if status == 'home':
            status = mt.homeStatuses()
        elif status == 'completed':
            status = mt.completedStatues()
        return mt.paint(status=status)

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
                cleanInstance = re.sub(ur'[\W]+', u'_', instance, flags=re.UNICODE)
                c = cur_plugin.__class__(instance=cleanInstance)
                break
        common.PM.cache()
        url = '%s/settings/' % common.SYSTEM.c.webRoot
        if c:
            url = '%s/settings/#%s' % (common.SYSTEM.c.webRoot, c.name.replace(' ', '_').replace('(', '').replace(')', ''))
        raise cherrypy.HTTPRedirect(url)

    @cherrypy.expose
    def removeInstance(self, plugin, instance):
        for cur_plugin in common.PM.getAll(True):
            if cur_plugin.type == plugin and cur_plugin.instance == instance:
                c = cur_plugin.deleteInstance()
                break
        common.PM.cache()
        self.redirect('/settings/')

    @cherrypy.expose
    def refreshinfo(self, id):
        log("init update")
        tasks.updateElement(Element.get(Element.id == id))
        raise cherrypy.HTTPRedirect('%s/' % common.SYSTEM.c.webRoot)

    @cherrypy.expose
    def delete(self, id):
        e = Element.get(Element.id == id)
        manager = e.manager
        manager.deleteElement(e)
        self.redirect('/')

    @cherrypy.expose
    def setStatus(self, id, s):
        ele = Element.get(Element.id == id)
        ele.status = common.getStatusByID(int(s))
        ele.save()
        if ele.status == common.WANTED:
            tasks.searchElement(ele)
        self.redirect('/')

    @cherrypy.expose
    def getDownload(self, id):
        download = Download.get(Download.id == id)
        tasks.snatchOne(download.element, [download])
        self.redirect('/')

    @cherrypy.expose
    def makePermanent(self, id):
        element = Element.get(Element.id == id)
        status = common.getStatusByID(element.manager.c.default_new_status_select)
        element.manager.makeReal(element, status)
        if status == common.WANTED:
            t = tasks.TaskThread(tasks.searchElement, element)
            t.start()
        self.redirect('/')

    # TODO: what in the world is this !?
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
        self.redirect('/')

    @cherrypy.expose
    def clearSearches(self):
        tasks.removeTempElements()
        self.redirect('/')

    @cherrypy.expose
    def startDownloadChecker(self):
        tasks.runChecker()
        self.redirect("/")

    @cherrypy.expose
    def log(self, entries=30):
        logEntries = ''
        entryTemplate = env.get_template('log_entry.html')
        for _log in log.getEntries(entries):
            logEntries += entryTemplate.render(log=_log)

        template = env.get_template('log.html')
        return template.render(platform=platform, logEntries=logEntries, logPath=xdm.LOGPATH, **self._globals())

    @cherrypy.expose
    def saveSettings(self, **kwargs):
        redirect_to = '/settings/'
        if 'saveOn' in kwargs:
            redirect_to += "#%s" % kwargs['saveOn']
            del kwargs['saveOn']
        self.ajax.save(**kwargs)
        self.redirect(redirect_to)


        # actions = list(set(actions))
        common.PM.cache()
        final_actions = {}
        for cur_class_name, cur_actions in actions.items():
            for cur_action in cur_actions:
                if not cur_action in final_actions:
                    final_actions[cur_action] = []
                final_actions[cur_action].append(cur_class_name)
        for action, plugins_that_called_it  in final_actions.items():
            actionManager.executeAction(action, plugins_that_called_it)
        common.SYSTEM = common.PM.getSystem('Default')[0] # yeah SYSTEM is a plugin
        return json.dumps({'result': True, 'data': {}, 'msg': 'Configuration saved.'})

