from xdm.plugins import *


class Torrent(DownloadType):
    version = "0.1"
    identifier = 'de.lad1337.torrent'
    extension = 'torrent'
    _config = {'enabled': True}
    config_meta = {'plugin_desc': 'Torrent download type.'}