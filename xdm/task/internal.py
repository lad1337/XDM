from time import sleep

from tornado.escape import json_decode
from tornado.web import RequestHandler
from tornado.web import asynchronous
from tornado.gen import coroutine

from xdm.model import Element

import logging
logger = logging.getLogger('xdm')


class Task(RequestHandler):

    route = r'/api/task/start/(\w+)$'

    @coroutine
    def post(self, task_name):
        if task_name not in ['update_check']:
            self.write({
                'errors': ['unknown task %s' % task_name]}
            )
            return
        method = getattr(self, task_name)
        data = {}
        if self.request.body:
            data = json_decode(self.request.body)
        logger.info('Starting task: %s', task_name)
        result = yield method(
            *data.get('args', tuple()),
            **data.get('kwargs', {})
        )
        logger.debug('task result: %s', result)
        self.write({'data': result})


    @coroutine
    def update_check(self):
        logger.info("Checking for update.")

        for i in range(10):
            logger.info('update check step: %s ... found %s old steps', i, len([]))
            sleep(1)
            e = Element({'type': 'update_check', 'step': i})
        return False
