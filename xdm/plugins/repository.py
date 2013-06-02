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

import zipfile
import StringIO
import xdm
import os
import shutil
import datetime

from xdm.logger import *
from lib import requests
from xdm.plugins.bases import __all__ as allClasses
from xdm import common, helper, actionManager


class RepoManager(object):

    def __init__(self, repos):
        self._repos = repos
        self.repos = []
        for repo in repos:
            self.repos.append(Repo(repo.name, repo.url))
        self.cached = False
        self.caching = False
        self.last_cache = None
        self.updateable_plugins = {}
        self.install_messages = []

    def cache(self):
        self.caching = True
        for repo in self.repos:
            try:
                repo.cache()
            except:
                log.error('%s had an error during cache' % repo)
            for r in self._repos:
                if r.url == repo.url:
                    if r.name != repo.name:
                        r.name = repo.name
                        r.save()
                    if r.info_url != repo.info_url:
                        r.info_url = repo.info_url
                        r.save()
        self.last_cache = datetime.datetime.now()
        self.cached = True
        self.caching = False
        self.checkForUpdate()

    def getRepos(self):
        return self.repos

    def checkForUpdate(self):
        plugins = common.PM.getAll(True, 'Default')
        updateable_plugins = {}
        for plugin in plugins:
            if plugin.identifier:
                for repo in self.repos:
                    for repo_plugin in repo.getPlugins():
                        if repo_plugin.identifier == plugin.identifier and self._updateable(repo_plugin, plugin):
                            updateable_plugins[plugin.identifier] = (repo_plugin, plugin)
                            common.MM.createInfo('%s as an update. Update now?' % (plugin.screenName), confirmJavascript="installModalFromMessage(this, '%s')" % plugin.identifier)

        log.info('%s Plugins have an update' % len(updateable_plugins))
        self.updateable_plugins = updateable_plugins

    def hasUpdate(self, identifier):
        if identifier in self.updateable_plugins:
            return self.updateable_plugins[identifier][0].versionHuman()
        return ''

    def _updateable(self, repo_plugin, plugin):
        return (repo_plugin.major_version, repo_plugin.minor_version) > (plugin.major_version, plugin.minor_version)

    def isInstalled(self, plugins, identifier):
        for plugin in plugins:
            if plugin.identifier == identifier:
                return True
        return False

    def _prepareIntall(self):
        self._read_messages = []
        helper.cleanTempFolder()

    def deinstall(self, identifier):
        self._read_messages = []
        self.install_messages = [('info', 'deinstall.py -i %s' % identifier)]
        if not identifier:
            self.setNewMessage('error', 'The identifier is empty this should not happen !!')
            self.setNewMessage('error', 'Deinstallation unsuccessful')
            self.setNewMessage('info', 'Done!')
            return

        old_instalation = None
        for plugin in common.PM.getAll(returnAll=True, instance='Default'):
            if plugin.identifier == identifier:
                self.setNewMessage('info', 'Deinstalling %s' % plugin.type)
                old_instalation = plugin
                break
        else:
            self.setNewMessage('error', 'Could not find a plugin with identifier %s' % identifier)
            self.setNewMessage('error', 'Deinstallation unsuccessful')
            self.setNewMessage('info', 'Done!')
            return
        install_path = os.path.abspath(old_instalation.get_plugin_isntall_path())
        self.setNewMessage('info', 'Deleting plugin folder')
        self.setNewMessage('info', install_path)
        try:
            shutil.rmtree(install_path)
        except Exception as ex:
            log.error('Something went wrong while deleting %s' % install_path)
            self.setNewMessage('error', 'Error during deletion')
            self.setNewMessage('error', '%s' % ex)
        else:
            self.setNewMessage('info', 'Recaching plugins...')
            actionManager.executeAction('recachePlugins', ['RepoManager'])
            self.setNewMessage('info', 'Recaching pugins done.')
            self.setNewMessage('info', 'Recaching repos...')
            self.cache()
            self.setNewMessage('info', 'Recaching repos done. (please refresh page)')
        self.setNewMessage('info', 'Done!')

    def install(self, identifier):
        self._prepareIntall()
        self.install_messages = [('info', 'install.py -i %s' % identifier)]
        self.setNewMessage('info', 'Getting download URL')

        plugin_to_update = None
        for repo in self.repos:
            for repo_plugin in repo.getPlugins():
                if repo_plugin.identifier == identifier:
                    plugin_to_update = repo_plugin
                    break

        if plugin_to_update is None:
            self.setNewMessage('error', 'Could not find a plugin with identifier %s' % identifier)
            self.setNewMessage('info', 'Done!')
            return

        self.setNewMessage('info', 'Installing %s(%s)' % (plugin_to_update.name, plugin_to_update.versionHuman()))
        old_instalation = None
        for plugin in common.PM.getAll(returnAll=True, instance='Default'):
            if plugin.identifier == plugin_to_update.identifier:
                if not self._updateable(plugin_to_update, plugin):
                    self.setNewMessage('error', '%s is already installed and does not need an update' % plugin_to_update.name)
                    self.setNewMessage('info', 'Done!')
                    return
                else:
                    self.setNewMessage('info', '%s is already installed but has an update' % plugin_to_update.name)
                    old_instalation = plugin
                    break
        else:
            self.setNewMessage('info', '%s is not yet installed' % plugin_to_update.name)

        if old_instalation is not None:
            old_plugin_path = os.path.abspath(old_instalation.get_plugin_isntall_path())
            old_plugin_path_parent = os.path.abspath(os.path.join(old_plugin_path, os.pardir))
            self.setNewMessage('info', 'Renaming old install path %s' % old_plugin_path)
            new_dir = '__old__%s%s' % (plugin.type, plugin.version)
            new_dir = new_dir.replace(' ', '-').replace('.', '_')
            new_path = os.path.join(old_plugin_path_parent, new_dir)
            self.setNewMessage('info', 'to %s' % new_path)
            os.rename(old_plugin_path, new_path)

        if repo_plugin.format == 'zip':
            downloader = ZipPluginInstaller()
        else:
            self.setNewMessage('error', 'Format %s is not supported. sorry' % plugin_to_update.format)
            self.setNewMessage('info', 'Done!')
            return

        install_path = common.SYSTEM.c.extra_plugin_path

        self.setNewMessage('info', 'Installing into %s' % install_path)
        self.setNewMessage('info', 'Starting download. please wait...')
        install_result = False
        try:
            install_result = downloader.install(self, plugin_to_update, install_path)
        except Exception as ex:
            log.error('Something went wrong during download')
            self.setNewMessage('error', 'Error during download')
            self.setNewMessage('error', '%s' % ex)

        if install_result:
            self.setNewMessage('info', 'Installation successful')
            self.setNewMessage('info', 'Recaching plugins...')
            actionManager.executeAction('recachePlugins', ['RepoManager'])
            self.setNewMessage('info', 'Recaching pugins done.')
            self.setNewMessage('info', 'Recaching repos...')
            self.cache()
            self.setNewMessage('info', 'Recaching repos done. (please refresh page)')
        else:
            self.setNewMessage('error', 'Installation unsuccessful')

        self.setNewMessage('info', 'Done!')

    def getLastInstallMessages(self):
        out = []
        for index, message in enumerate(self.install_messages):
            if not index in self._read_messages:
                out.append(message)
                self._read_messages.append(index)
        return out

    def setNewMessage(self, lvl, msg):
        self.install_messages.append((lvl, msg))

    def setFolderUpAsModule(self, path):
        if not os.path.isdir(path):
            os.mkdir(path)
        init_path = os.path.join(path, '__init__.py')
        if not os.path.isfile(init_path):
            init_file = open(init_path, 'w')
            init_file.write('')
            init_file.close()


class ZipPluginInstaller():

    def _resolved(self, x):
        return os.path.realpath(os.path.abspath(x))

    def _badpath(self, path, base):
        # joinpath will ignore base if path is absolute
        return not self.resolved(os.path.join(base, path)).startswith(base)

    def install(self, manager, repo_plugin, install_path):
        r = requests.get(repo_plugin.download_url)
        manager.setNewMessage('info', 'Download done.')
        z = zipfile.ZipFile(StringIO.StringIO(r.content))

        base = self.resolved(".")
        for memberPath in z.namelist():
            if self._badpath(memberPath, base):
                manager.setNewMessage('error', 'Security error. Path of file is absolute or contains ".." !')
                manager.setNewMessage('error', 'Please report this repository !')
                return False

        z.extractall(xdm.TEMPPATH)
        manager.setNewMessage('info', 'Extration done.')
        plugin_folder = ''
        for root, dirs, files in os.walk(xdm.TEMPPATH):
            for cur_dir in dirs:
                if cur_dir == repo_plugin.name:
                    manager.setNewMessage('info', 'Found extracted plugin folder.')
                    manager.setNewMessage('info', os.path.join(root, cur_dir))
                    plugin_folder = os.path.join(root, cur_dir)
                    break
            if plugin_folder:
                break
        else:
            manager.setNewMessage('error', 'Could not find the extracted plugin')
            manager.setNewMessage('error', '"name" field must match folder name!')
            return False

        manager.setNewMessage('info', 'Copying files to:')
        plugin_des = '%s %s %s' % (repo_plugin.name, repo_plugin.identifier, repo_plugin.versionHuman())
        plugin_des = plugin_des.replace(' ', '-').replace('.', '_')
        plugin_root = os.path.join(install_path, repo_plugin.type)
        manager.setFolderUpAsModule(plugin_root)
        final_path = os.path.join(plugin_root, plugin_des)
        manager.setNewMessage('info', final_path)

        shutil.copytree(plugin_folder, final_path)
        return True


class Repo(object):

    def __init__(self, name, url):
        self.name = name
        self.url = url
        self.info_url = ''
        self.plugins = []

    def getPlugins(self):
        return self.plugins

    def __str__(self):
        return '%s %s' % (self.name, self.url)

    def cache(self):
        """Checks the internet for plusings in repo"""
        self.plugins = []
        log.info("Checking if repo at %s" % self.url)
        try:
            r = requests.get(self.url, timeout=20)
        except (requests.ConnectionError, requests.Timeout):
            log.error("Error while retrieving repo information from %s" % self.url)
            return
        repo_info = r.json()
        self.name = repo_info['name']
        self.info_url = repo_info['info_url']
        for identifier, plugin_versions in repo_info['plugins'].items():
            for version_info in plugin_versions:
                self.plugins.append(ExternalPlugin(identifier, version_info))


class RepoPlugin(object):
    def __init__(self, identifier, info):
        self.major_version = int(info['major_version'])
        self.minor_version = int(info['minor_version'])
        self.format = info['format']
        self.name = info['name']
        self.desc = info['desc']
        self.download_url = info['download_url']
        self.type = info['type']
        self.identifier = identifier

    def checkType(self):
        return self.type in allClasses + ['Compilations']

    def versionHuman(self):
        return '%s.%s' % (self.major_version, self.minor_version)

    def __str__(self):
        return'Name: %s, identifier: %s, download_url: %s, desc: %s' % (self.name, self.identifier, self.download_url, self.desc)


class LocalPlugin(RepoPlugin):

    def __init__(self, identifier, info):
        self.local = True
        super(LocalPlugin, self).__init__(identifier, info)


class ExternalPlugin(RepoPlugin):

    def __init__(self, identifier, info):
        self.local = False
        super(ExternalPlugin, self).__init__(identifier, info)
