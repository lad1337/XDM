from conftest import test_logger

import pytest

from tornado import gen

from xdm.task import FINISHED
from xdm.task import IdentifierQueue
from xdm.task import QUEUED
from xdm.task import RUNNING
from xdm.task import TaskStatus


def test_queue_initial_status():
    q = IdentifierQueue(1)
    assert q.qsize() == 0
    id_ = 'a'
    q.put(id_, (1, 2))
    assert q.qsize() == 1
    assert q.get_status(id_) == QUEUED
    assert q.get_status(id_) == TaskStatus(QUEUED)


@pytest.mark.gen_test
def test_queue_status_development():
    q = IdentifierQueue(1)
    id_ = 'a'
    q.put(id_, (1, 2))

    assert q.get_status(id_) == QUEUED
    status, message_data = yield q.get()
    assert id_ is status.identifier
    assert q.get_status(id_) == RUNNING
    q.task_done(status.identifier)
    assert q.get_status(id_) == FINISHED


@pytest.mark.gen_test
def test_queue_status_progress():
    q = IdentifierQueue(1)
    id_ = 'a'
    q.put(id_, (1, 2))

    status, message_data = yield q.get()
    status = q.get_status(status.identifier)
    status.total = 7
    status.count = 4
    assert status.progress['total'] == 7


@pytest.mark.gen_test(timeout=5)
def test_queue_consumer(xdm):
    id_ = 'a'
    data = {'foo': 'bar'}
    xdm.queue.put(id_, (xdm, 'update_check', data))
    test_logger.debug('asserting status')
    yield xdm.queue.join()


@pytest.mark.gen_test(timeout=5)
def test_queue_progress(xdm):

    @gen.coroutine
    def foo(task_status, app, data):
        task_status.total = data['total']
        task_status.count = data['count']

    xdm.add_task('foo', foo)

    id_1 = 'a'
    data = {'total': 10, 'count': 5}
    xdm.queue.put(id_1, (xdm, 'foo', data))
    id_2 = 2
    data = {'total': 10, 'count': 0}
    xdm.queue.put(id_2, (xdm, 'foo', data))

    yield xdm.queue.join()
    status = xdm.queue.get_status(id_1)
    assert status == FINISHED
    assert status.total == 10
    assert status.count == 5
    assert status.progress == {
        'percentage': 50,
        'total': 10,
        'count': 5,
        'status': 'finished'
    }
    status = xdm.queue.get_status(id_2)
    assert status == FINISHED
    assert status.progress == {
        'percentage': 0,
        'total': 10,
        'count': 0,
        'status': 'finished'
    }
