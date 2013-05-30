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

import sys
import os
import xdm
from xdm.logger import *
from jsonrpclib.SimpleJSONRPCServer import SimpleJSONRPCServer
import threading
from xdm import actionManager, common
import json

from functools import partial, update_wrapper
from jsonrpclib.jsonrpc import ProtocolError, Fault
import types


class ApiDispatcher(object):

    def __init__(self):
        self._exposed = {}

    def exposeThis(self, fn, name):
        self._exposed[name] = fn

    def _listMethods(self):
        return self._exposed.keys()

    def _dispatch(self, method, params):
        print method, params
        checkApiKey = True
        if method in ('ping', 'version'):
            checkApiKey = False
        if method in self._exposed:
            func = self._exposed[method]
            if checkApiKey:
                print common.APIKEY
                print type(params)
                if  params and type(params) is types.ListType:
                    if params[0] != common.APIKEY:
                        return Fault(-31121, "Missing API key or wrong API key")
                    else:# correct api key as list
                        del params[0]
                elif 'apikey' not in params:
                    return Fault(-31121, "Missing API key")
                elif params['apikey'] != common.APIKEY:
                    return Fault(-31123, "API key denied access")
                else:# correct api key as keyword
                    del params['apikey']

            try:
                if type(params) is types.ListType:
                    response = func(*params)
                else:
                    response = func(**params)
                return response
            except TypeError:
                return Fault(-32602, 'Invalid parameters.')
        else:
            return Fault(-32601, 'Method %s not supported.' % method)

apiDispatcher = ApiDispatcher()


class expose(object):
    """Expose the function and add it to the apiDispatcher"""
    def __init__(self, target):
        print type(target), target.__objclass__
        self.target = target
        # dynamically name __call__ after the target
        wrapped = partial(self.__call__)
        self.__call__ = update_wrapper(wrapped, self.target)
        # dont ask me why or how but at some point of that name redirecting the __name__ of this instance is asked for
        # and we expect it to be the wrapped function name
        self.__name__ = self.target.__name__
        try:
            obj = self.obj
        except AttributeError: # if this is not an instance method self.obj is not defined
            exposedFunctionName = self.__name__
        else: # if this is a instance function automatically namspace it
            exposedFunctionName = "%s.%s" % (obj.__name__.lower(), self.__name__)

        apiDispatcher.exposeThis(self, exposedFunctionName)

    #http://stackoverflow.com/questions/8856164/class-decorator-decorating-method-in-python
    def __get__(self, obj, type=None):
        self.obj = obj
        return self

    def __call__(self, *args, **kwargs):
        try:
            obj = self.obj
        except AttributeError: # if this is not an instance method self.obj is not defined
            return self.target(*args, **kwargs)
        else:
            return self.target(obj, *args, **kwargs)


class JSONRPCapi(threading.Thread):

    def __init__(self, port):
        self.server = SimpleJSONRPCServer(('localhost', port))
        self.server.register_instance(apiDispatcher)
        self.server.register_introspection_functions()

        threading.Thread.__init__(self)

    def run(self):
        self.server.serve_forever()

    def register_function(self, *args, **kwargs):
        self.server.register_function(*args, **kwargs)


@expose
def ping(pong):
    return pong


@expose
def schmu():
    return 'schmus'


@expose
def reboot():
    actionManager.executeAction('reboot', 'JSONRPCapi')
