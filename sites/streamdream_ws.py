# -*- coding: utf-8 -*-
from resources.lib.gui.gui import cGui
from resources.lib.gui.guiElement import cGuiElement
from resources.lib.handler.requestHandler import cRequestHandler
from resources.lib.parser import cParser
from resources.lib import logger
from resources.lib.handler.ParameterHandler import ParameterHandler
from urlparse import urlparse

SITE_IDENTIFIER = 'streamdream_ws'
SITE_NAME = 'StreamDream'
SITE_ICON = 'streamdream.png'

URL_MAIN = 'http://streamdream.ws/'

EPISODE_URL = URL_MAIN + 'episodeholen.php'
HOSTER_URL = URL_MAIN + 'episodeholen2.php'
SEARCH_URL = URL_MAIN + 'searchy.php?ser=%s'

QUALITY_ENUM = {'SD': 1, 'HD': 4}


def load():
    logger.info("Load %s" % SITE_NAME)
    oGui = cGui()
    params = ParameterHandler()
    params.setParam('valueType', 'film')
    oGui.addFolder(cGuiElement('Filme', SITE_IDENTIFIER, 'showContentMenu'), params)
    params.setParam('valueType', 'serien')
    oGui.addFolder(cGuiElement('Serien', SITE_IDENTIFIER, 'showContentMenu'), params)
    oGui.addFolder(cGuiElement('Suche', SITE_IDENTIFIER, 'showSearch'))
    oGui.setEndOfDirectory()


def showContentMenu():
    oGui = cGui()
    params = ParameterHandler()
    valueType = params.getValue('valueType')

    sHtmlContent = cRequestHandler(URL_MAIN).request()
    pattern = 'href="(?:\.\.\/)*([neu|beliebt]+%s[^"]*)"[^>]*>([^<]+)<\/a><\/li>' % valueType
    isMatch, aResult = cParser.parse(sHtmlContent, pattern)

    for sID, sName in aResult:
        params.setParam('sUrl', URL_MAIN + sID)
        oGui.addFolder(cGuiElement(sName, SITE_IDENTIFIER, 'showEntries'), params)

    params.setParam('sUrl', URL_MAIN)
    oGui.addFolder(cGuiElement('Genre', SITE_IDENTIFIER, 'showGenre'), params)
    oGui.setEndOfDirectory()


def showGenre():
    oGui = cGui()
    params = ParameterHandler()
    entryUrl = params.getValue('sUrl')
    valueType = params.getValue('valueType')

    sHtmlContent = cRequestHandler(entryUrl).request()
    pattern = 'href="(?:\.\.\/)*(%s[^"]+)">([^<]+)<\/a><\/li>' % valueType
    isMatch, aResult = cParser.parse(sHtmlContent, pattern)

    if not isMatch:
        return

    for sID, sName in aResult:
        params.setParam('sUrl', entryUrl + sID)
        oGui.addFolder(cGuiElement(sName, SITE_IDENTIFIER, 'showEntries'), params)
    oGui.setEndOfDirectory()


def showEntries(entryUrl=False, sGui=False):
    oGui = sGui if sGui else cGui()
    params = ParameterHandler()
    if not entryUrl: entryUrl = params.getValue('sUrl')
    sBaseUrl = params.getValue('sBaseUrl')
    if not sBaseUrl:
        params.setParam('sBaseUrl', entryUrl)
        sBaseUrl = entryUrl

    sHtmlContent = cRequestHandler(entryUrl, ignoreErrors=(sGui is not False)).request()
    pattern = '<a[^>]*class="linkto"[^>]*href="(?:\.\.\/)*([^"]+)"[^>]*>.*?'  # link
    pattern += '<img[^>]*src="([^"]*)"[^>]*>(.*?)</div>'  # thumbnail / name
    isMatch, aResult = cParser.parse(sHtmlContent, pattern)

    if not isMatch:  # Fallback for Search-Results
        pattern = "<a[^>]*href='(?:\.\.\/)*([^']+)'[^>]*()>(.*?)\(\d+\s*-\s*\w+\)\s*</"  # link, filler, name
        isMatch, aResult = cParser.parse(sHtmlContent, pattern)

    if not isMatch:
        if not sGui: oGui.showInfo('steamon', 'Es wurde kein Eintrag gefunden')
        return

    total = len(aResult)
    for sUrl, sThumbnail, sName in aResult:
        isTvshow = True if 'serie' in sUrl else False
        oGuiElement = cGuiElement(sName, SITE_IDENTIFIER, 'showHosters')
        oGuiElement.setThumbnail(URL_MAIN + sThumbnail)
        oGuiElement.setMediaType("tvshow" if isTvshow else "movie")
        params.setParam('entryUrl', URL_MAIN + sUrl)
        params.setParam('Name', sName)
        params.setParam('isTvshow', isTvshow)
        params.setParam('sThumbnail', sThumbnail)
        oGui.addFolder(oGuiElement, params, isTvshow, total)

    if not sGui:
        pattern = '<a*[^>]class="righter"*[^>]href="(?:\.\.\/)*([^"]+)"'
        isMatchNextPage, sNextUrl = cParser.parseSingleResult(sHtmlContent, pattern)
        if isMatchNextPage:
            params.setParam('sUrl', sBaseUrl + sNextUrl)
            oGui.addNextPage(SITE_IDENTIFIER, 'showEntries', params)

        oGui.setView('tvshows' if 'serie' in entryUrl else 'movies')
        oGui.setEndOfDirectory()


def showHosters():
    params = ParameterHandler()
    entryUrl = params.getValue('entryUrl')
    isTvshowEntry = params.getValue('isTvshow')

    if isTvshowEntry == 'True':
        sHtmlContent = cRequestHandler(entryUrl).request()

        pattern = '<div[^>]*season="(\d+)"[^>]*>.*?'  # sSeasonID
        pattern += 'imdbid\s*:\s*"(\d+)".*?'  # imdbid
        pattern += 'language\s*:\s*"([^"]+)"'  # language
        isMatch, aResult = cParser.parse(sHtmlContent, pattern)

        if isMatch:
            isMatchDesc, aResultDesc = cParser.parse(sHtmlContent, '<p[^>]*style=[^>]*>(.*?)</p>')
            showSeason(aResult, params, '' if not isMatchDesc else aResultDesc[0])
    else:
        return getHosters(entryUrl)


def showSeason(aResult, params, sDesc):
    oGui = cGui()

    sTVShowTitle = params.getValue('Name')
    sThumbnail = params.getValue('sThumbnail')

    total = len(aResult)
    for sSeason, imdbid, slanguage in aResult:
        oGuiElement = cGuiElement('Staffel ' + sSeason, SITE_IDENTIFIER, 'showEpisodes')
        oGuiElement.setMediaType('season')
        oGuiElement.setTVShowTitle(sTVShowTitle)
        oGuiElement.setSeason(sSeason)
        oGuiElement.setDescription(sDesc)
        if sThumbnail:
            oGuiElement.setThumbnail(URL_MAIN + sThumbnail)
        params.setParam('Season', sSeason)
        params.setParam('imdbid', imdbid)
        params.setParam('language', slanguage)
        oGui.addFolder(oGuiElement, params, True, total)

    oGui.setView('seasons')
    oGui.setEndOfDirectory()


def showEpisodes():
    oGui = cGui()
    params = ParameterHandler()
    entryUrl = params.getValue('entryUrl')
    sThumbnail = params.getValue('sThumbnail')
    imdbid = params.getValue('imdbid')
    slanguage = params.getValue('language')
    sSeason = params.getValue('Season')
    sTVShowTitle = params.getValue('Name')

    oRequest = cRequestHandler(EPISODE_URL)
    oRequest.addHeaderEntry("X-Requested-With", "XMLHttpRequest")
    oRequest.setRequestType(1)
    oRequest.addParameters('imdbid', imdbid)
    oRequest.addParameters('language', slanguage)
    oRequest.addParameters('season', sSeason)

    sHtmlContent = oRequest.request()
    pattern = '>#([^<]+)</p>[^>]*[^>]*<script>.*?imdbid:[^>]"([^"]+).*?language:[^>]"([^"]+).*?season:[^>]"([^"]+)'
    isMatch, aResult = cParser.parse(sHtmlContent, pattern)

    if not isMatch:
        oGui.showInfo('steamon', 'Es wurde kein Eintrag gefunden')
        return

    sHtmlContent = cRequestHandler(entryUrl).request()
    isMatchDesc, aResultDesc = cParser.parse(sHtmlContent, '<p[^>]*style=[^>]*>(.*?)</p>')
    sDesc = ''

    if isMatchDesc:
        sDesc = aResultDesc[0]

    total = len(aResult)
    for sEpisode, imdbid, slanguage, sSeason in aResult:
        oGuiElement = cGuiElement('Folge ' + sEpisode, SITE_IDENTIFIER, 'getHosters')
        oGuiElement.setMediaType('season')
        oGuiElement.setSeason(sSeason)
        oGuiElement.setEpisode(sEpisode)
        oGuiElement.setMediaType('episode')
        oGuiElement.setTVShowTitle(sTVShowTitle)
        oGuiElement.setDescription(sDesc)
        if sThumbnail:
            oGuiElement.setThumbnail(URL_MAIN + sThumbnail)
        params.setParam('Episode', sEpisode)
        params.setParam('Season', sSeason)
        params.setParam('imdbid', imdbid)
        params.setParam('language', slanguage)
        oGui.addFolder(oGuiElement, params, False, total)

    oGui.setView('episodes')
    oGui.setEndOfDirectory()


def getHosters(sUrl=False):
    if not sUrl:
        params = ParameterHandler()
        oRequest = cRequestHandler(HOSTER_URL)
        oRequest.addHeaderEntry("X-Requested-With", "XMLHttpRequest")
        oRequest.setRequestType(1)
        oRequest.addParameters('imdbid', params.getValue('imdbid'))
        oRequest.addParameters('language', params.getValue('language'))
        oRequest.addParameters('season', params.getValue('Season'))
        oRequest.addParameters('episode', params.getValue('Episode'))
        sHtmlContent = oRequest.request()
    else:
        sHtmlContent = cRequestHandler(sUrl).request()

    if not sHtmlContent:
        return []

    sPattern = '<a[^>]*href="([^"]+)"[^>]*><img[^>]*class="([s|h]d+)linkbutton"'
    isMatch, aResult = cParser.parse(sHtmlContent, sPattern)

    hosters = []
    if not isMatch:
        return hosters

    for sUrl, sQuali in aResult:
        hoster = {}
        hoster['link'] = sUrl
        hoster['name'] = str(urlparse(sUrl).netloc).title()
        hoster['displayedName'] = '%s [%s]' % (hoster['name'], sQuali.upper())
        hoster['quality'] = QUALITY_ENUM[sQuali.upper()]
        hosters.append(hoster)

    if hosters:
        hosters.append('getHosterUrl')
    return hosters


def getHosterUrl(sUrl=False):
    if not sUrl: sUrl = ParameterHandler().getValue('url')
    return [{'streamUrl': sUrl, 'resolved': False}]


def showSearch():
    oGui = cGui()
    sSearchText = oGui.showKeyBoard()
    if not sSearchText: return
    _search(False, sSearchText)
    oGui.setEndOfDirectory()


def _search(oGui, sSearchText):
    if not sSearchText: return
    showEntries(SEARCH_URL % sSearchText.strip(), oGui)
