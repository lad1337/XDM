#!/usr/bin/python

import sys, os
from subprocess import call

if len(sys.argv) < 2:
    print "No folder supplied - is this being called from SABnzbd?"
    sys.exit()
else:
    scriptFile = os.path.join(os.path.dirname(sys.argv[0]), "add_mp3s_to_itunes.scpt")
    call(['osascript', scriptFile, sys.argv[1]])
