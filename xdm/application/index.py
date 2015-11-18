import logging

from tornado.gen import coroutine
from tornado.web import RequestHandler


logger = logging.getLogger('xdm')


class Index(RequestHandler):

    route = r'/'

    @coroutine
    def get(self):
        self.write('Hello World')
