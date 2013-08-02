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

import sys
import os
import xdm
from xdm.logger import *
from core_migrate import *
from lib import requests
from xdm import version, common, actionManager
import re
from subprocess import call
import urllib
import subprocess
import shutil

import platform
if "windows" in platform.system().lower():
    from lib.pbs import git
else:
    from lib.sh import git

install_type_exe = 0# any compiled windows build
install_type_mac = 1# any compiled mac osx build
install_type_git = 2# running from source using git
install_type_src = 3# running from source without git
install_type_names = {install_type_exe: 'Windows Binary',
                      install_type_mac: 'Mac App',
                      install_type_git: 'Git',
                      install_type_src: 'Source'}


class CoreUpdater(object):

    def __init__(self):
        self.install_type = self._find_install_type()
        self.info = None

        log.info('CoreUpdate is working with version %s on %s' % (xdm.common.getVersionString(), install_type_names[self.install_type]))
        if self.install_type == install_type_exe:
            self.updater = WindowsUpdateManager()
        if self.install_type == install_type_mac:
            self.updater = MacUpdateManager()
        elif self.install_type == install_type_git:
            self.updater = GitUpdateManager()
        elif self.install_type == install_type_src:
            self.updater = SourceUpdateManager()
        else:
            self.updater = None

    def getHumanInstallType(self):
        return install_type_names[self.install_type]

    def migrate(self):
        xdm.common.addState(1)
        #common.SM.reset()
        try:
            self._migrate()
        except:
            log.error("Error during migration")
            log.info("Shutting down because migration did not work sorry")
            actionManager.executeAction('shutdown', 'failed migration')
        #common.SM.reset()
        xdm.common.removeState(1)

    def _migrate(self):
        cur_version = xdm.common.getVersionTuple(noBuild=True)
        last_known_version = tuple([int(x) for x in common.SYSTEM.hc.last_known_version.split('.')])
        log.info('Checking migrate functions with last known version: %s and cur version: %s' % (last_known_version, cur_version))

        if last_known_version < (0, 4, 19) <= cur_version:
            msg = "Running migrate function migrate_0_4_19"
            common.SM.setNewMessage('###########<br>Migration: %s' % msg)
            log.info(msg)
            self.backupDatabases('pre-0.4.19-migration')
            migrate_0_4_19()

        # add more migrate function calls here
        common.SYSTEM.hc.last_known_version = ".".join([str(x) for x in xdm.common.getVersionTuple(noBuild=True)])

    def backupDatabases(self, reason):
        for databasePath in (xdm.CONFIG_DATABASE_PATH, xdm.HISTORY_DATABASE_PATH, xdm.DATABASE_PATH):
            backupFolder = os.path.join(os.path.dirname(databasePath), 'backups')
            oldname = os.path.basename(databasePath)
            if not os.path.isdir(backupFolder):
                os.mkdir(backupFolder)
            finalPath = os.path.join(backupFolder, '%s.%s.db' % (oldname.split('.')[0], reason))
            log('Creating backup of %s to %s' % (databasePath, finalPath))
            shutil.copy(databasePath, finalPath)

    def _find_install_type(self):
        """Determines how this copy of XDM was installed."""
        if getattr(sys, 'frozen', None) == 'macosx_app': # check if we're a mac build
            install_type = install_type_mac
        elif sys.platform == 'win32' and False: # check if we're a windows build.. disabeled for now since we dont have win exes
            install_type = install_type_exe
        elif os.path.isdir(os.path.join(xdm.APP_PATH, '.git')):
            install_type = install_type_git
        else:
            install_type = install_type_src

        return install_type

    def check(self):
        """Checks the internet for a newer version.
        returns: UpdateManager.UpdateResponse()
        """
        log.info("Checking if %s needs an update" % install_type_names[self.install_type])
        self.info = self.updater.need_update()
        if not self.info.needUpdate:
            log.info(u"No update needed")

        return self.info

    def update(self):
        xdm.common.addState(3)
        common.SM.setNewMessage("Initialising core update")
        if self.updater.update():
            actionManager.executeAction('reboot', 'Updater')
        xdm.common.removeState(3)
        return True


class UpdateResponse(object):
    def __init__(self):
        self._reset()

    def _reset(self):
        self.needUpdate = None
        self.localVersion = 0
        self.externalVersion = 0
        self.message = 'No update needed'
        self.extraData = {}

    def default(self):
        self._reset()
        return self

    def __str__(self):
        extra = '; '.join(self.extraData)
        return 'Needupdate: %s; current version: %s; external version: %s;\nExtra info: %s\n%s' % (self.needUpdate,
                                                                                                   self.localVersion,
                                                                                                   self.externalVersion,
                                                                                                   extra,
                                                                                                   self.message)


class UpdateManager(object):

    def __init__(self):
        self.response = UpdateResponse()

    def need_update(self):
        return self.response

    def update(self):
        log.warning('sorry update not implemented')
        return self.response


class BinaryUpdateManager(UpdateManager):

    def __init__(self):
        super(BinaryUpdateManager, self).__init__()
        self.base_url = 'http://xdm.lad1337.de/latest.php'
        self.branch = 'master'
        if version.build:
            self.branch = 'nightly'

        self.response.localVersion = common.getVersionHuman()


class WindowsUpdateManager(BinaryUpdateManager):
    pass


class MacUpdateManager(BinaryUpdateManager):

    def need_update(self):
        payload = {'os': 'osx',
                   'branch': self.branch}

        r = requests.get(self.base_url, params=payload)
        json = r.json()
        self.response.externalVersion = common.makeVersionHuman(json['major'], json['minor'], json['revision'], json['build'])

        if common.isThisVersionNewer(json['major'], json['minor'], json['revision'], json['build']):
            self.response.needUpdate = True
            msg = 'Update available %s' % self.response.externalVersion
            log.info(msg)
            self.response.message = msg
        else:
            self.response.needUpdate = False
            self.response.message = 'No update available'
        return self.response

    def update(self):

        payload = {'os': 'osx',
                   'branch': self.branch}
        r = requests.get(self.base_url, params=payload)
        json = r.json()
        new_link = json['link']

        if not new_link:
            msg = "Unable to find a new version link on , not updating"
            common.SM.setNewMessage(msg, 'error')
            common.SM.setNewMessage('Done!')
            log(msg)
            return False

        common.SM.setNewMessage("Download url %s" % new_link)

        # download the dmg
        try:
            m = re.search(r'(^.+?)/[\w_\-\. ]+?\.app', xdm.APP_PATH)
            installPath = m.group(1)
            msg = "Downloading update file..."
            log(msg)
            common.SM.setNewMessage(msg)
            (filename, headers) = urllib.urlretrieve(new_link) #@UnusedVariable
            msg = "New dmg at %s" % filename
            log(msg)
            common.SM.setNewMessage(msg)
            os.system("hdiutil mount %s | grep /Volumes/XDM >update_mount.log" % (filename))
            fp = open('update_mount.log', 'r')
            data = fp.read()
            fp.close()
            m = re.search(r'/Volumes/(.+)', data)
            updateVolume = m.group(1)
            msg = "Copying app from /Volumes/%s/XDM.app to %s" % (updateVolume, installPath)
            log(msg)
            common.SM.setNewMessage(msg)
            call(["cp", "-rf", "/Volumes/%s/XDM.app" % updateVolume, installPath])

            msg = "Eject imgae /Volumes/%s/" % updateVolume
            log(msg)
            common.SM.setNewMessage(msg)
            call(["hdiutil", "eject", "/Volumes/%s/" % updateVolume], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            # delete the dmg
            msg = "Deleting dmg file from %s" % filename
            log(msg)
            common.SM.setNewMessage(msg)
            os.remove(filename)

        except:
            msg = "Error while trying to updateing. Please see log"
            log.error(msg)
            common.SM.setNewMessage(msg, lvl='error')
            return False
        return True


class SourceUpdateManager(object):

    def need_update(self):
        self.response.needUpdate = None
        msg = 'sorry update not implemented for Source install'
        log.warning(msg)
        self.response.message = msg
        return self.response


class GitUpdateManager(UpdateManager):

    """
    # On branch master
    # Your branch is behind 'origin/master' by 4 commits, and can be fast-forwarded.
    #
    nothing to commit (use -u to show untracked files)"""
    en_US_behind_pattern = re.compile(r'behind .*? by (\d+) commits')
    en_US_ff_pattern = re.compile(r'can be fast-forwarded')
    """
    # On branch master
    # Your branch is ahead of 'origin/master' by 1 commit.
    #"""
    en_US_ahead_pattern = re.compile(r'ahead .*? by (\d+) commits')

    def need_update(self):
        self.response.localVersion = git("rev-parse", "HEAD").rstrip('\n')

        # is dirty will be some text unless its not dirty
        is_dirty = git("ls-files", "-m", "-o", "-d", "--exclude-standard", _cwd=xdm.APP_PATH)
        if is_dirty:
            self.response.extraData['dirty_git'] = True
            msg = "Running on a dirty git installation! No real check was done."
            log.warning(msg)
            self.response.message = msg
            return self.response

        git.remote("update", _cwd=xdm.APP_PATH)
        self.response.externalVersion = git("rev-parse", "origin").rstrip('\n')

        if self.response.localVersion == self.response.externalVersion: # local is updated; end
            self.response.message = 'No update needed'
            self.response.needUpdate = False
            return self.response
        info = git.status("-uno", _cwd=xdm.APP_PATH)
        log(unicode(info))
        #TODO: do something about other languages!
        p = self.en_US_behind_pattern
        match = p.search(unicode(info))
        if match is not None:
            behind = int(match.group(1))
            if behind > 0:
                self.response.needUpdate = True
            self.response.message = "Behind by %s commits" % behind
            return self.response
        p = self.en_US_ahead_pattern
        match = p.search(unicode(info))
        if match is not None:
            ahead = int(match.group(1))
            if ahead > 0:
                self.response.needUpdate = False
            self.response.message = "Ahead by %s commits. No update for you!" % ahead
            return self.response

        self.response.message = "I dont know what the the status of your git is."
        self.response.needUpdate = None
        return self.response

    def update(self):
        common.SM.setNewMessage('Init git pull on')
        pull = git.pull(_cwd=xdm.APP_PATH)                   # get the local repo
        if pull.exit_code == 0:
            log.warning("Git pull exited with an error\n %s" % pull)
            return False
        else:
            return True
