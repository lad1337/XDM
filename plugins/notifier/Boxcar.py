from xdm.plugins import *
from lib import requests


class Boxcar(Notifier):
    version = "0.4"
    addMediaTypeOptions = 'runFor'
    _config = {'email': '',
               'screenname': 'XDM'}

    def _sendTest(self, email, screenname):
        log("Testing boxcar")
        result = self._sendMessage("Test from XDM", email, screenname, None)
        return (result, {}, 'Message send. Check your device(s)')
    _sendTest.args = ['email', 'screenname']

    def _sendEnabled(self):
        log("Testing boxcar")
        self.sendMessage("You just enabled Boxcar on XDM")

    def sendMessage(self, msg, element=None):
        if not self.c.email:
            log.error("Boxcar email / user not set")
            return False
        return self._sendMessage(msg, self.c.email, self.c.screenname, element)

    def _sendMessage(self, msg, email, screenname, element):

        payload = {'notification[from_screen_name]': screenname,
                   'email': email,
                   'notification[message]': msg}

        r = requests.post('http://boxcar.io/devices/providers/MH0S7xOFSwVLNvNhTpiC/notifications', payload)
        log("boxbar url: %s payload: %s" % (r.url, payload))
        log("boxcar code %s" % r.status_code)
        return r.status_code == requests.codes.ok

    # config_meta is at the end because otherwise the sendTest function would not be defined
    config_meta = {'enabled': {'on_enable': [_sendEnabled]},
                   'plugin_buttons': {'sendTest': {'action': _sendTest, 'name': 'Send test'}},
                   'plugin_desc': 'Simple Boxcar.io notifier. Enable the Monitor Service at Boxcar.io'
                   }
