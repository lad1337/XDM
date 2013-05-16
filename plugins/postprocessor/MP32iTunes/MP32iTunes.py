# Author: Dennis Lutter <lad1337@gmail.com>
# URL: https://github.com/lad1337/XDM
#
# This file is part of XDM: Xtentable Download Manager.
#
#XDM: Xtentable Download Manager. Plugin based media collection manager.
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
import os
import subprocess
import platform


class MP32iTunes(PostProcessor):
    screenName = 'MP3 2 iTunes'
    _config = {'delete_files': False,
               'update_match': False,
               'hide_itunes': False}
    addMediaTypeOptions = 'runFor'
    config_meta = {'plugin_desc': "This will execute an apple script that adds all mp3's/m4a's to iTunes of the given download. MAC OSX only!",
                   'delete_files': {'human': "Delete the processed files"},
                   'update_match': {'human': 'Update iTunes match after adding'},
                   'hide_itunes': {'human': 'Hide iTunes after completion'}
                   }

    def testMe(self):
        if platform.system() == 'Darwin':
            return (True, 'Everything fine we are under Mac OSX')
        else:
            return (False, 'This plugin only runs under Mac OSX')

    def postProcessPath(self, element, filePath):
        scptPath = os.path.join(os.path.dirname(__file__), 'add_mp3s_to_itunes.scpt')
        log.info('MP32iTunes will run pp on %s' % filePath)
        if not os.path.isfile(scptPath):
            log.error("My apple script is missing. it is supposed to be at %s" % scptPath)
            return False

        process = subprocess.Popen(['osascript', scptPath, filePath, str(int(self.c.delete_files)), str(int(self.c.update_match)), str(int(self.c.hide_itunes))], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        output, error = process.communicate()

        if process.returncode:
            log.error("Some error during subprocess call. %s" % error)

        return (process.returncode == 0, output)
