from tornado.web import RequestHandler
from tornado.web import asynchronous
from tornado.gen import coroutine

class APIPing(RequestHandler):

    route = r'/api/ping'

    @coroutine
    def get(self):
        self.write({'data': 'pong'})

