from xdm.plugins import *
import re


class RegEx(Filter):
    version = "0.1"
    addMediaTypeOptions = 'runFor'
    _config = {'regex': '.*',
               'positive': True,
               'case_sensitive': False}
    config_meta = {'plugin_desc': 'Reject Search terms or Downloads based on regular expressions',
                   'positive': {'human': 'Accept term/download if RegEx matches'}}

    def compare(self, element=None, download=None, string=None):
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

        pattern = re.compile(rawRegex)
        if self.c.case_sensitive:
            result = pattern.match(string)
        else:
            result = pattern.match(string, re.I)
        return (result == self.c.positive, string)
