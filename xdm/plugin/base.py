import re

from xdm.constant import model
from xdm.model import Download


class Plugin():
    app = None

    def __init__(self, app, instance_name=None):
        self.instance_name = instance_name or 'default'
        self.app = app

    @staticmethod
    def register(func):
        func.hook = True
        return func


class System(Plugin):
    pass


class Notifier(Plugin):
    pass


class MediaTypeManager(Plugin):
    pass


class DownloadType(Plugin):
    """These plugins define the type of download like NZB."""
    _type = 'DownloadType'
    single = True
    addMediaTypeOptions = False
    extension = ''
    """The file extension if a file is created for this DownloadType"""
    identifier = ''
    """A absolute unique identifier in reverse URL style e.g. de.lad1337.nzb"""


class Downloader(Plugin):
    """These plugins of this class send Downloads to another Programs or directly download stuff."""
    types = []  # types the downloader can handle ... e.g. blackhole can handle both

    def add_download(self, download):
        """Add/download a Download to this downloader

        Arguments:
        download -- an Download object

        return:
        bool if the adding was successful
        >>>> False
        """
        return False

    def get_staus(self, element):
        """Get the staus of element that it has in this downloader

        Arguments:
        element -- an Element object

        return:
        tuple of Status, Download and a path (str)
        >>>> (model.UNKNOWN, Download(), '')
        """
        return (model.UNKNOWN, Download(), '')

    def _downloadName(self, download):
        """tmplate on how to call the nzb/torrent file. nzb_name for sab"""
        return "%s (XDM.%s-%s)" % (download.element.getName(), download.element.id, download.id)

    def _find_ids(self, strig):
        """find the element id and download id in s is based on the _downloadName()"""
        m = re.search("\((XDM.(?P<gid>\d+)-(?P<did>\d+))\)", strig)
        element_id, download_id = 0, 0
        if m and m.group('gid'):
            element_id = int(m.group('gid'))
        if m and m.group('did'):
            download_id = int(m.group('did'))
        return (element_id, download_id)

    def _find_element_id(self, s):
        return self._find_ids(s)[0]

    def _find_download_id(self, s):
        return self._find_ids(s)[1]
