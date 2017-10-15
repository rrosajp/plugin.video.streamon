# -*- coding: utf-8 -*-
import base64
import json
import re
from resources.lib import jsunpacker
from resources.lib import logger
from resources.lib.cCFScrape import cCFScrape
from resources.lib.gui.gui import cGui
from resources.lib.gui.guiElement import cGuiElement
from resources.lib.handler.ParameterHandler import ParameterHandler
from resources.lib.handler.requestHandler import cRequestHandler
from resources.lib.parser import cParser
from resources.lib.util import cUtil

SITE_IDENTIFIER = 'foxx_to'
SITE_NAME = 'Foxx'
SITE_ICON = 'foxx.png'

URL_MAIN = 'http://foxx.to/'
URL_FILME = URL_MAIN + 'film'
URL_SERIE = URL_MAIN + 'serie'
URL_SEARCH = URL_MAIN + 'wp-json/dooplay/search/?keyword=%s&nonce='

QUALITY_ENUM = {'240': 0, '360': 1, '480': 2, '720': 3, '1080': 4}


def load():
    params = ParameterHandler()
    oGui = cGui()
    params.setParam('sUrl', URL_FILME)
    oGui.addFolder(cGuiElement('Filme', SITE_IDENTIFIER, 'showEntries'), params)
    params.setParam('sUrl', URL_SERIE)
    oGui.addFolder(cGuiElement('Serien', SITE_IDENTIFIER, 'showEntries'), params)
    params.setParam('sUrl', URL_MAIN)
    params.setParam('sValue', 'Kategorie')
    oGui.addFolder(cGuiElement('Genres', SITE_IDENTIFIER, 'showValue'), params)
    params.setParam('sValue', 'Erscheinungsjahr')
    oGui.addFolder(cGuiElement('Erscheinungsjahr', SITE_IDENTIFIER, 'showValue'), params)
    oGui.addFolder(cGuiElement('Suche', SITE_IDENTIFIER, 'showSearch'))
    oGui.setEndOfDirectory()


def showValue():
    oGui = cGui()
    params = ParameterHandler()
    sHtmlContent = cRequestHandler(URL_MAIN).request()
    sPattern = '<h2>%s</h2>.*?</nav></div>' % params.getValue('sValue')
    isMatch, sHtmlContainer = cParser.parseSingleResult(sHtmlContent, sPattern)

    if not isMatch:
        oGui.showInfo('steamon', 'Es wurde kein Eintrag gefunden')
        return

    sPattern = '<a[^>]*href="([^"]+).*?>([^<]+)'
    isMatch, aResult = cParser.parse(sHtmlContainer, sPattern)

    if not isMatch:
        oGui.showInfo('steamon', 'Es wurde kein Eintrag gefunden')
        return

    for sUrl, sName in aResult:
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
        if not sGui: oGui.showInfo('steamon', 'Es wurde kein Eintrag gefunden')
        return

    total = len(aResult)
    for sThumbnail, sUrl, sName, sYear, sDesc in aResult:
        sThumbnail = re.sub('-\d+x\d+\.', '.', sThumbnail)
        sThumbnail = cCFScrape.createUrl(sThumbnail, oRequest)
        isTvshow = True if "serie" in sUrl else False
        if sThumbnail and not sThumbnail.startswith('http'):
            sThumbnail = URL_MAIN + sThumbnail
        oGuiElement = cGuiElement(sName, SITE_IDENTIFIER, 'showSeasons' if isTvshow else 'showHosters')
        oGuiElement.setMediaType('tvshow' if isTvshow else 'movie')
        oGuiElement.setThumbnail(sThumbnail)
        if sYear:
            oGuiElement.setYear(sYear)
        oGuiElement.setDescription(sDesc)
        sUrl = cUtil.quotePlus(sUrl)
        params.setParam('entryUrl', sUrl)
        params.setParam('sName', sName)
        params.setParam('sThumbnail', sThumbnail)
        oGui.addFolder(oGuiElement, params, isTvshow, total)

    if not sGui:
        sPattern = "span[^>]*class=[^>]*current[^>]*>.*?</span><a[^>]*href='([^']+)"
        isMatchNextPage, sNextUrl = cParser.parseSingleResult(sHtmlContent, sPattern)
        if isMatchNextPage:
            params.setParam('sUrl', sNextUrl)
            oGui.addNextPage(SITE_IDENTIFIER, 'showEntries', params)
        oGui.setView('tvshows' if 'serie' in sUrl else 'movies')
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
        oGui.showInfo('steamon', 'Es wurde kein Eintrag gefunden')
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
        oGui.showInfo('steamon', 'Es wurde kein Eintrag gefunden')
        return

    pattern = '<a[^>]*href="([^"]+)"[^>]*>\s*<img src="([^"]+).*?<div[^>]*class="numerando">[^-]*-\s*(\d+)\s*?</div>.*?<a[^>]*>([^<]*)</a>'
    isMatch, aResult = cParser.parse(sContainer, pattern)

    if not isMatch:
        oGui.showInfo('steamon', 'Es wurde kein Eintrag gefunden')
        return

    total = len(aResult)
    for sUrl, sThumbnail, sEpisodeNr, sName in aResult:
        oGuiElement = cGuiElement("%s - %s" % (sEpisodeNr, sName.strip()), SITE_IDENTIFIER, 'showHosters')
        oGuiElement.setTVShowTitle(sTVShowTitle)
        oGuiElement.setSeason(sSeasonNr)
        oGuiElement.setEpisode(sEpisodeNr)
        sThumbnail = re.sub('-\d+x\d+\.', '.', sThumbnail)
        sThumbnail = cCFScrape.createUrl(sThumbnail, oRequest)
        oGuiElement.setThumbnail(sThumbnail)
        oGuiElement.setMediaType('episode')
        params.setParam('entryUrl', sUrl.strip())
        oGui.addFolder(oGuiElement, params, False, total)
    oGui.setView('seasons')
    oGui.setEndOfDirectory()


def showHosters():
    params = ParameterHandler()
    sUrl = params.getValue('entryUrl')
    sHtmlContent = cRequestHandler(sUrl).request()
    pattern = '<source[^>]*src="([^"]+)'
    isMatch, aResult = cParser.parse(sHtmlContent, pattern)

    if not isMatch:
        pattern = "file: '([^']+)"
        isMatch, aResult = cParser.parse(sHtmlContent, pattern)

    if isMatch:
        hosters = []
        for sUrl in aResult:
            hosters.append({'link': sUrl, 'name': sUrl})
        if hosters:
            hosters.append('getHosterUrl')
        return hosters

    if not isMatch:
        sPattern = '<iframe[^>]*class="[^"]*metaframe[^"]*"[^>]*src="([^"]+)"'
        isMatch, streamUrl = cParser.parseSingleResult(sHtmlContent, sPattern)

    if not isMatch:
        return []

    oRequest = cRequestHandler(streamUrl)
    oRequest.addHeaderEntry('Referer', sUrl)
    sHtmlContent = oRequest.request()
    isMatch, aResult = cParser.parse(sHtmlContent, '\(["]?(.*)["]?\)')

    if isMatch:
        for packed in aResult:
            try:
                packed = packed.replace('"', '').replace('+', '')
                sHtmlContent += jsunpacker.unpack(base64.decodestring(packed))
            except:
                pass

    isMatch, aResult = cParser.parse(sHtmlContent, 'sources:(\[{".*?}\])')
    if not isMatch:
        logger.info("not Json in aResult")
        return []

    hosters = []
    for sJson in aResult:
        for data in json.loads(sJson):
            if 'file' not in data or 'label' not in data:
                continue
            sLabel = data['label'].encode('utf-8')
            hoster = dict()
            hoster['link'] = data['file'].replace('\\/', '/').replace('\/', '/')
            if data['label'].encode('utf-8')[:-1] in QUALITY_ENUM:
                hoster['quality'] = QUALITY_ENUM[data['label'].encode('utf-8')[:-1]]
            hoster['name'] = sLabel
            hosters.append(hoster)

    if hosters:
        hosters.append('getHosterUrl')
    return hosters


def getHosterUrl(sUrl=False):
    oParams = ParameterHandler()
    if not sUrl: sUrl = oParams.getValue('url')
    return [{'streamUrl': sUrl, 'resolved': False}]


def str_to_utf8(s):
    if '\\u00c4' in s:
        s = s.replace("\\u00c4", "Ä")
    if '\\u00e4' in s:
        s = s.replace("\\u00e4", "ä")
    if '\\u00d6' in s:
        s = s.replace("\\u00d6", "Ö")
    if '\\u00f6' in s:
        s = s.replace("\\u00f6", "ö")
    if '\\u00dc' in s:
        s = s.replace("\\u00dc", "Ü")
    if '\\u00fc' in s:
        s = s.replace("\\u00fc", "ü")
    if '\\u00df' in s:
        s = s.replace("\\u00df", "ß")
    return s


def showSearchEntries(entryUrl=False, sGui=False):
    oGui = sGui if sGui else cGui()
    params = ParameterHandler()
    if not entryUrl: entryUrl = params.getValue('sUrl')
    oRequest = cRequestHandler(entryUrl, ignoreErrors=(sGui is not False))
    sHtmlContent = oRequest.request()

    sPattern = '"title":"([^"]+)","url":"([^"]+)","img":"([^"]+).*?date":"([^"]+)'
    isMatch, aResult = cParser.parse(sHtmlContent, sPattern)

    if not isMatch:
        if not sGui: oGui.showInfo('steamon', 'Es wurde kein Eintrag gefunden')
        return

    total = len(aResult)
    for sName, sUrl, sThumbnail, sYear in aResult:
        sThumbnail = sThumbnail.replace('\\/', '/').replace('\/', '/')
        sUrl = sUrl.replace('\\/', '/').replace('\/', '/')
        sThumbnail = re.sub('-\d+x\d+\.', '.', sThumbnail)
        if sThumbnail and not sThumbnail.startswith('http'):
            sThumbnail = URL_MAIN + sThumbnail
        sThumbnail = cCFScrape.createUrl(sThumbnail, oRequest)
        isTvshow = True if "serie" in sUrl else False
        sName = str_to_utf8(sName)
        oGuiElement = cGuiElement(sName, SITE_IDENTIFIER, 'showSeasons' if isTvshow else 'showHosters')
        oGuiElement.setMediaType('tvshow' if isTvshow else 'movie')
        oGuiElement.setThumbnail(sThumbnail)
        oGuiElement.setYear(sYear)
        sUrl = cUtil.quotePlus(sUrl)
        params.setParam('entryUrl', sUrl)
        params.setParam('sName', sName)
        params.setParam('sThumbnail', sThumbnail)
        oGui.addFolder(oGuiElement, params, isTvshow, total)

    if not sGui:
        sPattern = "span[^>]*class=[^>]*current[^>]*>.*?</span><a[^>]*href='([^']+)"
        isMatchNextPage, sNextUrl = cParser.parseSingleResult(sHtmlContent, sPattern)
        if isMatchNextPage:
            params.setParam('sUrl', sNextUrl)
            oGui.addNextPage(SITE_IDENTIFIER, 'showEntries', params)
        oGui.setView('tvshows' if 'serie' in sUrl else 'movies')
        oGui.setEndOfDirectory()


def showSearch():
    oGui = cGui()
    sHtmlContent = cRequestHandler(URL_MAIN).request()
    try:
        nonce = re.findall('nonce":"([^"]+)', sHtmlContent)[0]
    except:
        nonce = '5d12d0fa54'

    sSearchText = oGui.showKeyBoard()
    if not sSearchText: return
    _search(False, sSearchText, nonce)
    oGui.setEndOfDirectory()


def _search(oGui, sSearchText, nonce):
    if not sSearchText: return
    showSearchEntries(URL_SEARCH % sSearchText.strip() + nonce, oGui)
