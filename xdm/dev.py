from xdm import logger
from xdm.logger import logging

fun_map = {logging.ERROR: '😡',
           logging.EXCEPTION: '😱',
           logging.WARNING: '😞',
           logging.CRITICAL: '😵',
           }

for lvl in logger.lvlNames:
    if lvl in fun_map:
        logger.lvlNames[lvl]['c'] = fun_map[lvl] + logger.lvlNames[lvl]['c'][1:]
