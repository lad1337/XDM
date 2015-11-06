import pytest

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


def test_config_get_attr():
    c = Config(debug=True, config_path='foo', port=1337)
    assert c.path.config == 'foo'

    with pytest.raises(AttributeError):
        assert c.foo_bar  # i dont wan't to assert it but the IDE complains otherwise
    with pytest.raises(AttributeError):
        assert c.server.foo_bar  # i don't want to assert it but the IDE complains otherwise

    assert c.server.port == 1337
    assert c.server.debug is True
