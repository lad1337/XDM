import logging
from logging import StreamHandler
from unittest.mock import MagicMock

from colorlog import ColoredFormatter


def init_logging():
    logger = logging.getLogger('xdm')
    stream_handler = StreamHandler()
    stream_handler.setFormatter(ColoredFormatter(
        '%(asctime)-15s %(log_color)s%(levelname)-8s%(reset)s %(message)s'
    ))
    logger.addHandler(stream_handler)
    logger.setLevel(logging.DEBUG)


def reset_logging():
    logger = logging.getLogger('xdm')
    for handler in logger.handlers:
        logger.removeHandler(handler)


init_logging()

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
    'element_db': Path(tmp_dir) / 'element_db',
    'config_db': Path(tmp_dir) / 'config_db',
    'plugins': Path(tmp_dir) / 'plugins/'
}

Config.create_directories = Mock()
Config.write_config_file = Mock()


@pytest.fixture
def fix_logging_handlers():
    reset_logging()
    init_logging()


@pytest.yield_fixture
def xdm():
    reset_logging()
    yield XDM(
        debug=True
    )


@pytest.yield_fixture
def plugin_manager():
    yield PluginManager(MagicMock(), [test_plugin_folder])
