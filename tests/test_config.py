
from xdm.config import Config


def test_config_path():
    c = Config()
    assert c.get('path', 'config')


def test_config_overwrite():
    c = Config(debug=True)
    assert c.getboolean('server', 'debug')


def test_config_not_overwrite():
    c = Config(debug=None)
    assert c.getboolean('server', 'debug') is False
