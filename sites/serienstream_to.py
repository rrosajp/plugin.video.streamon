# -*- coding: utf-8 -*-
import re
from resources.lib import logger
from resources.lib.cCFScrape import cCFScrape
from resources.lib.gui.gui import cGui
from resources.lib.gui.guiElement import cGuiElement
from resources.lib.handler.ParameterHandler import ParameterHandler
from resources.lib.handler.requestHandler import cRequestHandler
from resources.lib.parser import cParser
from resources.lib.config import cConfig

SITE_IDENTIFIER = 'serienstream_to'
SITE_NAME = 'SerienStream'
SITE_ICON = 'serienstream.png'
SITE_SETTINGS = '<setting id="serienstream.user" type="text" label="30083" default="serienstream@trash-mail.com" /><setting id="serienstream.pass" type="text" option="hidden" label="30084" default="test1234" />'

URL_MAIN = 'http://s.to'
URL_SERIES = URL_MAIN + '/serien'
URL_LOGIN = URL_MAIN + "/login"


def load():
    logger.info("Load %s" % SITE_NAME)
    oGui = cGui()
    params = ParameterHandler()
    params.setParam('sUrl', URL_SERIES)
    oGui.addFolder(cGuiElement('Alle Serien', SITE_IDENTIFIER, 'showAllSeries'), params)
    params.setParam('sUrl', URL_MAIN)
    params.setParam('sCont', 'catalogNav')
    oGui.addFolder(cGuiElement('A-Z', SITE_IDENTIFIER, 'showLinkList'), params)
    params.setParam('sUrl', URL_MAIN)
    params.setParam('sCont', 'homeContentGenresList')
    oGui.addFolder(cGuiElement('Genre', SITE_IDENTIFIER, 'showLinkList'), params)
    oGui.addFolder(cGuiElement('Suche', SITE_IDENTIFIER, 'showSearch'))
    oGui.setEndOfDirectory()

def showLinkList():
    oGui = cGui()
    params = ParameterHandler()
    sUrl = params.getValue('sUrl')
    sCont = params.getValue('sCont')

    sHtmlContent = cRequestHandler(sUrl).request()
    parser = cParser()
    isMatch, sContainer = parser.parseSingleResult(sHtmlContent,'<ul[^>]*class="%s"[^>]*>(.*?)<\/ul>' % sCont)

    if not isMatch:
        oGui.showInfo('streamon','Es wurde kein Eintrag gefunden')
        return

    isMatch, aResult = parser.parse(sContainer, '<li>\s*<a[^>]*href="([^"]*)"[^>]*>(.*?)<\/a>\s*<\/li>')

    if not isMatch: 
        oGui.showInfo('streamon','Es wurde kein Eintrag gefunden')
        return

    for sEntryUrl, sName in aResult:
        sEntryUrl = sEntryUrl if sEntryUrl.startswith('http') else URL_MAIN + sEntryUrl
        params.setParam('sUrl', sEntryUrl)
        oGui.addFolder(cGuiElement(sName.strip(), SITE_IDENTIFIER, 'showEntries'), params)  
    oGui.setEndOfDirectory()

def showAllSeries(entryUrl = False, sGui = False, sSearchText = False):
    oGui = sGui if sGui else cGui()
    params = ParameterHandler()

    if not entryUrl: entryUrl = params.getValue('sUrl')

    sHtmlContent = cRequestHandler(entryUrl, ignoreErrors = (sGui is not False)).request()
    pattern = '<a[^>]*href="(\/serie\/[^"]*)"[^>]*>(.*?)</a>'
    parser = cParser()
    isMatch, aResult = parser.parse(sHtmlContent, pattern)

    if not isMatch: 
        if not sGui: oGui.showInfo('streamon','Es wurde kein Eintrag gefunden')
        return

    total = len(aResult)
    for sEntryUrl, sName in aResult:
        if sSearchText and not re.search(sSearchText, sName, re.IGNORECASE):
            continue

        oGuiElement = cGuiElement(sName, SITE_IDENTIFIER, 'showSeasons')
        oGuiElement.setMediaType('tvshow')
        params.setParam('sUrl', URL_MAIN + sEntryUrl)
        oGui.addFolder(oGuiElement, params, True, total)

    if not sGui:
        oGui.setView('tvshows')
        oGui.setEndOfDirectory()

def showEntries(entryUrl = False, sGui = False):
    oGui = sGui if sGui else cGui()
    params = ParameterHandler()

    if not entryUrl: entryUrl = params.getValue('sUrl')

    oRequest = cRequestHandler(entryUrl, ignoreErrors = (sGui is not False))
    sHtmlContent = oRequest.request()

    pattern = '<div[^>]*class="col-md-[^"]*"[^>]*>.*?' # start element
    pattern += '<a[^>]*href="([^"]*)"[^>]*>.*?' # url
    pattern += '<img[^>]*src="([^"]*)"[^>]*>.*?' # thumbnail
    pattern += '<h3>(.*?)<span[^>]*class="paragraph-end">.*?' # title
    pattern += '<\/div>' # end element
    parser = cParser()
    isMatch, aResult = parser.parse(sHtmlContent, pattern)

    if not isMatch: 
        if not sGui: oGui.showInfo('streamon','Es wurde kein Eintrag gefunden')
        return

    total = len(aResult)
    for sEntryUrl, sThumbnail, sName in aResult:
        sThumbnail = cCFScrape().createUrl((URL_MAIN + sThumbnail), oRequest)
        oGuiElement = cGuiElement(sName, SITE_IDENTIFIER, 'showSeasons')
        oGuiElement.setThumbnail(sThumbnail)
        oGuiElement.setMediaType('tvshow')
        oGuiElement.setTVShowTitle(sName)
        params.setParam('sUrl', URL_MAIN + sEntryUrl)
        params.setParam('sThumbnail', sThumbnail)
        oGui.addFolder(oGuiElement, params, True, total)

    if not sGui:
        oGui.setView('tvshows')
        oGui.setEndOfDirectory()

def showSeasons():
    oGui = cGui()
    params = ParameterHandler()
    sUrl = params.getValue('sUrl')
    sThumbnail = params.getValue('sThumbnail')
    sTVShowTitle = params.getValue('TVShowTitle')

    oRequest = cRequestHandler(sUrl)
    sHtmlContent = oRequest.request()
    pattern = '<div[^>]*class="hosterSiteDirectNav"[^>]*>.*?<ul>(.*?)<\/ul>'
    parser = cParser()
    isMatch, sMainContent = parser.parseSingleResult(sHtmlContent, pattern)

    if not isMatch: 
        oGui.showInfo('streamon','Es wurde kein Eintrag gefunden')
        return

    pattern = '<a[^>]*href="([^"]*)"[^>]*title="([^"]*)"[^>]*>(.*?)<\/a>.*?'
    isMatch, aResult = parser.parse(sMainContent, pattern)

    if not isMatch: 
        oGui.showInfo('streamon','Es wurde kein Eintrag gefunden')
        return

    isMatchDesc, sDesc = parser.parseSingleResult(sHtmlContent, '<p[^>]*data-full-description="(.*?)"[^>]*>')

    if not sThumbnail:
        isMatchThumb, sThumbnail = parser.parseSingleResult(sHtmlContent, '<div[^>]*class="seriesCoverBox"[^>]*>.*?<img[^>]*src="([^"]*)"[^>]*>')

        if isMatchThumb:
            sThumbnail = cCFScrape().createUrl(sThumbnail, oRequest)
            params.setParam('sThumbnail', sThumbnail)

    total = len(aResult)
    for sEntryUrl, sName, sText in aResult:
        isMovie = sEntryUrl.endswith('filme')
        oGuiElement = cGuiElement(sName, SITE_IDENTIFIER, ('showEpisodes'))
        oGuiElement.setMediaType('season' if not isMovie else 'movie')
        if sThumbnail:
            oGuiElement.setThumbnail(sThumbnail)
        oGuiElement.setDescription(sDesc)
        if not isMovie:
            oGuiElement.setTVShowTitle(sTVShowTitle)
            oGuiElement.setSeason(sText)
            params.setParam('sSeason', sText)
        params.setParam('sUrl', URL_MAIN + sEntryUrl)
        oGui.addFolder(oGuiElement, params, True, total)

    oGui.setView('seasons')
    oGui.setEndOfDirectory()




def showEpisodes():
    oGui = cGui()
    params = ParameterHandler()

    sUrl = params.getValue('sUrl')
    sTVShowTitle = params.getValue('TVShowTitle')
    sThumbnail = params.getValue('sThumbnail')
    sSeason = params.getValue('sSeason')

    if not sSeason:
        sSeason = "0"

    isMovieList = sUrl.endswith('filme')
    sHtmlContent = cRequestHandler(sUrl).request()
    pattern = '<table[^>]*class="seasonEpisodesList"[^>]*>(.*?)<\/table>'
    parser = cParser()
    isMatch, sMainContent = parser.parseSingleResult(sHtmlContent, pattern)

    if not isMatch: 
        oGui.showInfo('streamon','Es wurde kein Eintrag gefunden')
        return

    pattern = '<tr[^>]*data-episode-season-id="(\d+)">.*?<td[^>]*class="seasonEpisodeTitle"[^>]*>.*?<a[^>]*href="([^"]*)"[^>]*>.*?(?:<strong>(.*?)</strong>.*?)?(?:<span>(.*?)</span>.*?)?<'
    isMatch, aResult = parser.parse(sMainContent, pattern)

    if not isMatch: 
        oGui.showInfo('streamon','Es wurde kein Eintrag gefunden')
        return

    isMatchDesc, sDesc = parser.parseSingleResult(sHtmlContent, '<p[^>]*data-full-description="(.*?)"[^>]*>')

    total = len(aResult)
    for sID , sEntryUrl, sNameGer, sNameEng in aResult:
        sName = "%d - " % int(sID)
        sName += sNameGer if sNameGer else sNameEng
        oGuiElement = cGuiElement(sName, SITE_IDENTIFIER, ('showHosters'))
        oGuiElement.setMediaType('episode' if not isMovieList else 'movie')
        if sThumbnail:
            oGuiElement.setThumbnail(sThumbnail)
        oGuiElement.setDescription(sDesc)
        if not isMovieList:
            oGuiElement.setSeason(sSeason)
            oGuiElement.setEpisode(int(sID))
            oGuiElement.setTVShowTitle(sTVShowTitle)
        params.setParam('sUrl', URL_MAIN + sEntryUrl)
        oGui.addFolder(oGuiElement, params, False, total)

    oGui.setView('episodes' if not isMovieList else 'movies')
    oGui.setEndOfDirectory()

def showHosters():
    oParams = ParameterHandler()
    sUrl = oParams.getValue('sUrl')
    sHtmlContent = cRequestHandler(sUrl).request()

    hosters = []

    pattern = '<img[^>]*data-lang-key="(\d)"[^>]*title="([^"]*)"[^>]*>'
    parser = cParser()
    isMatch, aResult = parser.parse(sHtmlContent, pattern)

    if not isMatch:
        return hosters

    totalLang = len(aResult)
    for sLangId , sLangName in aResult:
        pattern = '<li[^>]*data-lang-key="%s"[^>]*>.*?<a[^>]*href="([^"]*)"[^>]*>.*?<h4>([^<]+)<' % sLangId
        isMatchHoster, aResultHoster = parser.parse(sHtmlContent, pattern)

        if not isMatchHoster:
            continue

        for sHosterUrl , sHosterName in aResultHoster:
            hoster = {}
            hoster['name'] = sHosterName.strip()
            if totalLang > 1:
                hoster['displayedName'] = '%s (%s)' % (sHosterName.strip(), sLangName)
            hoster['link'] = sHosterUrl
            hosters.append(hoster)

    if hosters:
        hosters.append('getHosterUrl')

    return hosters

def getHosterUrl(sUrl = False):
    username = cConfig().getSetting('serienstream.user')
    password = cConfig().getSetting('serienstream.pass')

    oRequestHandler = cRequestHandler(URL_LOGIN, caching=False)
    oRequestHandler.addHeaderEntry('X-Requested-With', 'XMLHttpRequest')
    oRequestHandler.addResponse('email', username)
    oRequestHandler.addResponse('password', password)
    oRequestHandler.request()

    if not sUrl.startswith('http'):
        refUrl = ParameterHandler().getValue('sUrl')
        oRequest = cRequestHandler(URL_MAIN + sUrl, caching=False)
        oRequest.addHeaderEntry("Referer", refUrl)
        oRequest.addHeaderEntry('X-Requested-With', 'XMLHttpRequest')
        oRequest.request()
        sUrl = oRequest.getRealUrl()

    results = []
    result = {}
    result['streamUrl'] = sUrl
    result['resolved'] = False
    results.append(result)
    return results

def showSearch():
    oGui = cGui()
    sSearchText = oGui.showKeyBoard()
    if not sSearchText: return
    _search(False, sSearchText)
    oGui.setEndOfDirectory()

def _search(oGui, sSearchText):
    if not sSearchText: return
    showAllSeries(URL_SERIES, oGui, sSearchText)
