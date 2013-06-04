
API
***

Things you should know:

- The API is a JSON-RPC api v2.0 more info see http://en.wikipedia.org/wiki/JSON-RPC
- It runs on its own port, default is 8086
- The api key MUST be present in all methods except xdm.api.ping_ and xdm.api.version_

.. note::

   At the time of writing i failed to make a connection to XDM / the api from a webpage due to cross origin domain security issues.
   I was also not able to add a websocket implementation to the api.

.. warning::

   The api might completely change. goal is to have an api as XBMC provides. (Websockets and HTTP with an JSONRPC protocol)


Access
======

You must provider the api key either as the first none keyword argument or as a keyoword argument witht the name `apikey`.

Example in python
-----------------
Using `JSONRPClib <https://github.com/joshmarshall/jsonrpclib>`_

::

   >>>> import jsonrpclib
   >>>> server = jsonrpclib.Server('http://localhost:8086')
   >>>> server.ping()
   u'pong'
   >>>> server.system.listMethods('6vVSMLSDB9vPZkftahVwfBirjzvYzPuih3V6hmO1Nhk')
   [u'ping', u'plugins.cache', u'plugins.getActiveMediaTypes', u'system.listMethods', u'system.methodHelp', u'system.methodSignature', u'system.reboot', u'system.shutdown', u'version']



Namespace: None
===============

.. automodule:: xdm.api
   :members:
   :exclude-members: expose

Namespace: system
=================
      
.. automodule:: xdm.api.system
   :members:

Namespace: plugins
==================

.. automodule:: xdm.api.plugins
   :members:

