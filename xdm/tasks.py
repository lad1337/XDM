from xdm.logger import *
from xdm import common
from xdm.classes import *
from xdm.plugins import Indexer
import datetime
import os
import json
from xdm.jsonHelper import MyEncoder
import threading


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


def notify(game):
    for notifier in common.PM.N:
        createGenericEvent(game, 'Notifier', 'Sending notification with %s on status %s' % (notifier, game.status))
        if notifier.c.on_snatch and game.status == common.SNATCHED:
            notifier.sendMessage("%s has been snatched" % game, game)
        if notifier.c.on_complete and game.status in (common.COMPLETED, common.DOWNLOADED, common.PP_FAIL):
            notifier.sendMessage("%s is now %s" % (game, game.status), game)


def createGenericEvent(game, event_type, event_msg):
    h = History()
    h.game = game
    h.event = event_type
    h.obj_id = 0
    h.obj_class = 'Generic'
    h.old_obj = json.dumps(game, cls=MyEncoder)
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
    #blacklist = common.SYSTEM.getBlacklistForPlatform(ele.platform)
    #whitelist = common.SYSTEM.getWhitelistForPlatform(ele.platform)
    for indexer in common.PM.I:
        if not indexer.runFor(ele.manager):
            log('%s not running for %s' % (indexer, ele.manager))
            continue
        createGenericEvent(ele, 'Search', 'Searching %s on %s' % (ele, indexer))
        downloads = indexer.searchForElement(ele) #intensiv
        
        #downloads = _filterBadDownloads(blacklist, whitelist, downloads)
        downloads = _filterBadDownloads(downloads)
        return snatchOne(ele, downloads)
    return ele.status


# in a way we dont need ele here since each download holds a ref to each ele ... but it is easier to read
def snatchOne(ele, downloads):
    for downloader in common.PM.getDownloaders(types=Indexer.types):
        for download in downloads:
            if not download.type in downloader.types:
                continue
            createGenericEvent(ele, 'Snatch', 'Trying to snatch %s with %s' % (download.name, downloader))
            log.info('Trying to snatch %s with %s' % (download.name, downloader))
            if downloader.addDownload(download):
                ele.status = common.SNATCHED # games save status automatically
                download.status = common.SNATCHED # downloads don't
                download.save()
                notify(ele)
                return ele.status #exit on first success
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
            if old_download.status in (common.FAILED, common.DOWNLOADED):
                log.info("Found a Download(%s) with the same url and it failed or we downloaded it already. Skipping..." % download)
                continue
            if old_download.status == common.SNATCHED:
                if common.SYSTEM.c.resnatch_same:
                    continue
                log.info("Found a Download(%s) with the same url and we snatched it already. I'l get it again..." % download)
            download = old_download
            clean.append(download)
    return clean


def runChecker():
    games = Element.select().execute()
    for checker in common.PM.D:
        for game in games:
            if not game.status == common.SNATCHED:
                continue
            log("Checking status for %s" % game)
            status, download, path = checker.getGameStaus(game)
            log("%s gave back status %s for %s on download %s" % (checker, status, game, download))
            if status == common.DOWNLOADED:
                game.status = common.DOWNLOADED
                if download.id:
                    download.status = common.DOWNLOADED
                    download.save()
                ppGame(game, download, path)
                notify(game)
                if download.id:
                    commentOnDownload(download)
            elif status == common.SNATCHED:
                game.status = common.SNATCHED #status setting on Game saves automatically
                download.status = common.SNATCHED
                download.save()
            elif status == common.FAILED:
                download.status = common.FAILED
                download.save()
                if common.SYSTEM.c.again_on_fail:
                    game.status = common.WANTED
                    searchElement(game)
                else:
                    game.status = common.FAILED


def ppGame(game, download, path):
    pp_try = False
    for pp in common.PM.PP:
        createGenericEvent(game, 'PostProcess', 'Starting PP with %s' % pp)
        if pp.ppPath(game, path):
            game.status = common.COMPLETED # downloaded and pp success
            download.status = common.COMPLETED
            download.save()
            return True
        pp_try = True
    if pp_try:
        game.status = common.PP_FAIL # tried to pp but fail
        download.status = common.PP_FAIL
        download.save()
    return False


#TDOD: make this play nice with multiple providers !!
def updateGames():
    log("running game updater")
    for game in Game.select():
        if game.status == common.DELETED:
            continue
        updateGame(game)


def updateElement(element):
    for p in common.PM.P:
        if not p.runFor(element.manager) or element.manager.identifier not in p.types:
            continue
        pID = element.getField('id', p.tag)
        if not pID:
            log.info('we dont have this element(%s) on provider(%s) yet. we will search for it' % (element, p))
            #TODO search element by name or with help of xem ... yeah wishful thinking
        
        new_e = p.getElement(pID)
        createGenericEvent(element, 'Update', 'Serching for update on %s' % p)
        if new_e and new_e != element:
            log.info("Found new version of %s" % element)
            new_e.id = element.id
            new_e.status = element.status # this will save the new game stuff
            new_e.save()
            new_e.downloadImages()


def removeTempElements():
    def action():
        log.info("Removeing temp elements")
        for temp in Element.select().where(Element.status == common.TEMP):
            temp.delete_instance(silent=True)

    timer = threading.Timer(1, action)
    timer.start()
    
    