# Author: Dennis Lutter <lad1337@gmail.com>
# URL: https://github.com/lad1337/XDM
#
# This file is part of XDM: eXtentable Download Manager.
#
#XDM: eXtentable Download Manager. Plugin based media collection manager.
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

import datetime
import xml.etree.ElementTree as ET
from lib import requests
import re
from lib.dateutil.parser import parser as dateParser


class TheGamesDB(Provider):
    version = "0.11"
    _tag = 'tgdb'
    single = True
    types = ['de.lad1337.games']
    _config = {'enabled': True}
    config_meta = {'plugin_desc': 'THE information provider for games. Missing anything? check out http://thegamesdb.net'
                   }
    _pCache = {}

    def _boxartUrl(self, tag, platformID, base_url, type='front'):
        if tag is not None:
            imageTags = tag.getiterator('boxart')
            if imageTags:
                for curImage in imageTags:
                    if curImage.get('side') == type:
                        return base_url + curImage.text

        return base_url + "_platformviewcache/platform/boxart/" + platformID + "-1.jpg"

    def _fanartUrl(self, tag, base_url, type='original'):
        if tag is not None:
            fanartTag = tag.find('fanart')
            if fanartTag is not None:
                if type == 'original':
                    imageSiteTag = fanartTag.find('original')
                else:
                    imageSiteTag = fanartTag.find('thumb')
                if imageSiteTag is not None:
                    return base_url + imageSiteTag.text
        #print "could not find a fanart"
        return ""

    def _genresStr(self, tag):
        if tag is None:
            return "n/a"

        genres = []
        for curG in tag.getiterator('genre'):
            genres.append(curG.text)
        return ", ".join(genres)

    def _createGameFromTag(self, game_tag, base_url, rootElement):
        titleTag = game_tag.find('GameTitle')
        idTag = game_tag.find('id')
        platformTag = game_tag.find('Platform')
        platformIDTag = game_tag.find('PlatformId')
        imagesTag = game_tag.find('Images')
        genresTag = game_tag.find('Genres')
        overview = game_tag.find('Overview')
        release_date = game_tag.find('ReleaseDate')
        trailer = game_tag.find('Youtube')

        if titleTag is None or idTag is None or platformTag is None or platformIDTag is None:
            log("Not enough info to create game")
            return None
        """if overview != None:
            g.overview = overview.text
        if trailer != None:
            g.trailer = trailer.text
        """

        g = Element()
        g.type = 'Game'
        g.mediaType = MediaType.get(MediaType.identifier == 'de.lad1337.games')
        g.setField('id', int(idTag.text), self.tag)
        g.setField('name', titleTag.text, self.tag)
        g.setField('front_image', self._boxartUrl(imagesTag, platformIDTag.text, base_url, 'front'), self.tag)
        g.setField('fanart_image', self._fanartUrl(imagesTag, base_url, 'original'), self.tag)
        g.setField('genre', self._genresStr(genresTag), self.tag)

        if release_date is not None:
            try:
                g.setField('release_date', datetime.datetime.strptime(release_date.text, "%m/%d/%Y"), self.tag)
            except ValueError:
                ddd = None
                if release_date is not None:
                    ddd = dateParser(release_date.text)
                if ddd is not None and hasattr(ddd, 'year') and hasattr(ddd, 'month') and hasattr(ddd, 'day'):
                    g.setField('release_date', datetime.datetime(ddd.year, ddd.month, ddd.day), self.tag)
                else:
                    g.setField('release_date', datetime.datetime.now(), self.tag)
        else:
            g.setField('release_date', datetime.datetime.now(), self.tag)

        if trailer is not None:
            #http://stackoverflow.com/questions/2639582/python-small-regex-problem
            yid = re.search(r'(?<=\?v\=)[\w-]+', trailer.text) #the games db uses youtube urls
            g.setField('trailer', yid.group(0), self.tag)
        else:
            g.setField('trailer', '', self.tag)

        if int(platformIDTag.text) not in self._pCache:
            q = Element.select().where(Element.mediaType == rootElement.mediaType, Element.type == 'Platform')
            for e in q:
                if e.getField('id', self.tag) == int(platformIDTag.text):
                    platform = e.copy()
                    platform.parent = rootElement
                    platform.saveTemp()
                    self._pCache[int(platformIDTag.text)] = platform
                    g.parent = platform
                    g.saveTemp()
                    self.progress.addItem()
                    break
            else:
                return None
        else:
            g.parent = self._pCache[int(platformIDTag.text)]
            g.saveTemp()

            self.progress.addItem()
            return g

    def searchForElement(self, term=''):
        return self._searchForElement(term)

    def _searchForElement(self, term='', id=0):
        self.progress.reset()
        self._pCache = {}
        mt = MediaType.get(MediaType.identifier == 'de.lad1337.games')
        mtm = mt.manager
        rootElement = mtm.getFakeRoot(term)
        payload = {}
        url = 'http://thegamesdb.net/api/GetGame.php?'
        if term and not id:
            payload['name'] = term
        else:
            payload['id'] = id
        #r = requests.get('http://thegamesdb.net/api/GetGame.php', params=payload)
        r = requests.get(url, params=payload)
        log('tgdb search url ' + r.url)
        root = ET.fromstring(r.text.encode('utf-8'))

        baseImgUrlTag = root.find('baseImgUrl')
        if baseImgUrlTag is not None:
            base_url = baseImgUrlTag.text
        else:
            base_url = "http://thegamesdb.net/banners/"

        for curGame in root.getiterator('Game'):
            self._createGameFromTag(curGame, base_url, rootElement)

        log("%s found %s games" % (self.name, self.progress.count))

        return rootElement

    def getElement(self, id, element=None):
        id = int(id)
        root = self._searchForElement(id=id)
        for game in root.decendants:
            #print game, game.getField('id', self.tag), 'vs', id
            if game.getField('id', self.tag) == id:
                return game
        else:
            return False
