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
import json
import logging
import logging.handlers
import inspect
from jsonHelper import MyEncoder
import xdm
import traceback


lvlNames = {logging.ERROR:          {'c': '   ERROR', 'p': 'ERROR'},
                logging.WARNING:    {'c': ' WARNING', 'p': 'WARING'},
                logging.INFO:       {'c': '    INFO', 'p': 'INFO'},
                logging.DEBUG:      {'c': '   DEBUG', 'p': 'DEBUG'},
                logging.CRITICAL:   {'c': 'CRITICAL', 'p': 'CRITICAL'}
                }


cLogger = logging.getLogger('XDM.Console')
fLogger = logging.getLogger('XDM.File')
cLogger.setLevel(logging.INFO)
fLogger.setLevel(logging.DEBUG)
# create file handler which logs even debug messages
#this is now done in XDM.py to use the data dir
#fh = logging.handlers.RotatingFileHandler('xdm.log', maxBytes=10 * 1024 * 1024, backupCount=5)
# create console handler with a higher log level
ch = logging.StreamHandler()

# add the handlers to logger


cLogger.addHandler(ch)
#fLogger.addHandler(fh)
""" at some point i want the cherrypy stuff logged
cpLogger = logging.getLogger('cherrypy')
cph = logging.StreamHandler()
formatter = logging.Formatter('%(levelname)s| %(asctime)s: %(message)s ')
cph.setFormatter(formatter)
cpLogger.addHandler(cph)
"""


#http://stackoverflow.com/questions/2203424/python-how-to-retrieve-class-information-from-a-frame-object
def get_class_from_frame(fr):
    args, _, _, value_dict = inspect.getargvalues(fr)
    # we check the first parameter for the frame function is
    # named 'self'
    if len(args) and args[0] == 'self':
        # in that case, 'self' will be referenced in value_dict
        instance = value_dict.get('self', None)
        if instance:
            # return its class
            return getattr(instance, '__class__', None)
    # return None otherwise
    return None


class StructuredMessage(object):
    def __init__(self, lvl, message, calframe, **kwargs):
        self.lvl = lvl
        self.message = message
        self.calframe = calframe
        self.kwargs = kwargs
        self.time = datetime.datetime.now()

    def console(self):
        return '%s| %s: %s' % (lvlNames[self.lvl]['c'], self.time, self.message)

    def __str__(self):
        def _json(time, lvl, message, calframe, kwargs={}):
            return json.dumps({'time': time,
                           'lvl': lvlNames[lvl]['p'],
                            'msg': message,
                            'caller': {'file': calframe[2][1], 'line': calframe[2][2], 'fn': calframe[2][3]},
                            'data': kwargs},
                            cls=MyEncoder)

        try:
            return _json(self.time, self.lvl, self.message, self.calframe, self.kwargs)
        except TypeError:
            return _json(self.time, self.lvl, self.message, self.calframe)


class LogWrapper():

    def _log(self, lvl, msg, censor=None, **kwargs):
        if xdm.common.STARTOPTIONS is None or (not xdm.common.STARTOPTIONS.dev):
            if type(censor) == tuple:
                for s in censor:
                    msg = msg.replace(s, '##censored##')
            elif type(censor) == dict:
                for value, name in censor.items():
                    msg = msg.replace(value, '##%s##' % name)
            elif type(censor) == str:
                msg = msg.replace(censor, '##censored##')

        curframe = inspect.currentframe()
        calframe = inspect.getouterframes(curframe, 0)
        sm = StructuredMessage(lvl, msg, calframe, **kwargs)
        cLogger.log(lvl, sm.console())
        fLogger.log(lvl, sm)
        if lvl in (logging.WARNING, logging.ERROR):
            callerClass = get_class_from_frame(calframe[2][0])
            #was the error/warning send by a notifier ?
            if callerClass and callerClass.__bases__ and callerClass.__bases__[0] is not None and 'Notifier' == callerClass.__bases__[0].__name__:
                sm = StructuredMessage(logging.ERROR, 'Error while sending an error message with a notifier %s' % callerClass, calframe, **kwargs)
                cLogger.log(lvl, sm.console())
                fLogger.log(lvl, sm)
            else:
                self.debug('sending %s with notifiers' % lvlNames[lvl]['p'])
                for n in xdm.common.PM.N:
                    if (n.c.on_warning and lvl == logging.WARNING) or (n.c.on_error and lvl == logging.ERROR):
                        n.sendMessage('%s: %s' % (lvlNames[lvl]['p'], msg))

    def error(self, msg, censor=None, **kwargs):
        tb = traceback.format_exc()
        msg = '%s\nTraceback:\n%s' % (msg, tb)
        self._log(logging.ERROR, msg, censor=censor, **kwargs)
        return msg

    def info(self, msg, censor=None, **kwargs):
        self._log(logging.INFO, msg, censor=censor, **kwargs)
        return msg

    def warning(self, msg, censor=None, **kwargs):
        self._log(logging.WARNING, msg, censor=censor, **kwargs)
        return msg

    def debug(self, msg, censor=None, **kwargs):
        self._log(logging.DEBUG, msg, censor=censor, **kwargs)
        return msg

    def critical(self, msg, censor=None, **kwargs):
        self._log(logging.CRITICAL, msg, censor=censor, **kwargs)
        return msg

    def __call__(self, msg, censor=None, **kwargs):
        self._log(logging.DEBUG, msg, censor=censor, **kwargs)
        return msg

log = LogWrapper()


__all__ = ['log']
