
# all xdm related plugin stuff you get with this line incl logger functions
from xdm.plugins import *
# other libs should be imported as you need them but why dont you have a look at the libs xdm comes with
from lib import requests
import os


class Blackhole(Downloader):
    version = "0.2"
    types = ['torrent', 'nzb']
    config_meta = {'plugin_desc': 'This will download the nzb/torrent file into the platform path. It can not check for the status of a game.'
                   }
    useConfigsForElementsAs = 'Path'

    def addDownload(self, download):
        b_dir = self._getPath(download.element)
        if not os.path.isdir(b_dir):
            log.info("Download save to Blackhole at %s is not a valid folder" % b_dir)

        dst = os.path.join(b_dir, self._downloadName(download) + self._getTypeExtension(download.type))
        r = requests.get(download.url)
        if r.status_code == 200:
            with open(dst, 'wb') as f:
                for chunk in r.iter_content():
                    f.write(chunk)
        else:
            log.info("Download save to Blackhole at %s failed" % dst)
            return False

        log.info("Download saved to Blackhole at %s" % dst)
        return True
