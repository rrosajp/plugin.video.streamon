# -*- coding: utf-8 -*-
from resources.lib import logger
from resources.lib.gui.gui import cGui
from resources.lib.gui.guiElement import cGuiElement
from resources.lib.handler.ParameterHandler import ParameterHandler
from resources.lib.handler.requestHandler import cRequestHandler
from resources.lib.parser import cParser
import re

SITE_IDENTIFIER = 'cinematrix_to'
SITE_NAME = 'Cinematrix'
SITE_ICON = 'cinematrix_to.png'

URL_MAIN = 'http://www.cinematrix.to/'
URL_Filme = URL_MAIN + 'de/filme.html'
URL_Serien = URL_MAIN + 'de/serien.html'
URL_SEARCH = URL_MAIN + 'de/suche.html?q=%s'
URL_Episodes = URL_MAIN + 'ajax/getEpisodes.php'
URL_HosterFilme = URL_MAIN + 'ajax/getHosterFilme.php'
URL_MovieStream = URL_MAIN + 'ajax/getMovieStream.php'
URL_HosterSerien = URL_MAIN + 'ajax/getHosterSerien.php'
URL_SerienStream = URL_MAIN + 'ajax/getSeriesStream.php'


def load():
    logger.info("Load %s" % SITE_NAME)
    oGui = cGui()
    params = ParameterHandler()
    params.setParam('baseURL', URL_Filme)
    oGui.addFolder(cGuiElement('Filme', SITE_IDENTIFIER, 'showContentMenu'), params)
    params.setParam('baseURL', URL_Serien)
    oGui.addFolder(cGuiElement('Serien', SITE_IDENTIFIER, 'showContentMenu'), params)
    oGui.addFolder(cGuiElement('Suche', SITE_IDENTIFIER, 'showSearch'))
    oGui.setEndOfDirectory()


def showContentMenu():
    oGui = cGui()
    params = ParameterHandler()
    baseURL = params.getValue('baseURL')
    params.setParam('sUrl', baseURL + '?abc=Alle&sort=&genre=&country=&year=')
    oGui.addFolder(cGuiElement('Alle', SITE_IDENTIFIER, 'showEntries'), params)
    params.setParam('sUrl', baseURL + '?abc=Alle&sort=A-Z')
    oGui.addFolder(cGuiElement('A-Z', SITE_IDENTIFIER, 'showEntries'), params)
    params.setParam('sUrl', baseURL + '?abc=Alle&sort=IMDB')
    oGui.addFolder(cGuiElement('IMDB wertung', SITE_IDENTIFIER, 'showEntries'), params)
    params.setParam('sUrl', baseURL + '?abc=Alle&sort=Aufrufe')
    oGui.addFolder(cGuiElement('Aufrufe', SITE_IDENTIFIER, 'showEntries'), params)
    params.setParam('sUrl', URL_MAIN)
    params.setParam('valueType', 'genre')
    oGui.addFolder(cGuiElement('Genre', SITE_IDENTIFIER, 'showValue'), params)
    params.setParam('valueType', 'year')
    oGui.addFolder(cGuiElement('Jahr', SITE_IDENTIFIER, 'showValue'), params)
    params.setParam('valueType', 'country')
    oGui.addFolder(cGuiElement('Land', SITE_IDENTIFIER, 'showValue'), params)
    oGui.setEndOfDirectory()


def showValue():
    oGui = cGui()
    params = ParameterHandler()
    entryUrl = params.getValue('baseURL')
    valueType = params.getValue('valueType')
    sHtmlContent = cRequestHandler(entryUrl).request()
    pattern = 'name="%s.*?</option>.*?</option></select>' % valueType
    isMatch, sHtmlContainer = cParser.parseSingleResult(sHtmlContent, pattern)

    if not isMatch:
        oGui.showInfo('streamon', 'Es wurde kein Eintrag gefunden')
        return

    pattern = '<option[^>]value="([^"]+)">.*?([^<]+)'
    isMatch, aResult = cParser.parse(sHtmlContainer, pattern)

    if not isMatch:
        oGui.showInfo('streamon', 'Es wurde kein Eintrag gefunden')
        return

    for sName, sUrl in aResult:
        params.setParam('sUrl', entryUrl + '?' + valueType + '=' + sUrl)
        oGui.addFolder(cGuiElement(sName, SITE_IDENTIFIER, 'showEntries'), params)
    oGui.setEndOfDirectory()


def showEntries(entryUrl=False, sGui=False):
    oGui = sGui if sGui else cGui()
    params = ParameterHandler()
    if not entryUrl: entryUrl = params.getValue('sUrl')
    oRequest = cRequestHandler(entryUrl, ignoreErrors=(sGui is not False))
    sHtmlContent = oRequest.request()
    pattern = 'class="dataHover.*?footerContainer'
    isMatch, sContainer = cParser().parseSingleResult(sHtmlContent, pattern)

    if not isMatch:
        if not sGui:
            oGui.showInfo('streamon', 'Es wurde kein Eintrag gefunden')
        return

    pattern = '<a[^>]href="([^"]+)"><img[^>]src="([^"]+)"><div><span>([^<]+)'
    isMatch, aResult = cParser().parse(sContainer, pattern)

    if not isMatch:
        if not sGui:
            oGui.showInfo('streamon', 'Es wurde kein Eintrag gefunden')
        return

    total = len(aResult)
    for sUrl, sThumbnail, sName in aResult:
        hosterid = re.compile('\D/([\d]+)/').findall(sUrl)[0]
        isTvshow = True if "serie" in sUrl else False
        oGuiElement = cGuiElement(sName, SITE_IDENTIFIER, 'showSeasons' if isTvshow else 'showHosters')
        oGuiElement.setMediaType('tvshow' if isTvshow else 'movie')
        oGuiElement.setThumbnail(URL_MAIN + sThumbnail)
        params.setParam('entryUrl', URL_MAIN + sUrl)
        params.setParam('sName', sName)
        params.setParam('sThumbnail', URL_MAIN + sThumbnail)
        params.setParam('hosterid', hosterid)
        params.setParam('isTvshow', isTvshow)
        oGui.addFolder(oGuiElement, params, isTvshow, total)
    if not sGui:
        pattern = '<a[^>]href="([^"]+)">></a>'
        isMatchNextPage, sNextUrl = cParser.parseSingleResult(sHtmlContent, pattern)
        if isMatchNextPage:
            baseURL = params.getValue('baseURL')
            params.setParam('sUrl', baseURL + sNextUrl)
            oGui.addNextPage(SITE_IDENTIFIER, 'showEntries', params)
            oGui.setView('tvshows' if 'serie' in entryUrl else 'movies')
        oGui.setEndOfDirectory()


def showSeasons():
    oGui = cGui()
    params = ParameterHandler()
    sUrl = params.getValue('entryUrl')
    sThumbnail = params.getValue('sThumbnail')
    sTVShowTitle = params.getValue('sName')
    sHtmlContent = cRequestHandler(sUrl).request()
    eNr = re.compile('getEpisodes[^>]([\d]+)').findall(sHtmlContent)[0]
    pattern = '<option[^>]value="([^"]+)">([^<]+)'
    isMatch, aResult = cParser.parse(sHtmlContent, pattern)

    if not isMatch:
        oGui.showInfo('streamon', 'Es wurde kein Eintrag gefunden')
        return

    total = len(aResult)
    for sSeasonNr, sName in aResult:
        oGuiElement = cGuiElement(sName, SITE_IDENTIFIER, 'showEpisodes')
        oGuiElement.setMediaType('season')
        oGuiElement.setTVShowTitle(sTVShowTitle)
        oGuiElement.setSeason(sSeasonNr)
        oGuiElement.setThumbnail(sThumbnail)
        params.setParam('sSeasonNr', int(sSeasonNr))
        params.setParam('eNr', eNr)
        oGui.addFolder(oGuiElement, params, True, total)
    oGui.setView('seasons')
    oGui.setEndOfDirectory()


def showEpisodes():
    oGui = cGui()
    params = ParameterHandler()
    sTVShowTitle = params.getValue('sName')
    sThumbnail = params.getValue('sThumbnail')
    sSeasonNr = params.getValue('sSeasonNr')
    eNr = params.getValue('eNr')
    oRequest = cRequestHandler(URL_Episodes)
    oRequest.addParameters('c', 'PHPSESSID')
    oRequest.addParameters('st', sSeasonNr)
    oRequest.addParameters('v', eNr)
    oRequest.setRequestType(1)
    sHtmlContent = oRequest.request()
    pattern = '<option[^>]value="([^"]+)">([^<]+)'
    isMatch, aResult = cParser.parse(sHtmlContent, pattern)

    if not isMatch:
        oGui.showInfo('streamon', 'Es wurde kein Eintrag gefunden')
        return

    total = len(aResult)
    for sEpisodeNr, sName in aResult:
        oGuiElement = cGuiElement(sName, SITE_IDENTIFIER, 'showHosters')
        oGuiElement.setTVShowTitle(sTVShowTitle)
        oGuiElement.setSeason(sSeasonNr)
        oGuiElement.setEpisode(sEpisodeNr)
        oGuiElement.setMediaType('episode')
        oGuiElement.setThumbnail(sThumbnail)
        params.setParam('sEpisodeNr', sEpisodeNr)
        oGui.addFolder(oGuiElement, params, False, total)
    oGui.setView('episodes')
    oGui.setEndOfDirectory()


def getLinks(v, h, m, s, e):
    params = ParameterHandler()
    entryUrl = params.getValue('entryUrl')
    isTvshow = True if "serie" in entryUrl else False
    oRequest = cRequestHandler(URL_SerienStream if isTvshow else URL_MovieStream)
    oRequest.addParameters('c', 'PHPSESSID')
    oRequest.addParameters('h', h)
    oRequest.addParameters('m', m)
    if isTvshow:
        oRequest.addParameters('s', s)
        oRequest.addParameters('e', e)
    oRequest.addParameters('v', v)
    oRequest.setRequestType(1)
    sHtmlContent = oRequest.request()
    pattern = '(http[^"]+)'
    isMatch, aResult = cParser().parse(sHtmlContent, pattern)
    for sUrl in aResult:
        return sUrl


def showHosters():
    params = ParameterHandler()
    entryUrl = params.getValue('entryUrl')
    isTvshow = True if "serie" in entryUrl else False
    oRequest = cRequestHandler(URL_HosterSerien if isTvshow else URL_HosterFilme)
    oRequest.addParameters('c', 'PHPSESSID')
    if isTvshow:
        oRequest.addParameters('e', params.getValue('sEpisodeNr'))
        oRequest.addParameters('s', params.getValue('sSeasonNr'))
    oRequest.addParameters('v', params.getValue('hosterid'))
    oRequest.setRequestType(1)
    sHtmlContent = oRequest.request()
    if isTvshow:
        sPattern = 'title="([^"]+)"[^>]onclick=".*?Stream[^>]([\d]+),[^>]([\d]+),[^>]([\d]+),[^>]([\d]+),[^>]([\d]+)'
    else:
        sPattern = 'title="([^"]+)"[^>]onclick=".*?Stream[^>]([\d]+),[^>]([\d]+),[^>]([\d]+)'
    isMatch, aResult = cParser().parse(sHtmlContent, sPattern)
    hosters = []
    if isTvshow:
        for sName, v, h, s, e, m in aResult:
            sUrl = getLinks(v, h, m, s, e)
            hoster = {'link': sUrl, 'name': sName}
            hosters.append(hoster)
    else:
        for sName, v, h, m, in aResult:
            sUrl = getLinks(v, h, m, '', '')
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
    showEntries(URL_SEARCH % sSearchText, oGui)
