#!/usr/bin/env python
# Author: Dennis Lutter <lad1337@gmail.com>
# URL: https://github.com/lad1337/XDM
#
# This file is part of XDM: eXtentable Download Manager.
#
# XDM: eXtentable Download Manager. Plugin based media collection manager.
# Copyright (C) 2013  Dennis Lutter
#
# XDM is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# XDM is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see http://www.gnu.org/licenses/.

# my usual call line
# python tools/repoJSONmaker.py --download_url https://github.com/lad1337/XDM-main-plugin-repo/archive/master.zip --info_url https://github.com/lad1337/XDM-main-plugin-repo/ --name XDM\ main\ repo --path /Users/lad1337/workspace/XDM-main-plugin-repo/ --keep_xdm_version

# WARNING oh boy is this hacked !!! but since this is for the lazy i am lazy on this here

import argparse
import json
import sys
import os
import glob
from collections import OrderedDict

p = argparse.ArgumentParser(prog='XDM-repo-creator')
p.add_argument('--name', dest='name', default="Some repo and the dev gave it no name", help="Repo name")
p.add_argument('--info_url', dest='info_url', default="## enter your info url here ##", help="The info url")
p.add_argument('--download_url', dest='download_url', default="## enter your download url here", help="I you use one download url for all plugins set this.")
p.add_argument('--path', dest='path', default=None, help="Path to the plugins")
p.add_argument('--read', dest='old_json', default=False, help="Path to the old repo json")
p.add_argument('--keep_xdm_version', dest='keep_xdm_version', action="store_true", default=False, help="Keep the required version of xdm if found in the old meta")


options = p.parse_args()

if not options.path and not options.old_json:
    # lets do some guessing !
    glob_plugin_path = os.path.abspath(os.path.join("..", "XDM-*"))
    options.old_json = os.path.join(glob.glob(glob_plugin_path)[0], "meta.json")

if options.old_json:
    if not os.path.isfile(options.old_json):
        print "%s is not a file. sorry" % options.old_json
        exit(1)
    json_raw = open(options.old_json).read()
    old_json_data = json.loads(json_raw)

    name = old_json_data['name']
    info_url = old_json_data['info_url']
    download_url = options.download_url
    # lets try to get the download url from the FIRST plugin
    if len(old_json_data) and len(old_json_data['plugins']):
        download_url = old_json_data['plugins'].itervalues().next()[0]['download_url']
    plugin_path = os.path.abspath(os.path.dirname(options.old_json))
else:
    name = options.name
    info_url = options.info_url
    download_url = options.download_url
    plugin_path = options.path


if not plugin_path:
    print "I am sorry but i kinda need the path to all the plugins"
    exit(1)
else:
    print "using %s as plugin path" % plugin_path

sys.path.append(plugin_path)
sys.path.append(os.path.abspath("."))

sys.argv = []

import XDM
a = XDM.App()

from xdm import common
from xdm import actionManager


jsons = {
    "name": name,
    "info_url": info_url,
    "plugins": {}
}

common.PM.cache(extra_plugin_path=plugin_path)
metaPath = os.path.join(plugin_path, "meta.json")
try:
    with open(metaPath, "r") as f:
        old_meta = json.loads(f.read())
except:
    old_meta = {}


for plugin in common.PM.getAll(returnAll=True):
    # print "checking %s" % plugin
    pPath = plugin.get_plugin_isntall_path()['path']
    if not pPath.startswith(plugin_path):
        # print "%s not in the path you want to use plugin path:%s" % (plugin, plugin.get_plugin_isntall_path()['path'])
        continue

    if not plugin.identifier:
        print 'WARNING: %s has no identifier' % plugin
        continue

    if os.path.basename(pPath) != plugin.screenName:
        print 'WARNING: %s should be in a folder named "%s" not in "%s"' % (plugin, plugin.screenName, os.path.basename(pPath))
        continue

    info = plugin.createRepoJSON(True)[plugin.identifier]
    if options.keep_xdm_version:
        if old_meta and old_meta['plugins'] and plugin.identifier in old_meta['plugins']:
            old_version = old_meta['plugins'][plugin.identifier][0]["xdm_version"]
            info[0]["xdm_version"] = old_version
    info[0]['download_url'] = download_url
    jsons['plugins'][plugin.identifier] = info

jsons["plugins"] = OrderedDict(sorted(jsons['plugins'].iteritems(), key=lambda x: x[0]))


json = json.dumps(jsons, indent=4, sort_keys=False)

print
print "#############"
print "WARNING i will (over)write the file %s. i hope you use a svc!" % metaPath
print "#############"

# Write mode creates a new file or overwrites the existing content of the file.
# Write mode will _always_ destroy the existing contents of a file.
try:
    # This will create a new file or **overwrite an existing file**.
    with open(metaPath, "w") as f:
        f.write(json + "\n") # Write a string to a file
except IOError as e:
    print(e)
    raise e
else:
    print "written !"
    print "check: %s" % metaPath

actionManager.shutdown()
