.. XDM documentation master file, created by
   sphinx-quickstart on Sun Jun  2 15:09:29 2013.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.


Welcome to XDM's documentation!
*******************************
Thank you for showing interest in XDM! This documentation consists of 3 main sections:

- `Plugin Development`_
- `Core API Reference`_
- `Core`_

.. _`Plugin Development`: plugin/index.html
.. _`Core API Reference`: api/index.html
.. _`Core`: core/index.html

Contents:

.. toctree::
   :maxdepth: 1
   
   plugin/index
   

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`


.. automodule:: xdm.plugins


.. autoclass:: xdm.api.expose

.. autoclass:: xdm.classes.Element

.. autoclass:: xdm.updater.CoreUpdater
    :members: check, _find_install_type

