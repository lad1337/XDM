![XDM](http://xdm.lad1337.de/img/xdm-logo.svg "XDM")

XDM: eXtendable Download Manager. Plugin based media collection manager.

XDM is in BETA
Current official site [http://xdm.lad1337.de](http://xdm.lad1337.de)<br/>
Official main plugin repository at [https://github.com/lad1337/XDM-main-plugin-repo/](https://github.com/lad1337/XDM-main-plugin-repo/)

## Known support for Mediatypes

- Movies: add Movies and find and Postprocess (in core)
- Music: add Albums and find and Postprocess (only for Mac OSX adding to iTunes) (in core)
- Games: add PC, Xbox360, PS3 and Wii Games and find and Postprocess (in core)
- Books: add Books and find (in main repository)

For more info on available first party plugins see the main repository at [https://github.com/lad1337/XDM-main-plugin-repo/](https://github.com/lad1337/XDM-main-plugin-repo/).

Note: At some point in the future all MediaTypeManagers and corresponding plugins will be moved into the repository and out of the core.

### Documentation
is available online at [https://xdm.readthedocs.org](https://xdm.readthedocs.org)<br>
or in the source and can be build using [sphinx](http://sphinx-doc.org/)

Libraries in use
----------------

### Backend

- [CherryPy](http://www.cherrypy.org/): A Minimalist Python Web Framework
- [Requests](http://docs.python-requests.org/en/latest/): HTTP for Humans
- [pyDes](http://twhiteman.netfirms.com/des.html): This is a pure python implementation of the DES encryption algorithm.
- [profilehooks](http://mg.pov.lt/blog/profilehooks-1.0.html): Profiling/tracing wrapper
- [peewee](http://peewee.readthedocs.org/en/latest/): a small, expressive orm
- [Jinja2](http://jinja.pocoo.org/docs/): Jinja2 is a full featured template engine for Python.
- [pylint](http://www.logilab.org/project/pylint): analyzes Python source code looking for bugs and signs of poor quality
- [astng](https://pypi.python.org/pypi/logilab-astng): common base representation of python source code for projects such as pychecker, pyreverse, pylint
- [guessit](https://pypi.python.org/pypi/guessit): a library for guessing information from video files.
- [GitPython](http://gitorious.org/git-python): a python library used to interact with Git repositories.
- [gitdb](https://pypi.python.org/pypi/gitdb): Git Object Database
- [async](https://github.com/gitpython-developers/async): Distribute interdependent tasks to 0 or more threads
- [smmap](https://pypi.python.org/pypi/smmap): A pure git implementation of a sliding window memory map manager
- [tmdb](http://github.com/doganaydin/themoviedb): themoviedb.org wrapper for api v3
- [JSONRPClib](https://github.com/joshmarshall/jsonrpclib): A Python JSON-RPC over HTTP that mirrors xmlrpclib syntax.

### Frontend

- [Bootstrap](http://twitter.github.io/bootstrap/index.html): Sleek, intuitive, and powerful front-end framework for faster and easier web development.
- [Font Awesome](http://fortawesome.github.io/Font-Awesome/): The iconic font designed for Bootstrap.
- [jQuery](http://jquery.com/): is a fast, small, and feature-rich JavaScript library.
- [jQuery UI](http://jqueryui.com/): is a curated set of user interface interactions, effects, widgets, and themes built on top of the jQuery JavaScript Library.
- [modernizr](http://modernizr.com/): is a JavaScript library that detects HTML5 and CSS3 features in the user’s browser.
- [fancyBox](fancyapps.com): fancyBox is a tool that offers a nice and elegant way to add zooming functionality for images, html content and multi-media on your webpages.
- [Raphaël](http://raphaeljs.com/): JavaScript Vector Library
- [noty](http://needim.github.io/noty/): jquery notification plugin
- [jQuery resize event](http://benalman.com/projects/jquery-resize-plugin/): With jQuery resize event, you can now bind resize event handlers to elements other than window.
- [JQuery Countdown Timer](http://jaspreetchahal.org/a-simple-jquery-countdown-timer-with-callback/): A simple jQuery Countdown Timer with callback

(Plugins may use more libraries)

Screenshots
-----------

[More screenshots](http://xdm.lad1337.de)

Music plugin with some albums
![Music plugin](http://xdm.lad1337.de/img/home.png "Music plugin")

Movie plugin with some movies
![Movie plugin](http://xdm.lad1337.de/img/movies.png "Movie plugin")

Plugin and reposetory managment
![Music plugin](http://xdm.lad1337.de/img/repo.png "Plugin and reposetory managment")


Usage
-----
<pre>
sage: XDM [-h] [-d] [-v] [-D] [-p PIDFILE] [-P PORT] [-n] [-b DATADIR]
           [-c CONFIG] [--dev] [--noApi] [--apiPort APIPORT] [--noWebServer]
           [--pluginImportDebug] [--profile [PROFILE [PROFILE ...]]]

optional arguments:
  -h, --help            show this help message and exit
  -d, --daemonize       Run the server as a daemon.
  -v, --version         Print Version and exit.
  -D, --debug           Print debug log to screen.
  -p PIDFILE, --pidfile PIDFILE
                        Store the process id in the given file.
  -P PORT, --port PORT  Force webinterface to listen on this port.
  -n, --nolaunch        Don't start the browser.
  -b DATADIR, --datadir DATADIR
                        Set the directory for the database.
  -c CONFIG, --config CONFIG
                        Path to config file
  --dev                 Developer mode. Disables the censoring during log and
                        the plugin manager follows symlinks
  --noApi               Disable the api
  --apiPort APIPORT     Port the api runs on
  --noWebServer         Port the api runs on
  --pluginImportDebug   Extra verbosy debug during plugin import is printed.
  --profile [PROFILE [PROFILE ...]]
                        Wrap a decorated(!) function in a profiler. By default
                        all decorated functions are profiled. Decorate your
                        function with @profileMeMaybe
</pre>


i18n
----

You will need an instlled version of babel

    Build message catalog       $ pybabel extract -F babel.cfg -o ./i18n/messages.pot .
    Create language po          $ pybabel init -i ./i18n/messages.pot -d i18n -l ``language name``
    Update language po          $ pybabel update -i ./i18n/messages.pot -d i18n
    Compile mo files            $ pybabel compile -d i18n -f


License
=======
XDM: Xtentable Download Manager. Plugin based media collection manager.<br>
Copyright (C) 2013  Dennis Lutter

This program is free software: you can redistribute it and/or modify<br>
it under the terms of the GNU General Public License as published by<br>
the Free Software Foundation, either version 3 of the License, or<br>
(at your option) any later version.

This program is distributed in the hope that it will be useful,<br>
but WITHOUT ANY WARRANTY; without even the implied warranty of<br>
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the<br>
GNU General Public License for more details.<br>

You should have received a copy of the GNU General Public License<br>
along with this program.  If not, see http://www.gnu.org/licenses/.




