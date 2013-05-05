
from xdm.plugins import *
import time
import fnmatch
import os
import re
import shutil

class FileProcessor(PostProcessor):
    _config = {"replace_space_with": "_",
               }
    config_meta = {'plugin_desc': 'This will move all the iso, img, wbfs from the path that is given to the path of the games platform.',
                   'replace_space_with': {'desc': 'All spaces for the final file will be replaced with this.'}
                   }
    useConfigsForElementsAs = 'Path'

    def _getFinalPathForPlatform(self, platform):
        if platform == common.WII:
            return self.c.final_path_wii
        elif platform == common.PS3:
            return self.c.final_path_ps3
        elif platform == common.XBOX360:
            return self.c.final_path_xbox360
        elif platform == common.PC:
            return self.c.final_path_pc

    def ppPath(self, game, filePath):
        destPath = self._getFinalPathForPlatform(game.platform)
        if not destPath:
            log.warning("Destination path for %s is not set. Stopping PP." % game.platform)
            return False
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
                    newFileName = game.name + " CD" + str(index + 1) + extension
                else:
                    newFileName = game.name + extension
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
        logFileName = fixName(game.name + ".log", self.c.replace_space_with)
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

        return success
