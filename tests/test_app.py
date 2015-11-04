
from xdm.task import Q


def test_app_init(xdm):
    assert xdm.configuration
    assert xdm.db
    assert xdm.queue
    assert xdm.queue is Q
    assert xdm.queue.qsize() == 0
