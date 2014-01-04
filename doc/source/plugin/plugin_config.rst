
Plugin configuration
********************

Contents:

.. toctree::

XDM provides a framework to store basic configuration and display there form fields on the settings page.

There are three types of plugins config "scopes":

.. list-table::
   :widths: 20 20 40 40
   :header-rows: 1

   * - type/scope
     - access
     - defined in
     - meta defined in
   * - normal
     - ``self.c``
     - `_config`
     - `config_meta`
   * - hidden
     - ``self.hc``
     - `_hidden_config`
     - `hidden_config_meta`
   * - element
     - ``self.e``
     - `_config`
     - `config_meta`

Example
=======

To create settings simply fill the `_config` attribute of your plugin class:

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

Setting value types and resulting form fields
=============================================

Values can be one of the the following type


.. list-table::
   :widths: 20 80 
   :header-rows: 1

   * - type
     - Settings page field
   * - str
     - Text input field
   * - bool
     - Checkbox
   * - int / float
     - Number input field

.. note::

    Only these type are allowed as config values!

Additionally if the following strings are found in the the config name additional modification are made to the input field


.. list-table::
   :widths: 20 120 
   :header-rows: 1

   * - string
     - modification
   * - `path`
     - Adds a folder browser
   * - `filepath`
     - Adds a file browser
   * - `password`
     - Makes the input field an obfuscated password input field

Interaction between settings page and plugin
============================================

You can also interact from the settings page with your plugin.

- You can add generic buttons.
- You listen on events of the form fields.
- You can get the data from the config fields.
- You can send data back
- You can invoke custom javascript functions with your send data. See getConfigHtml_
- You can trigger global actions

.. _getConfigHtml: index.html#xdm.plugins.bases.Plugin.getConfigHtml

These are defined in the ``config_meta`` dict:

Buttons
-------

To define single action buttons
use the `plugin_buttons` key this holds another dict with button definitions

*Button example:*

.. code-block:: python

    config_meta = {'plugin_buttons': {'testConnection': {'action': _testConnection,
                                                         'name': 'Test Connection',
                                                         'desc': 'Test the connection with credentials'}
                                     }
                  }

This will create a button on the settings page with the text "Test Connection" on it and a greyed out text "Test the connection with credentials" behind it.
When clicked it will call the function ``_testConnection``

.. note::

    Since the "action" is a real python reference the config_meta should be at the end your your plugin class.

Events
------

To add "actions" to changes that are made with the input field (text is changed and focus is lost) you set the
"on_live_change" tot the function you want to call

*Event example:*

.. code-block:: python

    config_meta = {'plugin_desc': 'Sabnzb downloader. Send Nzbs and check for status',
                   'plugin_buttons': {'test_connection': {'action': _testConnection, 'name': 'Test connection'}},
                   'host': {'on_live_change': _testConnection},
                   'port': {'on_live_change': _testConnection},
                   'apikey': {'on_live_change': _testConnection}
                   }

Now the function _testConnection called when either the field host, port or apikey is changed, or when the test_connection button is clicked

The functions
-------------

The functions that are called should always return a tuple of the following schema:

.. code-block:: python

    t = (bool, dict, str)
    return t
    # t[0] is the overal result status
    # t[1] is data you want to send / it is converted into json
    # t[2] is a human readable message

and to get data from the config page
add a list named `args` with names of the config fields you want to the function
(yes add it as an attribute to the function(object))

.. code-block:: python

    _config = {'host': 'http://nzbs2go.com',
               'apikey': '',
               'port': None,
               'enabled': True,
               'comment_on_download': False,
               'retention': 900,
               'verify_ssl_certificate': True
               }

    def _gatherCategories(self, host, port, verify_ssl_certificate):
        return (True, {}, 'I found 3 categories')
    _gatherCategories.args = ['host', 'port', 'verify_ssl_certificate'] # <- this is what i mean


Use the data in javascript
--------------------------

To make use of data in javascript / your function
you modify the data-dict (``t[1]``) has to in the folowing structure:

.. code-block:: python

    dataWrapper = {'callFunction': 'javascript_function_name',
                   'functionData': data}

.. note::

    since all plugins can have multiple instances the functions should be namespaced with the current instance name.
    See following example

*Full example:*

.. code-block:: python

    class Newznab(Indexer):
        identifier = "de.lad1337.newznab"
        _config = {'host': 'http://nzbs2go.com',
                   'apikey': '',
                   'port': None,
                   'enabled': True,
                   'comment_on_download': False,
                   'retention': 900,
                   'verify_ssl_certificate': True
                   }
    
        def _gatherCategories(self, host, port, verify_ssl_certificate):
            # some magic that does stuff
            data = dict()
            dataWrapper = {'callFunction': 'newsznab_' + self.instance + '_spreadCategories', # use the "namespaced" name
                           'functionData': data}
    
            return (True, dataWrapper, 'I found %s categories' % len(data))
        _gatherCategories.args = ['host', 'port', 'verify_ssl_certificate']
    
        def getConfigHtml(self):
            return """<script>
                    function newsznab_""" + self.instance + """_spreadCategories(data){ """ # this gives the function a "namespace"
                      """console.log(data);
                      $.each(data, function(k,i){
                          $('#""" + helper.idSafe(self.name) + """ input[name$="'+k+'"]').val(i)
                      });
                    };
                    </script>
            """
    
        config_meta = {'plugin_desc': 'Generic Newznab indexer. Categories are there numerical id of Newznab, use "Get categories"',
                       'plugin_buttons': {'gather_gategories': {'action': _gatherCategories, 'name': 'Get categories'},
                                          'test_connection': {'action': _testConnection, 'name': 'Test connection'}},
                       }
