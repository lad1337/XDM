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
import re


class RegEx(DownloadFilter):
    version = "0.2"
    #addMediaTypeOptions = 'runFor'
    useConfigsForElementsAs = 'Enable'
    _config = {'regex': '.*',
               'positive': True,
               'case_sensitive': False}
    config_meta = {'plugin_desc': 'Reject Search terms or Downloads based on regular expressions',
                   'positive': {'human': 'Accept term/download if RegEx matches'}}

    def compare(self, element=None, download=None, string=None):
        if element is not None:
            if not self._getEnable(element):
                self.FilterResult(True, string)
        else:
            # cant check if i should run
            return self.FilterResult(True, 'No element given')

        if string is None:
            string = download.name

        rawRegex = self.c.regex
        fieldNamesPattern = re.compile(r'{{.*}}')
        for fieldNameCombi in re.findall(fieldNamesPattern, rawRegex):
            parts = fieldNameCombi.split('_')
            fieldName = parts[0]
            providerTag = ''
            if len(parts) > 1:
                providerTag = parts[1]
            replacement = element.getField('fieldname', providerTag)
            if replacement is None:
                replacement = ''
            rawRegex = rawRegex.replace('{{' + fieldName + '}}', replacement)

        pattern = re.compile(rawRegex) if self.c.case_sensitive else re.compile(rawRegex, re.I)
        result = pattern.match(string)

        return self.FilterResult(bool(result) == bool(self.c.positive), string)
