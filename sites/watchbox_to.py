# -*- coding: utf-8 -*-
import re
from resources.lib import logger
from resources.lib.gui.gui import cGui
from resources.lib.gui.guiElement import cGuiElement
from resources.lib.handler.ParameterHandler import ParameterHandler
from resources.lib.handler.requestHandler import cRequestHandler
from resources.lib.parser import cParser

SITE_IDENTIFIER = 'watchbox_to'
SITE_NAME = 'WatchBox.to'
SITE_ICON = 'watchbox_to.png'
SITE_GLOBAL_SEARCH = False

URL_MAIN = 'https://watchbox.to/'
URL_FILME = URL_MAIN + 'filme/'
URL_SERIE = URL_MAIN + 'serien/'
URL_SEARCH = URL_MAIN + '?s=%s'


def load():
    logger.info("Load %s" % SITE_NAME)
    oGui = cGui()
    params = ParameterHandler()
    params.setParam('sUrl', URL_FILME)
    oGui.addFolder(cGuiElement('Filme', SITE_IDENTIFIER, 'showEntries'), params)
    params.setParam('sUrl', URL_SERIE)
    oGui.addFolder(cGuiElement('Serien', SITE_IDENTIFIER, 'showEntries'), params)
    oGui.addFolder(cGuiElement('Genre', SITE_IDENTIFIER, 'showGenre'))
    oGui.addFolder(cGuiElement('Suche', SITE_IDENTIFIER, 'showSearch'))
    oGui.setEndOfDirectory()


def showGenre():
    oGui = cGui()
    params = ParameterHandler()
    sHtmlContent = cRequestHandler(URL_MAIN).request()
    pattern = '(category[^"]+)">([^"]+)</a></li>'
    isMatch, aResult = cParser.parse(sHtmlContent, pattern)

    if not isMatch:
        oGui.showInfo('streamon', 'Es wurde kein Eintrag gefunden')
        return

    for sUrl, sName in aResult:
        params.setParam('sUrl', URL_MAIN + sUrl)
        oGui.addFolder(cGuiElement(sName, SITE_IDENTIFIER, 'showEntries'), params)
    oGui.setEndOfDirectory()


def showEntries(entryUrl=False, sGui=False):
    oGui = sGui if sGui else cGui()
    params = ParameterHandler()
    if not entryUrl: entryUrl = params.getValue('sUrl')
    oRequest = cRequestHandler(entryUrl, ignoreErrors=(sGui is not False))

    sHtmlContent = oRequest.request()
    pattern = '<article[^>]id.*?class="TPost([^"]+)">.*?<a[^>]href="([^"]+)">.*?[^>]src="([^"]+)".*?<h2[^>]class="Title">([^<]+).*?<span[^>]class="Year">([^<]+).*?<div[^>]class="Description">([^"]+)</p>'
    isMatch, aResult = cParser().parse(sHtmlContent, pattern)

    if not isMatch:
        if not sGui: oGui.showInfo('streamon', 'Es wurde kein Eintrag gefunden')
        return

    total = len(aResult)
    for isTv, sUrl, sThumbnail, sName, sYear, sDesc in aResult:
        isTvshow = True if 'seasons' in isTv.lower() else False
        sThumbnail = re.sub('-\d+x\d+\.', '.', sThumbnail)
        oGuiElement = cGuiElement(sName, SITE_IDENTIFIER, 'showSeries' if isTvshow else 'showHosters')
        oGuiElement.setThumbnail(sThumbnail)
        oGuiElement.setFanart(sThumbnail)
        oGuiElement.setDescription(sDesc)
        oGuiElement.setYear(sYear)
        oGuiElement.setMediaType('tvshow' if isTvshow else 'movie')
        params.setParam('sThumbnail', sThumbnail)
        params.setParam('sName', sName)
        params.setParam('entryUrl', sUrl)
        oGui.addFolder(oGuiElement, params, isTvshow, total)
    if not sGui:
        isMatchNextPage, sNextUrl = cParser().parseSingleResult(sHtmlContent, 'href="([^"]+)">Weiter')
        if isMatchNextPage:
            params.setParam('sUrl', sNextUrl)
            oGui.addNextPage(SITE_IDENTIFIER, 'showEntries', params)
        oGui.setView('tvshows' if 'seasons' in isTv.lower() else 'movies')
        oGui.setEndOfDirectory()


def showSeries():
    oGui = cGui()
    params = ParameterHandler()
    entryUrl = params.getValue('entryUrl')
    sThumbnail = params.getValue('sThumbnail')
    sTVShowTitle = params.getValue('sName')
    sHtmlContent = cRequestHandler(entryUrl).request()
    pattern = '<td[^>]class="MvTbTtl"><a[^>]href="([^"]+)">'
    isMatch, aResult = cParser.parse(sHtmlContent, pattern)

    if not isMatch:
        oGui.showInfo('streamon', 'Es wurde kein Eintrag gefunden')
        return

    aResult = sorted(set(aResult), key=aResult.index)
    total = len(aResult)
    for sSeasonNr in aResult:
        res = re.search('-([\d]+)x([\d]+)', sSeasonNr, re.I)
        oGuiElement = cGuiElement('Staffel %s - Episode %s' % (res.group(1), int(res.group(2))), SITE_IDENTIFIER, 'showHosters')
        oGuiElement.setMediaType('season')
        oGuiElement.setTVShowTitle(sTVShowTitle)
        oGuiElement.setThumbnail(sThumbnail)
        params.setParam('entryUrl', sSeasonNr)
        oGui.addFolder(oGuiElement, params, False, total)
    oGui.setView('seasons')
    oGui.setEndOfDirectory()


def showHosters():
    sUrl = ParameterHandler().getValue('entryUrl')
    sHtmlContent = cRequestHandler(sUrl).request()
    sPattern = 'target="_blank"[^>]href="([^"]+)"[^>]class="Button.*?">([^<]+)</span>'
    isMatch, aResult = cParser().parse(sHtmlContent, sPattern)
    hosters = []
    if isMatch:
        for sUrl, sName in aResult:
            hoster = {'link': sUrl, 'name': sName}
            hosters.append(hoster)
    if hosters:
        hosters.append('getHosterUrl')
    return hosters


def getHosterUrl(sUrl=False):
    if 'filecrypt' in sUrl:
        oRequest = cRequestHandler(sUrl)
        sHtmlContent = oRequest.request()
        pattern = '<button[^>]href="([^"]+)'
        isMatch, sUrl = cParser().parseSingleResult(sHtmlContent, pattern)
        if isMatch:
            oRequest = cRequestHandler('https://www.filecrypt.cc/' + sUrl)
            sHtmlContent = oRequest.request()
            pattern = '''(http[^"']+)'''
            isMatch, sUrl = cParser().parseSingleResult(sHtmlContent, pattern)
            if isMatch:
                oRequest = cRequestHandler(sUrl, caching=False)
                oRequest.request()
                sUrl = oRequest.getRealUrl()
    return [{'streamUrl': sUrl, 'resolved': False}]


def showSearch():
    oGui = cGui()
    sSearchText = oGui.showKeyBoard()
    if not sSearchText: return
    _search(False, sSearchText)
    oGui.setEndOfDirectory()


def _search(oGui, sSearchText):
    if not sSearchText: return
    showEntries(URL_SEARCH % sSearchText, oGui)
