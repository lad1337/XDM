from configparser import ConfigParser
import logging
from pathlib import Path

from appdirs import AppDirs

app_dirs = AppDirs('XDM')

DEFAUL_CONFIG = {
    'paths': {
        'config': Path(app_dirs.user_config_dir) / 'xdm.ini',
        'db': Path(app_dirs.user_data_dir) / 'db',
        'plugins': Path(app_dirs.user_data_dir) / 'plugins/'
    },
    'server': {
        'port': 5000,
        'debug': False,
        'workers': 1
    },
    'tasks': {
        'broker_url': 'sqla+sqlite:///%s' % (Path(app_dirs.user_data_dir) / 'task_queue.sqlite'),
        'backend': 'db+sqlite:///%s' % (Path(app_dirs.user_data_dir) / 'task_queue.sqlite')
    }
}
ARGUMENT_MAP = {
    'port': 'server',
    'debug': 'server'
}

logger = logging.getLogger('xdm')


class Config(ConfigParser):
    
    def __init__(self, *args, **kwargs):
        self.comand_line_arguments = kwargs
        if self.comand_line_arguments.get('debug'):
            logger.setLevel(logging.DEBUG)

        super(Config, self).__init__()
        self.init(self.comand_line_arguments)
        self.apply_comand_line_arguments(self.comand_line_arguments)

    def init(self, arguments):

        if not arguments.get('config_path'):
            config_path = DEFAUL_CONFIG['paths']['config']
        else:
            config_path = Path(arguments['config_path'])

        if not config_path.parent.exists():
            logger.info("Creating directories at: %s", config_path.parent)
            config_path.parent.mkdir(parents=True)

        for section, values in DEFAUL_CONFIG.items():
            if section not in self:
                self[section] = values

        with config_path.open("w") as config_file:
            if not config_path.exists():
                logger.info("Writing new config at: %s", config_path)
                self.write(config_file)
            else:
                logger.info("Writing config at: %s", config_path)
                self.write(config_file)

        logger.debug('Reading config file at: %s', config_path)
        self.read(str(config_path))

    def apply_comand_line_arguments(self, arguments):
        for argument, value in arguments.items():
            # TODO: overwrite only values that have been passed, not with defaults
            if argument not in ARGUMENT_MAP or value is None:
                continue

            logger.debug(
                'Overwriting config "%s:%s" with "%s"',
                ARGUMENT_MAP[argument],
                argument,
                str(value)
            )
            self.set(ARGUMENT_MAP[argument], argument, str(value))

