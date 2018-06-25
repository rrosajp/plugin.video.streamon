# -*- coding: utf-8 -*-
import re
from resources.lib import logger
from resources.lib.gui.gui import cGui
from resources.lib.gui.guiElement import cGuiElement
from resources.lib.handler.ParameterHandler import ParameterHandler
from resources.lib.handler.requestHandler import cRequestHandler
from resources.lib.parser import cParser

SITE_IDENTIFIER = 'kinox_one'
SITE_NAME = 'KINOX.ONE'
SITE_ICON = 'kinox_one.png'
SITE_GLOBAL_SEARCH = False

URL_MAIN = 'http://kinox.one'
URL_FILME = URL_MAIN + '/movies/'
URL_SERIEN = URL_MAIN + '/tv-shows/'
URL_CARTOONS = URL_MAIN + '/cartoons/'


def load():
    logger.info("Load %s" % SITE_NAME)
    oGui = cGui()
    params = ParameterHandler()
    params.setParam('sUrl', URL_FILME)
    oGui.addFolder(cGuiElement('Filme', SITE_IDENTIFIER, 'showEntries'), params)
    params.setParam('sUrl', URL_SERIEN)
    oGui.addFolder(cGuiElement('Serien', SITE_IDENTIFIER, 'showEntries'), params)
    params.setParam('sUrl', URL_CARTOONS)
    oGui.addFolder(cGuiElement('Cartoons', SITE_IDENTIFIER, 'showEntries'), params)
    oGui.addFolder(cGuiElement('Genre', SITE_IDENTIFIER, 'showGenre'))
    oGui.addFolder(cGuiElement('Suche', SITE_IDENTIFIER, 'showSearch'))
    oGui.setEndOfDirectory()


def showGenre():
    oGui = cGui()
    params = ParameterHandler()
    sHtmlContent = cRequestHandler(URL_MAIN).request()
    isMatch, aResult = cParser.parse(sHtmlContent, '<a[^>]*href="([^"]+)">([^<]+)</a></li><li>')

    if not isMatch:
        oGui.showInfo('streamon', 'Es wurde kein Eintrag gefunden')
        return

    for sUrl, sName in aResult:
        params.setParam('sUrl', URL_MAIN + sUrl)
        oGui.addFolder(cGuiElement(sName, SITE_IDENTIFIER, 'showEntries'), params)
    oGui.setEndOfDirectory()


def showEntries(entryUrl=False, sGui=False, sSearchText=None):
    oGui = sGui if sGui else cGui()
    params = ParameterHandler()
    if not entryUrl: entryUrl = params.getValue('sUrl')
    oRequest = cRequestHandler(entryUrl, ignoreErrors=(sGui is not False))
    oRequest.addHeaderEntry('Upgrade-Insecure-Requests', '1')
    if sSearchText:
        oRequest.addParameters('do', 'search')
        oRequest.addParameters('story', sSearchText)
        oRequest.addParameters('subaction', 'search')  
        oRequest.setRequestType(1)
    sHtmlContent = oRequest.request()

    pattern = '<a[^>]href="([^"]+)"><div.*?<img[^>]src="([^"]+).*?<div[^>]class="tiitle">([^<]+).*?<div[^>]class="shortttt">([^<]+)'
    isMatch, aResult = cParser().parse(sHtmlContent, pattern)

    if not isMatch:
        if not sGui: oGui.showInfo('streamon', 'Es wurde kein Eintrag gefunden')
        return

    total = len(aResult)
    for sUrl, sThumbnail, sName, sYear in aResult:
        sYear = re.compile("([0-9]{4})").findall(sYear)
        for year in sYear:
            sYear = year
            break
        isTvshow = True if "staffel" in sName.lower() else False
        oGuiElement = cGuiElement(sName, SITE_IDENTIFIER, 'showEpisodes' if isTvshow else 'showHosters')
        oGuiElement.setMediaType('tvshow' if isTvshow else 'movie')
        oGuiElement.setThumbnail(URL_MAIN + sThumbnail)
        oGuiElement.setFanart(URL_MAIN + sThumbnail)
        oGuiElement.setYear(sYear)
        oGuiElement.setMediaType('movie')
        params.setParam('entryUrl', sUrl)
        oGui.addFolder(oGuiElement, params, isTvshow, total)
    if not sGui:
        isMatchNextPage, sNextUrl = cParser.parseSingleResult(sHtmlContent, '<a[^>]href="([^"]+)">Next</a>')
        if isMatchNextPage:
            params.setParam('sUrl', sNextUrl)
            oGui.addNextPage(SITE_IDENTIFIER, 'showEntries', params)
        oGui.setView('movies')
        oGui.setEndOfDirectory()


def showEpisodes():
    oGui = cGui()
    params = ParameterHandler()
    sUrl = ParameterHandler().getValue('entryUrl')
    oRequest = cRequestHandler(sUrl)
    oRequest.addHeaderEntry('Upgrade-Insecure-Requests', '1')
    sHtmlContent = oRequest.request()
    
    pattern = 'data-title="([^"]+).*?data-url="([^"]+)'
    isMatch, aResult = cParser.parse(sHtmlContent, pattern)
    if not isMatch:
        oGui.showInfo('streamon', 'Es wurde kein Eintrag gefunden')
        return
    total = len(aResult)
    for sName, sUrl in aResult:
        if not 'trailer' in sName.lower():
            oGuiElement = cGuiElement(sName, SITE_IDENTIFIER, 'getHosterUrl')
            params.setParam('sUrl', sUrl)
            oGui.addFolder(oGuiElement, params, False, total)
    oGui.setView('episodes')
    oGui.setEndOfDirectory()


def showSearch():
    oGui = cGui()
    sSearchText = oGui.showKeyBoard()
    if not sSearchText: return
    _search(False, sSearchText)
    oGui.setEndOfDirectory()


def _search(oGui, sSearchText):
    if not sSearchText: return
    showEntries(URL_MAIN, oGui, sSearchText)


def showHosters():
    sUrl = ParameterHandler().getValue('entryUrl')
    oRequest = cRequestHandler(sUrl)
    oRequest.addHeaderEntry('Upgrade-Insecure-Requests', '1')
    sHtmlContent = oRequest.request()
    sPattern = '"[^>]href="([^"]+)" target'
    isMatch, aResult = cParser().parse(sHtmlContent, sPattern)

    hosters = []
    if isMatch:
        for sUrl in aResult:
            hoster = {'link': sUrl, 'name': 'Kinox.one'}
            hosters.append(hoster)
    if hosters:
        hosters.append('getHosterUrl')
    return hosters


def getHosterUrl(sUrl=False):
    if not sUrl:
        sUrl = ParameterHandler().getValue('sUrl')
    return [{'streamUrl': sUrl, 'resolved': True}]
