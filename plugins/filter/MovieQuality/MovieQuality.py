from xdm.plugins import *
import guessit


class MovieQuality(Filter):
    version = "0.1"
    screenName = 'Movie Quality'
    addMediaTypeOptions = 'runFor'
    _config = {'format_select': '',
               'screenSize_select': '',
               'audioCodec_select': '',
               'any_all_select': ''}

    elementConfig = {'format_select': 'format_select',
                     'screenSize_select': 'screenSize_select',
                     'audioCodec_select': 'audioCodec_select',
                     'any_all_select': 'any_all_select'}

    def __init__(self, instance='Default'):
        """
        example of how to add all qualitys as checkboxes to the default config and each element
        and set the global value as the default for the element
        for attrName in dir(self):
            if attrName.startswith('quality_'):
                self._config['%s_enable' % attrName] = False
                self.elementConfig['%s_enable' % attrName] = '%s_enable' % attrName
        """
        self._config['run_on_hook_select'] = common.FOUNDDOWNLOADS
        Filter.__init__(self, instance=instance)

    def compare(self, element=None, download=None, string=None):
        guess = guessit.guess_movie_info(download.name, info=['filename'])
        self.e.getConfigsFor(element) #this will load all the elements configs
        # into the the self.e cache
        # needed for .<config_name_access>

        finalReason = []
        for attribute in ('format_select', 'screenSize_select', 'audioCodec_select'):
            attributeGuessName = attribute[:-7]
            attributeElementConfigValue = self.e.getConfig(attribute, element).value
            if attributeElementConfigValue == 'any': # current is any so we accept anything !
                finalReason.append('%s can be anything' % attributeGuessName)
                continue
            # attribute not set in guessit and current setting is not any (see above)
            # so we cant say we wan this one
            if attributeGuessName not in guess:
                return self.FilterResult(False, 'needed %s not in guess' % attributeGuessName)

            if guess[attributeGuessName] == attributeElementConfigValue:
                if self.e.any_all_select == 'any':
                    return self.FilterResult(True, '%s is correct with %s and we only needed one to be correct.' % (attributeGuessName, attributeElementConfigValue))
                else:
                    finalReason.append('%s is correct with %s' % (attributeGuessName, attributeElementConfigValue))
            elif self.e.any_all_select == 'any':
                finalReason.append('%s can be anything and it was %s' % (attributeGuessName, guess[attributeGuessName]))
                continue # lets try the next one
            elif self.e.any_all_select == 'all':
                return self.FilterResult(False, '%s is %s but we want %s and we only needed one to be correct.' % (attributeGuessName, guess[attributeGuessName], attributeElementConfigValue))
        else: # all cool
            return self.FilterResult(True, 'Everything looked great %s.' % ', '.join(finalReason))

    def _format_select(self):
        out = {'any': 'Any'}
        for formatName, notUsed in guessit.patterns.prop_multi['format'].items():
            out[formatName] = formatName
        return out

    def _screenSize_select(self):
        out = {'any': 'Any'}
        for screenSizeName, notUsed in guessit.patterns.prop_multi['screenSize'].items():
            out[screenSizeName] = screenSizeName
        return out

    def _audioCodec_select(self):
        out = {'any': 'Any'}
        for audioCodecName, notUsed in guessit.patterns.prop_multi['audioCodec'].items():
            out[audioCodecName] = audioCodecName
        return out

    def _any_all_select(self):
        return {'any': 'any', 'all': 'all'}
