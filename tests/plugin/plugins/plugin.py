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

    @Plugin.register_hook
    def download(self, download):
        return download

    @Plugin.register_task
    def search_downloads(self):
        for i in range(10):
            yield Download({
                'link': 'foo',
                'name': 'download number %s' % i
            })

    @coroutine
    @Plugin.register_task
    def search_element(self):
        for i in range(10):
            yield Element({
                'link': 'foo',
                'name': 'download number %s' % i
            })
