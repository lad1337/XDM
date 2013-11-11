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

import tasks
from xdm import common


def migrate_0_4_19():
    """Force a refresh on all Elements
    this is donw because the releasedate was introduced and every element should then use a real datetime object for it
    """
    common.SM.setNewMessage("Migration: Updating all (wanted) elements, not recaching images. This will take a while...(it took 10 minutes on my machine)")
    tasks.updateAllElements()
    for mtm in common.PM.MTM:
        for element in mtm.getElementsWithStatusIn(common.getCompletedStatuses()):
            common.SM.setNewMessage("Migration: Updating %s (not recaching images)" % element)
            tasks.updateElement(element, downloadImages=False)
