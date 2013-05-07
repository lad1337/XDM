from xdm.plugins import *

from libs import discogs_client as discogs
import re


class Discogs(Provider):
    version = "0.11"
    _tag = 'discogs'
    single = True
    types = ['de.lad1337.music']
    _config = {'enabled': True,
               'search_range_select': 'master'}
    config_meta = {'plugin_desc': 'Information provider for music from http://www.discogs.com'
                   }

    search_range_select_map = {'master': {'t': 'Master Releases', 'c': ('MasterRelease',)},
                               'both': {'t': 'Master & Normal Releases', 'c': ('MasterRelease','Release')},
                               'releases': {'t': 'Releases', 'c': ('Release',)}}

    def _search_range_select(self):
        out = {}
        for i, o in self.search_range_select_map.items():
            out[i] = o['t']
        return out

    def searchForElement(self, term='', id=0):

        self.progress.reset()
        #artist = discogs.Artist('Aphex Twin')
        mt = MediaType.get(MediaType.identifier == 'de.lad1337.music')
        mts = MediaType.select().where(MediaType.identifier == 'de.lad1337.music')
        q = Element.select().where(Element.mediaType << mts, Element.type == 'Platform')
        mtm = common.PM.getMediaTypeManager('de.lad1337.music')

        if id:
            try:
                id = int(id)
                addType = 'album'
            except ValueError:
                addType = 'artist'
    
            if addType == 'album':
                res = [discogs.Release(id), discogs.MasterRelease(id)]
            elif addType == 'artist':
                res = [discogs.Artist(id)]
        else:
            log('Discogs searching for %s' % term)
            s = discogs.Search(term)
            res = s.results()

        root = mtm.getFakeRoot(term)
        filtered = [album for album in res if album.__class__.__name__ in self.search_range_select_map[self.c.search_range_select]['c']]
        self.progress.total = len(filtered)

        for r in filtered:
            self.progress.addItem()
            #print '\n\n\n\n\n\n\n', r.data['formats'], r.data['status']
            if r.__class__.__name__ == 'Release':
                if r.data['formats'][0]['name'] != 'CD' or not r.data['year']:
                    continue

            artist = r.artists[0]
            # some artist names we get have some wiered (2) or (1) at the end
            artistName = re.sub(r'\(\d{1,2}\)$', '', artist.name)

            try:
                artistElement = Element.getWhereField(mt, 'Artist', {'id': artistName}, self.tag, root)
            except Element.DoesNotExist:
                artistElement = Element()
                artistElement.mediaType = mt
                artistElement.parent = root
                artistElement.type = 'Artist'
                artistElement.setField('name', artistName, self.tag)
                artistElement.setField('id', artistName, self.tag)
                artistElement.saveTemp()
            try:
                albumElement = Element.getWhereField(mt, 'Album', {'id': r.data['id']}, self.tag, artistElement)
            except Element.DoesNotExist:
                albumElement = Element()
                albumElement.mediaType = mt
                albumElement.parent = artistElement
                albumElement.type = 'Album'
                albumElement.setField('name', r.title, self.tag)
                albumElement.setField('year', r.data['year'], self.tag)
                albumElement.setField('id', r.data['id'], self.tag)
                if 'images' in r.data:
                    for img in r.data['images']:
                        if img['uri']:
                            albumElement.setField('cover_image', img['uri'], self.tag)
                            break
                albumElement.saveTemp()
                for track in r.tracklist:
                    trackElement = Element()
                    trackElement.mediaType = mt
                    trackElement.parent = albumElement
                    trackElement.type = 'Song'
                    trackElement.setField('title', track['title'], self.tag)
                    trackElement.setField('length', track['duration'], self.tag)
                    trackElement.setField('position', track['position'], self.tag)
                    trackElement.saveTemp()
                albumElement.downloadImages()

        return root

    def getElement(self, id):
        for ele in self.searchForElement(id=id):
            if ele.getField('id', self.tag) == id:
                return ele
        else:
            return False
