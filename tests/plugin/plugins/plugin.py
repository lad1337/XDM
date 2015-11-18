from datetime import timedelta

from tornado.gen import coroutine

from xdm.model import Download
from xdm.model import Element
from xdm.plugin.base import Plugin


class MyPlugin(Plugin):

    @Plugin.register_hook
    def download(self, download):
        return download

    @Plugin.register_hook(identifier='pre_download')
    def before_download(self, download):
        return download


class MyPlugin2(Plugin):

    identifier = 'de.lad1337.test_plugin2'

    @Plugin.register_hook
    def download(self, download):
        return download

    @coroutine
    @Plugin.register_task
    def search_downloads(self):
        results = []
        for i in range(10):
            results.append(Download({
                'link': 'foo',
                'name': 'download number %s' % i
            }))
        return results

    @Plugin.register_task(identifier='update_elements')
    def search_element(self):
        return Element({
            'link': 'foo',
            'name': 'Element name'
        })

    @coroutine
    @Plugin.register_task(interval=timedelta(seconds=1))
    def clean_db(self):
        self.logger.info('Cleaning the DB')
        self.app.side_effect = True
        return
