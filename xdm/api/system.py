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

from xdm import actionManager, common, tasks
from xdm import api


@api.expose
def shutdown():
    """just return True and starts a thread to shutdown XDM"""
    common.SM.reset()
    t = tasks.TaskThread(actionManager.executeAction, 'shutdown', 'JSONRPCapi')
    t.start()
    return True
shutdown.signature = [['bool']]


@api.expose
def reboot():
    """just return True and starts a thread to reboot XDM"""
    common.SM.reset()
    t = tasks.TaskThread(actionManager.executeAction, 'reboot', 'JSONRPCapi')
    t.start()
    return True
reboot.signature = [['bool']]


@api.expose
def listMethods():
    return api.apiDispatcher.getExposedMethods()
listMethods.signature = [['array']]


@api.expose
def methodSignature(mehtodeName='system.methodSignature'):
    try:
        fn = api.apiDispatcher.getFunction(mehtodeName)
    except KeyError:
        return []
    return fn.signature
methodSignature.signature = [['array', 'string'], ['array']]


@api.expose
def methodHelp(mehtodeName='system.methodHelp'):
    """This method returns a text description of a particular method.
    The method takes one parameter, a string. Its value is the name of
    the jsonrpc method about which information is being requested.
    The result is a string. The value of that string is a text description,
    for human use, of the method in question.

    Keyword arguments:
    mehtodeName -- str The name of the method (default 'system.methodHelp')
    Return:
    str The documentation text of the method.
    """
    try:
        fn = api.apiDispatcher.getFunction(mehtodeName)
    except KeyError:
        return 'No such method!'
    return fn.help
methodHelp.signature = [['string', 'string'], ['string']]


@api.expose
def getActiveMediaTypes():
    return [mtm.identifier for mtm in common.PM.MTM]
methodSignature.signature = [['array']]
