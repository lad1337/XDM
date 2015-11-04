
from xdm.config import Config


def test_config_path():
    c = Config()
    assert c.get('path', 'config')
