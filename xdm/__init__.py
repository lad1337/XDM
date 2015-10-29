from argparse import ArgumentParser
from xdm.application import XDM

import logging
from logging import StreamHandler

logger = logging.getLogger("XDM")
stream_handler = StreamHandler()
logger.addHandler(stream_handler)

def run():
    parser = ArgumentParser(description='XDM: eXtendable Download Manager.'
                                        'Plugin based media collection manager.')
    parser.add_argument('--port', type=int, help='port to listen on')
    parser.add_argument('--config_path', help='Path to the config file')
    parser.add_argument('--debug', action='store_true', help='Debug logging on')
    args = parser.parse_args()

    xdm = XDM(**vars(args))
    xdm.run()

if __name__ == "__main__":
    run()
