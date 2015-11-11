import logging
from logging import StreamHandler
from unittest.mock import MagicMock

from colorlog import ColoredFormatter


def init_logging():
    logger = logging.getLogger('xdm')
    logging.getLogger('xdm.test')
    stream_handler = StreamHandler()
    stream_handler.setFormatter(ColoredFormatter(
        '%(asctime)-15s %(log_color)s%(levelname)-8s%(blue)s%(name)-20s%(reset)s %(message)s'
    ))
    logger.addHandler(stream_handler)
    logger.setLevel(logging.DEBUG)


def reset_logging():
    logger = logging.getLogger('xdm')
    for handler in logger.handlers:
        logger.removeHandler(handler)


init_logging()
test_logger = logging.getLogger('xdm.test')

from pathlib import Path

import tempfile
from unittest.mock import Mock

import pytest

from xdm.application import XDM
from xdm.config import Config
from xdm.config.default import DEFAUL_CONFIG
from xdm.plugin import PluginManager

test_plugin_folder = Path(__file__).parent / 'plugin' / 'plugins'

Config.create_directories = Mock()
Config.write_config_file = Mock()


def set_tmp_dir(tmp_dir):
    global DEFAUL_CONFIG
    DEFAUL_CONFIG['path'] = {
        'config': Path(tmp_dir) / 'xdm.ini',
        'element_db': Path(tmp_dir) / 'element_db',
        'config_db': Path(tmp_dir) / 'config_db',
        'plugin': Path(tmp_dir) / 'plugins/'
    }


def no_gen(gen):
    return [i for i in gen]


@pytest.fixture
def fix_logging_handlers():
    reset_logging()
    init_logging()


@pytest.yield_fixture
def xdm(io_loop):
    reset_logging()
    with tempfile.TemporaryDirectory() as tmp_dir:
        set_tmp_dir(tmp_dir)
        yield XDM(
            debug=True
        )


@pytest.yield_fixture
def xdm_loaded(io_loop):
    reset_logging()
    with tempfile.TemporaryDirectory() as tmp_dir:
        set_tmp_dir(tmp_dir)
        yield XDM(
            debug=True,
            plugin_folder=test_plugin_folder
        )


@pytest.yield_fixture
def plugin_manager():
    yield PluginManager(MagicMock(), [test_plugin_folder])
