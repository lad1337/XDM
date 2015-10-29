import logging

from flask import Flask
from blitzdb import FileBackend

from xdm.config import Config
from xdm.application.index import index
from xdm.application.api import api

from xdm.task import TaskQueue
from xdm.task import Worker
from xdm.task import internal

logger = logging.getLogger('XDM')

class XDM(Flask):

    def __init__(self, *args, **kwargs):
        super(XDM, self).__init__("XDM")
        self.configuration = Config(**kwargs)
        self.debug = self.configuration.get('server', 'debug')
        self.db = FileBackend(self.configuration.get('paths', 'db'))
        self._register_routes()
        self.task_queue = TaskQueue(
            self,
            self.configuration['tasks']['broker_url'],
            self.configuration['tasks']['backend'])

        self.tasks = {}
        self._register_tasks()
        self._workers = []
        self._register_workers()

    def run(self, host=None, port=None, debug=None, **options):
        try:
            self.start_workers()
            super(XDM, self).run(host=None, port=None, debug=None, **options)
        finally:
            self.stop_workers()

    def stop_workers(self):
        for worker in self._workers:
            worker.terminate()

    def start_workers(self):
        for worker in self._workers:
            worker.start()

    def _register_routes(self):
        for blueprint_ in (index, api):
            self.register_blueprint(blueprint_)

    def _register_tasks(self):
        self.add_task(internal.update_check)

    def _register_workers(self):
        for index in range(self.configuration.getint('server', 'workers')):
            self._workers.append(Worker(self.task_queue, "worker %s" % index))

    def add_blueprint(self, blueprint_):
        logger.debug("Registering route: %s", blueprint_.name)
        self.register_blueprint(blueprint_)

    def add_task(self, callable_):
        logger.debug('Registering task: %s', callable_.__name__)
        self.tasks[callable_.__name__] = self.task_queue.task(callable_)

    def run_task(self, name, *args, **kwargs):
        return self.tasks[name].delay(*args, **kwargs)

    def get_task(self, name):
        return self.tasks[name]

    def get_task_status(self, name, id_):
        return self.tasks[name].AsyncResult(id_)
