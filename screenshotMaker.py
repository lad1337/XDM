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

import os
from os import path
from time import sleep
try:
    from lib.sh import wkhtmltoimage
except ImportError:
    print "wkhtmltoimage is not installed"
    exit(1)
    
destination_dir = "dist/"
xdm_config_data_path = "/Users/lad1337/Desktop/XDM_conf/"

xdm_args = ["-n", "-b", xdm_config_data_path]

print "Booting XDM"
import XDM
app = XDM.App(xdm_args)
app.startWebServer()

from xdm import common
from xdm import actionManager

print "Booting XDM done"
common.addState(2)
common.removeState(0)


class Page(object):
    basic_url = "http://localhost:8085/"

    def __init__(self, name, url, height=0, width=1440, delay=500, js=""):
        self.name = name
        self._url = url
        self.height = height
        self.width = width
        self.delay = delay
        self.js = js
    
    @property
    def url(self):
        return "%s%s" % (self.basic_url, self._url)
    

pages = []
pages.append(Page('Movies','', js='m = $(".movie").first(); $(".door>img", m).first().click()'))
# might be not cool to display this in the net
#pages.append(Page('MoviesDownloads','', js='m = $(".movie").first(); $(".door>img", m).first().click(); $(".info-downloads", m).click(); '))
pages.append(Page('Music','#de_lad1337_music', js='$(\'.Album[data-id="6421"]>img\').click()'))
pages.append(Page('Games','#de_lad1337_games'))
pages.append(Page('Books','#de_lad1337_books'))
pages.append(Page('Settings','settings/'))
pages.append(Page('PluginManager','plugins/', delay=10000))
# log page does not because i guess the windows size is none in the renderer
#pages.append(Page('Log','log/', height=800, delay=10000))
pages.append(Page('About','about/'))


done = False
def process_error_log_line(line):
    global done
    print "%s" % line,
    if 'Done' in line:
        done = True

if not os.path.isdir(destination_dir):
    os.mkdir(destination_dir)

for page in pages:
    image_path = path.abspath("%s%s.jpg" % (destination_dir, page.name))
    args = ["--width", page.width,
            "--quality", 100,
            "--javascript-delay", page.delay,
            "--no-stop-slow-scripts"]
    if page.height:
        args.extend(("--height", page.height))
    if page.js:
        args.extend(("--run-script", page.js))

    args.extend((page.url, image_path))

    print "Making screenshot %s of %s writing to %s" % (page.name, page.url, image_path)
    done = False
    p = wkhtmltoimage(*args, _err=process_error_log_line)
    while not done:
        sleep(1)
    p.kill()
sleep(1)

print "#"*20
print "Screenshots are at %s" % destination_dir
print "#"*20
print

actionManager.shutdown()

