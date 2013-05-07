
from xdm.plugins import *
import os
import subprocess


class MP32iTunes(PostProcessor):
    screenName = 'MP3 2 iTunes'
    _config = {'delete_files': False,
               'update_match': False,
               'hide_itunes': False}
    addMediaTypeOptions = 'runFor'
    config_meta = {'plugin_desc': "This will execute an apple script that adds all mp3's/m4a's to iTunes of the given download. MAC OSX only!",
                   'delete_files': {'human': "Delete the processed files"},
                   'update_match': {'human': 'Update iTunes match after completion'}
                   }

    def ppPath(self, element, filePath):
        scptPath = os.path.join(os.path.dirname(__file__), 'add_mp3s_to_itunes.scpt')
        log.info('MP32iTunes will run pp on %s' % filePath)
        if not os.path.isfile(scptPath):
            log.error("My apple script is missing. it is supposed to be at %s" % scptPath)
            return False

        process = subprocess.Popen(['osascript', scptPath, filePath, str(int(self.c.delete_files)), str(int(self.c.update_match)), str(int(self.c.hide_itunes))], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        process.communicate()

        if process.returncode:
            log.error("Some error during subprocess call.")

        return process.returncode == 0
