# -*- coding: utf-8 -*-
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

import os
import re
import sys
import json
import webbrowser
from logger import *
from datetime import datetime, timedelta
from xdm import common
import xdm
import shutil

import base64
import random
import hashlib
from babel.dates import format_timedelta
import urllib


def getSystemDataDir(progdir):
    if sys.platform == 'darwin':
        home = os.environ.get('HOME')
        if home:
            return '%s/Library/Application Support/XDM' % home
        else:
            return progdir
    elif sys.platform == "win32":
        # TODO: implement
        return progdir


def replace_some(text):
    dic = {' ': '_', '(': '', ')': '', '.': '_'}
    return replace_x(text, dic)


def idSafe(text):
    dic = {' ': '_', '(': '', ')': '', '.': '_', ':': '_'}
    return replace_x(text, dic)


def replace_all(text):
    dic = {'...':'', ' & ':' ', ' = ': ' ', '?':'', '$':'s', ' + ':' ', '"':'', ',':'', '*':'', '.':'', ':':'', "'":'', "#":''}
    return replace_x(text, dic)

def turn_into_ascii(string):
    return string.encode("ascii", 'ignore')

def replace_x(text, dic):
    text = u'%s' % text
    for bad, good in dic.iteritems():
        text = text.replace(bad, good)
    return text


def fileNameClean(text):
    dic = {'<': '', '>': '', ':': '', '"': '', '/': '', '\\': '', '|': '', '?': '', '*': ''}
    return replace_x(text, dic)


def replaceUmlaute(text):
    return replace_x(text, {u'ü': u'ue', u'ä': u'ae', u'ö': 'oe',
                            u'Ü': u'Ue', u'Ä': u'Ae', u'Ö': 'Oe',
                            u'ß': 'ss'})


def statusLabelClass(status):
    if status == common.UNKNOWN:
        return 'label'
    elif status == common.SNATCHED:
        return 'label label-info'
    elif status in (common.DOWNLOADED, common.COMPLETED, common.DOWNLOADING):
        return 'label label-success'
    elif status == common.FAILED:
        return 'label label-important'
    elif status == common.PP_FAIL:
        return 'label label-warning'
    else:
        return 'label'


# form couchpotato
def launchBrowser(host, port, https):

    if host == '0.0.0.0':
        host = 'localhost'

    if https:
        url = 'https://%s:%d' % (host, int(port))
    else:
        url = 'http://%s:%d' % (host, int(port))
    try:
        webbrowser.open(url, 2, 1)
    except:
        try:
            webbrowser.open(url, 1, 1)
        except:
            log.error('Could not launch a browser.')


# Code from Sickbeard
def create_https_certificates(ssl_cert, ssl_key):
    """
    Create self-signed HTTPS certificares and store in paths 'ssl_cert' and 'ssl_key'
    """
    try:
        from OpenSSL import crypto
        from certgen import createKeyPair, createCertRequest, createCertificate, TYPE_RSA, serial
    except ImportError:
        log.error("pyopenssl module missing, please install for https access\n try\n $ easy_install PyOpenSSL")
        return False

    # Create the CA Certificate
    cakey = createKeyPair(TYPE_RSA, 1024)
    careq = createCertRequest(cakey, CN='Certificate Authority')
    cacert = createCertificate(careq, (careq, cakey), serial, (0, 60 * 60 * 24 * 365 * 10)) # ten years

    cname = 'XDM'
    pkey = createKeyPair(TYPE_RSA, 1024)
    req = createCertRequest(pkey, CN=cname)
    cert = createCertificate(req, (cacert, cakey), serial, (0, 60 * 60 * 24 * 365 * 10)) # ten years

    # Save the key and certificate to disk
    try:
        open(ssl_key, 'w').write(crypto.dump_privatekey(crypto.FILETYPE_PEM, pkey))
        open(ssl_cert, 'w').write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert))
    except:
        log("Error creating SSL key and certificate")
        return False

    return True


def updateCherrypyPluginDirs():
    log("Updating static paths.")
    pluginResPaths = {}
    for identifier, info in common.PM.path_cache.items():
        # NOTE: this pattern is also used in xdm.plugins.bases.myUrl()
        url = "/%s.v%s" % (identifier, info['version'])
        pluginResPaths[url] = {'tools.staticdir.on': True, 'tools.staticdir.dir': os.path.abspath(info['path'])}
    common.PUBLIC_PATHS.extend(pluginResPaths.keys())
    common.PUBLIC_PATHS = list(set(common.PUBLIC_PATHS))
    if common.CHERRYPY_APP is not None:
        common.CHERRYPY_APP.merge(pluginResPaths)
    else:
        log.error("Setting the static plugins folder for the server failed, there is no CHERRYPY_APP.")


def reltime(date):
    if date == common.FAKEDATE or not date:
        return "unknown"
    # FIXME use isinstance() ... but test it
    if type(date).__name__ not in ('date', 'datetime'):
        return "reltime needs a date or datetime we got: '%s'" % repr(date)
    return format_timedelta(date - datetime.now(), locale=common.getLocale(), add_direction=True)

# http://code.activestate.com/recipes/576644-diff-two-dictionaries/
KEYNOTFOUND = '<KEYNOTFOUND>' # KeyNotFound for dictDiff


def dict_diff(first, second):
    """ Return a dict of keys that differ with another config object.  If a value is
        not found in one fo the configs, it will be represented by KEYNOTFOUND.
        @param first:   Fist dictionary to diff.
        @param second:  Second dicationary to diff.
        @return diff:   Dict of Key => (first.val, second.val)
    """
    diff = {}
    # Check all keys in first dict
    for key in first.keys():
        if (not key in second):
            diff[key] = (first[key], KEYNOTFOUND)
        elif (first[key] != second[key]):
            diff[key] = (first[key], second[key])
    # Check all keys in second dict to find missing
    for key in second.keys():
        if (not key in first):
            diff[key] = (KEYNOTFOUND, second[key])
    return diff


# taken from Sick-Beard
# https://github.com/midgetspy/Sick-Beard/
# i dont know how this works but is does work pretty well !
def daemonize():
    """
    Fork off as a daemon
    """

    # pylint: disable=E1101
    # Make a non-session-leader child process
    try:
        pid = os.fork() # @UndefinedVariable - only available in UNIX
        if pid != 0:
            sys.exit(0)
    except OSError, e:
        raise RuntimeError("1st fork failed: %s [%d]" % (e.strerror, e.errno))

    os.setsid() # @UndefinedVariable - only available in UNIX

    # Make sure I can read my own files and shut out others
    prev = os.umask(0)
    os.umask(prev and int('077', 8))

    # Make the child a session-leader by detaching from the terminal
    try:
        pid = os.fork() # @UndefinedVariable - only available in UNIX
        if pid != 0:
            sys.exit(0)
    except OSError, e:
        raise RuntimeError("2nd fork failed: %s [%d]" % (e.strerror, e.errno))

    dev_null = file('/dev/null', 'r')
    os.dup2(dev_null.fileno(), sys.stdin.fileno())


def cleanTempFolder():
    shutil.rmtree(xdm.TEMPPATH)
    os.mkdir(xdm.TEMPPATH)


def getContainerTpl():
    return '<div class="{{type}}">{{children}}<div class="clearfix"></div></div>'


def getLeafTpl():
    return '{{this.getName()}}<br>'


def webVars(obj):
    return vars(obj)


def generateApiKey():
    return base64.b64encode(hashlib.sha256(str(random.getrandbits(256))).digest(), random.choice(['rA', 'aZ', 'gQ', 'hH', 'hG', 'aR', 'DD'])).rstrip('==')


def dereferMe(url):
    if common.SYSTEM.c.use_derefer_me:
        return "http://www.dereferer.org/?%s" % urllib.quote(url, "")
    return url


def dereferMeText(html):
    if not common.SYSTEM.c.use_derefer_me:
        return html
    urls = re.findall(r'href=[\'"]?([^\'" >]+)', html)
    for url in urls:
        html = re.sub(r'href=([\'"])%s([\'"])' % url, r'href=\1%s\1' % dereferMe(url), html)
    return html

# FIXME: this is like O(N^2)!
def getNewNodes(old_tree, new_tree, tag):
    new_nodes = []
    for node in new_tree.decendants:
        old_node = findOldNode(node, old_tree, tag)
        if old_node is None:
            new_nodes.append(node)
    return new_nodes

def findOldNode(node, root, tag):
    new_XDMID = node.getXDMID(tag)
    # print "looking for node with XDMID: %s" % new_XDMID
    for old_node in [root] + root.decendants:
        # print "new: %s vs %s" % (new_XDMID, old_node.getXDMID(tag))
        if old_node.getXDMID(tag) == new_XDMID:
            return old_node
    return None

def sameElements(a, b):
    """b is considered the new version"""
    if a.type != b.type:
        return False

    a_fields = list(a.fields)
    b_fields = list(b.fields)
    a_fields_dict = {f.name:f.value for f in a_fields}
    b_fields_dict = {f.name:f.value for f in b_fields}

    for b_name, b_value in b_fields_dict.items():
        if not b_name in a_fields_dict:
            return False
        if b_value != a_fields_dict[b_name]:
            return False
    return True

def convertV(cur_v):
    """helper function to convert kwargs to python typed values"""
    try:
        f = float(cur_v)
        if f.is_integer():
            return int(f)
        return f
    except TypeError: # its a list for bools / checkboxes "on" and "off"... "on" is only send when checked "off" is always send
        return True
    except ValueError:
        if cur_v in ('None', 'off'):
            cur_v = False
        return cur_v

def guiGlobals(self):
    return {'mtms': common.PM.MTM,
            'system': common.SYSTEM,
            'PM': common.PM,
            'common': common,
            'messages': common.MM.getMessages(),
            'webRoot': common.SYSTEM.c.webRoot}


releaseThresholdDelta = {1: timedelta(days=1),
                        2: timedelta(days=2),
                        3: timedelta(days=7), # a week
                        4: timedelta(days=30), # a month
                        5: timedelta(days=60)} # two months


def spreadConfigsFromFile(options, config_file_path):
    if not os.path.isfile(config_file_path):
        log.warning("Can't find config file at {}".format(config_file_path))
        return options
    with open(config_file_path, "r") as config_file:
        try:
            config = json.loads(config_file.read())
        except:
            log.critical("Looks like i could not parse the config file!")
            raise
    common.updateConfigOverwrite(config)
    # TODO: create a XDM name space in config and use these as args
    # if they have not been set by args
    pre_run_system_settings_fields = ("port", "api_port", "socket_host",
        "dont_open_browser", "login_user", "login_password", "datadir")
    if options.systemIdentifer in config and "Default" in config[options.systemIdentifer]:
        pre_run_system_settings = config[options.systemIdentifer]["Default"]
        for field in pre_run_system_settings_fields:
            if field in pre_run_system_settings:
                setattr(options, field, pre_run_system_settings[field])
    return options


# http://code.activestate.com/recipes/440514-dictproperty-properties-for-dictionary-attributes/
class dictproperty(object):

    class _proxy(object):

        def __init__(self, obj, fget, fset, fdel, fiter):
            self._obj = obj
            self._fget = fget
            self._fset = fset
            self._fdel = fdel
            self._fiter = fiter

        def __getitem__(self, key):
            if self._fget is None:
                raise TypeError, "can't read item"
            return self._fget(self._obj, key)

        def __setitem__(self, key, value):
            if self._fset is None:
                raise TypeError, "can't set item"
            self._fset(self._obj, key, value)

        def __delitem__(self, key):
            if self._fdel is None:
                raise TypeError, "can't delete item"
            self._fdel(self._obj, key)

        def __contains__(self, key):
            if self._fget is None:
                raise TypeError, "can't read item"
            try:
                self._fget(self._obj, key)
                return True
            except KeyError:
                return False

        def __iter__(self):
              return self._fiter(self._obj)

        def items(self):
            return [(key, self[key]) for key in self._fiter(self._obj)]

    def __init__(self, fget=None, fset=None, fdel=None, fiter=None, doc=None):
        self._fget = fget
        self._fset = fset
        self._fdel = fdel
        self._fiter = fiter
        self.__doc__ = doc

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        return self._proxy(obj, self._fget, self._fset, self._fdel, self._fiter)


