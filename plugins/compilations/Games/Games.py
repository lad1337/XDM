from xdm.plugins import *


class Game(object):
    name = ''
    genres = ''
    describtion = ''
    front_image = ''
    back_image = ''
    release_date = datetime.datetime.now()

    _orderBy = 'name'

    def getTemplate(self):
        # me is the object !!
        # each field can be accesed directly
        # special stiff like {{actions}} will be explained defined later
        # {{image}} will return the field value
        # {{this.image}} will return the local src
        # {{this.getField('image')}} will return the image obj. str(Image) is the local src
        return """
        <tr class="game">
            <td>{{actions}}{{status}}</td>
            <td style="width:200px;height:282px;position:relative;" class="coverContainer">
            <div class="cover">
                <div class="back">
                    <img class="back" src="{{this.back_image}}" width=200/>
                </div>
                <div class="front">
                    <img class="front" src="{{this.front_image}}" width=200/>
                </div>
            </div>
            </td>
            <td>{{name}}<!-- and {{this.name}} and {{this.getName()}}--></td>
            <td>{{this.parent.alias}}</td>
        </tr>
        """

    """def asdadagetSearchTpl(self):
        return self.parent.paint(single=True).replace('{{children}}', self.getTpl())"""

    def getSearchTerms(self):
        return [self.name]

    def getName(self):
        return '%s' % self.name


class Platform(object):
    name = ''
    alias = ''
    _orderBy = 'alias'
    def getTemplate(self):
        return """
        <div class="platform">
            <h3 style="display:none;">{{this.name}}</h3>
            <table>
            <tbody>
            {{children}}
            </tbody>
            </table>
        </div>
        """

    def getName(self):
        return '%s' % self.name


class Games(MediaTypeManager):
    _config = {'enabled': True}
    config_meta = {'plugin_desc': 'Games support. For, Wii, Wii U, Xbox 360, PS3 and PC'}
    order = (Platform, Game)
    download = Game
    #TODO: implement that stuff or dont ... donno
    """# if a value for a interval is smaller then 24h it will create a shedular in that interval on longer intervals
    # it will write the next check date into the config db and a generic shedular will check that every 12h
    schedule = {'update': {Game: {'default': 122400}, Platform: {'default': 3600*21}}, # update all games every 24h and update the Platforms every 21 days
                'search': {Game: {'default': 3600}}, # search for wanted games every hour
                'check': {Game: {'default': 180}}} # check for a game in the downloaders every 3 minutes"""
    # some plugins will get configs based on all Elements of the type
    # empty tuple for none you want to add
    # this will add configs for all the below items to other plugins
    # each plugin can choose what / how the config is used for
    # e.g. the sab plugin adds categories for each platform and the black hole downloader adds paths for each categorie
    elementConfigsFor = (Platform,)
    # a unique identifier for this mediatype
    identifier = 'de.lad1337.games'
    addConfig = {}
    addConfig[Indexer] = [{'type':'category', 'default': None, 'prefix': 'Category for', 'sufix': 'Games'}]
    defaultElements = {}
    defaultElements[Platform] = [{'tgdb':{'name': 'Nintendo Wii', 'alias':'Wii', 'id': 9}},
                                 {'tgdb':{'name': 'Microsoft Xbox 360', 'alias': 'Xbox360', 'id': 15}},
                                 {'tgdb':{'name': 'Sony Playstation 3', 'alias': 'PS3', 'id': 12}},
                                 {'tgdb':{'name': 'PC', 'alias': 'PC', 'id': 1}},
                                 {'tgdb':{'name': 'Nintendo Wii U', 'alias': 'WiiU', 'id': 38}}]

    def makeReal(self, game):
        oldPlatform = game.parent
        for platform in Element.select().where(Element.type == oldPlatform.type, Element.mediaType == self.mt):
            if platform.getField('id') == oldPlatform.getField('id'):
                break
        else:
            log.error('We dont have the platform we need in the db ... what is this?')
            return False
        game.parent = platform
        game.status = common.getStatusByID(self.c.default_new_status_select)
        game.save()
        game.downloadImages()
        return True

    def headInject(self):
        return """
        <link rel="stylesheet" href="/Games/style.css">
        """

