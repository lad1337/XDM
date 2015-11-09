from functools import wraps
import inspect
import logging

from xdm.plugin.config import Config

logger = logging.getLogger('xdm.plugin')


def attach_identifier(func, identifier=None):
    identifier = identifier or func.__name__
    logger.warning('Attaching identifier "%s" to method %s', identifier, func)
    func.identifier = identifier


def wrap_with_logger(type_, func):
    @wraps(func)
    def log_wapper(*args, **kwargs):
        logger.info('Calling %s %s', type_, func)
        result = func(*args, **kwargs)
        logger.info('End %s %s', type_, func)
        return result
    return log_wapper


def prepare_method(type_, *args, **kwargs):
    if len(args) and (inspect.isfunction(args[0]) or inspect.ismethod(args[0])):
        logger.debug(
            'register_hook used as simple decorator with %s & %s', args, kwargs
        )
        func = args[0]
        setattr(func, type_, True)
        attach_identifier(func)
        return wrap_with_logger(type_, func)
    # else this is called with arguments, we don't have the method yet
    logger.debug(
        'register_hook used as complex decorator with %s & %s', args, kwargs
    )

    def decorator(func):
        logger.debug('wrapper called with %s', func)
        attach_identifier(func, kwargs.get('identifier'))
        setattr(func, type_, True)
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

    def __repr__(self):
        return '<%s>' % self

    def __str__(self):
        return '{class_}:{identifier}:{instance}'.format(
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
