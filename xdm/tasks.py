# Author: Dennis Lutter <lad1337@gmail.com>
# URL: https://github.com/lad1337/XDM
#
# This file is part of XDM: Xtentable Download Manager.
#
#XDM: Xtentable Download Manager. Plugin based media collection manager.
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

from xdm.logger import *
from xdm import common
from xdm.classes import *
import json
from xdm.jsonHelper import MyEncoder
import threading


class TaskThread(threading.Thread):
    def __init__(self, target, *args):
        self._target = target
        self._args = args
        threading.Thread.__init__(self)

    def run(self):
        log.debug('Running %s' % self._target.__name__)
        self._target(*self._args)


def coreUpdateCheck():
    updateResponse = common.UPDATER.check()
    log.info('%s' % updateResponse)
    if updateResponse.needUpdate == True:
        common.MM.createInfo('%s Update now?' % updateResponse.message, confirm=coreUpdateDo)
    elif updateResponse.needUpdate is None:
        common.MM.createWarning(updateResponse.message)


def coreUpdateDo():
    updateResponse = common.UPDATER.update()


def runSearcher():
    log("running searcher")
    for mtm in common.PM.MTM:
        for ele in mtm.getDownloadableElements():
            if ele.status == common.FAILED and common.SYSTEM.c.again_on_fail:
                ele.status = common.WANTED
            elif ele.status != common.WANTED:
                continue
            #TODO: find a standart way for a release date maybe just add it :/
            """elif ele.release_date and ele.release_date > datetime.datetime.now(): # is the release date in the future
                continue"""
            log("Looking for %s" % ele)
            searchElement(ele)


def notify(element):

    if element.status == common.SNATCHED:
        common.MM.createInfo("%s was snatched" % element.getName())
    elif element.status == common.COMPLETED:
        common.MM.createInfo("%s is Completed" % element.getName())
    elif element.status == common.DOWNLOADED:
        common.MM.createInfo("%s was downloaded" % element.getName())
    elif element.status == common.PP_FAIL:
        common.MM.createWarning("%s had an error during post processing" % element.getName())

    for notifier in common.PM.N:
        createGenericEvent(element, 'notifier', 'Sending notification with %s on status %s' % (notifier, element.status))
        if notifier.c.on_snatch and element.status == common.SNATCHED:
            notifier.sendMessage("%s has been snatched" % element.getName(), element)
        if notifier.c.on_complete and element.status in (common.COMPLETED, common.DOWNLOADED, common.PP_FAIL):
            notifier.sendMessage("%s is now %s" % (element, element.status), element)


def createGenericEvent(ele, event_type, event_msg):
    h = History()
    h.event = event_type
    h.obj_id = ele.id
    h.obj_class = ele.__class__.__name__
    h.obj_type = ele.type
    h.old_obj = json.dumps(ele, cls=MyEncoder)
    h.new_obj = json.dumps({'_data': {'msg': event_msg}})
    h.save()


def commentOnDownload(download):
    for indexer in common.PM.I:
        if indexer.type != download.indexer or indexer.instance != download.indexer_instance:
            continue
        if indexer.c.comment_on_download and download.status == common.FAILED:
            indexer.commentOnDownload('Gamez snatched this but it failed to download (automtic notice)', download)
        if indexer.c.comment_on_download and download.status in (common.COMPLETED, common.DOWNLOADED, common.PP_FAIL):
            indexer.commentOnDownload('Gamez snatched this and it downloaded successfully (automtic notice)', download)


def searchElement(ele):
    didSearch = False
    for indexer in common.PM.getIndexers(runFor=ele.manager):
        createGenericEvent(ele, 'search', 'Searching %s on %s' % (ele, indexer))
        downloads = indexer.searchForElement(ele) #intensiv
        createGenericEvent(ele, 'result', '%s found %s results' % (indexer, len(downloads)))
        didSearch = True

        #downloads = _filterBadDownloads(blacklist, whitelist, downloads)
        downloads = _filterBadDownloads(downloads)
        if downloads:
            return snatchOne(ele, downloads)
        else:
            log.info("We filtered all downloads out for %s" % ele)
    if not didSearch:
        log.warning("No Indexer active/available for %s" % ele.manager)
    return ele.status


# in a way we dont need ele here since each download holds a ref to each ele ... but it is easier to read
def snatchOne(ele, downloads):
    for downloader in common.PM.getDownloaders():
        triedSnatch = False
        for download in downloads:
            if not download.type in downloader.types:
                continue
            createGenericEvent(ele, 'snatchTry', 'Trying to snatch %s with %s' % (download.name, downloader))
            createGenericEvent(download, 'snatchTry', '%s is trying to snatch me' % (downloader))
            log.info('Trying to snatch %s with %s' % (download.name, downloader))
            if downloader.addDownload(download):
                ele.status = common.SNATCHED
                ele.save()
                download.status = common.SNATCHED
                download.save()
                createGenericEvent(download, 'snatch', '%s snatched me' % (downloader))
                notify(ele)
                return ele.status #exit on first success
            triedSnatch = True
        if triedSnatch and downloads:
            log.warning("No Downloaders active/available for %s (or they all failed)" % download.type)
        elif not downloads:
            log.info("No downloads found for %s" % download.element)
    return ele.status


def _filterBadDownloads(downloads):
    clean = []
    for download in downloads:
        old_download = None
        try:
            old_download = Download.get(Download.url == download.url)
        except Download.DoesNotExist:
            #no download with that url found
            pass

        if not old_download:
            log("Saving the new download we found %s" % download)
            download.status = common.UNKNOWN
            download.save()
        else:
            try:
                Element.get(Element.id == download.element.id)
            except Element.DoesNotExist:
                log.warning("The element for the download(%s) does not exist any more deleting the old one but taking the status from the old one" % download.id)
                download.status = old_download.status
                old_download.delete_instance()
                download.save()
                old_download = download
            if old_download.status in (common.FAILED, common.DOWNLOADED):
                log.info("Found a Download(%s) with the same url and it failed or we downloaded it already. Skipping..." % download)
                continue
            if old_download.status == common.SNATCHED:
                if common.SYSTEM.c.resnatch_same:
                    continue
                log.info("Found a Download(%s) with the same url and we snatched it already. I'l get it again..." % download)
            download = old_download

        for curFilterPlugin in common.PM.getFilters(hook=common.FOUNDDOWNLOADS, runFor=download.element.manager):
            filterResult = curFilterPlugin.compare(element=download.element, download=download)
            if not filterResult.result:
                log.info('%s did not like %s, reason: %s' % (curFilterPlugin, download, filterResult.reason))
                #createGenericEvent(download.element, 'filter', '%s did not like %s, reason: %s' % (curFilterPlugin, download, filterResult.reason))
                createGenericEvent(download, 'filter', '%s did not like me, reason: %s' % (curFilterPlugin, filterResult.reason))
                break
            else:
                log.info('%s liked %s, reason: %s' % (curFilterPlugin, download, filterResult.reason))
                createGenericEvent(download.element, 'filter', '%s liked %s, reason: %s' % (curFilterPlugin, download, filterResult.reason))
                createGenericEvent(download, 'filter', '%s liked me, reason: %s' % (curFilterPlugin, filterResult.reason))
        else:
            clean.append(download)
    return clean


def runChecker():
    elements = list(Element.select().execute())
    for checker in common.PM.D:
        for element in elements:
            if not element.status == common.SNATCHED:
                continue
            log("Checking status for %s" % element)
            status, download, path = checker.getElementStaus(element)
            log("%s gave back status %s for %s on download %s" % (checker, status, element, download))
            if status == common.DOWNLOADED:
                element.status = common.DOWNLOADED
                element.save()
                if download.id:
                    download.status = common.DOWNLOADED
                    download.save()
                ppElement(element, download, path)
                notify(element)
                if download.id:
                    commentOnDownload(download)
            elif status == common.SNATCHED:
                element.status = common.SNATCHED
                element.save()
                download.status = common.SNATCHED
                download.save()
            elif status == common.FAILED:
                download.status = common.FAILED
                download.save()
                if common.SYSTEM.c.again_on_fail:
                    element.status = common.WANTED
                    element.save()
                    searchElement(element)
                else:
                    element.status = common.FAILED
                    element.save()


def ppElement(element, download, path):
    pp_try = False
    for pp in common.PM.getPostProcessors(runFor=element.manager):
        createGenericEvent(element, 'postProcess', 'Starting PP with %s' % pp)
        log('Starting PP on %s with %s at %s' % (element, pp, path))
        ppResult, pp_log = pp.postProcessPath(element, path)
        pp_try = True
        if ppResult:
            element.status = common.COMPLETED
            element.save()
            download.status = common.COMPLETED
            download.pp_log = 'LOG from %s:\n%s\n######\n%s' % (pp, pp_log, download.pp_log)
            download.save()
            if pp.c.stop_after_me_select == common.STOPPPONSUCCESS or pp.c.stop_after_me_select == common.STOPPPALWAYS:
                return True
        else:
            if pp.c.stop_after_me_select == common.STOPPPONFAILURE or pp.c.stop_after_me_select == common.STOPPPALWAYS:
                break
    if pp_try:
        element.status = common.PP_FAIL # tried to pp but fail
        element.save()
        download.status = common.PP_FAIL
        download.save()
    return False


def updateElement(element, force=False):
    for p in common.PM.getProvider(runFor=element.manager):
        #TODO: make sure we use the updated element after one provider is done
        pID = element.getField('id', p.tag)
        if not pID:
            log.info('we dont have this element(%s) on provider(%s) yet. we will search for it' % (element, p))
            #TODO search element by name or with help of xem ... yeah wishful thinking
            #new_e = p.searchForElement(element.getName())
            log.warning('getting an element by name is not implemented can not refresh')
            return None
        log.debug('Getting element with provider id %s on %s' % (pID, p))
        new_e = p.getElement(pID)
        createGenericEvent(element, 'refreshing', 'Serching for update on %s' % p)
        if new_e:
            log.info("%s returned an element" % p)
        else:
            log.info("%s returned NO element" % p)
        if new_e and new_e != element:
            log.info("Found new version of %s" % element)
            for f in list(new_e.fields):
                element.setField(f.name, f.value, f.provider)
            element.deleteImages()
            element.downloadImages()
            return


def runMediaAdder():
    for adder in common.PM.MA:
        medias = adder.runShedule()
        successfulAdd = []
        for media in medias:
            #print '######'
            #print media.mediaTypeIdentifier
            #print media.externalID
            #print media.name
            mtm = common.PM.getMediaTypeManager(media.mediaTypeIdentifier)[0]
            try:
                new_e = Element.getWhereField(mtm.mt, media.elementType, {'id': media.externalID}, media.providerTag, mtm.root)
            except Element.DoesNotExist:
                pass
            else:
                log('We already have %s' % new_e)
                successfulAdd.append(media)
                continue
            for provider in common.PM.getProvider(runFor=mtm):
                log.info('%s is looking for %s(%s) on %s' % (adder, media.name, media.externalID, provider))
                ele = provider.getElement(media.externalID)
                if ele:
                    log.info('we found %s. now lets gets real' % ele)
                    if ele.manager.makeReal(ele):
                        createGenericEvent(ele, 'autoAdd', 'I was added by %s' % adder)
                        common.MM.createInfo('%s added %s' % (adder, ele.getName()))
                        if media not in successfulAdd:
                            successfulAdd.append(media)
                            if ele.status == common.WANTED:
                                t = TaskThread(searchElement, ele)
                                t.start()
                else:
                    log.info('%s did not find %s(%s)' % (provider, media.name, media.externalID))
        adder.successfulAdd(successfulAdd)


def removeTempElements():
    for temp in Element.select().where(Element.status == common.TEMP):
        temp.delete_instance(silent=True)

    log.info("Removeing temp elements DONE")


def cacheRepos():
    common.REPOMANAGER.cache()
    common.REPOMANAGER.checkForUpdate(common.PM.getAll(True, 'Default'))


# these might not belong in here
def installPlugin(identifier):
    common.REPOMANAGER.install(identifier)


def deinstallPlugin(identifier):
    common.REPOMANAGER.deinstall(identifier)
