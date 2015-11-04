import logging

from tornado import gen
from tornado.queues import Queue

logger = logging.getLogger('xdm')

QUEUED = 1
RUNNING = 2
FINISHED = 3


class IdentifierQueue(Queue):

    def __init__(self, maxsize=0):
        super(IdentifierQueue, self).__init__(maxsize=maxsize)
        self._task_status = {}

    def put(self, identifier, item, timeout=None):
        identifier = str(identifier)
        self._task_status[identifier] = {'status': QUEUED}
        logger.debug('Adding task %s', identifier)
        return super(IdentifierQueue, self).put((identifier, item), timeout=timeout)

    def task_done(self, identifier):
        super(IdentifierQueue, self).task_done()
        logger.debug('Task done %s', identifier)
        self._task_status[identifier]['status'] = FINISHED

    def get_status(self, identifier):
        return self._task_status.get(identifier)

    def set_status(self, identifier, status):
        self._task_status[identifier]['status'] = status


Q = IdentifierQueue(maxsize=200)


# http://tornadokevinlee.readthedocs.org/en/latest/queues.html
@gen.coroutine
def consumer():
    while True:
        task_id, task_data = yield Q.get()
        app, task_name, task_data = task_data
        logger.debug('%s, %s', app, task_name)

        logger.info('Doing work on %s:%s %s', task_name, task_id, type(task_id))
        try:
            task_result = yield app.task_map.get(task_name)(task_id, app, task_data)
        finally:
            Q.task_done(task_id)
            logger.info('Work on %s:%s done', task_name, task_id)
        logger.debug('Task result: %s', task_result)
