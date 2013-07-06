# -*- coding: utf-8 -*-
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
from xdm.helper import replaceUmlaute


class Umlaute(SearchTermFilter):
    version = "0.1"
    _config = {}
    config_meta = {'plugin_desc': u'For each search term generate another one where ä is replaced with ae and so forth.'}

    def compare(self, element, terms):
        log('Fixing umlaute for %s and %s' % (element, terms))
        out = list(terms)
        for t in terms:
            out.append(replaceUmlaute(t))
        return out
