import logging
from logging import StreamHandler

from colorlog import ColoredFormatter

logger = logging.getLogger('xdm')
stream_handler = StreamHandler()
stream_handler.setFormatter(ColoredFormatter(
    '%(asctime)-15s %(log_color)s%(levelname)-8s%(reset)s %(message)s'
))
logger.addHandler(stream_handler)
logger.setLevel(logging.DEBUG)


from pathlib import Path

import tempfile
from unittest.mock import Mock

import pytest

from xdm.application import XDM
from xdm.config import Config
from xdm.config.default import DEFAUL_CONFIG
from xdm.plugin import PluginManager

tmp_dir = str(tempfile.TemporaryDirectory())
test_plugin_folder = Path(__file__).parent / 'plugin' / 'plugins'


DEFAUL_CONFIG['path'] = {
    'config': Path(tmp_dir) / 'xdm.ini',
    'db': Path(tmp_dir) / 'db',
    'plugins': Path(tmp_dir) / 'plugins/'
}

Config.create_directories = Mock()
Config.write_config_file = Mock()


@pytest.yield_fixture
def xdm():
    yield XDM(
        debug=True
    )


@pytest.yield_fixture
def plugin_manager():
    yield PluginManager(None, [test_plugin_folder])
