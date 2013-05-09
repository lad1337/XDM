from xdm.logger import *
from xdm import common
from xdm.classes import *
from xdm.plugins import Indexer
import datetime
import os
import json
from xdm.jsonHelper import MyEncoder
import threading


class TaskThread(threading.Thread):
    def __init__(self, target, *args):
        self._target = target
        self._args = args
        threading.Thread.__init__(self)

    def run(self):
        self._target(*self._args)


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
            createGenericEvent(ele, 'snatch', 'Trying to snatch %s with %s' % (download.name, downloader))
            log.info('Trying to snatch %s with %s' % (download.name, downloader))
            if downloader.addDownload(download):
                ele.status = common.SNATCHED
                ele.save()
                download.status = common.SNATCHED
                download.save()
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
            acceptence, string = curFilterPlugin.compare(element=download.element, download=download)
            if not acceptence:
                log.info('%s did not like %s' % (curFilterPlugin, download))
                createGenericEvent(download.element, 'filter', '%s did not like %s' % (curFilterPlugin, download))
                break
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
            return


def removeTempElements():
    def action():
        log.info("Removeing temp elements")
        for temp in Element.select().where(Element.status == common.TEMP):
            temp.delete_instance(silent=True)

        log.info("Removeing temp elements DONE")

    timer = threading.Timer(1, action)
    timer.start()
    
    