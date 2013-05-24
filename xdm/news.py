# -*- coding: utf-8 -*-
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

import xdm
from lib import feedparser

XDM_FEED_URL = 'http://xdm.lad1337.de/?feed=rss2'


class NewsManager(object):

    def __init__(self):
        self.feed = None
        self.news = []

    def cache(self):
        xdm.common.MM.clearRole('news')
        self.news = []
        self.feed = feedparser.parse(XDM_FEED_URL)
        for e in self.feed.entries:
            tags = []
            for tag in e.tags:
                tags.append(tag['term'])
            self.news.append(SimpleNews(e.summary_detail.value, e.link, tags))


class SimpleNews(object):

    def __init__(self, message, link, tags):
        self.message = message
        self.link = link
        self.tags = tags
