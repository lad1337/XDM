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

from xdm.plugins import *
from lib import requests


class Sabnzbd(Downloader):
    version = "0.2"
    _config = {'port': 8083,
               'host': 'http://localhost',
               'apikey': ''}
    _history = []
    _queue = []
    types = ['de.lad1337.nzb']

    def _baseUrl(self, host='', port=0):
        if not host:
            host = self.c.host
            if not host.startswith('http'):
                log("Fixing url. Adding http://")
                self.c.host = "http://%s" % host
            host = self.c.host
        else:
            if not host.startswith('http'):
                host = "http://%s" % host

        if not port:
            port = self.c.port

        return "%s:%s/sabnzbd/api" % (host, port)

    def addDownload(self, download):
        payload = {'apikey': self.c.apikey,
                 'name': download.url,
                 'nzbname': self._downloadName(download),
                 'mode': 'addurl'
                 }

        cat = self._getCategory(download.element)
        if cat is not None:
            payload['cat'] = cat
        try:
            r = requests.get(self._baseUrl(), params=payload, timeout=10)
        except:
            log.error("Unable to connect to Sanzbd. Most likely a timout. is Sab running")
            return False
        log("final sab url %s" % r.url, censor={self.c.apikey: 'apikey'})
        log("sab response code: %s" % r.status_code)
        log("sab response: %s" % r.text)
        log.info("NZB added to Sabnzbd")
        return True

    def _getHistory(self):

        payload = {'apikey': self.c.apikey,
                   'mode': 'history',
                   'output': 'json'}
        r = requests.get(self._baseUrl(), params=payload)
        log("Sab hitory url %s" % r.url, censor={self.c.apikey: 'apikey'})
        response = r.json()
        self._history = response['history']['slots']
        return self._history

    def _getQueue(self):

        payload = {'apikey': self.c.apikey,
                   'mode': 'qstatus',
                   'output': 'json'}
        r = requests.get(self._baseUrl(), params=payload)
        response = r.json()
        self._queue = response['jobs']
        return self._queue

    def getDownloadPercentage(self, element):
        if not self._queue:
            self._getQueue()
        for i in self._queue:
            element_id = self._findGamezID(i['filename'])
            if element_id != element.id:
                continue

            percentage = 100 - ((i['mbleft'] / i['mb']) * 100)
            return percentage
        else:
            0

    def getElementStaus(self, element):
        """returns a Status and path"""
        #log("Checking for status of %s in Sabnzbd" % element)
        download = Download()
        download.status = common.UNKNOWN
        if not self._history:
            self._getHistory()
        if not self._queue:
            self._getQueue()
        for curListIdentifier, curList in (('filename', self._queue), ('name', self._history)):
            for i in curList:
                element_id = self._findGamezID(i[curListIdentifier])
                download_id = self._findDownloadID(i[curListIdentifier])
                #log("Game ID: %s Download ID: %s" % (game_id, download_id))
                if element_id != element.id:
                    continue

                try:
                    download = Download.get(Download.id == download_id)
                except Download.DoesNotExist:
                    pass
                if curListIdentifier == 'filename': # if we found it in the queue we are downloading it !
                    return (common.DOWNLOADING, download, '')

                if i['status'] == 'Completed':
                    return (common.DOWNLOADED, download, i['storage'])
                elif i['status'] == 'Failed':
                    return (common.FAILED, download, '')
                else:
                    return (common.SNATCHED, download, '')
        else:
            return (common.UNKNOWN, download, '')

    @profileMeMaybe
    def _testConnection(self, host, port, apikey):
        payload = {'mode': 'version',
                   'output': 'json'}
        try:
            requests.get(self._baseUrl(host, port), params=payload, timeout=10)
        except requests.Timeout:
            return (False, {}, 'Connetion failure: Timeout. Check host and port.')
        except requests.ConnectionError:
            return (False, {}, 'Connetion failure: ConnectionError. Check host and port.')

        payload['mode'] = 'queue'
        payload['apikey'] = apikey
        r = requests.get(self._baseUrl(host, port), params=payload, timeout=20)
        response = r.json()
        log("Sab test url %s" % r.url, censor={self.c.apikey: 'apikey'})
        if 'status' in response and not response['status']:
            return (False, {}, 'Connetion failure: %s' % response['error'])
        elif 'queue' in response:
            return (True, {}, 'Connetion Established!')
        else:
            return (False, {}, 'We got some strange message from sab. I guess this wont work :/')
    _testConnection.args = ['host', 'port', 'apikey']

    config_meta = {'plugin_desc': 'Sabnzb downloader. Send Nzbs and check for status',
                   'plugin_buttons': {'test_connection': {'action': _testConnection, 'name': 'Test connection'}},
                   'host': {'on_live_change': _testConnection},
                   'port': {'on_live_change': _testConnection},
                   'apikey': {'on_live_change': _testConnection}
                   }
