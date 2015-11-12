from collections import defaultdict
import logging
from logging import StreamHandler

from colorlog import ColoredFormatter

from blitzdb import FileBackend

import tornado.httpserver
from tornado.ioloop import IOLoop
from tornado.ioloop import PeriodicCallback
import tornado.web

from xdm.application import api
from xdm.config import Config
from xdm.plugin import PluginManager
from xdm.task import Consumer
from xdm.task import IdentifierQueue
from xdm.task import internal


class XDM(tornado.web.Application):

    def __init__(self, *args, **kwargs):

        # TODO(lad1337): do this somewhere else, currently here to properly log config init
        self.logger = logging.getLogger('xdm')
        self.init_logging(kwargs.get('debug'))
        self.config = Config(**kwargs)
        super(XDM, self).__init__()

        self.debug = self.config.server.debug
        self.db = FileBackend(self.config.path.element_db)
        self.config_db = FileBackend(self.config.path.config_db)
        # adding default routes
        self.add_handlers(".*$", [(h.route, h) for h in (api.APIPing, api.Task)])
        # spawn Q consumers
        self.queue = IdentifierQueue()
        self.consumer = Consumer(self.queue)
        IOLoop.current().spawn_callback(self.consumer)
        self.task_map = {
            "update_check": internal.update_check
        }
        self.plugins = PluginManager(
            self,
            paths=[self.config.path.plugin],
            follow_symlinks=self.config.server.debug
        )
        self.schedules = defaultdict(list)
        self.plugins.load()

    def init_logging(self, debug):
        def set_sevel(logger):
            if debug:
                logger.setLevel(logging.DEBUG)
            else:
                logger.setLevel(logging.INFO)
        set_sevel(self.logger)
        stream_handler = StreamHandler()
        stream_handler.setFormatter(ColoredFormatter(
            '%(asctime)-15s %(log_color)s%(levelname)-8s%(blue)s%(name)-20s%(reset)s %(message)s'
        ))
        self.logger.addHandler(stream_handler)
        self.loggers = []
        self.loggers = {
            'xdm': self.logger,
            'server.access': logging.getLogger("tornado.access"),
            'server.app': logging.getLogger("tornado.application"),
            'server.general': logging.getLogger("tornado.general")
        }
        for logger_name, logger in self.loggers.items():
            logger.addHandler(stream_handler)
            set_sevel(self.logger)

    def add_task(self, name, callable):
        self.task_map[name] = callable

    def add_schedule(self, name, callback, timedelta):
        milliseconds = timedelta.seconds * 1000
        self.logger.debug('Adding schedule %s:%s to run every %sms', name, callback, milliseconds)

        periodic_callback = PeriodicCallback(callback, milliseconds)
        periodic_callback.start()
        self.schedules[name].append(
            periodic_callback
        )
