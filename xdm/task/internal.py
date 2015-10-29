from time import sleep

from xdm.model import Element

import logging
logger = logging.getLogger('XDM')


def update_check():
    logger.info("Checking for update.")

    for i in range(30):
        logger.info('update check step: %s ... found %s old steps', i, len([]))
        sleep(1)
        e = Element({'type': 'update_check', 'step': i})
    return False
