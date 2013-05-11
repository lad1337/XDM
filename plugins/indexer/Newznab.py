
from xdm.plugins import *
from xdm.helper import replace_all
from lib import requests
from xdm import helper


class Newznab(Indexer):
    version = "0.1"
    _config = {'host': 'http://nzbs2go.com',
               'apikey': '',
               'port': None,
               'enabled': True,
               'comment_on_download': False,
               'retention': 900,
               }

    types = ['de.lad1337.nzb']

    def _baseUrl(self, host, port=None):
        if not host.startswith('http'):
            host = 'http://%s' % host
        if port:
            return "%s:%s/api" % (host, port)
        return "%s/api" % host

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
            r = requests.get(self._baseUrl(self.c.host, self.c.port), params=payload)
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
                d.type = 'de.lad1337.nzb'
                downloads.append(d)

        return downloads

    def commentOnDownload(self, msg, download):
        payload = {'apikey': self.c.apikey,
                   't': 'commentadd',
                   'id': download.external_id,
                   'text': msg}
        r = requests.get(self._baseUrl(self.c.host, self.c.port), params=payload)
        log("Newsnab final comment for %s is %s on url %s" % (download.name, msg, r.url))
        if 'error' in r.text:
            log("Error posting the comment: %s" % r.text)
            return False
        log("Comment successful %s" % r.text)
        return True

    def _testConnection(self, host, port, apikey):
        payload = {'apikey': apikey,
           't': 'search',
           'o': 'json',
           'q': 'testing_apikey'
           }
        try:
            r = requests.get(self._baseUrl(host, port), params=payload)
        except:
            return (False, {}, 'Please check host!')
        if 'Incorrect user credentials' in r.text:
            return (False, {}, 'Wrong apikey!')

        return (True, {}, 'Connection made!')

    # this is neither clean nor pretty
    # but its just a gimick and should illustrate how to use ajax calls that send data back
    def _gatherCategories(self, host, port):
        payload = {'t': 'caps',
                   'o': 'json'
                   }
        r = requests.get(self._baseUrl(self.c.host, self.c.port), params=payload)

        data = {}
        for cat in r.json()['categories']['category']:
            name = cat['@attributes']['name']
            id = cat['@attributes']['id']
            for config in self.c.configs:
                if config.name in data:
                    continue
                if self.useConfigsForElementsAs.lower() in config.name.lower():
                    if config.name.lower().endswith(name.lower()):
                        data[config.name] = id

            for subcat in cat['subcat']:
                if type(subcat) is not dict:
                    continue
                if '@attributes' not in subcat:
                    continue
                if 'name' not in subcat['@attributes']:
                    continue
                subName = subcat['@attributes']['name']
                subID = subcat['@attributes']['id']
                for config in self.c.configs:
                    if config.name in data:
                        continue
                    if self.useConfigsForElementsAs.lower() in config.name.lower():
                        if config.name.lower().endswith(subName.lower()):
                            data[config.name] = subID

        dataWrapper = {'callFunction': 'newsznab_' + self.instance + '_spreadCategories',
                       'functionData': data}

        return (True, dataWrapper, 'I found %s categories' % len(data))

    def getConfigHtml(self):
        return """<script>
                function newsznab_""" + self.instance + """_spreadCategories(data){
                  console.log(data);
                  $.each(data, function(k,i){
                      $('#""" + helper.replace_some(self.name) + """ input[name$="'+k+'"]').val(i)
                  });
                };
                </script>
        """

    config_meta = {'plugin_desc': 'Generic Newznab indexer.',
                   'plugin_buttons': {'gather_gategories': {'action': _gatherCategories, 'name': 'Get categories. Experimental!'},
                                      'test_connection': {'action': _testConnection, 'name': 'Test connection'}},
                   }

