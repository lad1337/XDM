from xdm.plugins import *
from lib import requests


class Boxcar(Notifier):
    version = "0.4"
    _config = {'email': '',
               'screenname': 'XDM'}

    def _sendTest(self):
        log("Testing boxcar")
        self.sendMessage("You just enabled Boxcar on Gamez")

    def sendMessage(self, msg, game=None):
        raise Exception('something is wrong in this plugin')
        if not self.c.email:
            log.error("Boxcar email / user not set")
            return

        payload = {'notification[from_screen_name]': self.c.screenname,
                   'email': self.c.email,
                   'notification[message]': msg}

        r = requests.post('http://boxcar.io/devices/providers/MH0S7xOFSwVLNvNhTpiC/notifications', payload)
        log("boxbar url: %s payload: %s" % (r.url, payload))
        log("boxcar code %s" % r.status_code)

    # config_meta is at the end because otherwise the sendTest function would not be defined
    config_meta = {'enabled': {'on_enable': [_sendTest]},
                   'plugin_desc': 'Simple Boxcar.io notifier. Enable the Monitor Service at Boxcar.io'
                   }
