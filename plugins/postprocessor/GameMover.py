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
import time
import fnmatch
import os
import re
import shutil


class GameMover(PostProcessor):
    _config = {"replace_space_with": "_",
               }
    version = "0.2"
    identifier = 'de.lad1337.games.mover'
    screenName = 'Game Mover'
    addMediaTypeOptions = ['de.lad1337.games']
    config_meta = {'plugin_desc': 'This will move all the iso, img, wbfs from the path that is given to the path of the games platform.',
                   'replace_space_with': {'desc': 'All spaces for the final file will be replaced with this.'}
                   }
    useConfigsForElementsAs = 'Path'

    def postProcessPath(self, element, filePath):
        destPath = self._getPath(element)
        if not destPath:
            msg = "Destination path for %s is not set. Stopping PP." % element
            log.warning(msg)
            return (False, msg)
        # log of the whole process routine from here on except debug
        # this looks hacky: http://stackoverflow.com/questions/7935966/python-overwriting-variables-in-nested-functions
        processLog = [""]

        def processLogger(message):
            log.info(message)
            createdDate = time.strftime("%a %d %b %Y / %X", time.localtime()) + ": "
            processLog[0] = processLog[0] + createdDate + message + "\n"

        def fixName(name, replaceSpace):
            return re.sub(r'[\\/:"*?<>|]+', "", name.replace(" ", replaceSpace))

        # gather all images -> .iso and .img
        allImageLocations = []
        for root, dirnames, filenames in os.walk(filePath):
            for filename in fnmatch.filter(filenames, '*.iso') + fnmatch.filter(filenames, '*.img') + fnmatch.filter(filenames, '*.wbfs'):
                curImage = os.path.join(root, filename)
                allImageLocations.append(curImage)
                processLogger("Found image: " + curImage)

        processLogger("Renaming and Moving Game")
        success = True
        allImageLocations.sort()
        for index, curFile in enumerate(allImageLocations):
            processLogger("Processing image: " + curFile)
            try:
                extension = os.path.splitext(curFile)[1]
                if len(allImageLocations) > 1:
                    newFileName = element.name + " CD" + str(index + 1) + extension
                else:
                    newFileName = element.name + extension
                newFileName = fixName(newFileName, self.c.replace_space_with)
                processLogger("New Filename shall be: %s" % newFileName)
                dest = os.path.join(destPath, newFileName)
                processLogger("Moving File from: %s to: %s" % (curFile, dest))
                shutil.move(curFile, dest)
            except Exception, msg:
                processLogger("Unable to rename and move game: " + curFile + ". Please process manually")
                processLogger("given ERROR: %s" % msg)
                success = False

        processLogger("File processing done")
        # write process log
        logFileName = fixName(element.name + ".log", self.c.replace_space_with)
        logFilePath = os.path.join(filePath, logFileName)
        try:
            # This tries to open an existing file but creates a new file if necessary.
            logfile = open(logFilePath, "a")
            try:
                logfile.write(processLog[0])
            finally:
                logfile.close()
        except IOError:
            pass

        return (success, processLog[0])
