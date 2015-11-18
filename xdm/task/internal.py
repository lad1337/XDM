import logging
logger = logging.getLogger('xdm')

from tornado import gen

from xdm.model import Element


@gen.coroutine
def update_check(task_id, app, data):
    logger.info("Checking for update.")

    for i in range(2):
        old = app.db.filter(Element, {'type': 'update_check'})
        logger.info('update check step: %s ... found %s old steps', i, len(old))
        e = Element({
            'type': 'update_check', 'step': i, 'id': task_id})
        yield gen.sleep(1)
        app.db.save(e)
        app.db.commit()
