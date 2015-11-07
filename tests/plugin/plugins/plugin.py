from xdm.plugin.base import Plugin


class MyPlugin(Plugin):

    @Plugin.register
    def download(self, download):
        return download
