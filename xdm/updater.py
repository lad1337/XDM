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
import git
from xdm.logger import *
from core_migrate import *
from lib import requests
from xdm import version, common, actionManager
import re
from subprocess import call
import urllib
import subprocess
from git.util import RemoteProgress
import shutil

install_type_exe = 0# any compiled windows build
install_type_mac = 1# any compiled mac osx build
install_type_git = 2# running from source using git
install_type_source = 3# running from source without git
install_type_names = {install_type_exe: 'Windows Binary',
                   install_type_mac: 'Mac App',
                   install_type_git: 'Git',
                   install_type_source: 'Source'}

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
        elif self.install_type == install_type_source:
            self.updater = SourceUpdateManager()
        else:
            self.updater = None

    def migrate(self):
        xdm.common.addState(1)
        common.SM.reset()
        try:
            self._migrate()
        except:
            log.error("Error during migration")
            log.info("Shutting down because migration did not work sorry")
            actionManager.executeAction('shutdown', 'failed migration')
        common.SM.reset()
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
        elif sys.platform == 'win32': # check if we're a windows build
            install_type = install_type_exe
        elif os.path.isdir(os.path.join(xdm.APP_PATH, '.git')):
            install_type = install_type_git
        else:
            install_type = install_type_source

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

    #http://stackoverflow.com/questions/8290233/gitpython-get-list-of-remote-commits-not-yet-applied
    def need_update(self):
        repo = git.Repo(xdm.APP_PATH)                   # get the local repo
        local_commit = repo.commit()                    # latest local commit
        remote = git.remote.Remote(repo, 'origin')      # remote repo
        info = remote.fetch()[0]                        # fetch changes
        remote_commit = info.commit

        self.response.localVersion = local_commit.hexsha
        self.response.externalVersion = remote_commit.hexsha

        if repo.is_dirty():
            self.response.extraData['dirty_git'] = True
            msg = "Running on a dirty git installation! No real check was done."
            log.warning(msg)
            self.response.message = msg
            return self.response

        behind = 0
        if local_commit.hexsha == remote_commit.hexsha: # local is updated; end
            self.response.message = 'No update needed'
            self.response.needUpdate = False
            return self.response

        self.response.needUpdate = True
        for commit in self._repo_changes(remote_commit):
            if commit.hexsha == local_commit.hexsha:
                if behind == 1:
                    msg = '%s commit behind.' % behind
                else:
                    msg = '%s commits behind.' % behind
                self.response.message = msg
                return self.response
            behind += 1
        else:
            msg = 'Looks like you are ahead. No update for YOU!'
            log(msg)
            self.response.message = msg
            self.response.needUpdate = None
            return self.response

    def _repo_changes(self, commit):
        "Iterator over repository changes starting with the given commit."
        next_parent = None
        yield commit                           # return the first commit itself
        while len(commit.parents) > 0:         # iterate
            for parent in commit.parents:        # go over all parents
                yield parent                       # return each parent
                next_parent = parent               # for the next iteration
            commit = next_parent                 # start again

    def update(self):
        repo = git.Repo(xdm.APP_PATH)                   # get the local repo
        remote = git.remote.Remote(repo, 'origin')      # remote repo
        rp = self.MyRemoteProgress()

        common.SM.setNewMessage('Init git pull on %s' % remote)
        remote.pull(progress=rp)
        return True

    class MyRemoteProgress(RemoteProgress):

        def update(self, op_code, cur_count, max_count=None, message=''):
            common.SM.setNewMessage(self._cur_line)
