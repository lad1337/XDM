import logging
import uuid

from tornado.web import RequestHandler
from tornado.escape import json_decode
from tornado.gen import coroutine

from xdm.task import Q

logger = logging.getLogger('xdm')


class APIPing(RequestHandler):

    route = r'/api/ping'

    @coroutine
    def get(self):
        self.write({'data': 'pong'})


class Task(RequestHandler):

    route = r'/api/task/start/([\w\-]+)$'

    @coroutine
    def post(self, task_name):
        data = {}
        if self.request.body:
            data = json_decode(self.request.body)
        logger.info('Starting task: %s', task_name)
        task_id = uuid.uuid4()
        yield Q.put(task_id, (
            self.application,
            task_name,
            data
        ))
        self.write({'data': {'status': 'started', 'id': str(task_id)}})

    @coroutine
    def get(self, task_id):
        self.write({
            'status': self.application.queue.status(task_id)
        })
