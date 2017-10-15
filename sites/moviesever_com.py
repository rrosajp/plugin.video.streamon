# -*- coding: utf-8 -*-
import re, base64
from resources.lib import logger
from resources.lib.gui.gui import cGui
from resources.lib.gui.guiElement import cGuiElement
from resources.lib.handler.ParameterHandler import ParameterHandler
from resources.lib.handler.requestHandler import cRequestHandler
from resources.lib.parser import cParser
from resources.lib.util import cUtil

SITE_IDENTIFIER = 'moviesever_com'
SITE_NAME = 'MoviesEver'
SITE_ICON = 'moviesever.png'

URL_MAIN = 'http://moviesever.com/'
URL_FILME = URL_MAIN + 'filme/'
URL_SERIEN = URL_MAIN + 'serien/'
URL_SEARCH = URL_MAIN + 'wp-json/dooplay/search/?keyword=%s&nonce='


def load():
    logger.info("Load %s" % SITE_NAME)
    params = ParameterHandler()
    oGui = cGui()
    params.setParam('sUrl', URL_FILME)
    oGui.addFolder(cGuiElement('Filme', SITE_IDENTIFIER, 'showEntries'), params)
    params.setParam('sUrl', URL_SERIEN)
    oGui.addFolder(cGuiElement('Serien', SITE_IDENTIFIER, 'showEntries'), params)
    params.setParam('sGenreId', 'genres')
    oGui.addFolder(cGuiElement('Genres', SITE_IDENTIFIER, 'showGenres'), params)
    params.setParam('sGenreId', 'releases')
    oGui.addFolder(cGuiElement('Erscheinungsjahr', SITE_IDENTIFIER, 'showGenres'), params)
    oGui.addFolder(cGuiElement('Suche', SITE_IDENTIFIER, 'showSearch'))
    oGui.setEndOfDirectory()


def showGenres():
    oGui = cGui()
    params = ParameterHandler()
    sHtmlContent = cRequestHandler(URL_MAIN).request()
    sPattern = '<nav[^>]*class="%s">.*?</ul></nav>' % params.getValue('sGenreId')
    isMatch, sHtmlContainer = cParser.parseSingleResult(sHtmlContent, sPattern)

    if not isMatch:
        oGui.showInfo('streamon', 'Es wurde kein Eintrag gefunden')
        return
    sPattern2 = '<a[^>]*href="([^"]+)">([^<]+)'
    isMatch, aResult = cParser.parse(sHtmlContainer, sPattern2)

    if not isMatch:
        oGui.showInfo('streamon', 'Es wurde kein Eintrag gefunden')
        return

    for sUrl, sName in aResult:
        if sUrl and not sUrl.startswith('http'):
           sUrl = URL_MAIN + sUrl
        params.setParam('sUrl', sUrl)
        oGui.addFolder(cGuiElement(sName, SITE_IDENTIFIER, 'showEntries'), params)
    oGui.setEndOfDirectory()


def showEntries(entryUrl=False, sGui=False):
    oGui = sGui if sGui else cGui()
    params = ParameterHandler()
    if not entryUrl: entryUrl = params.getValue('sUrl')
    oRequest = cRequestHandler(entryUrl, ignoreErrors=(sGui is not False))
    sHtmlContent = oRequest.request()

    sPattern = '<div[^>]*class="poster">.*?<img[^>]*src="([^"]+).*?<a[^>]*href="([^"]+)">([^<]+).*?(?:<span>([^<]+)?).*?<div[^>]*class="texto">([^<]+)'
    isMatch, aResult = cParser.parse(sHtmlContent, sPattern)

    if not isMatch:
        if not sGui: oGui.showInfo('streamon', 'Es wurde kein Eintrag gefunden')
        return

    total = len(aResult)
    for sThumbnail, sUrl, sName, sYear, sDesc in aResult:
        sThumbnail = re.sub('-\d+x\d+\.', '.', sThumbnail)
        isTvshow = True if "serien" in sUrl else False
        if sThumbnail and not sThumbnail.startswith('http'):
            sThumbnail = URL_MAIN + sThumbnail
        oGuiElement = cGuiElement(sName, SITE_IDENTIFIER, 'showSeasons' if isTvshow else 'showHosters')
        oGuiElement.setMediaType('tvshow' if isTvshow else 'movie')
        oGuiElement.setThumbnail(sThumbnail)
        if sYear:
            oGuiElement.setYear(sYear)
        oGuiElement.setDescription(sDesc)
        sUrl = cUtil.quotePlus(sUrl)
        if sUrl and not sUrl.startswith('http'):
           sUrl = URL_MAIN + sUrl
        params.setParam('entryUrl', sUrl)
        params.setParam('sName', sName)
        params.setParam('sThumbnail', sThumbnail)
        oGui.addFolder(oGuiElement, params, isTvshow, total)

    if not sGui:
        sPattern = '<div[^>]*class="resppages"><a[^>]*href="([^"]+)">'
        isMatchNextPage, sNextUrl = cParser.parseSingleResult(sHtmlContent, sPattern)
        if isMatchNextPage:
            if sNextUrl and not sNextUrl.startswith('http'):
                sNextUrl = URL_MAIN + sNextUrl
            params.setParam('sUrl', sNextUrl)
            oGui.addNextPage(SITE_IDENTIFIER, 'showEntries', params)
        oGui.setView('tvshows' if 'serien' in sUrl else 'movies')
        oGui.setEndOfDirectory()


def showSeasons():
    oGui = cGui()
    params = ParameterHandler()
    entryUrl = params.getValue('entryUrl')
    sThumbnail = params.getValue('sThumbnail')
    sTVShowTitle = params.getValue('sName')

    sHtmlContent = cRequestHandler(entryUrl).request()
    pattern = '<span[^>]*class="se-t[^"]*"[^>]*>(\d+)</span>'
    isMatch, aResult = cParser.parse(sHtmlContent, pattern)

    if not isMatch:
        oGui.showInfo('streamon', 'Es wurde kein Eintrag gefunden')
        return

    total = len(aResult)
    for sSeasonNr in aResult:
        oGuiElement = cGuiElement("Staffel " + sSeasonNr, SITE_IDENTIFIER, 'showEpisodes')
        oGuiElement.setMediaType('season')
        oGuiElement.setTVShowTitle(sTVShowTitle)
        oGuiElement.setSeason(sSeasonNr)
        oGuiElement.setThumbnail(sThumbnail)
        params.setParam('sSeasonNr', int(sSeasonNr))
        oGui.addFolder(oGuiElement, params, True, total)
    oGui.setView('seasons')
    oGui.setEndOfDirectory()


def showEpisodes():
    oGui = cGui()
    params = ParameterHandler()
    sTVShowTitle = params.getValue('TVShowTitle')
    entryUrl = params.getValue('entryUrl')
    sSeasonNr = params.getValue('sSeasonNr')
    oRequest = cRequestHandler(entryUrl)
    sHtmlContent = oRequest.request()
    pattern = '<span[^>]*class="se-t[^"]*">%s</span>.*?<ul[^>]*class="episodios"[^>]*>(.*?)</ul>' % sSeasonNr
    isMatch, sContainer = cParser.parseSingleResult(sHtmlContent, pattern)

    if not isMatch:
        oGui.showInfo('streamon', 'Es wurde kein Eintrag gefunden')
        return

    pattern = '<a[^>]*href="([^"]+)"[^>]*>\s*<img src="([^"]+).*?<div[^>]*class="numerando">[^-]*-\s*(\d+)\s*?</div>.*?<a[^>]*>([^<]*)</a>'
    isMatch, aResult = cParser.parse(sContainer, pattern)

    if not isMatch:
        oGui.showInfo('streamon', 'Es wurde kein Eintrag gefunden')
        return

    total = len(aResult)
    for sUrl, sThumbnail, sEpisodeNr, sName in aResult:
        oGuiElement = cGuiElement("%s - %s" % (sEpisodeNr, sName.strip()), SITE_IDENTIFIER, 'showHosters')
        oGuiElement.setTVShowTitle(sTVShowTitle)
        oGuiElement.setSeason(sSeasonNr)
        oGuiElement.setEpisode(sEpisodeNr)
        sThumbnail = re.sub('-\d+x\d+\.', '.', sThumbnail)
        oGuiElement.setThumbnail(sThumbnail)
        oGuiElement.setMediaType('episode')
        if sUrl and not sUrl.startswith('http'):
           sUrl = URL_MAIN + sUrl
        params.setParam('entryUrl', sUrl.strip())
        oGui.addFolder(oGuiElement, params, False, total)
    oGui.setView('seasons')
    oGui.setEndOfDirectory()


def showHosters():
    params = ParameterHandler()
    sUrl = params.getValue('entryUrl')
    sHtmlContent = cRequestHandler(sUrl).request()
    pattern = '"link":"([^"]+)"'
    isMatch, aResult = cParser.parse(sHtmlContent, pattern)

    if not isMatch:
        return []

    hosters = []
    for sUrl in aResult:
        sUrl = __decodeHash(sUrl)
        try:
            hname = re.compile('^(?:https?:\/\/)?(?:[^@\n]+@)?([^:\/\n]+)', flags=re.I | re.M).findall(sUrl)[0]
        except:
            pass
        hoster = {}
        hoster['name'] = hname
        hoster['link'] = sUrl
        hosters.append(hoster)
    if hosters:
        hosters.append('getHosterUrl')
    return hosters


def __decodeHash(sHash):
    sHash = sHash.replace("!BeF", "R")
    sHash = sHash.replace("@jkp", "Ax")
    try:
        return base64.b64decode(sHash)
    except:
        logger.error("Invalid Base64: %s" % sHash)


def getHosterUrl(sUrl=False):
    oParams = ParameterHandler()
    if not sUrl: sUrl = oParams.getValue('url')
    return [{'streamUrl': sUrl, 'resolved': False}]


def showSearchEntries(entryUrl=False, sGui=False):
    oGui = sGui if sGui else cGui()
    params = ParameterHandler()
    if not entryUrl: entryUrl = params.getValue('sUrl')
    oRequest = cRequestHandler(entryUrl, ignoreErrors=(sGui is not False))
    sHtmlContent = oRequest.request()

    sPattern = '"title":"([^"]+)","url":"([^"]+)","img":"([^"]+).*?date":"([^"]+)'
    isMatch, aResult = cParser.parse(sHtmlContent, sPattern)

    if not isMatch:
        if not sGui: oGui.showInfo('streamon', 'Es wurde kein Eintrag gefunden')
        return

    total = len(aResult)
    for sName, sUrl, sThumbnail, sYear in aResult:
        sThumbnail = sThumbnail.replace('\\/', '/').replace('\/', '/')
        sUrl = sUrl.replace('\\/', '/').replace('\/', '/')
        sThumbnail = re.sub('-\d+x\d+\.', '.', sThumbnail)
        if sThumbnail and not sThumbnail.startswith('http'):
            sThumbnail = URL_MAIN + sThumbnail
        isTvshow = True if "serie" in sUrl else False
        oGuiElement = cGuiElement(sName, SITE_IDENTIFIER, 'showSeasons' if isTvshow else 'showHosters')
        oGuiElement.setMediaType('tvshow' if isTvshow else 'movie')
        oGuiElement.setThumbnail(sThumbnail)
        oGuiElement.setYear(sYear)
        sUrl = cUtil.quotePlus(sUrl)
        params.setParam('entryUrl', sUrl)
        params.setParam('sName', sName)
        params.setParam('sThumbnail', sThumbnail)
        oGui.addFolder(oGuiElement, params, isTvshow, total)


def showSearch():
    oGui = cGui()
    sHtmlContent = cRequestHandler(URL_MAIN).request()
    try:
        nonce = re.findall('nonce":"([^"]+)', sHtmlContent)[0]
    except:
        nonce = '033ba26c1b'
    sSearchText = oGui.showKeyBoard()
    if not sSearchText: return
    _search(False, sSearchText, nonce)
    oGui.setEndOfDirectory()


def _search(oGui, sSearchText, nonce):
    if not sSearchText: return
    showSearchEntries(URL_SEARCH % sSearchText.strip() + nonce, oGui)
