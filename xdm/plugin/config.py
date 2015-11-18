from collections import OrderedDict
import logging

from xdm.model import Config as ConfigModel

logger = logging.getLogger('xdm.plugin.config')


class Config():

    db = None
    owner = None
    _config = None
    _definitions = {}

    def __init__(self, *args):
        self._definitions = OrderedDict({
            entry.name: entry for entry in args
        })
        self.db = None
        self.owner = None
        self._config = None

    def load(self):
        try:
            self._config = self.db.get(ConfigModel, {'owner': self.owner})
        except ConfigModel.DoesNotExist:
            logger.warning('No config found for %s, creating default', self.owner)
            self._create_config_entry()
            self._config = self.db.get(ConfigModel, {'owner': self.owner})

        self.apply_config(self._config)

    def _create_config_entry(self):
        config = ConfigModel(self.to_dict())
        self.db.save(config)
        self.db.commit()

    def apply_config(self, config):
        for field_name, field_data in config.fields.items():
            entry = self._definitions.get(field_name)
            if entry is None:
                # TODO(lad1337): remove surplus config fields
                logger.warning('Field "%s" not found in definitions', entry)
                continue
            entry.value = field_data

    def set_db(self, db):
        self.db = db

    def set_owner(self, owner):
        self.owner = str(owner)
        for entry in self._definitions.values():
            entry.owner = owner

    def persist(self):
        self.db.save(self._config)

    def to_dict(self):
        return dict(
            owner=self.owner,
            fields={field: entry.value for field, entry in self._definitions.items()}
        )

    def get(self, item, default=None):
        if item not in self._definitions:
            return default
        return self._definitions.get(item)

    def __getattr__(self, item):
        if item not in self._definitions:
            raise AttributeError('No config field "%s"', item)
        return self._definitions[item].value

    def __setattr__(self, key, value):
        try:
            self.get(key).value = value
        except AttributeError:
            super(Config, self).__setattr__(key, value)


class Entry():

    def __init__(self, name, default_value=None, type_=str, frontend_name=None):
        self.name = name
        self.default_value = default_value
        self.type = type_
        self.frontend_name = frontend_name
        self._value = None

    @property
    def value(self):
        return self.default_value if self._value is None else self._value

    @value.setter
    def value(self, value):
        logger.debug('Setting %s to "%s" of %s', self.name, value, self.owner)
        self._value = self.type(value)
