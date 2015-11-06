import tempfile

from xdm.application import XDM
from xdm.task import Q


def test_app_init(xdm):
    assert xdm.config
    assert xdm.db
    assert xdm.queue
    assert xdm.queue is Q
    assert xdm.queue.qsize() == 0


def test_app_with_args():
    config_file = str(tempfile.TemporaryFile())
    xdm = XDM(
        debug=True,
        config_path=config_file
    )
    assert xdm.config.get('path', 'config') == config_file
    assert xdm.config.getboolean('server', 'debug')
