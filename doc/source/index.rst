.. XDM documentation master file, created by
   sphinx-quickstart on Sun Jun  2 15:09:29 2013.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.


XDM: eXtendable Download Manager. Plugin based media collection manager
***********************************************************************

.. image:: ../../Meta-Resources/xdm-logo.svg

XDM is in BETA
Official site http://xdm.lad1337.de
Official main plugin repository at https://github.com/lad1337/XDM-main-plugin-repo/

This documentation consists of 3 main sections:

.. toctree::
   :maxdepth: 1
   
   plugin/index
   api/index
   core/index
   

Usage
=====

::

   usage: XDM [-h] [-d] [-v] [-D] [-p PIDFILE] [-P PORT] [-n] [-b DATADIR]
              [-c CONFIG] [--noApi] [--apiPort APIPORT] [--noWebServer]
              [--pluginImportDebug] [--profile [PROFILE [PROFILE ...]]]
   
optional arguments:

-h, --help                     show this help message and exit
-d, --daemonize                Run the server as a daemon.
-v, --version                  Print Version and exit.
-D, --debug                    Print debug log to screen.
-p PIDFILE, --pidfile PIDFILE  Store the process id in the given file.
-P PORT, --port PORT           Force webinterface to listen on this port.
-n, --nolaunch                 Don't start the browser.
-b DATADIR, --datadir DATADIR  Set the directory for the database.
-c CONFIG, --config CONFIG     Path to config file
--noApi                        Disable the api
--apiPort APIPORT              Port the api runs on
--noWebServer                  Port the api runs on
--pluginImportDebug            Extra verbosy debug during plugin import is printed.
--profile PROFILE              Wrap a decorated(!) function in a profiler. By default all decorated functions are profiled. Decorate your function with @profileMeMaybe.

Libraries in use
================

Backend (Python)
----------------

- `CherryPy <http://www.cherrypy.org/>`_: A Minimalist Python Web Framework
- `Requests <http://docs.python-requests.org/en/latest/>`_: HTTP for Humans
- `pyDes <http://twhiteman.netfirms.com/des.html>`_: This is a pure python implementation of the DES encryption algorithm.
- `profilehooks <http://mg.pov.lt/blog/profilehooks-1.0.html>`_: Profiling/tracing wrapper
- `peewee <http://peewee.readthedocs.org/en/latest/>`_: a small, expressive orm
- `Jinja2 <http://jinja.pocoo.org/docs/>`_: Jinja2 is a full featured template engine for Python.
- `pylint <http://www.logilab.org/project/pylint>`_: analyzes Python source code looking for bugs and signs of poor quality
- `astng <https://pypi.python.org/pypi/logilab-astng>`_: common base representation of python source code for projects such as pychecker, pyreverse, pylint
- `guessit <https://pypi.python.org/pypi/guessit>`_: a library for guessing information from video files.
- `GitPython <http://gitorious.org/git-python>`_: a python library used to interact with Git repositories.
- `gitdb <https://pypi.python.org/pypi/gitdb>`_: Git Object Database
- `async <https://github.com/gitpython-developers/async>`_: Distribute interdependent tasks to 0 or more threads
- `smmap <https://pypi.python.org/pypi/smmap>`_: A pure git implementation of a sliding window memory map manager
- `tmdb <http://github.com/doganaydin/themoviedb>`_: themoviedb.org wrapper for api v3
- `JSONRPClib <https://github.com/joshmarshall/jsonrpclib>`_: A Python JSON-RPC over HTTP that mirrors xmlrpclib syntax.

Frontend (css/js/etc)
---------------------

- `Bootstrap <http://twitter.github.io/bootstrap/index.html>`_: Sleek, intuitive, and powerful front-end framework for faster and easier web development.
- `Font Awesome <http://fortawesome.github.io/Font-Awesome/>`_: The iconic font designed for Bootstrap.
- `jQuery <http://jquery.com/>`_: is a fast, small, and feature-rich JavaScript library.
- `jQuery UI <http://jqueryui.com/>`_: is a curated set of user interface interactions, effects, widgets, and themes built on top of the jQuery JavaScript Library.
- `modernizr <http://modernizr.com/>`_: is a JavaScript library that detects HTML5 and CSS3 features in the user’s browser.
- `fancyBox <fancyapps.com>`_: fancyBox is a tool that offers a nice and elegant way to add zooming functionality for images, html content and multi-media on your webpages.
- `Raphaël <http://raphaeljs.com/>`_: JavaScript Vector Library
- `noty <http://needim.github.io/noty/>`_: jquery notification plugin
- `jQuery resize event <http://benalman.com/projects/jquery-resize-plugin/>`_: With jQuery resize event, you can now bind resize event handlers to elements other than window.
- `JQuery Countdown Timer <http://jaspreetchahal.org/a-simple-jquery-countdown-timer-with-callback/>`_: A simple jQuery Countdown Timer with callback

.. note::

    Plugins may use more libraries


