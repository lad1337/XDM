from pathlib import Path

from appdirs import AppDirs

app_dirs = AppDirs('XDM')

DEFAULT_CONFIG = {
    'path': {
        'config': Path(app_dirs.user_config_dir) / 'xdm.ini',
        'element_db': Path(app_dirs.user_data_dir) / 'element_db',
        'config_db': Path(app_dirs.user_data_dir) / 'config_db',
        'plugin': Path(app_dirs.user_data_dir) / 'plugins/'
    },
    'server': {
        'port': (5000, int),
        'debug': (False, bool)
    },
    'task': {
        'broker_url': 'sqla+sqlite:///%s' % (Path(app_dirs.user_data_dir) / 'task_queue.sqlite'),
        'backend': 'db+sqlite:///%s' % (Path(app_dirs.user_data_dir) / 'task_queue.sqlite')
    }
}

ARGUMENT_MAP = {
    'port': ('server', 'port'),
    'debug': ('server', 'debug'),
    'config_path': ('path', 'config'),
    'plugin_folder': ('path', 'plugin')
}
