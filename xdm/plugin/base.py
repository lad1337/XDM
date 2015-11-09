from functools import wraps
import inspect
import logging


logger = logging.getLogger('xdm.plugin')


def attach_identifier(func, identifier=None):
    identifier = identifier or func.__name__
    logger.warning('Attaching identifier "%s" to method %s', identifier, func)
    func.identifier = identifier


def wrapp_with_logger(type_, func):
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
        return wrapp_with_logger(type_, func)
    # else this is called with arguments, we don't have the method yet
    logger.debug(
        'register_hook used as complex decorator with %s & %s', args, kwargs
    )

    def decorator(func):
        logger.debug('wrapper called with %s', func)
        attach_identifier(func, kwargs.get('identifier'))
        setattr(func, type_, True)
        return wrapp_with_logger(type_, func)
    return decorator


class Plugin():
    app = None

    def __init__(self, app, instance_name=None):
        self.instance_name = instance_name or 'default'
        self.app = app

    @staticmethod
    def register_hook(*args, **kwargs):
        return prepare_method('hook', *args, **kwargs)

    @staticmethod
    def register_task(*args, **kwargs):
        return prepare_method('task', *args, **kwargs)
