from pathlib import Path

from appdirs import AppDirs

app_dirs = AppDirs('XDM')

DEFAUL_CONFIG = {
    'path': {
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
