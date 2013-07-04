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

import cherrypy
from jinja2 import Environment, FileSystemLoader
from xdm.classes import *
from xdm import common, tasks, helper


class Wizard(object):
    steps = 3

    def __init__(self, env):
        self.env = env

    __globals = helper.guiGlobals

    def _globals(self, step):
        prevStep = step - 1
        if prevStep < 0:
            prevStep = 0
        nextStep = step + 1
        if nextStep > Wizard.steps:
            nextStep = 'finished'

        out = {'step': step,
               'nextStep': nextStep,
               'prevStep': prevStep,
               'maxStep': Wizard.steps}
        out.update(self.__globals())
        return out

    @cherrypy.expose
    def default(self, step=0):
        step = int(step)

        if step <= Wizard.steps:
            if hasattr(self, 'step_%s' % step):
                return getattr(self, 'step_%s' % step)()
            else:
                template = self.env.get_template('wizard/step_%s.html' % step)
                common.SYSTEM.hc.setup_wizard_step = step
                return template.render(**self._globals(step))
        else:
            raise cherrypy.HTTPRedirect('%s/wizard/finished' % common.SYSTEM.c.webRoot)

    @cherrypy.expose
    def step_0(self):
        template = self.env.get_template('wizard/step_0.html')
        return template.render(**self._globals(0))

    @cherrypy.expose
    def skip(self):
        common.removeState(7)
        common.SYSTEM.hc.setup_wizard_step = Wizard.steps
        raise cherrypy.HTTPRedirect(common.SYSTEM.c.webRoot)

    @cherrypy.expose
    def finished(self):
        common.removeState(7)
        common.SYSTEM.hc.setup_wizard_step = Wizard.steps
        template = self.env.get_template('wizard/finished.html')
        return template.render(**self._globals(0))


    @cherrypy.expose
    def complete(self, term):
        pass
