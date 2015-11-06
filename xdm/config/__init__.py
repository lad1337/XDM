from configparser import ConfigParser
import logging
from pathlib import Path

from attrdict import AttrDict

from xdm.config.default import ARGUMENT_MAP
from xdm.config.default import DEFAUL_CONFIG

logger = logging.getLogger('xdm')


class Config(ConfigParser):

    def __init__(self, *args, **kwargs):
        self.arguments = kwargs
        if self.arguments.get('debug'):
            logger.setLevel(logging.DEBUG)

        super(Config, self).__init__()
        self.load_defaults()
        self.load_arguments(self.arguments)

        self.init(self.arguments)
        self.load_arguments(self.arguments)

    def init(self, arguments):
        config_path = Path(self.get('path', 'config'))

        if not config_path.parent.exists():
            self.create_directories(config_path)
        if arguments.get('reset') or not config_path.exists():
            self.write_config_file(config_path)

        logger.debug('Reading config file at: %s', config_path)
        self.read(str(config_path))

    def load_defaults(self):
        def value_for_maybe_type(value):
            if isinstance(value, tuple):
                return value[0]
            return str(value)
        for section, values in DEFAUL_CONFIG.items():
            self[section] = {
                k: value_for_maybe_type(v) for k, v in values.items()}

    def load_arguments(self, arguments):
        for name, value in arguments.items():
            if value is None:
                continue
            section, target_name = ARGUMENT_MAP.get(name, {})
            # TODO(lad1337): overwrite only values that have been passed, not with defaults
            if section is None or target_name is None:
                logger.warning('Unknown command line argument: "%s"', name)
                continue
            self.set(section, target_name, str(value))
            logger.debug(
                'Overwriting config "%s:%s" with "%s"',
                section,
                target_name,
                str(value)
            )

    def create_directories(self, config_path):  # noqa
        logger.info("Creating directories at: %s", config_path.parent)
        config_path.parent.mkdir(parents=True)

    def write_config_file(self, config_path):  # noqa
        with config_path.open("w") as config_file:
            logger.info("Writing config at: %s", config_path)
            self.write(config_file)

    def typed(self, section, key):
        default_value_data = DEFAUL_CONFIG.get(section, {}).get(key)
        if not isinstance(default_value_data, tuple):
            return self.get(section, key)
        type_ = default_value_data[1]
        if type_ is bool:
            return self.getboolean(section, key)
        elif type_ is int:
            return self.getint(section, key)
        elif type_ is float:
            return self.getfloat(section, key)
        return self.get(section, key)

    def __getattr__(self, section):
        if section not in self.sections():
            raise AttributeError('No section "%s"' % section)

        return AttrDict({
            key: self.typed(section, key) for key in self[section]
        })
