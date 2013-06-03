
Plugins
*******

Contents:

.. toctree::
    :glob:
 
    *


Getting started
===============
Things you should know:

- Each plugin is a subclass one of the `plugin types`_.
- A .py file can contain multiple plugins.
- If you have a folder structure the main foler must be a python module.

Plugins are loaded dynamically by traversing the *core plugin path* and the extraPluginPath, each .py file is checked for any of the `plugin type`_ classes.

.. _`plugin type`: #plugin-types

Basic folderstructure::

    <extraPluginFolder>-+
                        |
                        +-<My Plugin Folder>-+
                                             |
                                             +- __init__.py (empty file)
                                             |
                                             +- <My Plugin .py>
                                             |
                                             +- <more .py that the plugin needs> (optional)
                                             |
                                             +- <folder with libarys> (optional)
                                             |
                                             +- pluginRootLibarys (optional)

.. note::

    Not all .py files are checked. Files that start with '__' or files that are in a folder called `pluginRootLibarys`_ are **not** checked for plugins.

A simple notification plugin
----------------------------
The file structure for this would look like::

    <extraPluginFolder>-+
                        |
                        +-Printer-+
                                  |
                                  +- __init__.py
                                  |
                                  +- Printer.py
                 
Contents of ``printer.py``:

.. code-block:: python

    from xdm.plugins import * # by using this one import line you have everything a plugin will need from XDM
    
    class Printer(Notifier): # subclass Notifier 
    
        def sendMessage(msg, element=None)
            print msg
            return True

This is absolutely sufficient for a Notifier plugin.

Adding configuration
--------------------

To create settings simply fill the `_config` attribute of your plugin class:

.. code-block:: python

    from xdm.plugins import * # by using this one import line you have everything a plugin will need from XDM
    
    class Printer(Notifier): # subclass Notifier 
        _config = {'add_message': 'my print plugin'}
    
        def sendMessage(msg, element=None)
            print msg
            return True

This will create a text field in on the settings page and the default value is `my print plugin`.

Each type of default value will determine the input field in the settings

:str:
    Text input field

:bool:
    Checkbox

:int / float:
    Number input field

.. note::

    Only these type are allowed as config values!

To get the config value access the ``c`` object of you plugin and then the attribute with the name of your config.

.. code-block:: python

    from xdm.plugins import *
    
    class Printer(Notifier):
        _config = {'add_message': 'my print plugin'}

        def sendMessage(msg, element=None)
            userAddition = self.c.add_message # just make sure its the same spelling as the key in the config
            print msg + userAddition
            return True

.. note::

    ``self.c`` is only available *after* the __init__() of Plugin_. 

It was never explained how the `add_message` is used, to change that we use the ``config_meta`` attribute.

.. code-block:: python

    from xdm.plugins import *
    
    class Printer(Notifier):
        _config = {'add_message': 'my print plugin'}
        # add_message: same key as in _config
        config_meta = {'add_message': {'human': 'Additional text', # a more human friendly name
                                        'desc': 'This text will be added after every printed message'}}
                                        # the description will be a tooltip on the input field

        def sendMessage(msg, element=None)
            userAddition = self.c.add_message
            print msg + userAddition
            return True

More info on `Plugin configuration`_

.. _`Plugin configuration`: plugin_config.html


Reserved attributes
===================
Following class / instance attributes are reserved and **are not to be set** by a plugin!

c
    The configuration manager

type
    The class name e.g. `Printer`

_type
    Its the plugin type name e.g. `Downloader`

instance
    The instance name
    
name
    The class name and instance name e.g. `Printer (Default)`
    
More info see Plugin_

Plugin Types
============

DownloadType_
    A simple description of a download type.

Downloader_
    These plugins provider the connection to the downloader programs

Indexer_
    These plugins provide connection to the sites that have information on releases

Notifier_
    These plugins provide means to send notification to third party services or other program’s on certain events

Provider_
    These plugins connect to databases and create elements based on the media type they work for.

PostProcessor_
    These plugins move rename or do whatever they like with a given path and element.

System_
    Well there is only one of this kind and maybe there will never be more. The system config is a plugin of this type

DownloadFilter_
    These plugins can filter found downloads as they wish.

SearchTermFilter_
    These plugins can add or remove search terms, before they are used by the Provider_

MediaAdder_
    These plugins can add elements. From various sources e.g. `Trakt.tv`_ watchlist.

MediaTypeManager_
    These plugins are the core of XDM. These plugins define the structure of a media type and provide functions to save and store them. The look is also defined here.


.. _DownloadType: DownloadType.html
.. _Downloader: Downloader.html
.. _Indexer: Indexer.html
.. _Notifier: Notifier.html
.. _Provider: Provider.html
.. _PostProcessor: PostProcessor.html
.. _System: System.html
.. _DownloadFilter: DownloadFilter.html
.. _SearchTermFilter: SearchTermFilter_.html
.. _MediaAdder: MediaAdder.html
.. _MediaTypeManager: MediaTypeManager.html

.. _`Trakt.tv`: http://trakt.tv


PluginRootLibarys
=================
If you need to include a library that expects to by installed system wide,
therefore being in the python path can be used when put in a folder called **pluginRootLibarys**.
The absolute path of that folder is added to the python path.

.. note::

    An info level message when the path is added it created.
    
Plugin
======

.. autoclass:: xdm.plugins.bases.Plugin
    :members:
    :private-members:
