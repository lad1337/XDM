
from xdm.plugins import *
import os
import subprocess


class MP32iTunes(PostProcessor):
    screenName = 'MP3 2 iTunes'
    addMediaTypeOptions = 'runFor'
    config_meta = {'plugin_desc': "This will execute an apple script that adds all mp3's to iTunes of the given download. MAC OSX only!"
                   }

    def __init__(self, instance='Default'):
        print 'MP32iTunes addMediaTypeOptions', self.addMediaTypeOptions
        PostProcessor.__init__(self, instance=instance)

    def ppPath(self, element, filePath):
        scptPath = os.path.join(os.path.dirname(__file__), 'add_mp3s_to_itunes.scpt')
        if not os.path.isfile(scptPath):
            log.error("My apple script is missing. it is supposed to be at %s" % scptPath)
            return False
        output = subprocess.Popen(['osascript', scptPath, filePath], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        if output.returncode:
            log.error("Some error during subprocess call.")

        return output != 0
