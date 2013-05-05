from xdm.logger import *
import collections
import traceback


class ConfigWrapper(object):
    """this will be the "c" of a plugin to easily get the config for the current plugin
    also handels the saving of the new config"""
    configs = []

    def __init__(self):
        self.configs = []

    def addConfig(self, c):
        self.configs.append(c)

    def finalSort(self, enabled):
        self.configs.sort(key=lambda x: x.name, reverse=False)
        self.configs.insert(0, self.configs.pop(self.configs.index(enabled)))

    def __getattr__(self, name):
        for cur_c in self.configs:
            if cur_c.name == name:
                return cur_c.value
        raise AttributeError

    def __setattr__(self, name, value):
        for cur_c in self.configs:
            if cur_c.name == name:
                cur_c.value = value
                cur_c.save()
                return
        else:
            super(ConfigWrapper, self).__setattr__(name, value)


class ConfigMeta(collections.MutableMapping):
    def __init__(self, *args, **kwargs):
        self.store = dict()
        self.update(dict(*args, **kwargs)) # use the free update to set keys

    def __getitem__(self, key):
        try:
            return self.store[self.__keytransform__(key)]
        except KeyError:
            return None

    def __setitem__(self, key, value):
        self.store[self.__keytransform__(key)] = value

    def __delitem__(self, key):
        del self.store[self.__keytransform__(key)]

    def __iter__(self):
        return iter(self.store)

    def __len__(self):
        return len(self.store)

    def __keytransform__(self, key):
        return key


def pluginMethodWrapper(caller_name, run, alternative):
    """Return a wrapped instance method"""
    def outer(*args, **kwargs):
        try:
            return run(*args, **kwargs)
        except Exception as ex:
            tb = traceback.format_exc()
            out = alternative(*args, **kwargs)
            try:
                log.error("Error during %s of %s \nError: %s\n\n%s\nNew value:%s" % (run.__name__, caller_name, ex, tb, out), traceback=tb, new_out=out, exception=ex)
            except:
                log.error("Error during %s of %s \nError: %s\n\n%s" % (run.__name__, caller_name, ex, tb))
            return out
    return outer
