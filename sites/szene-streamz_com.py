# -*- coding: utf-8 -*-
from resources.lib import logger
from resources.lib.gui.gui import cGui
from resources.lib.gui.guiElement import cGuiElement
from resources.lib.handler.ParameterHandler import ParameterHandler
from resources.lib.handler.requestHandler import cRequestHandler
from resources.lib.parser import cParser
import re

SITE_IDENTIFIER = 'szene-streamz_com'
SITE_NAME = 'SzeneStreams'
SITE_ICON = 'szenestreams.png'

URL_MAIN = 'http://www.szene-streamz.com/'
URL_MOVIES = URL_MAIN + 'publ/'


def load():
    logger.info("Load %s" % SITE_NAME)
    oGui = cGui()
    params = ParameterHandler()
    params.setParam('PageId', 1)
    params.setParam('sUrl', URL_MOVIES)
    oGui.addFolder(cGuiElement('Alle Filme', SITE_IDENTIFIER, 'showEntries'), params)
    oGui.addFolder(cGuiElement('Genre', SITE_IDENTIFIER, 'showGenre'), params)
    oGui.addFolder(cGuiElement('Suche', SITE_IDENTIFIER, 'showSearch'))
    oGui.setEndOfDirectory()


def showGenre():
    oGui = cGui()
    params = ParameterHandler()
    oRequestHandler = cRequestHandler(params.getValue('sUrl'))
    sHtmlContent = oRequestHandler.request()
    pattern = '<a[^>]*?class="CatInf"[^>]*?href="([^"]+).*?'  # Link
    pattern += '<div[^>]*?class="CatNumInf">(\d+).*?'  # count
    pattern += '<div[^>]*?class="CatNameInf">([^<]+)'  # Name
    isMatch, aResult = cParser.parse(sHtmlContent, pattern)

    if not isMatch:
        oGui.showInfo('streamon', 'Es wurde kein Eintrag gefunden')
        return

    for sUrl, sCount, sName in aResult:
        params.setParam('sUrl', sUrl)
        params.setParam('PageId', 1)
        oGui.addFolder(cGuiElement("%s (%d)" % (sName, int(sCount)), SITE_IDENTIFIER, 'showEntries'), params)
    oGui.setEndOfDirectory()


def showEntries(entryUrl=False, sGui=False, sSearchText=None):
    oGui = sGui if sGui else cGui()
    params = ParameterHandler()
    if not entryUrl: entryUrl = params.getValue('sUrl')
    oRequest = cRequestHandler(entryUrl, ignoreErrors=(sGui is not False))
    if sSearchText:
        oRequest.addParameters('query', sSearchText)
        oRequest.addParameters('a', '2')
        oRequest.setRequestType(1)
    sHtmlContent = oRequest.request()
    pattern = '<div[^>]*class="screenshot".*?<a[^>]*href="([^"]+)".*?'  # thumbnail
    pattern += 'entryLink"[^>]*<a=.*?href="([^"]+)">(.*?)</a>.*?'  # name and link
    pattern += '<div[^>]*class="MessWrapsNews2".*?>([^<>]+)</div>'  # description
    isMatch, aResult = cParser.parse(sHtmlContent, pattern)

    if not isMatch:
        if not sGui: oGui.showInfo('streamon', 'Es wurde kein Eintrag gefunden')
        return

    total = len(aResult)
    for sThumbnail, sUrl, sName, sDesc in aResult:
        sName = re.sub('\((.*?)\)', '', sName)
        oGuiElement = cGuiElement(sName.strip(), SITE_IDENTIFIER, 'showHosters')
        oGuiElement.setMediaType('movie')
        oGuiElement.setThumbnail(URL_MAIN + sThumbnail)
        oGuiElement.setDescription(sDesc.strip())
        params.setParam('entryUrl', URL_MAIN + sUrl)
        oGui.addFolder(oGuiElement, params, False, total)
    if not sGui:
        pattern = '<a class="swchItem" href="([^"]+)".*?><span>(\d+)</span></a>'
        aResult = cParser().parse(sHtmlContent, pattern)
        if aResult[0]:
            currentPage = int(params.getValue('PageId'))
            for sUrl, sPage in aResult[1]:
                page = int(sPage)
                if page <= currentPage: continue
                params.setParam('sUrl', URL_MAIN + sUrl)
                params.setParam('PageId', page)
                oGui.addNextPage(SITE_IDENTIFIER, 'showEntries', params)
                break
        oGui.setView('movies')
        oGui.setEndOfDirectory()


def showHosters():
    params = ParameterHandler()
    sHtmlContent = cRequestHandler(params.getValue('entryUrl')).request()
    pattern = 'blank"[^>]*href="([^"]+)">'
    aResult = cParser().parse(sHtmlContent, pattern)
    hosters = []
    if aResult[1]:
        for sUrl in aResult[1]:
            sName = re.compile('^(?:https?://)?(?:www\.)?(?:[^@\n]+@)?([^:/\n]+)').findall(sUrl)[0]
            hoster = {'link': sUrl, 'name': sName}
            hosters.append(hoster)
    if hosters:
        hosters.append('getHosterUrl')
    return hosters


def getHosterUrl(sUrl=False):
    return [{'streamUrl': sUrl, 'resolved': False}]


def showSearch():
    oGui = cGui()
    sSearchText = oGui.showKeyBoard()
    if not sSearchText: return
    _search(False, sSearchText)
    oGui.setEndOfDirectory()


def _search(oGui, sSearchText):
    if not sSearchText: return
    showEntries(URL_MOVIES, oGui, sSearchText)
