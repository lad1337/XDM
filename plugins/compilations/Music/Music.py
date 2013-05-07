

from xdm.plugins import *
from xdm.helper import replaceUmlaute


class Song(object):
    position = 0
    title = ''
    lenght = 0.0

    _orderBy = 'position'

    def getTemplate(self):
        return '<li class="bORw"><span class="songPosition bORw">{{this.position}}</span><span class="songTitle bORw">{{this.title}}</span><span class="length bORw">{{this.length}}</span></li>'


class Album(object):
    name = ''
    year = 0
    cover_image = ''

    _orderBy = 'year'

    def getTemplate(self):
        return """<div class="Album {{statusCssClass}}">
                      <img src="{{this.cover_image}}">
                      <p>{{name}}<br><span class="artistName">{{this.parent.name}}</span></p>
                      <div class="indi">&#x25B2;</div>
                      <div class="songs">
                          <div class="info">
                              <strong class="bORw">{{name}}</strong>{{actions}}{{status}}
                              <p class="bORw">{{this.parent.name}} ({{this.year}})</p>
                          </div>
                          <ol class="bORw">{{children}}</ol>
                      </div>
                  </div>
                """

    def getSearchTerms(self):
        terms = ['%s %s' % (self.parent.name, self.name)]
        german_fixed = []
        for term in terms:
            replaced = replaceUmlaute(term)
            if replaced != term:
                german_fixed.append(replaceUmlaute(term))
        return terms + german_fixed

    def getName(self):
        return self.name


class Artist(object):
    name = ''
    bio = ''

    _orderBy = 'name'

    def getName(self):
        return self.name

    def getTemplate(self):
        return '{{children}}'


class Music(MediaTypeManager):
    single = True
    _config = {'enabled': True}
    config_meta = {'plugin_desc': 'Music support. Good for Albums'}
    order = (Artist, Album, Song)
    download = Album
    identifier = 'de.lad1337.music'
    addConfig = {}
    addConfig[Downloader] = [{'type':'category', 'default': None, 'prefix': 'Category for', 'sufix': 'Music'}]
    addConfig[Indexer] = [{'type':'category', 'default': None, 'prefix': 'Category for', 'sufix': 'Music'}]
    addConfig[PostProcessor] = [{'type':'path', 'default': None, 'prefix': 'Final path for', 'sufix': 'Music'}]

    def makeReal(self, album):
        oldArtist = album.parent
        for artist in Element.select().where(Element.type == oldArtist.type,
                                             Element.mediaType == self.mt,
                                             Element.parent == self.root):
            if artist.getField('id') == oldArtist.getField('id'):
                album.parent = artist
                album.status = common.getStatusByID(self.c.default_new_status_select)
                album.save()
                album.downloadImages()
                return True
        else:
            log('We dont have the artist so we copy that')
            newArtist = album.parent.copy()
            newArtist.parent = self.root
            newArtist.save()
            album.parent = newArtist
            album.status = common.getStatusByID(self.c.default_new_status_select)
            album.save()
            for song in album.children:
                song.save()
            album.downloadImages()
            return True

    def headInject(self):
        return """
        <link rel="stylesheet" href="/Music/style.css">
        <script src="/Music/script.js"></script>
        """
