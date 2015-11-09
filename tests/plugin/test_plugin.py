from unittest.mock import MagicMock

import pytest

from xdm.plugin.base import Plugin
from xdm.plugin.config import Config
from xdm.plugin.config import Entry


class MyPlugin(Plugin):

    identifier = 'de.lad1337.test.my_plugin'

    config = Config(
        Entry('foo', 'bar', frontend_name='Value for foo'),
        Entry('other_value', 1, int, frontend_name='how many do you want?'),
        Entry('domain', '6box.me')
    )

    @Plugin.register_hook
    def download(self, download):
        return download

    @Plugin.register_hook(identifier='pre_download')
    def before_download(self, download):
        return download


def test_plugin_config(xdm):
    mp = MyPlugin(xdm)
    assert mp.config.get('noob') is None
    assert mp.config.get('noob', True) is True
    with pytest.raises(AttributeError):
        assert mp.config.noob
    assert mp.config.get('domain').value == '6box.me'
    assert mp.config.domain == '6box.me'
    mp.config.domain = 'nzb.su'
    assert mp.config.get('domain').value == 'nzb.su'
    assert mp.config.domain == 'nzb.su'


def test_plugin_decorators():
    mp = MyPlugin(MagicMock())
    assert mp.download.hook
    assert mp.download.identifier == 'download'
    assert mp.download(1) == 1
    assert mp.before_download.hook
    assert mp.before_download.identifier == 'pre_download'
    assert mp.before_download(1) == 1


def test_hooks(plugin_manager):
    plugin_manager.load()
    for downloader in plugin_manager.get_hooks('download'):
        assert downloader(3) == 3


@pytest.mark.gen_test
def test_tasks(plugin_manager):
    plugin_manager.load()
    for searcher in plugin_manager.get_tasks('search_downloads'):
        results = yield searcher()
        assert len([download for download in results]) == 10
