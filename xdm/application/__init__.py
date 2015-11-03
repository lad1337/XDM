import logging
from logging import StreamHandler

import tornado.web
import tornado.httpserver
from blitzdb import FileBackend

from xdm.config import Config
from xdm.application import api
from xdm.task import internal

class XDM(tornado.web.Application):

    def __init__(self, *args, **kwargs):

        self.logger = logging.getLogger('xdm')
        stream_handler = StreamHandler()
        self.logger.addHandler(stream_handler)
        self.configuration = Config(**kwargs)
        self.init_logging(stream_handler)

        super(XDM, self).__init__()
        self.debug = self.configuration.get('server', 'debug')
        self.db = FileBackend(self.configuration.get('paths', 'db'))
        self._add_handlers()

    def init_logging(self, stream_handler):
        self.loggers = {
            'server.access': logging.getLogger("tornado.access"),
            'server.app': logging.getLogger("tornado.application"),
            'server.general': logging.getLogger("tornado.general")
        }
        for logger_name, logger in self.loggers.items():
            if self.configuration.getboolean('server', 'debug'):
                logger.setLevel(logging.DEBUG)
            logger.addHandler(stream_handler)


    def _add_handlers(self):
        handlers = (api.APIPing, internal.Task)
        self.add_handlers(".*$", [(h.route, h) for h in handlers])
