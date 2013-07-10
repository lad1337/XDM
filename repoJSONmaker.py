#!/usr/bin/env python
# Author: Dennis Lutter <lad1337@gmail.com>
# URL: https://github.com/lad1337/XDM
#
# This file is part of XDM: eXtentable Download Manager.
#
#XDM: eXtentable Download Manager. Plugin based media collection manager.
#Copyright (C) 2013  Dennis Lutter
#
#XDM is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.
#
#XDM is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.
#
#You should have received a copy of the GNU General Public License
#along with this program.  If not, see http://www.gnu.org/licenses/.


#WARNING oh boy is this hacked !!! but since this is for the lazy i am lazy on this here

import argparse
import json
import sys
import os

p = argparse.ArgumentParser(prog='XDM-repo-creator')
p.add_argument('--name', dest='name', default="Some repo and the dev gave it no name", help="Repo name")
p.add_argument('--info_url', dest='info_url', default="## enter your info url here ##", help="The info url")
p.add_argument('--download_url', dest='download_url', default="## enter your download url here", help="I you use one download url for all plugins set this.")
p.add_argument('--path', dest='path', default=None, help="Port the api runs on")


options = p.parse_args()

if not options.path:
    print "I am sorry but i kinda need the path to all the plugins"
    exit(1)


sys.path.append(options.path)


sys.argv = []

import XDM
a = XDM.App()

from xdm import common
from xdm import actionManager


jsons = {
    "name": options.name,
    "info_url": options.info_url,
    "plugins": {}}

common.PM.cache(extra_plugin_path=options.path)

for plugin in common.PM.getAll(returnAll=True):
    #print "checking %s" % plugin
    pPath = plugin.get_plugin_isntall_path()['path']
    if not pPath.startswith(options.path):
        #print "%s not in the path you want to use plugin path:%s" % (plugin, plugin.get_plugin_isntall_path()['path'])
        continue

    if not plugin.identifier:
        print 'WARNING: %s has no identifier' % plugin
        continue

    if os.path.basename(pPath) != plugin.screenName:
        print 'WARNING: %s should be in a folder named "%s" not in "%s"' % (plugin, plugin.screenName, os.path.basename(pPath))
        continue

    info = plugin.createRepoJSON(True)[plugin.identifier]
    info[0]['download_url'] = options.download_url
    jsons['plugins'][plugin.identifier] = info

json = json.dumps(jsons, indent=4, sort_keys=False)

metaPath = os.path.join(options.path, "meta.json")
print
print "#############"
print "WARNING i will (over)write the file %s. i hope you use a svc!" % metaPath
print "#############"

# Write mode creates a new file or overwrites the existing content of the file. 
# Write mode will _always_ destroy the existing contents of a file.
try:
    # This will create a new file or **overwrite an existing file**.
    f = open(metaPath, "w")
    try:
        f.write(json) # Write a string to a file
    finally:
        f.close()
        print "written !"
        print "check: %s" % metaPath
except IOError:
    pass

actionManager.shutdown()
