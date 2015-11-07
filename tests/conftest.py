import logging
from logging import StreamHandler
from pathlib import Path
import tempfile
from unittest.mock import Mock

from colorlog import ColoredFormatter

import pytest

from xdm.application import XDM
from xdm.config import Config
from xdm.config.default import DEFAUL_CONFIG

logger = logging.getLogger('xdm')
stream_handler = StreamHandler()
stream_handler.setFormatter(ColoredFormatter(
    '%(asctime)-15s %(log_color)s%(levelname)-8s%(reset)s %(message)s'
))
logger.addHandler(stream_handler)
logger.setLevel(logging.DEBUG)


tmp_dir = str(tempfile.TemporaryDirectory())

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
