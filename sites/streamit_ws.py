# -*- coding: utf-8 -*-
from resources.lib.gui.gui import cGui
from resources.lib.gui.guiElement import cGuiElement
from resources.lib.handler.requestHandler import cRequestHandler
from resources.lib.parser import cParser
from resources.lib import logger
from resources.lib.handler.ParameterHandler import ParameterHandler
from resources.lib.cCFScrape import cCFScrape
import re

SITE_IDENTIFIER = 'streamit_ws'
SITE_NAME = 'StreamIt'
SITE_ICON = 'streamit.png'

URL_MAIN = 'http://streamit.ws'
URL_SERIELINKS = 'http://streamit.ws/lade_episode.php'
URL_Kinofilme = URL_MAIN + '/kino'
URL_Filme = URL_MAIN + '/film'
URL_HDFilme = URL_MAIN + '/hd-film'
URL_SERIES = URL_MAIN + '/serie'
URL_GENRES_FILM = URL_MAIN + '/genre-filme'
URL_GENRES_SERIE = URL_MAIN + '/genre-serien'
#URL_SEARCH = URL_MAIN + '/livesearch.php'


def load():
    logger.info("Load %s" % SITE_NAME)
    oGui = cGui()
    params = ParameterHandler()

    params.setParam('sUrl', URL_Kinofilme)
    oGui.addFolder(cGuiElement('Kino Filme', SITE_IDENTIFIER, 'showEntries'), params)
    params.setParam('sUrl', URL_Filme)
    oGui.addFolder(cGuiElement('Alle Filme', SITE_IDENTIFIER, 'showEntries'), params)
    params.setParam('sUrl', URL_HDFilme)
    oGui.addFolder(cGuiElement('HD Filme', SITE_IDENTIFIER, 'showEntries'), params)
    params.setParam('sUrl', URL_GENRES_FILM)
    oGui.addFolder(cGuiElement('Genre Filme', SITE_IDENTIFIER, 'showGenre'), params)
    params.setParam('sUrl', URL_SERIES)
    oGui.addFolder(cGuiElement('Neue Serien', SITE_IDENTIFIER, 'showEntries'), params)
    params.setParam('sUrl', URL_GENRES_SERIE)
    oGui.addFolder(cGuiElement('Genre Serien', SITE_IDENTIFIER, 'showGenre'), params)
#    oGui.addFolder(cGuiElement('Suche', SITE_IDENTIFIER, 'showSearch'))
    oGui.setEndOfDirectory()


def showGenre():
    oGui = cGui()
    params = ParameterHandler()
    entryUrl = params.getValue('sUrl')
    sHtmlContent = cRequestHandler(entryUrl).request()
    parser = cParser()
    isMatch, aResult = parser.parse(sHtmlContent, '<h3 class="title">Alle Kategorien</h3>.*?</ul><div class="clear">')

    if isMatch:
        sHtmlContent = aResult[0]

    pattern = '<a[^>]href="([^"]+)"[^>]*>([^<]+)</a>([^<]+)'  # url / title / Nr
    isMatch, aResult = parser.parse(sHtmlContent, pattern)

    for sUrl, sTitle, Nr in aResult:
        params.setParam('sUrl', URL_MAIN + '/' + sUrl)
        oGui.addFolder(cGuiElement(sTitle + Nr, SITE_IDENTIFIER, 'showEntries'), params)

    oGui.setEndOfDirectory()


def showEntries(entryUrl=False, sGui=False):
    oGui = sGui if sGui else cGui()
    params = ParameterHandler()

    if not entryUrl: entryUrl = params.getValue('sUrl')

    iPage = int(params.getValue('page'))
    if iPage > 0:
        entryUrl = entryUrl + ('&' if '?' in entryUrl else '?') + 'page=' + str(iPage)

    oRequestHandler = cRequestHandler(entryUrl, ignoreErrors = (sGui is not False))
    sHtmlContent = oRequestHandler.request()
    pattern = '<a[^>]*href="([^"]+)" title="([^"]+)"><img src="([^"]+)" alt="'
    parser = cParser()
    isMatch, aResult = parser.parse(sHtmlContent, pattern)

    if not isMatch: 
        if not sGui: oGui.showInfo('xStream','Es wurde kein Eintrag gefunden')
        return

    total = len(aResult)
    for sUrl, sName, sThumbnail in aResult:
        sFunction = "showHosters" if not "serie" in sUrl else "showSeasons"
        if sThumbnail.startswith('/'):
           sThumbnail = URL_MAIN + sThumbnail
        sThumbnail = cCFScrape().createUrl(sThumbnail, oRequestHandler)
        oGuiElement = cGuiElement(sName, SITE_IDENTIFIER, sFunction)
        oGuiElement.setThumbnail(sThumbnail)
        oGuiElement.setMediaType('serie' if 'serie' in sUrl else 'movie')
        params.setParam('entryUrl', URL_MAIN + sUrl)
        params.setParam('sName', sName)
        params.setParam('Thumbnail', sThumbnail)
        oGui.addFolder(oGuiElement, params, bIsFolder="serie" in sUrl, iTotal=total)

    if not sGui:
        isMatch, strPage = parser.parseSingleResult(sHtmlContent, '<a[^>]*class="next page-numbers"[^>]*href="[^>]*page=([^"]+)">Next &raquo;')
        if isMatch:
            params.setParam('page', int(strPage))
            oGui.addNextPage(SITE_IDENTIFIER, 'showEntries', params)

        oGui.setView('tvshows' if 'serie' in entryUrl else 'movies')
        oGui.setEndOfDirectory()

def showSeasons():
    oGui = cGui()
    oParams = ParameterHandler()

    sUrl = oParams.getValue('entryUrl')
    sThumbnail = oParams.getValue("Thumbnail")
    sName = oParams.getValue('sName')
    sHtmlContent = cRequestHandler(sUrl).request()

    sPattern = '<select[^>]*class="staffelauswahl"[^>]*>(.*?)</select>' # container
    parser = cParser()
    isMatch, strContainer = parser.parseSingleResult(sHtmlContent, sPattern)

    if isMatch: 
        sPattern = '<option[^>]*value="(.*?)"[^>]*>(.*?)</option>' # container
        isMatch, aResult = parser.parse(strContainer, sPattern)

    if not isMatch: 
        oGui.showInfo('xStream','Es wurde kein Eintrag gefunden')
        return

    total = len(aResult)
    for iSeason, sTitle in aResult:
        oGuiElement = cGuiElement("Staffel " + str(iSeason),SITE_IDENTIFIER, 'showEpisodes')
        oGuiElement.setTVShowTitle(sName)
        oGuiElement.setSeason(iSeason)
        oGuiElement.setMediaType('season')
        oGuiElement.setThumbnail(sThumbnail)
        oGui.addFolder(oGuiElement, oParams, iTotal = total)

    oGui.setView('seasons')
    oGui.setEndOfDirectory()

def showEpisodes():
    oGui = cGui()
    oParams = ParameterHandler()

    sUrl = oParams.getValue('entryUrl')
    sThumbnail = oParams.getValue("Thumbnail")
    sSeason = oParams.getValue('season')
    sShowName = oParams.getValue('TVShowTitle')
    sHtmlContent = cRequestHandler(sUrl).request()

    parser = cParser()
    sPattern = '<a[^>]*href="#(s%se(\d+))"[^>]*>(.*?)</a>' % sSeason
    isMatch, aResult = parser.parse(sHtmlContent, sPattern)

    if not isMatch: 
        oGui.showInfo('xStream','Es wurde kein Eintrag gefunden')
        return

    result, imdb = parser.parseSingleResult(sHtmlContent,'IMDB\s?=\s?\'(\d+)')
    
    total = len(aResult)
    for sEpisodeUrl, sEpisodeNr, sEpisodeTitle in aResult:
        res = re.search('%s (.*)' % sEpisodeNr, sEpisodeTitle)
        if res:
            sEpisodeTitle = '%s - %s' % (sEpisodeNr, res.group(1))
        oGuiElement = cGuiElement(sEpisodeTitle, SITE_IDENTIFIER, "showHosters")
        oGuiElement.setThumbnail(sThumbnail)
        oGuiElement.setTVShowTitle(sShowName)
        oGuiElement.setEpisode(sEpisodeNr)
        oGuiElement.setSeason(sSeason)
        oGuiElement.setMediaType('episode')
        oParams.setParam('entryUrl', sUrl)
        oParams.setParam('val', sEpisodeUrl)
        oParams.setParam('IMDB', imdb)
        oGui.addFolder(oGuiElement, oParams, bIsFolder=False, iTotal=total)

    oGui.setView('episodes')
    oGui.setEndOfDirectory()

def showHosters():
    oParams = ParameterHandler()
    sUrl = oParams.getValue('entryUrl')
    oRequestHandler = cRequestHandler(sUrl)

    if oParams.getValue('val'):
        oRequestHandler = cRequestHandler(URL_SERIELINKS)
        oRequestHandler.addParameters('val', oParams.getValue('val'))
        oRequestHandler.addParameters('IMDB', oParams.getValue('IMDB'))
        oRequestHandler.setRequestType(1)

    sHtmlContent = oRequestHandler.request()
    hosters = []
    parser = cParser()
    isMatch, sContainer = parser.parseSingleResult(sHtmlContent, '<select[^>]*class="sel_quali"[^>]*>(.*?)</select>')  # filter main content if needed

    if not isMatch:
        return hosters

    isMatch, aResult = parser.parse(sContainer, '<option[^>]*\((?:[^>]*quality/(\d+)\.png)?[^>]*id="(\w+)"[^>]*>(.*?)</option>')  # filter main content if needed

    if not isMatch:
        return hosters

    for sQulityNr, sID, sQulityTitle in aResult:
        sPattern = '<div[^>]*class="mirrors\w+"[^>]*id="%s">(.*?)</div></div>' % sID
        isMatchMirrors, sMirrorContainer = parser.parse(sHtmlContent, sPattern)

        if not isMatchMirrors:
            continue

        isMatchUrls, aResultMirrors = parser.parse(sMirrorContainer[0], '<a[^>]*href="([^"]+)"[^>]*>.*?name="save"[^>]*value="(.*?)"[^>]*/>')

        if not isMatchUrls:
            continue

        for sUrl, sName in aResultMirrors:
            hoster = {}
            hoster['name'] = sName.strip()
            hoster['displayedName'] = '[%s] %s' % (sQulityTitle, sName.strip())
            hoster['quality'] = sQulityNr if sQulityNr else '0'
            hoster['link'] = URL_MAIN + sUrl
            hosters.append(hoster)

    if hosters:
        hosters.append('getHosterUrl')
    return hosters


def getHosterUrl(sUrl = False):
    if not sUrl: sUrl = ParameterHandler().getValue('url')

    sHtmlContent = cRequestHandler(sUrl).request()
    isMatch, redirectUrl = cParser().parseSingleResult(sHtmlContent, 'none"><a[^>]*href="([^"]+)')

    results = []
    if isMatch:
        result = {}
        result['streamUrl'] = redirectUrl
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
    showSearchEntries(URL_SEARCH, oGui, sSearchText)


def showSearchEntries(entryUrl = False, sGui = False, sSearchText = None):
    oGui = sGui if sGui else cGui()
    params = ParameterHandler()
    if not entryUrl: entryUrl = params.getValue('sUrl')
    oRequest = cRequestHandler(URL_SEARCH)
    if sSearchText:
       oRequest.addHeaderEntry('X-Requested-With', 'XMLHttpRequest')
       oRequest.addParameters('val', sSearchText.strip)
       oRequest.setRequestType(1)
    sHtmlContent = oRequest.request()
    pattern = '<a[^>]* href="([^"]+)"[^>]*>([^<]+)'
    isMatch, aResult = cParser.parse(sHtmlContent, pattern)

    if not isMatch:
        return

    total = len (aResult)
    for sUrl, sName in aResult:
        oGuiElement = cGuiElement(sName, SITE_IDENTIFIER, 'showHosters')
        params.setParam('entryUrl', URL_MAIN + sUrl)
        oGui.addFolder(oGuiElement, params, False, total)
