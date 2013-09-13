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
import xdm
from xdm.logger import log
import datetime
import uuid as uuidModule

MAXIMUM_FAILS = 3


class Task(threading.Thread):

    def __init__(self, action, loopdelay, initdelay, uuid, name=None):
        self._action = action
        self._loopdelay = loopdelay
        self._initdelay = initdelay
        self._uuid = uuid
        self._running = 1
        self._fails = 0
        self._sleeping = 1
        self._blockCount = 0
        self._failMessage = ''
        self._neverRun = True
        self._runNow = False
        self._nextRun = self._calcNextRun(self._initdelay)
        self._lastRun = None
        threading.Thread.__init__(self)
        if name is not None:
            self.name = name
        else:
            self.name = self._action.__name__

    def _calcNextRun(self, sleepTime):
        return datetime.datetime.now() + datetime.timedelta(seconds=sleepTime)

    def getNextRunDatetime(self):
        return self._nextRun

    def __repr__(self):
        return '%s %s %s' % (self._action, self._loopdelay, self._initdelay)

    def run(self):
        if self._initdelay:
            time.sleep(self._initdelay)
        self._runtime = time.time()
        while self._running:
            start = time.time()
            if not (xdm.xdm_states[0] in xdm.common.STATES or\
                    xdm.xdm_states[1] in xdm.common.STATES or\
                    xdm.xdm_states[3] in xdm.common.STATES or\
                    xdm.xdm_states[6] in xdm.common.STATES):
                self._sleeping = 0
                self._blockCount = 0
                self._neverRun = False
                self._runNow = False
                self._lastRun = datetime.datetime.now()
                try:
                    self._action()
                    # this is here to test the failMessage gui
                    """if 'coreUpdateCheck' == self.name and not self._fails:
                        raise AttributeError("fake error on first run")"""
                except:
                    self._fails += 1
                    self._failMessage = log.error('Error in the scheduler thread of %s. %s fails so far.' % (self.name, self._fails))
                    if self._fails >= MAXIMUM_FAILS:
                        log.error('This scheduler %s is dead to me!' % self.name)
                        self._running = 0
                        break
            else:
                self._blockCount += 1
                log("XDM is in state %s not running action: %s" % (xdm.common.STATES, self.name))

            self._runtime += self._loopdelay
            self._sleeping = 1

            if self._neverRun and self._initdelay:
                # this will create times like -10 and -20 ater this will be -(-20) = 20
                timeDelta = min(5 * 60, (self._blockCount * self._initdelay))
                sleepTime = max(0, self._initdelay + timeDelta)
            else:
                # this will reduce the _loopdelay by half for each time we have been blocked
                # e.g. looptime = 120s _blockCount = 1
                # = minus 60s
                # e.g. looptime = 120s _blockCount = 2
                # = minus 90s
                # the key is the 0.5 ** _blockCount ... ** means "to the power of"
                timeDelta = self._loopdelay - ((0.5 ** self._blockCount) * self._loopdelay)
                sleepTime = max(0, (self._runtime - start) - timeDelta)
            if self._blockCount:
                # these lines are from hell
                if self._neverRun:
                    log("Adding %s seconds because %s has been blocked, before it's first run, %s times. I will sleep for %ss instead of %ss thats %s%% if the normal time" %\
                        (timeDelta, self.name, self._blockCount, sleepTime, self._initdelay, int((sleepTime / self._initdelay) * 100)))
                else:
                    log("Removing %s seconds because %s has been blocked %s times. I will sleep for %ss instead of %ss thats %s%% if the normal time" %\
                        (timeDelta, self.name, self._blockCount, sleepTime, self._loopdelay, 100 - int((sleepTime / self._loopdelay) * 100)))

            self._nextRun = self._calcNextRun(sleepTime)
            for second in xrange(int(sleepTime / 2)):
                time.sleep(2)
                if (not self._running) or self._runNow:
                    break

    def stop(self):
        self._running = 0

    def isRunning(self):
        return bool(self._running)

    def setRunning(self):
        if not self.isRunning():
            self._running = 1
            self._sleeping = 0
            self._blockCount = 0
            self._neverRun = True
            self._runNow = False
            try:
                self.start()
            except RuntimeError:
                pass

    def isSleeping(self):
        return bool(self._sleeping)

    def getFails(self):
        return self._fails

    def getFailMessage(self):
        return self._failMessage

    def getLoopDelay(self):
        return self._loopdelay

    def getUuid(self):
        return self._uuid
    
    def getLastRun(self):
        return self._lastRun

    def runNow(self):
        self._runNow = True


class Scheduler:
    """Simple manager for recurring tasks"""
    def __init__(self):
        self._tasks = []

    def __repr__(self):
        rep = ''
        for task in self._tasks:
            rep += '%s\n' % task
        return rep

    def addTask(self, action, loopdelay, initdelay=0, name=None):
        """add a task

        Params:

        action
            a function reference

        loopdelay
            delay between calls in seconds

        initdelay
            initial delay in seconds (default = 0)

        name
            name (default = None). will default to action.__name__

        """
        task = Task(action, loopdelay, initdelay, str(uuidModule.uuid4()), name)
        self._tasks.append(task)

    def getTasks(self):
        return self._tasks

    def startAllTasks(self):
        """Start all task threads"""
        for task in self._tasks:
            task.start()

    def runTaskNow(self, uuid):
        for task in self._tasks:
            if task.getUuid() == uuid:
                if task.isRunning():
                    log.info("Telling task %s to run now" % task.name)
                    task.runNow()
                else:
                    log.info("Restarting task %s" % task.name)
                    task.setRunning()
                return True
        log.info("No task with uuid %s found" % uuid)
        return False

    def stopAllTasks(self):
        """Stop all task threads"""
        msg = "Stopping all tasks"
        xdm.common.SM.setNewMessage(msg)
        log.info(msg)
        for task in self._tasks:
            msg = 'Stopping scheduled task %s' % task.name
            xdm.common.SM.setNewMessage(msg)
            log.info(msg)
            if not (task.isSleeping() or not task.isRunning()):
                msg = 'Looks like %s is running. checking in 1 second again' % task.name
                xdm.common.SM.setNewMessage(msg)
                log.info(msg)
                time.sleep(1)
                if not (task.isSleeping() or not task.isRunning()):
                    msg = 'Looks like %s is really running. please wait...' % task.name
                    xdm.common.SM.setNewMessage(msg)
                    log.info(msg)
                    task.stop()
                    task.join()
                    continue
            task.stop()
            task.join(0)
