from datetime import timedelta
from functools import wraps
import inspect
import logging

from xdm.plugin.config import Config

logger = logging.getLogger('xdm.plugin')

METHOD_TYPES = [
    'hook',
    'task'
]


def attach_attributes(func, type_, kwargs=None):
    setattr(func, type_, True)
    for other_type in METHOD_TYPES:
        if other_type != type_:
            setattr(func, other_type, False)

    func.identifier = None
    func.interval = None
    func.kwargs = kwargs

    kwargs = kwargs or {}
    identifier = kwargs.get('identifier') or func.__name__
    logger.info('Attaching identifier "%s" to method %s', identifier, func)
    func.identifier = identifier

    if kwargs.get('interval'):
        interval = kwargs['interval']
        if not isinstance(interval, timedelta):
            logger.error(
                'Interval for %s is not of type timedelta, got %s instead',
                func,
                type(interval)
            )
        else:
            func.interval = kwargs['interval']


def wrap_with_logger(type_, func):
    @wraps(func)
    def log_wapper(*args, **kwargs):
        logger.info('Start %s %s', type_, func)
        result = func(*args, **kwargs)
        logger.info('End %s %s', type_, func)
        return result
    return log_wapper


def prepare_method(type_, *args, **kwargs):
    if len(args) and (inspect.isfunction(args[0]) or inspect.ismethod(args[0])):
        func = args[0]
        logger.debug(
            'register_hook used as simple decorator for %s', func
        )
        attach_attributes(func, type_)
        return wrap_with_logger(type_, func)
    # else this is called with arguments, we don't have the method yet
    logger.debug(
        'register_hook used as complex decorator with %s & %s', args, kwargs
    )

    def decorator(func):
        logger.debug('wrapper called with %s', func)
        attach_attributes(func, type_, kwargs)
        return wrap_with_logger(type_, func)
    return decorator


class Plugin():
    identifier = None
    app = None
    config = Config()

    def __init__(self, app, instance=None):
        self.instance = instance or 'default'
        self.app = app
        self.config.set_db(app.config_db)
        self.config.set_owner(self)
        self.config.load()
        self.logger = logging.getLogger('xdm.plugin.%s' % self)

    def __repr__(self):
        return '<%s>' % self

    def __str__(self):
        return '{identifier}:{instance}'.format(
            class_=self.__class__,
            identifier=self.identifier,
            instance=self.instance
        )

    @staticmethod
    def register_hook(*args, **kwargs):
        return prepare_method('hook', *args, **kwargs)

    @staticmethod
    def register_task(*args, **kwargs):
        return prepare_method('task', *args, **kwargs)
