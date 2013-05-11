from xdm.plugins import *
from lib import requests


class Sabnzbd(Downloader):
    version = "0.2"
    _config = {'port': 8083,
               'host': 'http://localhost',
               'apikey': ''}
    _history = []
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
        log("final sab url %s" % r.url)
        log("sab response code: %s" % r.status_code)
        log("sab response: %s" % r.text)
        log.info("NZB added to Sabnzbd")
        return True

    def _getHistory(self):

        payload = {'apikey': self.c.apikey,
                   'mode': 'history',
                   'output': 'json'}
        r = requests.get(self._baseUrl(), params=payload)
        log("Sab hitory url %s" % r.url)
        response = r.json()
        self._history = response['history']['slots']
        return self._history

    def getElementStaus(self, element):
        """returns a Status and path"""
        #log("Checking for status of %s in Sabnzbd" % element)
        download = Download()
        download.status = common.UNKNOWN
        if not self._history:
            self._getHistory()
        for i in self._history:
            #log("Sab slot: " + i['name'])
            game_id = self._findGamezID(i['name'])
            download_id = self._findDownloadID(i['name'])
            #log("Game ID: %s Download ID: %s" % (game_id, download_id))
            if not game_id:
                #log("Sab slot: " + i['name'] + " no Gamez ID found")
                continue
            slot_game = None
            try:
                slot_game = Element.get(Element.id == game_id)
            except Element.DoesNotExist:
                continue
            # i dont think this is needed
            if slot_game is None:
                continue
            if slot_game.id != element.id:
                continue #wrong slot

            try:
                download = Download.get(Download.id == download_id)
            except Download.DoesNotExist:
                pass

            if i['status'] == 'Completed':
                return (common.DOWNLOADED, download, i['storage'])
            elif i['status'] == 'Failed':
                return (common.FAILED, download, '')
            else:
                return (common.SNATCHED, download, '')
        else:
            return (common.UNKNOWN, download, '')

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
        if 'status' in response and not response['status']:
            return (False, {}, 'Connetion failure: %s' % response['error'])
        elif 'queue' in response:
            return (True, {}, 'Connetion Established!')
        else:
            return (False, {}, 'We got some strange message from sab. I guess this wont work :/')


    config_meta = {'plugin_desc': 'Sabnzb downloader. Send Nzbs and check for status',
                   'plugin_buttons': {'test_connection': {'action': _testConnection, 'name': 'Test connection'}},
                   'host': {'on_live_change': _testConnection},
                   'port': {'on_live_change': _testConnection},
                   'apikey': {'on_live_change': _testConnection}
                   }
