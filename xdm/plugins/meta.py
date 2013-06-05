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

from xdm.logger import *
import collections
import traceback
from xdm.classes import Config


class ConfigWrapper(object):
    """this will be the "c" of a plugin to easily get the config for the current plugin
    also handels the saving of the new config"""
    configs = []

    def __init__(self, plugin, configDefinition):
        self._plugin = plugin
        self._configDefinition = configDefinition
        self.configs = []
        self._configValueCache = {}

    def addConfig(self, c):
        self.configs.append(c)

    def finalSort(self, enabled=None):
        self.configs.sort(key=lambda x: x.name, reverse=False)
        if enabled is not None:
            self.configs.insert(0, self.configs.pop(self.configs.index(enabled)))

    def getConfig(self, name, element=None):
        for cur_c in self.configs:
            if cur_c.name == name and element is None:
                return cur_c
            elif cur_c.name == name and element == cur_c.element:
                return cur_c
        return None

    def getConfigsFor(self, element):
        out = []
        for k, v in self._configDefinition.items():
            try:
                cur_c = Config.get(Config.section == self._plugin.__class__.__name__,
                                   Config.module == 'Plugin',
                                   Config.instance == self._plugin.instance,
                                   Config.name == k,
                                   Config.element == element)
            except Config.DoesNotExist:
                cur_c = Config()
                cur_c.module = 'Plugin'
                cur_c.section = self._plugin.__class__.__name__
                cur_c.instance = self._plugin.instance
                cur_c.name = k
                if v == k:
                    v = getattr(self._plugin.c, v)
                cur_c.value = v
                cur_c.type = 'element_config'
                cur_c.element = element
                cur_c.save()
            out.append(cur_c)
            self.addConfig(cur_c)
        return out

    def __getattr__(self, name):
        try:
            return self._configValueCache[name]
        except KeyError:
            pass
        for cur_c in self.configs:
            if cur_c.name == name:
                self._configValueCache[name] = cur_c.value
                return cur_c.value
        raise AttributeError

    def __setattr__(self, name, value):
        for cur_c in self.configs:
            if cur_c.name == name:
                self._configValueCache = {}
                cur_c.value = value
                cur_c.save()
                return
        else:
            super(ConfigWrapper, self).__setattr__(name, value)


class ConfigMeta(collections.MutableMapping):
    def __init__(self, *args, **kwargs):
        self.store = dict()
        self.update(dict(*args, **kwargs)) # use the free update to set keys

    def __getitem__(self, key):
        try:
            return self.store[self.__keytransform__(key)]
        except KeyError:
            return None

    def __setitem__(self, key, value):
        self.store[self.__keytransform__(key)] = value

    def __delitem__(self, key):
        del self.store[self.__keytransform__(key)]

    def __iter__(self):
        return iter(self.store)

    def __len__(self):
        return len(self.store)

    def __keytransform__(self, key):
        return key


def pluginMethodWrapper(caller_name, run, alternative):
    """Return a wrapped instance method"""
    def outer(*args, **kwargs):
        try:
            return run(*args, **kwargs)
        except Exception as ex:
            tb = traceback.format_exc()
            out = alternative(*args, **kwargs)
            try:
                log.error("Error during %s of %s \nError: %s\n\n%s\nNew value:%s" % (run.__name__, caller_name, ex, tb, out), traceback=tb, new_out=out, exception=ex)
            except:
                log.error("Error during %s of %s \nError: %s\n\n%s" % (run.__name__, caller_name, ex, tb))
            return out
    return outer

__all__ = ['pluginMethodWrapper', 'ConfigMeta', 'ConfigWrapper']
