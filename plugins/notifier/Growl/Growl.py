from xdm.plugins import *
import gntp.notifier

class Growl(Notifier):
    version = "0.1"
    _config = {}

    def _sendEnable(self):
        return (self.sendMessage("You just enabled Growl on XDM"), {}, '')

    def _sendTest(self):
        return (self.sendMessage("Test from XDM"), {}, '')

    def sendMessage(self, msg, element=None):
        return gntp.notifier.mini(msg)

    # config_meta is at the end because otherwise the sendTest function would not be defined
    config_meta = {'plugin_buttons': {'sendTest': {'action': _sendTest, 'name': 'Send test'}},
                   'enabled': {'on_enable': [_sendEnable]},
                   'plugin_desc': 'Simple Growl notifier.'
                   }
