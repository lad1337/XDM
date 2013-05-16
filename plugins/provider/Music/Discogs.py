# Author: Dennis Lutter <lad1337@gmail.com>
# URL: https://github.com/lad1337/XDM
#
# This file is part of XDM: Xtentable Download Manager.
#
#XDM: Xtentable Download Manager. Plugin based media collection manager.
#Copyright (C) 2013  Dennis Lutter
#
#XDM is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.
#
#XDM is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.
#
#You should have received a copy of the GNU General Public License
#along with this program.  If not, see http://www.gnu.org/licenses/.

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
    config_meta = {'plugin_desc': 'Information provider for music from http://www.discogs.com. Note: Image download is limited to 1000 per 24h per IP'
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
        mediatype = MediaType.get(MediaType.identifier == 'de.lad1337.music')
        mtm = common.PM.getMediaTypeManager('de.lad1337.music')[0]

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

        fakeRoot = mtm.getFakeRoot(term)
        filtered = [album for album in res if album.__class__.__name__ in self.search_range_select_map[self.c.search_range_select]['c']]
        self.progress.total = len(filtered)

        for release in filtered:
            self.progress.addItem()
            #print '\n\n\n\n\n\n\n', release.data['formats'], release.data['status']
            if release.__class__.__name__ == 'Release':
                if release.data['formats'][0]['name'] != 'CD' or not release.data['year']:
                    continue
            self._createAlbum(fakeRoot, mediatype, release)

        return fakeRoot

    def _createAlbum(self, fakeRoot, mediaType, release):

        artist = release.artists[0]
        artistName = re.sub(r'\(\d{1,2}\)$', '', artist.name)
        try:
            artistElement = Element.getWhereField(mediaType, 'Artist', {'id': artistName}, self.tag, fakeRoot)
        except Element.DoesNotExist:
            artistElement = Element()
            artistElement.mediaType = mediaType
            artistElement.parent = fakeRoot
            artistElement.type = 'Artist'
            artistElement.setField('name', artistName, self.tag)
            artistElement.setField('id', artistName, self.tag)
            artistElement.saveTemp()
        try:
            albumElement = Element.getWhereField(mediaType, 'Album', {'id': release.data['id']}, self.tag, artistElement)
        except Element.DoesNotExist:
            albumElement = Element()
            albumElement.mediaType = mediaType
            albumElement.parent = artistElement
            albumElement.type = 'Album'
            albumElement.setField('name', release.title, self.tag)
            albumElement.setField('year', release.data['year'], self.tag)
            albumElement.setField('id', release.data['id'], self.tag)
            if 'images' in release.data:
                for img in release.data['images']:
                    if img['uri']:
                        albumElement.setField('cover_image', img['uri'], self.tag)
                        break
            albumElement.saveTemp()
            for track in release.tracklist:
                trackElement = Element()
                trackElement.mediaType = mediaType
                trackElement.parent = albumElement
                trackElement.type = 'Song'
                trackElement.setField('title', track['title'], self.tag)
                trackElement.setField('length', track['duration'], self.tag)
                trackElement.setField('position', track['position'], self.tag)
                trackElement.saveTemp()
            albumElement.downloadImages()

    def getElement(self, id):
        mt = MediaType.get(MediaType.identifier == 'de.lad1337.music')
        mtm = common.PM.getMediaTypeManager('de.lad1337.music')[0]
        fakeRoot = mtm.getFakeRoot('%s ID: %s' % (self.tag, id))
        release = discogs.Release(id)
        self._createAlbum(fakeRoot, mt, release)

        for ele in fakeRoot.decendants:
            if ele.getField('id', self.tag) == id:
                return ele
        else:
            return False
