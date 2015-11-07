import logging

from tornado import gen
from tornado.queues import Queue

from xdm.constant.task import FINISHED
from xdm.constant.task import QUEUED
from xdm.constant.task import RUNNING
from xdm.constant.task import STATUS_MAP

logger = logging.getLogger('xdm')


class TaskStatus(object):

    def __init__(self, identifier, status=None):
        self.identifier = identifier
        self.status = status or QUEUED
        self.total = None
        self.count = None

    @property
    def progress(self):
        total = self.total or 0
        count = self.count or 0
        percentage = 0
        if count != 0:
            percentage = round(100 / (total / count))
        return {
            'percentage': percentage,
            'total': self.total,
            'count': self.count,
            'status': STATUS_MAP.get(self.status)
        }

    def __eq__(self, other):
        if isinstance(other, TaskStatus):
            return self.status == other.status
        return self.status == other

    def __repr__(self):
        return "<TaskStatus status:{status} {count}/{total}>".format(
            status=STATUS_MAP[self.status],
            count=self.count,
            total=self.total
        )


class IdentifierQueue(Queue):

    def __init__(self, maxsize=0):
        super(IdentifierQueue, self).__init__(maxsize=maxsize)
        self._task_status = {}

    def put(self, identifier, item, timeout=None):
        task_status = TaskStatus(identifier)
        self._task_status[identifier] = task_status
        logger.debug('Adding task "%s"', identifier)
        return super(IdentifierQueue, self).put((task_status, item), timeout=timeout)

    @gen.coroutine
    def get(self, timeout=None):
        logger.debug('Getting task')
        task = yield super(IdentifierQueue, self).get(timeout=timeout)
        task_status, _ = task
        logger.debug('Got task "%s"', task_status)
        task_status.status = RUNNING
        return task

    def task_done(self, identifier):
        super(IdentifierQueue, self).task_done()
        logger.debug('Task done "%s"', identifier)
        self.set_status(identifier, FINISHED)

    def get_status(self, identifier):
        return self._task_status.get(identifier)

    def set_status(self, identifier, status):
        logger.debug('Setting status of task "%s" to %s', identifier, STATUS_MAP.get(status))
        self._task_status[identifier].status = status


Q = IdentifierQueue(maxsize=200)


# http://tornadokevinlee.readthedocs.org/en/latest/queues.html
@gen.coroutine
def consumer():
    while True:
        task_status, task_data = yield Q.get()
        app, task_name, task_data = task_data
        logger.debug('%s, %s', app, task_name)

        logger.info('Doing work on %s:%s', task_name, task_status)
        try:
            task_result = yield app.task_map.get(task_name)(task_status, app, task_data)
        finally:
            Q.task_done(task_status.identifier)
            logger.info('Work on %s:%s done', task_name, task_status)
        logger.debug('Task result: %s', task_result)
