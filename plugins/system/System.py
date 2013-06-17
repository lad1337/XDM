# Author: Dennis Lutter <lad1337@gmail.com>
# URL: https://github.com/lad1337/XDM
#
# This file is part of XDM: eXtentable Download Manager.
#
#XDM: eXtentable Download Manager. Plugin based media collection manager.
#Copyright (C) 2013  Dennis Lutter
#
#XDM is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.
#
#XDM is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.
#
#You should have received a copy of the GNU General Public License
#along with this program.  If not, see http://www.gnu.org/licenses/.

from xdm.plugins import *


# this class is special because it will be set to SYSTEM in the whole app
class SystemConfig(System):
    version = "0.19"
    _config = {'login_user': '',
               'login_password': '',
               'port': 8085,
               'port_api': 8086,
               'socket_host': '0.0.0.0',
               'https': False,
               'https_cert_filepath': 'server.crt',
               'https_key_filepath': 'server.key',
               'extra_plugin_path': '',
               'interval_update': 1440, # minutes
               'interval_check': 3,
               'interval_mediaadder': 3,
               'interval_core_update': 720,
               'enabled': True,
               'again_on_fail': False,
               'resnatch_same': False,
               'defaut_mt_select': '',
               'dont_open_browser': False,
               'webRoot': '',
               'show_feed': True,
               'api_active': True,
               'api_key': ''
               }

    def _clearAllUnsedConfgs(self):
        amount = common.PM.clearAllUnsedConfgs()
        return (True, {}, '%s configs removed' % amount)

    config_meta = {'plugin_buttons': {'clearAllUnsedConfgs': {'action': _clearAllUnsedConfgs, 'name': 'Clear unused configs', 'desc': 'Clear configs that are not used.'}},
                   'login_user': {'on_change_actions': ['serverReStart']},
                    'login_password': {'on_change_actions': ['serverReStart']},
                    'interval_search': {'human': 'Search interval (minutes)'},
                    'interval_update': {'human': 'Update interval (minutes)'},
                    'https': {'human': 'https / SSL', 'desc': 'If changed XDM will reboot', 'on_change_actions': ['reboot']},
                    'https_cert_filepath': {'human': 'SSL certificate file', 'desc': 'If changed XDM will reboot', 'on_change_actions': ['reboot']},
                    'https_key_filepath': {'human': 'SSL key file', 'desc': 'If changed XDM will reboot', 'on_change_actions': ['reboot']},
                    'webRoot': {'human': 'WebRoot', 'desc': 'Use this if you want to run XDM behind a reverse proxy. If changed XDM will reboot', 'on_change_actions': ['reboot']},
                    'interval_search': {'human': 'Search interval (minutes)', 'on_change_actions': ['serverReStart']},
                    'interval_update': {'human': 'Update interval (minutes)', 'desc': 'Set this to 0 if you want to disable XDM core update checks','on_change_actions': ['serverReStart']},
                    'interval_check': {'human': 'Download check interval (minutes)', 'on_change_actions': ['serverReStart']},
                    'again_on_fail': {'human': 'Retry a different download after a failed one', 'desc': 'If on XDM tries to find (another) download after a failure, also see Resnatch Same'},
                    'resnatch_same': {'human': 'Resnatch Same', 'desc': 'If on XDM will resnatch the same download after a failure (if Retry is on at all)'},
                    'extra_plugin_path': {'human': 'Extra Plugin Path', 'on_change_actions': ['serverReStart']},
                    'plugin_desc': 'System wide configurations',
                    'defaut_mt_select': {'human': 'Default MediaType'},
                    'dont_open_browser': {'human': 'Dont open the browser on start'}
                    }
    single = True

    def _defaut_mt_select(self):
        out = {}
        for mt in common.PM.MTM:
            out[mt.identifier] = str(mt)
        return out
