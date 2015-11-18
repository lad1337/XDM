![XDM](http://xdm.lad1337.de/wp-content/uploads/2013/05/xdm-logo.h100.png "XDM")

XDM: eXtendable Download Manager. Plugin based media collection manager.

Homepage: [http://xdm.lad1337.de](http://xdm.lad1337.de)<br/>

[![Build Status](https://travis-ci.org/lad1337/XDM.svg)](https://travis-ci.org/lad1337/XDM)
[![Gitter chat](https://badges.gitter.im/lad1337/XDM.png)](https://gitter.im/lad1337/XDM)

## Rewrite status / basic idea
XDM is only a framework that supplies the following:

- [x] based on [tornado](http://www.tornadoweb.org)
- [x] [blitzdb](http://blitzdb.readthedocs.org/en/latest/)
- [x] Unittesting
- [ ] a basic frontend to install plugins during first launch
- [ ] documentation
- [x] plugin system
- [ ] plugin repo system (very similar to old one)
- [ ] automatic plugin updater (very similar to old one)
- [x] plugin config management
- [ ] plugin persistent data management
- [ ] automatic core updater (similar to old one)
    - [ ] git
    - [ ] source
    - [ ] mac app
    - [ ] windows app
- [x] interface to register tasks / messages
- [x] interface to register inteval tasks
- [ ] interface to register http routes
- [ ] complete web based configuration interface
- [ ] new set of plugins
- [ ] find a new word for the "D" in XDM. XDM is still e__X__tendable and a __M__anager but the core app is not download specific.

The idea behind the structure is that plugins control the whole workflow.
Plugins do not have specific roles, they just define tasks.
These tasks can either be schedules or "hooks" called from other plugins.
e.g. the plugins *ElementUpdates* defines a scheduled task that queries all *Elements* that can be requests for update (not yet defined how to identify, maybe simply by: has no parent -> Root type).
The schedules task then gets all tasks with the name *get_element* (name and interface defined by convention between plugins) and calls each task with each *Element*. *get_element* is defined in multiple plugins like a plugin that can get meta data from *trakt.tv* and another that gets scores from IMDB. The initial *ElementUpdates* task then compares the results from the *get_element* and updates the *elements*

The user interface (in this case web based) will be supplied by a plugin, that attaches tornado based *RequestHandler*s to the root application. this will also need the ability to expose files (js, css, etc.) of plugins in some form.

At the time of writing it is not clear how other plugins interface / inject into the the web interface / HTML.
neither is it clear if the html is rendered on the server or client.
this might also lead to a very close cupeling between plugins -> the "first" Gui plugin defines the content inject interface, it is preferable to define this interface in the base application.

## Requirements

- python 3.4

## How to develop

### install
```bash    
git clone git@github.com:lad1337/XDM.git
git checkout -b develop origin/develop
cd XDM
```
### running the tests
if tox is not installed: `pip install tox`
```bash
tox
```

### running the app
note: using mkvirtualenv for convenience

```bash
mkvirtualenv xdm --python=python3
pip install -e .
# might need a "rehash" or shell equivalent
xdm-server --debug
```


## License
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


