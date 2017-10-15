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

QUALITY_ENUM = {'240p': 0, '360p': 1, '480p': 2, '720p': 3, '1080p': 4}

URL_GENRES_LIST = {'Action': 'genre/action', 'Comedy': 'genre/comedy/', 'Drama': 'genre/drama/',
                   'History': 'genre/history/', 'Music': 'genre/music', 'Reality': 'genre/reality',
                   'Sci-Fi': 'genre/science-fiction', 'War': 'genre/war', 'Adventure': 'genre/adventure',
                   'Crime': 'genre/crime', 'Family': 'genre/family', 'Horror': 'genre/horror',
                   'Mystery': 'genre/mystery', 'Fantasy': 'genre/fantasy', 'Romance': 'genre/romance',
                   'Soap': 'genre/soap', 'War &#038; Politics': 'genre/war-politics', 'Animation': 'genre/animation',
                   'Documentary': 'genre/documentary', 'Kids': 'genre/kids', 'News': 'genre/news',
                   'Sci-Fi &#038; Fantasy': 'genre/sci-fi-fantasy', 'Thriller': 'genre/thriller',
                   'Western': 'genre/western'}


def load():
    params = ParameterHandler()
    oGui = cGui()
    params.setParam('sUrl', URL_FILME)
    oGui.addFolder(cGuiElement('Filme', SITE_IDENTIFIER, 'showEntries'), params)
    params.setParam('sUrl', URL_SERIE)
    oGui.addFolder(cGuiElement('Serien', SITE_IDENTIFIER, 'showEntries'), params)
    params.setParam('sUrl', URL_MAIN)
    oGui.addFolder(cGuiElement('Genres', SITE_IDENTIFIER, 'showGenresList'), params)
    oGui.addFolder(cGuiElement('Suche', SITE_IDENTIFIER, 'showSearch'))
    oGui.setEndOfDirectory()


def showGenresList():
    oGui = cGui()
    for key in sorted(URL_GENRES_LIST):
        params = ParameterHandler()
        params.setParam('sUrl', (URL_MAIN + URL_GENRES_LIST[key]))
        oGui.addFolder(cGuiElement(key, SITE_IDENTIFIER, 'showEntries'), params)
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
        sPattern = '<link rel="next" href="([^"]+)'
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
        sThumbnail = cCFScrape.createUrl(sThumbnail, oRequest)
        oGuiElement.setThumbnail(sThumbnail)
        oGuiElement.setMediaType('episode')
        params.setParam('entryUrl', sUrl.strip())
        oGui.addFolder(oGuiElement, params, False, total)
    oGui.setView('seasons')
    oGui.setEndOfDirectory()


def showHosters():
    oParams = ParameterHandler()
    sUrl = oParams.getValue('entryUrl')
    sHtmlContent = cRequestHandler(sUrl).request()
    sPattern = '<iframe class="metaframe rptss" src="([^"]+)'  # url
    aResult = cParser().parse(sHtmlContent, sPattern)
    hosters = []
    if aResult[1]:
        for hUrl in aResult[1]:
            if 'rapidvideo' in hUrl:
                oRequest = cRequestHandler(hUrl, ignoreErrors=(True))
                oRequest.addHeaderEntry('Referer', sUrl)
                sHtmlContent = oRequest.request()
                aResult = cParser.parse(sHtmlContent, '<a[^>]*href="([^"]+)">.*?">([^<]+)')
                for sUrl, sQuality in aResult[1]:
                    hoster = {'link': sUrl, 'name': 'Rapidvideo ' + sQuality, 'quality': QUALITY_ENUM[sQuality]}
                    hosters.append(hoster)

            if 'wp-embed.php' in hUrl:
                oRequest = cRequestHandler(hUrl, ignoreErrors=(True))
                oRequest.addHeaderEntry('Referer', sUrl)
                sHtmlContent = oRequest.request()
                aResult = cParser.parse(sHtmlContent, '{file: "([^"]+).*?label: "([^"]+)')
                for sUrl, sQuality in aResult[1]:
                    hoster = {'link': sUrl, 'name': 'Gvideo ' + sQuality, 'quality': QUALITY_ENUM[sQuality]}
                    hosters.append(hoster)

            if 'play' in hUrl:
                oRequest = cRequestHandler(hUrl, ignoreErrors=(True))
                oRequest.addHeaderEntry('Referer', sUrl)
                sHtmlContent = oRequest.request()
                isMatch, aResult = cParser.parse(sHtmlContent, '(eval\s*\(function.*?)</script>')
                if isMatch:
                    for packed in aResult:
                        try:
                            sHtmlContent += jsunpacker.unpack(packed)
                        except:
                            pass

                    isMatch, aResult = cParser.parse(sHtmlContent, 'file":"([^"]+)","label":"([^"]+)"')
                    print isMatch
                    if not isMatch:
                        logger.info("not aResult")
                    for sUrl, sQuality in aResult:
                        hoster = {'link': sUrl, 'name': 'Gvideo ' + sQuality}
                        hosters.append(hoster)

        if hosters:
            hosters.append('getHosterUrl')
        return hosters


def getHosterUrl(sUrl=False):
    if not sUrl: sUrl = ParameterHandler().getValue('url')
    results = []
    result = {'streamUrl': sUrl}
    if 'rapidvideo' in sUrl:
        result['resolved'] = False
    else:
        result['resolved'] = True
    results.append(result)
    return results


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
        if not sGui: oGui.showInfo('streamon', 'Es wurde kein Eintrag gefunden')
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
