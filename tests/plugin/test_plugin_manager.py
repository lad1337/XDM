from pathlib import Path
from unittest.mock import Mock

from xdm.plugin import PluginManager

test_plugin_folder = Path(__file__).parent / 'plugins'


def test_plugin_manager():
    pm = PluginManager(Mock(), [test_plugin_folder])
    assert {str(test_plugin_folder)} == pm.paths
    assert pm.load()
    plugin = pm._classes.pop()
    assert pm._hooks['download'][0] == plugin
