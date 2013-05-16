XDM
===

XDM: Xtentable Download Manager. Plugin based media collection manager.

XDM is at BETA STAGE
Current offical site [http://xdm.lad1337.de](http://xdm.lad1337.de)<br/>
Official main plugin repository at [https://github.com/lad1337/XDM-main-plugin-repo/](https://github.com/lad1337/XDM-main-plugin-repo/)


Libraries in use
===============

Backend
-------

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

Frontend
---------

- [bootstrap](http://twitter.github.io/bootstrap/index.html): Sleek, intuitive, and powerful front-end framework for faster and easier web development.
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
===========

[More screenshots](http://xdm.lad1337.de)

Music plugin with some albums
![Music plugin](http://xdm.lad1337.de/img/home.png "Music plugin")

Movie plugin with some movies
![Movie plugin](http://xdm.lad1337.de/img/movies.png "Movie plugin")

Plugin and reposetory managment
![Music plugin](http://xdm.lad1337.de/img/repo.png "Plugin and reposetory managment")



Notes on the plugin development api (not final nor complete)
--
<pre>
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

</pre>

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




