from xdm.plugins import *


class NZB(DownloadType):
    version = "0.1"
    identifier = 'de.lad1337.nzb'
    extension = 'nzb'
    _config = {'enabled': True}
    config_meta = {'plugin_desc': 'NZB / Usenet download type.'}