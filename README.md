XDM
===

XDM: Xtentable Download Manager.
Plugin based media collection manager.

XDM is at ALPHA STAGE

Notes on the plugin development api (not final nor complete)
--
Plugin Class attributes:

addMediaTypeOptions (bool / list / str):
Should options defined by the MediaType be added to your plugin.
This is not done for plugins of the type: MediaTypeManager and System

bool:
- Default: True, this will add all options defined by the MediaType.
- False will add no options.
list:
- a list of MediaType identifiers e.g. ['de.lad1337.music','de.lad1337.games'], this will add only options from the MediaType with the given identifier
str:
- only str value allowed is 'runFor', this will only add runFor options to your plugin.

useConfigsForElementsAs (str):
How do you want to use the options for your plugin.
Setting this to e.g. 'Path' will create config options that have a file browser in the system settings and the appropriate human name/label.


str:
- Default: 'Category'

You can retrive the config value by running self._get<useConfigsForElementsAs>(element)
e.g. self._getCategory(element) or self._getPath(element).
The function will return the value set in the config or None.
NOTE: MediaType plugins can force this option and you will not be able to retrive it with self._get<useConfigsForElementsAs>(element)


