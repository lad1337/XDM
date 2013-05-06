
from xdm.plugins import *


# this class is special because it will be set to SYSTEM in the whole app
class SystemConfig(System):
    version = "0.17"
    _config = {'login_user': '',
               'login_password': '',
               'port': 8085,
               'socket_host': '0.0.0.0',
               'https': False,
               'extra_plugin_path': '',
               'interval_search': 120, # minutes
               'interval_update': 1440, # minutes
               'interval_check': 3,
               'enabled': True,
               'again_on_fail': False,
               'resnatch_same': False,
               'defaut_mt_select': ''
               }

    def _clearAllUnsedConfgs(self):
        amount = common.PM.clearAllUnsedConfgs()
        return (True, {}, '%s configs removed' % amount)

    config_meta = {'plugin_buttons': {'clearAllUnsedConfgs': {'action': _clearAllUnsedConfgs, 'name': 'Clear unused configs', 'desc': 'Clear Configs that are not used (this is also done on startup)'}},
                   'login_user': {'on_change_actions': ['reboot']},
                    'login_password': {'on_change_actions': ['reboot']},
                    'interval_search': {'human': 'Search interval (minutes)'},
                    'interval_update': {'human': 'Update interval (minutes)'},
                    'https': {'human': 'HTTPS', 'desc': 'NOT IMPLEMENTED YET'},
                    'interval_search': {'human': 'Search interval (minutes)', 'on_change_actions': ['reboot']},
                    'interval_update': {'human': 'Update interval (minutes)', 'on_change_actions': ['reboot']},
                    'interval_check': {'human': 'Download check interval (minutes)', 'on_change_actions': ['reboot']},
                    'again_on_fail': {'human': 'Retry a different download after a failed one', 'desc': 'If on XDM tries to find (another) download after a failure, also see Resnatch Same'},
                    'resnatch_same': {'human': 'Resnatch Same', 'desc': 'If on XDM will resnatch the same download after a failure (if Retry is on at all)'},
                    'extra_plugin_path': {'human': 'Extra Plugin Path', 'on_change_actions': ['reboot']},
                    'plugin_desc': 'System wide configurations',
                    'defaut_mt_select': {'human': 'Default MediaType'}
                    }
    single = True

    def _defaut_mt_select(self):
        out = {}
        for mt in common.PM.MTM:
            out[mt.identifier] = str(mt)
        return out