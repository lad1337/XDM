from conftest import test_logger

import tempfile

import pytest
from tornado import gen
from tornado.ioloop import IOLoop

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


@pytest.mark.gen_test(timeout=5)
def test_app_scheduled_task(xdm_loaded):
    xdm = xdm_loaded
    assert xdm.schedules
    tasks = xdm.schedules['clean_db']
    assert len(tasks) == 1
    task = tasks[0]
    assert task.is_running()
    test_logger.debug("sleep 3")
    yield gen.sleep(2)
    print(id(IOLoop.current()))
    assert xdm.side_effect, 'schedule was not run and did not effect the attribute'
