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
from xdm import common
from xdm.classes import Element, Field
from xdm.logger import *


def soFreshAndSoClean():
    """Runs every available clean function
    the garbage collector scheduler will call this
    """
    common.addState(6)
    cleanTemporaryElements()

    deleteOrphanFields()
    # add more functions here
    common.removeState(6)


def cleanTemporaryElements():
    for temp in list(Element.select().where(Element.status == common.TEMP)):
        temp.delete_instance(silent=True)

    log.info("Removeing temp elements DONE")

def deleteOrphanFields():
    log.info("Getting orphanaged fields")
    elements = Element.select()
    fields_dq = Field.delete().where(~(Field.element << elements))
    deleted_rows = fields_dq.execute()
    log.info("Deleted %s orphanaged fields" % deleted_rows)
