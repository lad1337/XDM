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

import datetime
import uuid as uuidModule
from logging import INFO
from logging import WARNING
from logging import CRITICAL
from xdm.logger import *
from operator import attrgetter


class MessageManager(object):
    """Class that manages GUI messages / notifications"""

    def __init__(self):
        self.messages = {}

    def createInfo(self, message, role="system", confirm=None, deny=None, confirmJavascript=None, denyJavascript=None):
        """creates a info message"""
        return self._createMessage(INFO, message, role=role, confirm=confirm, deny=deny, confirmJavascript=confirmJavascript, denyJavascript=denyJavascript)

    def createWarning(self, message, role="system", confirm=None, deny=None, confirmJavascript=None, denyJavascript=None):
        """creates a warning message"""
        return self._createMessage(WARNING, message, role=role, confirm=confirm, deny=deny, confirmJavascript=confirmJavascript, denyJavascript=denyJavascript)

    def _createMessage(self, messageType, message, role="system", confirm=None, deny=None, confirmJavascript=None, denyJavascript=None):

        uuid = str(uuidModule.uuid4())
        m = Message(messageType, message, uuid, role)

        if confirm is not None:
            m.addConfirmAction(MessageAction(confirm))
        if deny is not None:
            m.addDenyAction(MessageAction(deny))
        if confirmJavascript is not None:
            m.addConfirmJavascriptAction(MessageJavascriptAction(confirmJavascript))
        if denyJavascript is not None:
            m.addDenyJavascriptAction(MessageJavascriptAction(denyJavascript))

        self.messages[uuid] = m
        return m

    def _removeMessage(self, uuid):
        if uuid in self.messages:
            log('Message %s(%s) removed' % (self.messages[uuid].text, uuid))
            del self.messages[uuid]

    def confirmMessage(self, uuid):
        result = self.messages[uuid].confirm()
        log('Message %s(%s) confirm' % (self.messages[uuid].text, uuid))
        if result:
            self._removeMessage(uuid)
        return result

    def denyMessage(self, uuid):
        log('Message %s(%s) deny' % (self.messages[uuid].text, uuid))
        if self.messages[uuid].deny is None:
            self.suspendMessage(uuid)
            return True

        result = self.messages[uuid].deny()
        if result:
            self._removeMessage(uuid)
        return result

    def suspendMessage(self, uuid, forMinutes=60):
        self.messages[uuid].suspendFor(forMinutes)
        log('Message %s(%s) suspended till %s' % (self.messages[uuid].text, uuid, self.messages[uuid].showAfterTime))
        return True

    def getMessages(self):
        now = datetime.datetime.now()
        out = []
        for uuid, message in self.messages.items():
            if now > message.showAfterTime:
                out.append(message)
        return sorted(out, key=attrgetter('createTime'))

    def closeMessage(self, uuid):
        m = self.messages[uuid]
        if m is None:
            return
        if m.confirm is None and m.deny is None:
            self._removeMessage(uuid)
        else:
            self.suspendMessage(uuid)
        return True

    def clearRole(self, role):
        for uuid, m in self.messages.items():
            if m.role == role:
                self._removeMessage(uuid)


class Message(object):

    def __init__(self, messageType, text, uuid, role):
        self.messageType = messageType
        self.text = text
        self.createTime = datetime.datetime.now()
        self.showAfterTime = self.createTime
        self.uuid = uuid
        self.role = role
        self.confirm = None
        self.deny = None
        self.confirmJavascript = None
        self.denyJavascript = None

    def addConfirmAction(self, action):
        self.confirm = action

    def addDenyAction(self, action):
        self.deny = action

    def addConfirmJavascriptAction(self, action):
        self.confirmJavascript = action

    def addDenyJavascriptAction(self, action):
        self.denyJavascript = action

    def suspendFor(self, minutes):
        self.showAfterTime = datetime.datetime.now() + datetime.timedelta(minutes=60)

    def getClass(self):
        if self.messageType == INFO:
            return 'info'
        elif self.messageType == WARNING:
            return 'warning'
        elif self.messageType == CRITICAL:
            return 'error'
        return ''


class MessageAction(object):

    def __init__(self, fn, *args, **kwargs):
        self.fn = fn
        self.args = args
        self.kwargs = kwargs

    def __call__(self):
        return self.fn(*self.args, **self.kwargs)


class MessageJavascriptAction(object):

    def __init__(self, callString):
        self.callString = callString


class SystemMessageManager(object):
    """manages system messages mostly used for ajax calls and there messages
    not thread save! ... it is not checked who/what browser session created the message
    """

    def __init__(self):
        self.system_messages = []
        self._read_messages = []

    def reset(self):
        self.system_messages = []
        self._read_messages = []

    def setNewMessage(self, msg, lvl='info'):
        self.system_messages.append((lvl, msg))

    def getLastMessages(self):
        out = []
        for index, message in enumerate(self.system_messages):
            if not index in self._read_messages:
                out.append(message)
                self._read_messages.append(index)
        return out
 