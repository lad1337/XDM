from argparse import ArgumentParser
from pkg_resources import get_distribution
import signal

from xdm.application import XDM

from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop


__version__ = get_distribution(__name__).version


def run():  # noqa
    parser = ArgumentParser(description='XDM: eXtendable Download Manager.'
                                        'Plugin based media collection manager.')
    parser.add_argument('-p', '--port', type=int, help='port to listen on')
    parser.add_argument(
        '-c', '--config-path', help='Path to the config file', dest='config_path')
    parser.add_argument(
        '--plugin-folder', help='Path to the plugin folder', dest='plugin_folder')
    parser.add_argument('-d', '--debug', action='store_true', help='Debug logging on')
    args = parser.parse_args()

    xdm = XDM(**vars(args))
    http_server = HTTPServer(xdm)
    port = xdm.config.server.port
    http_server.listen(port)
    xdm.logger.info("Listening on port: %s", port)
    # http://stackoverflow.com/a/22314390
    signal.signal(
        signal.SIGINT,
        lambda sig, frame: IOLoop.instance().add_callback_from_signal(xdm.shutdown))

    IOLoop.instance().start()


if __name__ == '__main__':
    run()
