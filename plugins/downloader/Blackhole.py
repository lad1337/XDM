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

# all xdm related plugin stuff you get with this line incl logger functions
from xdm.plugins import *
# other libs should be imported as you need them but why dont you have a look at the libs xdm comes with
from lib import requests
import os


class Blackhole(Downloader):
    version = "0.2"
    types = []
    config_meta = {'plugin_desc': 'This will download the nzb/torrent file into the platform path. It can not check for the status of a game.'
                   }
    useConfigsForElementsAs = 'Path'

    def addDownload(self, download):
        b_dir = self._getPath(download.element)
        if not os.path.isdir(b_dir):
            log.info("Download save to Blackhole at %s is not a valid folder" % b_dir)

        dst = os.path.join(b_dir, '%s.%s' % (self._downloadName(download), self._getDownloadTypeExtension(download.type)))
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
