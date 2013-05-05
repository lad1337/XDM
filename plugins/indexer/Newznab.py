
from xdm.plugins import *
from xdm.helper import replace_all
from lib import requests

class Newznab(Indexer):
    version = "0.1"
    _config = {'host': 'http://nzbs2go.com',
               'apikey': '',
               'port': None,
               'enabled': True,
               'comment_on_download': False,
               'retention': 900,
               }

    types = [common.TYPE_NZB]
    config_meta = {'plugin_desc': 'Generic Newznab indexer.'
                   }

    def _baseUrl(self):
        if not self.c.host.startswith('http'):
            self.c.host = "http://%s" % self.c.host
        if not self.c.port:
            return "%s/api/" % self.c.host
        else:
            return "%s:%s/api/" % (self.c.host, self.c.port)

    def _chooseCat(self, platform):
            return 0

    def searchForElement(self, element):
        payload = {'apikey': self.c.apikey,
                   't': 'search',
                   'maxage': self.c.retention,
                   'cat': self._getCategory(element),
                   'o': 'json'
                   }

        downloads = []
        terms = element.getSearchTerms()
        for term in terms:
            payload['q'] = term
            r = requests.get(self._baseUrl(), params=payload)
            log("Newsnab final search for term %s url %s" % (term, r.url))
            response = r.json()
            #log.info("jsonobj: " +jsonObject)
            if not 'item' in response["channel"]:
                log.info("No search results for %s" % term)
                continue
            items = response["channel"]["item"]
            if type(items).__name__ == 'dict': # we only have on search result
                items = [items]
            for item in items:
                #log.info("item: " + item["title"])
                title = item["title"]
                url = item["link"]
                ex_id = 0
                curSize = 0
                for curAttr in item['attr']:
                    if curAttr['@attributes']['name'] == 'size':
                        curSize = int(curAttr['@attributes']['value'])
                    if curAttr['@attributes']['name'] == 'guid':
                        ex_id = curAttr['@attributes']['value']

                log("%s found on Newznab: %s" % (element.type, title))
                d = Download()
                d.url = url
                d.name = title
                d.element = element
                d.size = curSize
                d.external_id = ex_id
                downloads.append(d)

        return downloads

    def commentOnDownload(self, msg, download):
        payload = {'apikey': self.c.apikey,
                   't': 'commentadd',
                   'id': download.external_id,
                   'text': msg}
        r = requests.get(self._baseUrl(), params=payload)
        log("Newsnab final comment for %s is %s on url %s" % (download.name, msg, r.url))
        if 'error' in r.text:
            log("Error posting the comment: %s" % r.text)
            return False
        log("Comment successful %s" % r.text)
        return True
