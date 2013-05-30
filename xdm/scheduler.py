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

#based on http://code.activestate.com/recipes/114644/
import time
import threading
from xdm.logger import log

MAXIMUM_FAILS = 3


class Task( threading.Thread):
    def __init__(self, action, loopdelay, initdelay):
        self._action = action
        self._loopdelay = loopdelay
        self._initdelay = initdelay
        self._running = 1
        self._fails = 0
        threading.Thread.__init__(self)

    def __repr__(self):
        return '%s %s %s' % (self._action, self._loopdelay, self._initdelay)

    def run(self):
        if self._initdelay:
            time.sleep(self._initdelay)
        self._runtime = time.time()
        while self._running:
            start = time.time()
            try:
                self._action()
            except:
                self._fails += 1
                log.error('Error in the scheduler thread of %s. %s fails so far.' % (self._action.__name__, self._fails))
                if self._fails >= MAXIMUM_FAILS:
                    log.error('This scheduler %s is dead to me!' % self._action.__name__)
                    self._running = 0
                    break
            self._runtime += self._loopdelay
            time.sleep(max(0, self._runtime - start))

    def stop(self):
        self._running = 0


class Scheduler:
    def __init__(self):
        self._tasks = []

    def __repr__(self):
        rep = ''
        for task in self._tasks:
            rep += '%s\n' % task
        return rep

    def addTask(self, action, loopdelay, initdelay=0):
        task = Task(action, loopdelay, initdelay)
        self._tasks.append(task)

    def startAllTasks(self):
        for task in self._tasks:
            task.start()

    def stopAllTasks(self):
        for task in self._tasks:
            task.stop()
            task.join()
