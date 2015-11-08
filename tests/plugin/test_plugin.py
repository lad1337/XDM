from xdm.plugin.base import Plugin


class MyPlugin(Plugin):

    @Plugin.register_hook
    def download(self, download):
        return download

    @Plugin.register_hook(identifier='pre_download')
    def before_download(self, download):
        return download


def test_plugin_decorators():
    mp = MyPlugin(None)
    assert mp.download.hook
    assert mp.download.identifier == 'download'
    assert mp.download(1) == 1
    assert mp.before_download.hook
    assert mp.before_download.identifier == 'pre_download'
    assert mp.before_download(1) == 1


def test_plugin_hooks(plugin_manager):
    for downloader in plugin_manager.get_hooks('download'):
        assert downloader(3) == 3
