# Author: Dennis Lutter <lad1337@gmail.com>
# URL: https://github.com/lad1337/XDM
#
# This file is part of XDM: eXtentable Download Manager.
#
# XDM: eXtentable Download Manager. Plugin based media collection manager.
# Copyright (C) 2013  Dennis Lutter
#
# XDM is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# XDM is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see http://www.gnu.org/licenses/.

from xdm.plugins import *
import os
import xdm
from xdm import web
from babel.core import Locale
from collections import OrderedDict
import gettext
import locale
import traceback
import inspect


# this class is special because it will be set to SYSTEM in the whole app
class SystemConfig(System):
    version = "0.24"
    identifier = "de.lad1337.systemconfig"
    _config = OrderedDict([
               ('defaut_mt_select', ''),
               ('login_user', ''),
               ('login_password', ''),
               ('port', 8085),
               ('port_api', 8086),
               ('socket_host', '0.0.0.0'),
               ('https', False),
               ('https_cert_filepath', 'server.crt'),
               ('https_key_filepath', 'server.key'),
               ('extra_plugin_path', ''),
               ('interval_update', 1440), # 24 hours in minutes
               ('interval_check', 3), # minutes
               ('interval_mediaadder', 3), # minutes
               ('interval_core_update', 720),
               ('interval_clean', 1440), # 24 hours in minutes
               ('enabled', True),
               ('again_on_fail', False),
               ('resnatch_same', False),
               ('mediaadder_search_by_name', False),
               ('dont_open_browser', False),
               ('webRoot', ''),
               ('show_feed', True),
               ('api_active', False),
               ('api_key', ''),
               ('language_select', 'automatic'),
               ('use_derefer_me', True),
               ('auto_update_plugins', False),
               ('auto_update_core', False),
               ('censor_xdm_dir', False),
               ])

    _hidden_config = {'last_known_version': '0.4.18', # this was introduced in 0.4.19. so in order to run migration for 0.4.19 we have a value of 0.4.18
                      'setup_wizard_step': 0 # starting point of wizard step, when the wizard only has like 5 steps but a later has an additional step 6 it should start at that step
                      }
    """this is the attr for hidden config it can be used just as the _config but is not visable to the user / settings page"""

    def _clearAllUnsedConfgs(self):
        amount = common.PM.clearAllUnsedConfgs()
        return (True, {}, '%s configs removed' % amount)

    def _defaut_mt_select(self):
        out = {}
        for mt in common.PM.MTM:
            out[mt.identifier] = unicode(mt)
        return out

    def _setLocale(self, setting):
        if setting != 'automatic':
            self._locale = setting
        else:
            self._locale = locale.getdefaultlocale()[0]
        try:
            str(self._locale)
        except (UnicodeEncodeError, UnicodeDecodeError):
            log.info(u"Setting language to en_US because the locale '%s' was not encodable with ascii" % self._locale)
            self._locale = "en_US"
        log(u"Language setting is '%s' resulting locale: '%s'" % (setting, self._locale))

    def _getLocale(self):
        try:
            return self._locale
        except AttributeError:
            self._setLocale(self.c.language_select)
        return self._locale

    locale = property(_getLocale)

    def _switchLanguage(self):
        del self._locale
        languages = None
        if self.c.language_select != 'automatic':
            languages = [self.locale]

        log(u'Trying to set language to: "%s"' % languages)
        translationPath = os.path.abspath(os.path.join(xdm.APP_PATH, 'i18n'))
        log.info(u"Using i18n path %s" % translationPath)

        if not os.path.isdir(translationPath):
            log.error(u"%s is not a path. where is the i18n folder?" % translationPath)
            return
        fallback = common.STARTOPTIONS.dev
        try:
            t = gettext.translation('messages', translationPath, languages=languages, fallback=fallback)
        except IOError:
            log.warning(u"No language file found that matches %s. your locale %s" % (languages, locale.getlocale()))
            log.info("Trying to install language en_US as fallback")
            t = gettext.translation('messages', translationPath, languages=['en_US'], fallback=True)
            log.info("Setting language to en_US because of fallback")
            self.c.language_select = 'en_US'

        if isinstance(t, gettext.GNUTranslations):
            log.info(u'Instaling language "%s"' % t.info()['language-team'])
        else:
            log.warning(u'Installing a NULL translator because we could not find any matching .mo files not even for en_US :(')
        self._setLocale(self.c.language_select)
        t.install(True, ('gettext', 'ngettext', 'lgettext', 'lngettext'))
        # we need to re install the functions becuase they have changed
        # this is a very close binding of a plugin and the core XDM
        # but since this is the SYSTEM plugin i consider this ok
        # pylint: disable=E1101, E0602
        xdm.classes.elementWidgetEnvironment.install_gettext_callables(_, ngettext, newstyle=True)
        # pylint: disable=E1101, E0602
        web.env.install_gettext_callables(_, ngettext, newstyle=True)

    def _language_select(self):
        out = {'automatic': _('automatic')}
        i18n_dir = os.path.join(xdm.APP_PATH, 'i18n')
        # http://stackoverflow.com/questions/800197/get-all-of-the-immediate-subdirectories-in-python
        for language in [name for name in os.listdir(i18n_dir) if os.path.isdir(os.path.join(i18n_dir, name))]:
            out[language] = Locale.parse(language, sep='_').display_name
        return out

    config_meta = {'plugin_buttons': {'clearAllUnsedConfgs': {'action': _clearAllUnsedConfgs, 'name': 'Clear unused configs', 'desc': 'Clear configs that are not used.'}},
                   'login_user': {'on_change_actions': ['serverReStart']},
                    'login_password': {'on_change_actions': ['serverReStart']},
                    'https': {'human': 'https / SSL', 'desc': 'If changed XDM will reboot', 'on_change_actions': ['reboot']},
                    'https_cert_filepath': {'human': 'SSL certificate file', 'desc': 'If changed XDM will reboot', 'on_change_actions': ['reboot']},
                    'https_key_filepath': {'human': 'SSL key file', 'desc': 'If changed XDM will reboot', 'on_change_actions': ['reboot']},
                    'webRoot': {'human': 'WebRoot', 'desc': 'Use this if you want to run XDM behind a reverse proxy. If changed XDM will reboot', 'on_change_actions': ['reboot']},
                    'interval_search': {'human': 'Search interval (minutes)', 'on_change_actions': ['serverReStart']},
                    'interval_update': {'human': 'Update interval (minutes)', 'desc': 'Set this to 0 if you want to disable XDM core update checks', 'on_change_actions': ['serverReStart']},
                    'interval_check': {'human': 'Download check interval (minutes)', 'on_change_actions': ['serverReStart']},
                    'again_on_fail': {'human': 'Retry a different download after a failed one', 'desc': 'If on XDM tries to find (another) download after a failure, also see Resnatch Same'},
                    'resnatch_same': {'human': 'Resnatch Same', 'desc': 'If on XDM will resnatch the same download after a failure (if Retry is on at all)'},
                    'extra_plugin_path': {'human': 'Extra Plugin Path', 'on_change_actions': ['serverReStart']},
                    'plugin_desc': 'System wide configurations',
                    'defaut_mt_select': {'human': 'Default MediaType'},
                    'dont_open_browser': {'human': 'Dont open the browser on start'},
                    'language_select': {'human': 'XDM language', 'on_change_actions': [_switchLanguage]},
                    'mediaadder_search_by_name': {'human': 'Fallback to search by name', 'desc': "This will search by name if a MediaAdder wants to add something but is not found by the id."},
                    'use_derefer_me': {'human': 'Use http://derefer.org/ for external links', 'desc': 'Using this makes XDM safer but a little slower (not noticeable) to render pages.'}
                    }
    single = True
