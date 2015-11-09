from collections import defaultdict
import inspect
import logging
import os
import site

from xdm.plugin import base

logger = logging.getLogger('xdm.plugin_manager')


class PluginManager():
    """Class that manages/provides and finds plugins"""

    _classes = set()
    _hooks = {}
    _tasks = {}

    def __init__(self, app, paths=None, follow_symlinks=False):
        self.app = app
        self.paths = {str(path) for path in paths} if paths else set()
        for path in self.paths:
            site.addsitedir(path)
        self.clear_cache()

        self.follow_symlinks = follow_symlinks

    def clear_cache(self):
        self._classes = set()
        self._hooks = defaultdict(set)
        self._tasks = defaultdict(set)

    def load(self, system_only=False, path=None):
        paths = [str(path)] if path else self.paths
        classes = []
        for path in paths:
            site.addsitedir(path)
            classes.extend(self._load_plugins(path))
        logger.debug('Loaded classes: %s', classes)
        return classes

    def _load_plugins(self, path):
        logger.debug('Current search domain: %s', self.paths | {path})
        classes = self.find_subclasses(base.Plugin, path)
        for cls in classes:
            logger.debug('Found %s', cls)
            self.register(cls)
        return classes

    def register(self, cls):
        try:
            instance = cls(self.app)
        except Exception:
            logger.exception('Can not instantiate "%s", skipping')
            return
        for member_name, member in inspect.getmembers(instance):
            for type_ in ('hook', 'task'):
                if hasattr(member, type_) and getattr(member, type_):
                    logger.info(
                        'Register %s "%s" of %s as "%s"',
                        type_, member_name, cls, member.identifier)
                    getattr(self, '_%ss' % type_,)[member.identifier].add((cls, member_name))
        self._classes.add(cls)
        logger.info('Registered "%s"', cls)

    def get_instances(self, cls):
        # TODO(lad1337): get all instances for plugin
        return [cls(self.app, 'default')]

    def get_tasks(self, name):
        return self._get_items('_tasks', name)

    def get_hooks(self, name):
        return self._get_items('_hooks', name)

    def _get_items(self, attribute, name):
        items = getattr(self, attribute).get(name)
        if items is None:
            return None
        callbacks = []
        for cls, member_name in items:
            for instance in self.get_instances(cls):
                callbacks.append(getattr(instance, member_name))
        return callbacks

    def find_subclasses(self, cls, path, reloadModule=False):
        """Find all subclass of cls in py files located below path

        """
        subclasses = []
        for root, dirs, files in os.walk(str(path), followlinks=self.follow_symlinks):
            if '__old__' in root:
                continue
            for name in files:
                if not name.endswith(".py"):
                    continue
                current_path = os.path.join(root, name).replace(path, '')
                modulename = current_path.rsplit('.', 1)[0].replace(os.sep, '.')[1:]
                try:
                    subclasses.extend(self.look_for_subclass(cls, modulename))
                except ImportError:
                    # dir = os.path.dirname(current_path)
                    # TODO(lad1337): install python requirements
                    '''
                    if not common.REPOMANAGER.install_requirements_for_plugin(dir):
                        exit(1)
                        raise
                    module = __import__(modulename)
                    '''
                    logger.exception('During import of "%s"', modulename)

        return subclasses

    def look_for_subclass(self, cls, modulename):
        logger.debug('Looking for subclasses of %s in "%s"', cls, modulename)
        subclasses = []
        try:
            module = __import__(modulename)
        except ImportError:
            raise subclasses
        except Exception:  # catch everything we dont know what kind of error a plugin might have
            logger.exception('During import of "%s"', modulename)
            return subclasses

        # walk the dictionaries to get to the last one
        d = module.__dict__
        for m in modulename.split('.')[1:]:
            d = d[m].__dict__

        # look through this dictionary for things
        # that are subclass of Job
        # but are not Job itself
        for key, entry in d.items():
            if key == cls.__name__:
                continue
            try:
                if issubclass(entry, cls):
                    subclasses.append(entry)
            except TypeError:
                # this happens when a non-type is passed in to issubclass. We
                # don't care as it can't be a subclass of Job if it isn't a
                # type
                continue
        return subclasses
