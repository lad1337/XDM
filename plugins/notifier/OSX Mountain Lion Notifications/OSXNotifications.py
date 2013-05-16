from xdm.plugins import *
from pync import Notifier as OSXNotifier

class OSXNotifications(Notifier):
    screenName = 'OSX Notification Center'
    identifier = 'de.lad1337.osxnotifications'
    version = "0.1"
    _config = {}
    single = True

    def _sendEnable(self):
        return (self.sendMessage("You just enabled OSX Notifications on XDM"), {}, '')

    def _sendTest(self):
        return (self.sendMessage("Test from XDM"), {}, '')

    def sendMessage(self, msg, element=None):
        code = OSXNotifier.notify(msg, title='XDM').poll()
        return code != 0

    # config_meta is at the end because otherwise the sendTest function would not be defined
    config_meta = {'plugin_buttons': {'sendTest': {'action': _sendTest, 'name': 'Send test'}},
                   'enabled': {'on_enable': [_sendEnable]},
                   'plugin_desc': 'Sends Mac OS 10.8 Notification Center notifications. It will appear as "terminal-notifer" in the system settings.'
                   }
