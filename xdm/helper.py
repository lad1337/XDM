# -*- coding: utf-8 -*-
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

import os
import re
import sys
import webbrowser
import math
from logger import *
from datetime import datetime
import inspect
import urllib
from xdm import common
import xdm
import shutil


def getSystemDataDir(progdir):
    if sys.platform == 'darwin':
        home = os.environ.get('HOME')
        if home:
            return '%s/Library/Application Support/XDM' % home
        else:
            return progdir
    elif sys.platform == "win32":
        #TODO: implement
        return progdir

def replace_some(text):
    dic = {' ': '_', '(': '', ')': '', '.': '_'}
    return replace_x(text, dic)


def replace_all(text):
    dic = {'...':'', ' & ':' ', ' = ': ' ', '?':'', '$':'s', ' + ':' ', '"':'', ',':'', '*':'', '.':'', ':':'', "'":''}	
    return replace_x(text, dic)


def replace_x(text, dic):
    text = u'%s' % text
    for i, j in dic.iteritems():
        text = text.replace(i, j)
    return text


def fileNameClean(text):
    dic = {'<': '', '>': '', ':': '', '"': '', '/':'', '\\':'', '|':'', '?':'', '*':''}
    return replace_x(text, dic)


def replaceUmlaute(text):
    return replace_x(text, {u'ü': u'ue', u'ä': u'ae', u'ö': 'oe',
                            u'Ü': u'UE', u'Ä': u'AE', u'Ö': 'OE',
                            u'ß': 'ss'})


def statusLabelClass(status):
    if status == common.UNKNOWN:
        return 'label'
    elif status == common.SNATCHED:
        return 'label label-info'
    elif status in (common.DOWNLOADED, common.COMPLETED):
        return 'label label-success'
    elif status == common.FAILED:
        return 'label label-important'
    elif status == common.PP_FAIL:
        return 'label label-warning'
    else:
        return 'label'


# form couchpotato
def launchBrowser(host, port,https):

    if host == '0.0.0.0':
        host = 'localhost'

    if(https == '1'):
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


# looks if adress contain https

def ControlHost(host):
    
    if 'https' in host:
        checkedhost = host
    elif 'http' in host:
        checkedhost = host
    else:
        checkedhost = "http://" + host
    
    return checkedhost


# Code from Sickbeard
def create_https_certificates(ssl_cert, ssl_key):
    """
    Create self-signed HTTPS certificares and store in paths 'ssl_cert' and 'ssl_key'
    """
    try:
        from OpenSSL import crypto
        from lib.certgen import createKeyPair, createCertRequest, createCertificate, TYPE_RSA, serial
    except ImportError:
        log.error("pyopenssl module missing, please install for https access")
        return False

    # Create the CA Certificate
    cakey = createKeyPair(TYPE_RSA, 1024)
    careq = createCertRequest(cakey, CN='Certificate Authority')
    cacert = createCertificate(careq, (careq, cakey), serial, (0, 60*60*24*365*10)) # ten years

    cname = 'Gamez'
    pkey = createKeyPair(TYPE_RSA, 1024)
    req = createCertRequest(pkey, CN=cname)
    cert = createCertificate(req, (cacert, cakey), serial, (0, 60*60*24*365*10)) # ten years

    # Save the key and certificate to disk
    try:
        open(ssl_key, 'w').write(crypto.dump_privatekey(crypto.FILETYPE_PEM, pkey))
        open(ssl_cert, 'w').write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert))
    except:
        log("Error creating SSL key and certificate")
        return False

    return True


#https://gist.github.com/deontologician/3503910
def reltime(date, compare_to=None, at=':'):
    r'''Takes a datetime and returns a relative representation of the
    time.
    :param date: The date to render relatively
    :param compare_to: what to compare the date to. Defaults to datetime.now()
    :param at: date/time separator. defaults to "@". "at" is also reasonable.
 
    >>> from datetime import datetime, timedelta
    >>> today = datetime(2050, 9, 2, 15, 00)
    >>> earlier = datetime(2050, 9, 2, 12)
    >>> reltime(earlier, today)
    'today @ 12pm'
    >>> yesterday = today - timedelta(1)
    >>> reltime(yesterday, compare_to=today)
    'yesterday @ 3pm'
    >>> reltime(datetime(2050, 9, 1, 15, 32), today)
    'yesterday @ 3:32pm'
    >>> reltime(datetime(2050, 8, 31, 16), today)
    'Wednesday @ 4pm (2 days ago)'
    >>> reltime(datetime(2050, 8, 26, 14), today)
    'last Friday @ 2pm (7 days ago)'
    >>> reltime(datetime(2049, 9, 2, 12, 00), today)
    'September 2nd, 2049 @ 12pm (last year)'
    >>> today = datetime(2012, 8, 29, 13, 52)
    >>> last_mon = datetime(2012, 8, 20, 15, 40, 55)
    >>> reltime(last_mon, today)
    'last Monday @ 3:40pm (9 days ago)'
    '''
    def ordinal(n):
        r'''Returns a string ordinal representation of a number
        Taken from: http://stackoverflow.com/a/739301/180718
        '''
        if 10 <= n % 100 < 20:
            return str(n) + 'th'
        else:
            return str(n) + {1 : 'st', 2 : 'nd', 3 : 'rd'}.get(n % 10, "th")
 
    compare_to = compare_to or datetime.now()
    if date > compare_to:
        return NotImplementedError('reltime only handles dates in the past')
    #get timediff values
    diff = compare_to - date
    if diff.seconds < 60 * 60 * 8: #less than a business day?
        days_ago = diff.days
    else:
        days_ago = diff.days + 1
    months_ago = compare_to.month - date.month
    years_ago = compare_to.year - date.year
    weeks_ago = int(math.ceil(days_ago / 7.0))
    #get a non-zero padded 12-hour hour
    hr = date.strftime('%I')
    if hr.startswith('0'):
        hr = hr[1:]
    wd = compare_to.weekday()
    #calculate the time string
    if date.minute == 0:
        time = '{0}{1}'.format(hr, date.strftime('%p').lower())
    else:
        time = '{0}:{1}'.format(hr, date.strftime('%M%p').lower())
    #calculate the date string
    if days_ago == 0:
        datestr = 'today {at} {time}'
    elif days_ago == 1:
        datestr = 'yesterday {at} {time}'
    elif (wd in (5, 6) and days_ago in (wd+1, wd+2)) or \
            wd + 3 <= days_ago <= wd + 8:
        #this was determined by making a table of wd versus days_ago and
        #divining a relationship based on everyday speech. This is somewhat
        #subjective I guess!
        datestr = 'last {weekday} {at} {time} ({days_ago} days ago)'
    elif days_ago <= wd + 2:
        datestr = '{weekday} {at} {time} ({days_ago} days ago)'
    elif years_ago == 1:
        datestr = '{month} {day}, {year} {at} {time} (last year)'
    elif years_ago > 1:
        datestr = '{month} {day}, {year} {at} {time} ({years_ago} years ago)'
    elif months_ago == 1:
        datestr = '{month} {day} {at} {time} (last month)'
    elif months_ago > 1:
        datestr = '{month} {day} {at} {time} ({months_ago} months ago)'
    else: 
        #not last week, but not last month either
        datestr = '{month} {day} {at} {time} ({days_ago} days ago)'
    return datestr.format(time=time,
                          weekday=date.strftime('%A'),
                          day=ordinal(date.day),
                          days=diff.days,
                          days_ago=days_ago,
                          month=date.strftime('%B'),
                          years_ago=years_ago,
                          months_ago=months_ago,
                          weeks_ago=weeks_ago,
                          year=date.year,
                          at=at)


#http://code.activestate.com/recipes/576644-diff-two-dictionaries/
KEYNOTFOUND = '<KEYNOTFOUND>'       # KeyNotFound for dictDiff


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
        pid = os.fork()  # @UndefinedVariable - only available in UNIX
        if pid != 0:
            sys.exit(0)
    except OSError, e:
        raise RuntimeError("1st fork failed: %s [%d]" % (e.strerror, e.errno))

    os.setsid()  # @UndefinedVariable - only available in UNIX

    # Make sure I can read my own files and shut out others
    prev = os.umask(0)
    os.umask(prev and int('077', 8))

    # Make the child a session-leader by detaching from the terminal
    try:
        pid = os.fork()  # @UndefinedVariable - only available in UNIX
        if pid != 0:
            sys.exit(0)
    except OSError, e:
        raise RuntimeError("2nd fork failed: %s [%d]" % (e.strerror, e.errno))

    dev_null = file('/dev/null', 'r')
    os.dup2(dev_null.fileno(), sys.stdin.fileno())


def getSystemDataDir(progdir):
    if sys.platform == 'darwin':
        home = os.environ.get('HOME')
        if home:
            return '%s/Library/Application Support/XDM' % home
        else:
            return progdir
    elif sys.platform == "win32":
        #TODO: implement
        return progdir


def cleanTempFolder():
    shutil.rmtree(xdm.TEMPPATH)
    os.mkdir(xdm.TEMPPATH)


def getContainerTpl():
    return '<div class="{{type}}">{{children}}<div class="clearfix"></div></div>'


def getLeafTpl():
    return '{{this.getName()}}<br>'

def webVars(obj):
    return vars(obj)

