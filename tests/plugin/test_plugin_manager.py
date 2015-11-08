from conftest import test_plugin_folder

from xdm.plugin.base import Plugin


def test_plugin_manager(plugin_manager):
    assert {str(test_plugin_folder)} == plugin_manager.paths
    assert plugin_manager.load()
    assert len(plugin_manager._hooks['download']) == 2


def test_import_error(plugin_manager):  # noqa
    class BrokenPlugin(Plugin):

        def __init__(self, app):
            super(BrokenPlugin, self).__init__(app)
            import foo  # noqa

    assert not plugin_manager.register(BrokenPlugin)


def test_plugin_hooks(plugin_manager):
    plugin_manager.load()
    assert not plugin_manager.get_hooks('foo')
    assert plugin_manager.get_hooks('foo', [1]) == [1]
    assert len(plugin_manager.get_hooks('download')) == 2
    assert len(plugin_manager.get_hooks('pre_download')) == 1


def test_plugin_tasks(plugin_manager):
    plugin_manager.load()
