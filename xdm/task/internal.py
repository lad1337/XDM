import logging
logger = logging.getLogger('xdm')

from tornado import gen

from xdm.model import Element

@gen.coroutine
def update_check(app, data):
    logger.info("Checking for update.")

    for i in range(10):
        old = app.db.filter(Element , {'type': 'update_check'})
        logger.info('update check step: %s ... found %s old steps', i, len(old))
        e = Element({'type': 'update_check', 'step': i})
        yield gen.sleep(1)
        app.db.save(e)
        app.db.commit()
    return False
