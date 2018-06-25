# -*- coding: utf-8 -*-
import re
from resources.lib import logger
from resources.lib.gui.gui import cGui
from resources.lib.gui.guiElement import cGuiElement
from resources.lib.handler.ParameterHandler import ParameterHandler
from resources.lib.handler.requestHandler import cRequestHandler
from resources.lib.parser import cParser

SITE_IDENTIFIER = 'watchbox_de'
SITE_NAME = 'WatchBox.de'
SITE_ICON = 'watchbox_de.png'
SITE_GLOBAL_SEARCH = False

URL_MAIN = 'https://www.watchbox.de'
URL_NEUE_FILME = URL_MAIN + '/filme/neu/'
URL_SERIES = URL_MAIN + '/serien/neu/'
URL_GENRES = URL_MAIN + '/genres/'
URL_SEARCH = 'https://api.watchbox.de/v1/search/?active=true&maxPerPage=28&page=1&term="%s"&types=["film", "serie"]'


def load():
    logger.info("Load %s" % SITE_NAME)
    oGui = cGui()
    params = ParameterHandler()
    params.setParam('sUrl', URL_NEUE_FILME)
    oGui.addFolder(cGuiElement('Filme', SITE_IDENTIFIER, 'showEntries'), params)
    params.setParam('valueType', 'filme')
    oGui.addFolder(cGuiElement('Film Genre', SITE_IDENTIFIER, 'showGenres'), params)
    params.setParam('sUrl', URL_SERIES)
    oGui.addFolder(cGuiElement('Serien', SITE_IDENTIFIER, 'showEntries'), params)
    params.setParam('valueType', 'serien')
    oGui.addFolder(cGuiElement('Serien Genre', SITE_IDENTIFIER, 'showGenres'), params)
    oGui.addFolder(cGuiElement('Suche', SITE_IDENTIFIER, 'showSearch'))
    oGui.setEndOfDirectory()


def showGenres():
    oGui = cGui()
    params = ParameterHandler()
    valueType = params.getValue('valueType')
    sHtmlContent = cRequestHandler(URL_GENRES).request()
    sPattern = '<a[^>]class="genre-teaser"[^>]href="([^"]+).*?title">([^<]+)'
    isMatch, aResult = cParser.parse(sHtmlContent, sPattern)

    if not isMatch:
        oGui.showInfo('streamon', 'Es wurde kein Eintrag gefunden')
        return
    for sUrl, sName in aResult:
        params.setParam('sUrl', URL_MAIN + sUrl + valueType)
        oGui.addFolder(cGuiElement(sName, SITE_IDENTIFIER, 'showEntries'), params)
    oGui.setEndOfDirectory()


def showEntries(entryUrl=False, sGui=False):
    oGui = sGui if sGui else cGui()
    params = ParameterHandler()
    if not entryUrl: entryUrl = params.getValue('sUrl')
    sHtmlContent = cRequestHandler(entryUrl, ignoreErrors=(sGui is not False)).request()
    sPattern = 'data-asset-title="([^"]+).*?href="([^"]+)">.*?src="([^"]+).*?<div[^>]class="text_teaser-portrait-meta">([^<]+).*?description">([^<]+)'
    isMatch, aResult = cParser.parse(sHtmlContent, sPattern)

    if not isMatch:
        if not sGui: oGui.showInfo('streamon', 'Es wurde kein Eintrag gefunden')
        return

    total = len(aResult)
    for sName, sUrl, sThumbnail, sYear, sDesc in aResult:
        try:
            isTvshow = True if "serien" in sUrl else False
            if sThumbnail and sThumbnail.startswith('/'):
                sThumbnail = 'http:' + sThumbnail
            Year = re.compile('(\d{4})', flags=re.I | re.M).findall(sYear)[0]
            oGuiElement = cGuiElement(sName, SITE_IDENTIFIER, 'showSeasons' if isTvshow else 'getHosterUrl')
            oGuiElement.setMediaType('tvshow' if isTvshow else 'movie')
            oGuiElement.setThumbnail(sThumbnail)
            oGuiElement.setFanart(sThumbnail)
            oGuiElement.setYear(Year)
            oGuiElement.setDescription(sDesc)
            params.setParam('sThumbnail', sThumbnail)
            params.setParam('entryUrl', URL_MAIN + sUrl)
            params.setParam('sName', sName)
            oGui.addFolder(oGuiElement, params, isTvshow, total)
        except:
            pass
    if not sGui:
        sPattern = '><link[^>]*href="([^"]+)"[^>]*rel="next"'
        isMatchNextPage, sNextUrl = cParser.parseSingleResult(sHtmlContent, sPattern)
        if isMatchNextPage:
            params.setParam('sUrl', sNextUrl)
            oGui.addNextPage(SITE_IDENTIFIER, 'showEntries', params)
        oGui.setView('tvshows' if 'serien' in entryUrl else 'movies')
        oGui.setEndOfDirectory()


def showSeasons():
    oGui = cGui()
    params = ParameterHandler()
    entryUrl = params.getValue('entryUrl')
    sThumbnail = params.getValue('sThumbnail')
    sTVShowTitle = params.getValue('sName')
    sHtmlContent = cRequestHandler(entryUrl).request()
    pattern = 'season-number="([^"]+).*?href="([^"]+)'
    isMatch, aResult = cParser.parse(sHtmlContent, pattern)

    if not isMatch:
        oGui.showInfo('streamon', 'Es wurde kein Eintrag gefunden')
        return

    total = len(aResult)
    for sSeasonNr, sSeasonUrl in aResult:
        oGuiElement = cGuiElement("Staffel " + sSeasonNr, SITE_IDENTIFIER, 'showEpisodes')
        oGuiElement.setMediaType('season')
        oGuiElement.setTVShowTitle(sTVShowTitle)
        oGuiElement.setSeason(sSeasonNr)
        if sThumbnail:
            oGuiElement.setThumbnail(sThumbnail)
        params.setParam('sSeasonNr', int(sSeasonNr))
        params.setParam('entryUrl', URL_MAIN + sSeasonUrl)
        oGui.addFolder(oGuiElement, params, True, total)
    oGui.setView('seasons')
    oGui.setEndOfDirectory()


def showEpisodes():
    oGui = cGui()
    params = ParameterHandler()
    sTVShowTitle = params.getValue('TVShowTitle')
    entryUrl = params.getValue('entryUrl')
    sSeasonNr = params.getValue('sSeasonNr')
    sHtmlContent = cRequestHandler(entryUrl).request()
    pattern = '<section[^>]class="swiper-slide">.*?season-tab.*?href="([^"]+).*?src="([^"]+).*?alt="([^"]+).*?Episode[^>]([\d+]+)'
    isMatch, aResult = cParser.parse(sHtmlContent, pattern)

    if not isMatch:
        oGui.showInfo('streamon', 'Es wurde kein Eintrag gefunden')
        return

    total = len(aResult)
    for sUrl, sThumbnail, sName, sEpisodeNr in aResult:
        if sThumbnail and sThumbnail.startswith('/'):
            sThumbnail = 'http:' + sThumbnail
        oGuiElement = cGuiElement(sName, SITE_IDENTIFIER, 'getHosterUrl')
        oGuiElement.setTVShowTitle(sTVShowTitle)
        oGuiElement.setSeason(sSeasonNr)
        oGuiElement.setEpisode(sEpisodeNr)
        oGuiElement.setThumbnail(sThumbnail)
        oGuiElement.setMediaType('episode')
        params.setParam('entryUrl', URL_MAIN + sUrl)
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
    showSearchEntries(URL_SEARCH % sSearchText.strip(), oGui)


def showSearchEntries(entryUrl=False, sGui=False):
    oGui = sGui if sGui else cGui()
    params = ParameterHandler()
    if not entryUrl: entryUrl = params.getValue('sUrl')
    oRequest = cRequestHandler(entryUrl, ignoreErrors=(sGui is not False))
    sHtmlContent = oRequest.request()
    sPattern = 'type":"([^"]+).*?entityId":([\d]+).*?headline":"([^"]+).*?description":"([^"]+).*?productionYear":"([^"]+).*?seoPath":"([^"]+)'
    isMatch, aResult = cParser.parse(sHtmlContent, sPattern)

    if not isMatch:
        if not sGui: oGui.showInfo('streamon', 'Es wurde kein Eintrag gefunden')
        return

    total = len(aResult)
    for sType, sId, sName, sDesc, sYear, sUrl in aResult:
        isTvshow = True if "serie" in sType else False
        oGuiElement = cGuiElement(sName, SITE_IDENTIFIER, 'showSeasons' if isTvshow else 'getHosterUrl')
        oGuiElement.setMediaType('tvshow' if isTvshow else 'movie')
        oGuiElement.setYear(sYear)
        sThumbnail = 'https://aiswatchbox-a.akamaihd.net/watchbox/format/' + sId + '_dvdcover/bild.jpg'
        oGuiElement.setThumbnail(sThumbnail)
        oGuiElement.setFanart(sThumbnail)
        oGuiElement.setDescription(sDesc)
        if isTvshow:
            params.setParam('entryUrl', URL_MAIN + '/serien/' + sUrl + '-' + sId)
        else:
            params.setParam('entryUrl', URL_MAIN + '/filme/' + sUrl + '-' + sId)
        params.setParam('sName', sName)
        params.setParam('sThumbnail', sThumbnail)
        oGui.addFolder(oGuiElement, params, isTvshow, total)


def getHosterUrl():
    sUrl = ParameterHandler().getValue('entryUrl')
    sHtmlContent = cRequestHandler(sUrl).request()
    isMatch, hLink = cParser().parseSingleResult(sHtmlContent, "hls:[^>]'([^']+)',")
    if isMatch:
        return [{'streamUrl': hLink, 'resolved': True}]
