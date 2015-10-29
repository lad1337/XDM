import logging
import multiprocessing
from celery import Celery

logger = logging.getLogger('XDM')
from xdm.task import internal


class TaskQueue(Celery):

    def __init__(self, app, broker, backend=None):
        super(TaskQueue, self).__init__(
            app.import_name, broker=broker, backend=backend)

        self.conf.update(app.config)
        TaskBase = self.Task
        class ContextTask(TaskBase):
            abstract = True
            def __call__(self, *args, **kwargs):
                with app.app_context():
                    return TaskBase.__call__(self, *args, **kwargs)
        self.Task = ContextTask


class Worker(multiprocessing.Process):

    def __init__(self, queue, name):
        super().__init__(name=name)
        self.queue = queue

    def run(self):
        logger.info("Starting task worker: %s", self.name)
        argv = [
            'worker',
            '--loglevel=WARNING',
            '--hostname=local',
        ]
        self._worker = self.queue.worker_main(argv)
        self._worker.logger = logger
