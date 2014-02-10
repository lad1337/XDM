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

from xdm.logger import *
from xdm import common, helper
from xdm.classes import *
from xdm.plugins.bases import DownloadFilter
import json
from xdm.jsonHelper import MyEncoder
import threading
import datetime
from babel.dates import format_timedelta
import Queue


class TaskThread(threading.Thread):
    def __init__(self, target, *args, **kwargs):
        self._target = target
        self._args = args
        self._kwargs = kwargs
        threading.Thread.__init__(self)

    def run(self):
        log.debug(u'Running %s with args: %s and kwargs: %s' % (self._target.__name__, self._args, self._kwargs))
        self._target(*self._args, **self._kwargs)


def checkQ():
    try:
        key, body = common.Q.get(False)
    except Queue.Empty:
        return
    try:
        if key == 'image.download':
            try:
                e = Element.get(Element.id == body['id'])
                e.downloadImages()
            except Element.DoesNotExist:
                pass
    except:
        raise
    finally:
        common.Q.task_done()


def coreUpdateCheck():
    common.MM.clearRole("coreUpdate")
    updateResponse = common.UPDATER.check()
    log.info('%s' % updateResponse)
    if updateResponse.needUpdate == True:
        common.MM.createInfo('%s Update now?' % updateResponse.message, confirmJavascript='modalCoreUpdate(this)', role="coreUpdate")
        if common.SYSTEM.c.auto_update_core:
            t = TaskThread(common.UPDATER.update)
            t.start()
        else:
            for notifier in common.PM.N:
                if notifier.c.on_update:
                    notifier.sendMessage(updateResponse.message)
    elif updateResponse.needUpdate is None:
        common.MM.createWarning(updateResponse.message, role="coreUpdate")


def coreUpdateDo():
    updateResponse = common.UPDATER.update()


def runSearcher():
    log("running searcher")
    for mtm in common.PM.MTM:
        runSearcherForMediaType(mtm)


def runSearcherForMediaType(mtm, root=None):
    for ele in mtm.getDownloadableElements():
        if root and ele not in root.decendants:
            log.debug("%s is not under given root %s, skipping" % (ele, root))
            continue
        if ele.status == common.FAILED and common.SYSTEM.c.again_on_fail:
            ele.status = common.WANTED
        elif ele.status != common.WANTED:
            continue

        log(u"Looking for %s" % ele)
        searchElement(ele)

def notify(element):
    if element.status == common.SNATCHED:
        common.MM.createInfo(u"%s was snatched" % element.getName())
    elif element.status == common.COMPLETED:
        common.MM.createInfo(u"%s is Completed" % element.getName())
    elif element.status == common.DOWNLOADED:
        common.MM.createInfo(u"%s was downloaded" % element.getName())
    elif element.status == common.PP_FAIL:
        common.MM.createWarning(u"%s had an error during post processing" % element.getName())

    for notifier in common.PM.N:
        createGenericEvent(element, 'notifier', u'Sending notification with %s on status %s' % (notifier, element.status))
        if notifier.c.on_snatch and element.status == common.SNATCHED:
            notifier.sendMessage(u"%s: %s has been snatched" % (element.manager.type, element.getName()), element)
        if notifier.c.on_complete and element.status in (common.COMPLETED, common.DOWNLOADED, common.PP_FAIL):
            notifier.sendMessage(u"%s: %s is now %s" % (element.manager.type, element.getName(), element.status), element)


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
            indexer.commentOnDownload('XDM snatched this but it failed to download (automtic notice)', download)
        if indexer.c.comment_on_download and download.status in (common.COMPLETED, common.DOWNLOADED, common.PP_FAIL):
            indexer.commentOnDownload('XDM snatched this and it downloaded successfully (automtic notice)', download)


def searchElement(ele, forced=False):
    for pre_filter in common.PM.getDownloadFilters(runFor=ele.manager):
        if DownloadFilter._pre_search not in pre_filter.stages:
            continue
        pre_result = pre_filter.compare(ele, forced=forced)
        if not pre_result:
            createGenericEvent(ele, u'filter', "%s did't liked %s, reason: %s" % (pre_filter, ele, pre_result.reason))
            return ele.status

    didSearch = False
    downloads = []
    for indexer in common.PM.getIndexers(runFor=ele.manager):
        createGenericEvent(ele, 'search', u'Searching %s on %s' % (ele, indexer))
        log.info(u"Init search of %s on %s" % (ele, indexer))
        downloads.extend(indexer.searchForElement(ele)) # intensiv
        createGenericEvent(ele, 'result', u'%s found %s results' % (indexer, len(downloads)))
        didSearch = True

    if not didSearch:
        log.warning(u"No Indexer active/available for %s" % ele.manager)
    else:
        _downloads = _filterBadDownloads(downloads, ele)
        if _downloads:
            return snatchOne(ele, _downloads)
        else:
            log.info(u"We filtered all downloads out for %s" % ele)
    return ele.status


# in a way we dont need ele here since each download holds a ref to each ele ... but it is easier to read
def snatchOne(ele, downloads):
    downloaders = common.PM.getDownloaders()
    if not downloaders:
        log.warning(u"No Downloaders active/installed")
        return ele.status

    for downloader in downloaders:
        triedSnatch = False
        for download in downloads:
            if not download.type in downloader.types:
                continue
            createGenericEvent(ele, 'snatchTry', u'Trying to snatch %s with %s' % (download.name, downloader))
            createGenericEvent(download, 'snatchTry', u'%s is trying to snatch me' % (downloader))
            log.info(u'Trying to snatch %s with %s' % (download.name, downloader))
            if downloader.addDownload(download):
                ele.status = common.SNATCHED
                ele.save()
                download.status = common.SNATCHED
                download.save()
                log(u'%s snatched %s' % (downloader, download))
                createGenericEvent(download, 'snatch', u'%s snatched me' % (downloader))
                notify(ele)
                return ele.status # exit on first success
            triedSnatch = True
        if triedSnatch and downloads:
            log.warning(u"No Downloaders active/available for %s (or they all failed)" % download.type)
        elif not downloads:
            log.info(u"No downloads found for %s" % download.element)
    return ele.status


def _filterBadDownloads(downloads, element, forced=False):
    clean = []
    for download in downloads:
        old_download = None
        try:
            old_download = Download.get(Download.url == download.url)
        except Download.DoesNotExist:
            # no download with that url found
            pass

        if not old_download:
            log(u"Saving the new download we found %s" % download)
            download.status = common.UNKNOWN
            download.save()
        else:
            try:
                Element.get(Element.id == download.element.id)
            except Element.DoesNotExist:
                log.warning(u"The element for the download(%s) does not exist any more deleting the old one but taking the status from the old one" % download.id)
                download.status = old_download.status
                old_download.delete_instance()
                download.save()
                old_download = download

            if old_download.status in (common.FAILED, common.DOWNLOADED):
                log.info(u"Found a Download(%s) with the same url and it failed or we downloaded it already. Skipping..." % download)
                continue
            #TODO: do something about downloads that where found for multiple elements
            if old_download.element != element:
                log.warning(u"Old Download(%s) was connected to %s, connecting it now to %s" % (download, download.element, element))
                old_download.element = element
                old_download.save()
            if old_download.status == common.SNATCHED:
                if common.SYSTEM.c.resnatch_same:
                    continue
                log.info(u"Found a Download(%s) with the same url and we snatched it already. I'l get it again..." % download)
            download = old_download

        for curFilterPlugin in common.PM.getDownloadFilters(runFor=download.element.manager):
            filterResult = curFilterPlugin.compare(element=download.element, download=download)
            if not filterResult.result:
                log.info(u'%s did not like %s, reason: %s' % (curFilterPlugin, download, filterResult.reason))
                # createGenericEvent(download.element, 'filter', '%s did not like %s, reason: %s' % (curFilterPlugin, download, filterResult.reason))
                createGenericEvent(download, 'filter', u'%s did not like me, reason: %s' % (curFilterPlugin, filterResult.reason))
                break
            else:
                log.info(u'%s liked %s, reason: %s' % (curFilterPlugin, download, filterResult.reason))
                createGenericEvent(download.element, u'filter', '%s liked %s, reason: %s' % (curFilterPlugin, download, filterResult.reason))
                createGenericEvent(download, 'filter', u'%s liked me, reason: %s' % (curFilterPlugin, filterResult.reason))
        else:
            clean.append(download)
    return clean


def runChecker():
    elements = list(Element.select().execute())
    for checker in common.PM.D:
        for element in elements:
            if element.status not in (common.SNATCHED, common.DOWNLOADING):
                continue
            log(u"Checking status for %s" % element)
            status, download, path = checker.getElementStaus(element)
            log(u"%s gave back status %s for %s on download %s" % (checker, status, element, download))
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
                if element.status != common.SNATCHED: # dont "resnatch" its during download
                    element.status = common.SNATCHED
                    element.save()
                    download.status = common.SNATCHED
                    download.save()
            elif status == common.DOWNLOADING:
                if element.status != common.DOWNLOADING: # dont reset the downloading status during download
                    element.status = common.DOWNLOADING
                    element.save()
                    if download.id:
                        commentOnDownload(download)
                    download.status = common.DOWNLOADING
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

def ppElementLocations():
    pass

def ppElement(element, download, initial_path):
    pp_try = False
    new_location = initial_path
    ppResult = False

    for pp in common.PM.getPostProcessors(runFor=element.manager):
        createGenericEvent(element, 'postProcess', 'Starting PP with %s' % pp)
        log(u'Starting PP on %s with %s at %s' % (element, pp, new_location))
        ppResult, _new_location, pp_log = pp.postProcessPath(element, new_location)
        pp_try = True
        download.pp_log = u'LOG from %s:\n%s\n######\n%s' % (pp, pp_log, download.pp_log)
        if ppResult:
            if _new_location:
                new_location = _new_location
            element.status = common.COMPLETED
            element.save()
            download.status = common.COMPLETED
            if pp.c.stop_after_me_select == common.STOPPPONSUCCESS or pp.c.stop_after_me_select == common.STOPPPALWAYS:
                break
        else:
            if pp.c.stop_after_me_select == common.STOPPPONFAILURE or pp.c.stop_after_me_select == common.STOPPPALWAYS:
                break
        download.save()

    element.addLocation(new_location, download)
    if not ppResult:
        if pp_try:
            element.status = common.PP_FAIL # tried to pp but fail
            element.save()
            download.status = common.PP_FAIL
            download.save()
        return False
    return True


def updateElement(element, force=False, new_node_status=None):
    if new_node_status is None:
        new_node_status = common.getStatusByID(element.manager.c.new_node_status_select)
    if not isinstance(new_node_status, Status):
        log.error(
            "I expected the new_node_status to be of instance Status but i got {}. Not updating {}".format(
                new_node_status.__class__, element)
        )
        return
    else:
        log.debug("Using new_node_status %s" % new_node_status)

    for p in common.PM.getProvider(runFor=element.manager):
        # TODO: make sure we use the updated element after one provider is done
        for current_tag in p.tags:
            pID = element.getField('id', current_tag)
            if not pID:
                log.info(u'we dont have this element(%s) on provider(%s) with tag %s' % (element, p, current_tag))
                # TODO search element by name or with help of xem ... yeah wishful thinking
                # new_e = p.searchForElement(element.getName())
                log.warning('getting an element by name is not implemented can not refresh')
                continue
            log(u'Getting %s with provider id %s on %s' % (element, pID, p))
            new_e = p.getElement(pID, element, tag=current_tag)
            createGenericEvent(element, 'refreshing', u'Serching for update on %s' % p)
            if new_e:
                log.info(u"%s returned an element" % p)
            else:
                log.info(u"%s returned NO element" % p)
                continue

            log("Processing new data tree %s" % new_e)
            new_nodes = helper.getNewNodes(element, new_e, current_tag)
            log("Processing %s done" % new_e)
            if new_nodes:
                for new_node in new_nodes:
                    log.info("%s is a new node compared to the root %s" % (new_node, element))
                    new_parent = helper.findOldNode(new_node.parent, element, current_tag)
                    log.debug("attaching %s to %s" % (new_node, new_parent))
                    new_node.parent = new_parent
                    log.debug("Setting status of new node %s to %s" % (new_node, new_node_status))
                    new_node.status = new_node_status
                    new_node.save()
                    common.Q.put(('image.download', {'id': new_node.id}))
            else:
                log("No new nodes found in %s" % new_e)

            log("Clearing cache from %s" % element)
            element.clearTreeCache()
            log("Clearing cache from %s" % new_e)
            new_e.clearTreeCache()

            for updated_node in [new_e] + new_e.decendants:
                old_node = helper.findOldNode(updated_node, element, current_tag)
                if old_node is None:
                    log.error("No old node found for %s in %s" % (updated_node, element))
                    continue

                if not helper.sameElements(old_node, updated_node):
                    log.info(u"Found new version of %s" % old_node)
                    for f in list(updated_node.fields):
                        old_node.setField(f.name, f.value, f.provider)
                    common.Q.put(('image.download', {'id': old_node.id}))


def updateAllElements():
    log('updating all elements')
    for mtm in common.PM.MTM:
        for element in mtm.getUpdateableElements(True):
            updateElement(element)


def runMediaAdder():
    for adder in common.PM.MA:
        medias = adder.runShedule()
        successfulAdd = []
        for media in medias:
            # print '######'
            # print media.mediaTypeIdentifier
            # print media.externalID
            # print media.name
            mtm = common.PM.getMediaTypeManager(media.mediaTypeIdentifier)[0]
            try:
                new_e = Element.getWhereField(mtm.mt, media.elementType, {'id': media.externalID}, media.providerTag, mtm.root)
            except Element.DoesNotExist:
                pass
            else:
                log(u'We already have %s' % new_e)
                media.root = new_e
                successfulAdd.append(media)
                continue
            for provider in common.PM.getProvider(runFor=mtm):
                log.info(u'%s is looking for %s(%s:%s) on %s' % (adder, media.name, media.providerTag, media.externalID, provider))
                ele = provider.getElement(media.externalID, tag=media.providerTag)

                if not ele and common.SYSTEM.c.mediaadder_search_by_name:
                    log.info(u'%s did not find %s(%s) trying now by NAME' % (provider, media.name, media.externalID))
                    rootElement = mtm.search(media.name)
                    if len(list(rootElement.children)) == 1:
                        log.info("We found one by with the name %s adding it!" % media.name)
                        ele = list(rootElement.children)[0]
                    else:
                        log.info("We found multiple results with by name %s" % media.name)
                        for child in rootElement.children:
                            log.info("found %s" % child)

                if ele:
                    log.info(u'we found %s. now lets gets real' % ele)
                    if media.status is None:
                        new_status = common.getStatusByID(ele.manager.c.automatic_new_status_select)
                    else:
                        new_status = media.status
                    if ele.manager.makeReal(ele, new_status):
                        createGenericEvent(ele, u'autoAdd', 'I was added by %s' % adder)
                        common.MM.createInfo(u'%s added %s' % (adder, ele.getName()))
                        media.root = ele
                        if media not in successfulAdd:
                            successfulAdd.append(media)
                            if new_status == common.WANTED:
                                t = TaskThread(runSearcherForMediaType, ele.manager, ele)
                                t.start()
                else:
                    log.info("Nothing found :(")

        adder.successfulAdd(successfulAdd)


def removeTempElements():
    common.addState(6)
    silent = not common.STARTOPTIONS.dev
    for temp in list(Element.select().where(Element.status == common.TEMP)):
        temp.delete_instance(silent=silent)

    log.info("Removeing temp elements DONE")
    common.removeState(6)


def cacheRepos():
    common.REPOMANAGER.cache()


# these might not belong in here
def installPlugin(identifier):
    common.REPOMANAGER.install(identifier)


def deinstallPlugin(identifier):
    common.REPOMANAGER.deinstall(identifier)
