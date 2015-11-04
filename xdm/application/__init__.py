import logging
from logging import StreamHandler

from colorlog import ColoredFormatter

from blitzdb import FileBackend

import tornado.httpserver
from tornado.ioloop import IOLoop
import tornado.web

from xdm.application import api
from xdm.config import Config
from xdm.task import consumer
from xdm.task import internal
from xdm.task import Q


class XDM(tornado.web.Application):

    def __init__(self, *args, **kwargs):

        # TODO(lad1337): do this somewhere else, currently here to properly log config init
        self.logger = logging.getLogger('xdm')
        stream_handler = StreamHandler()
        stream_handler.setFormatter(ColoredFormatter(
            '%(asctime)-15s %(log_color)s%(levelname)-8s%(reset)s %(message)s'
        ))
        self.logger.addHandler(stream_handler)
        self.configuration = Config(**kwargs)
        self.init_logging(stream_handler)

        super(XDM, self).__init__()
        self.debug = self.configuration.get('server', 'debug')
        self.db = FileBackend(self.configuration.get('path', 'db'))
        # adding default routes
        self.add_handlers(".*$", [(h.route, h) for h in (api.APIPing, api.Task)])
        # spawn Q consumers
        self.queue = Q
        IOLoop.current().spawn_callback(consumer)

        self.task_map = {
            "update_check": internal.update_check
        }

    def init_logging(self, stream_handler):
        self.loggers = {
            'xdm': self.logger,
            'server.access': logging.getLogger("tornado.access"),
            'server.app': logging.getLogger("tornado.application"),
            'server.general': logging.getLogger("tornado.general")
        }
        for logger_name, logger in self.loggers.items():
            if self.configuration.getboolean('server', 'debug'):
                logger.setLevel(logging.DEBUG)
            logger.addHandler(stream_handler)
