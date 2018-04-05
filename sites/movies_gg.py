# -*- coding: utf-8 -*-
import base64, re
from resources.lib import logger
from resources.lib.gui.gui import cGui
from resources.lib.gui.guiElement import cGuiElement
from resources.lib.handler.ParameterHandler import ParameterHandler
from resources.lib.handler.requestHandler import cRequestHandler
from resources.lib.parser import cParser

SITE_IDENTIFIER = 'movies_gg'
SITE_NAME = 'Movies.GG'
SITE_ICON = 'movies_gg.png'

URL_MAIN = 'https://movies.gg'
URL_KINO = URL_MAIN + '/de/kino-filme/'
URL_FILME = URL_MAIN + '/de/genres'
URL_SEARCH = URL_MAIN + '/de/search?q=%s'


def load():
    logger.info("Load %s" % SITE_NAME)
    oGui = cGui()
    params = ParameterHandler()
    params.setParam('sUrl', URL_KINO)
    oGui.addFolder(cGuiElement('Kino Filme', SITE_IDENTIFIER, 'showEntries'), params)
    params.setParam('sUrl', URL_FILME)
    oGui.addFolder(cGuiElement('Filme', SITE_IDENTIFIER, 'showEntries'), params)
    oGui.addFolder(cGuiElement('Genre', SITE_IDENTIFIER, 'showGenre'))
    oGui.addFolder(cGuiElement('Suche', SITE_IDENTIFIER, 'showSearch'))
    oGui.setEndOfDirectory()


def showGenre():
    oGui = cGui()
    params = ParameterHandler()
    sHtmlContent = cRequestHandler('https://movies.gg/de/genres#genresmenu').request()
    isMatch, aResult = cParser.parse(sHtmlContent, '<a[^>]href="(/de/genres/[^"]+)".*?>([^<]+)')

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
    sHtmlContent = cRequestHandler(entryUrl, ignoreErrors=(sGui is not False)).request()
    pattern = '<a href="href="([^"]+).*?src="([^"]+)" alt="([^"]+)'
    isMatch, aResult = cParser().parse(sHtmlContent, pattern)

    if not isMatch:
        if not sGui: oGui.showInfo('streamon', 'Es wurde kein Eintrag gefunden')
        return

    total = len(aResult)
    for sUrl, sThumbnail, sName in aResult:
        sYear = re.compile("-([0-9]{4})").findall(sUrl)
        for year in sYear:
            sYear = year
            break
        oGuiElement = cGuiElement(sName, SITE_IDENTIFIER, 'showHosters')
        oGuiElement.setMediaType('movie')
        oGuiElement.setThumbnail(sThumbnail)
        oGuiElement.setFanart(sThumbnail)
        oGuiElement.setYear(sYear)
        oGuiElement.setMediaType('movie')
        params.setParam('entryUrl', URL_MAIN + sUrl)
        oGui.addFolder(oGuiElement, params, False, total)
    if not sGui:
        isMatchNextPage, sNextUrl = cParser.parseSingleResult(sHtmlContent, '<a[^>]href="([^"]+)"[^>]rel="next">&raquo')
        if isMatchNextPage:
            params.setParam('sUrl', sNextUrl)
            oGui.addNextPage(SITE_IDENTIFIER, 'showEntries', params)
        oGui.setView('movies')
        oGui.setEndOfDirectory()


def showSearch():
    oGui = cGui()
    sSearchText = oGui.showKeyBoard()
    if not sSearchText: return
    _search(False, sSearchText)
    oGui.setEndOfDirectory()


def _search(oGui, sSearchText):
    if not sSearchText: return
    showEntries(URL_SEARCH % sSearchText.strip(), oGui)


def showHosters():
    sUrl = ParameterHandler().getValue('entryUrl')
    sHtmlContent = cRequestHandler(sUrl).request()
    sPattern = 'alt="([^"]+).*?value="([\d]+)'
    isMatch, aResult = cParser().parse(sHtmlContent, sPattern)
    pattern = "_token':'([^']+)','movie_imdb':'([^']+)','movie_tmdb':'([^']+)"
    token, movie_imdb, movie_tmdb = re.compile(pattern, flags=re.I | re.M).findall(sHtmlContent)[0]
    hosters = []
    for sName, link_id in aResult:
        sUrl2 = getLinks(sUrl, movie_imdb, movie_tmdb, token, link_id)
        hoster = {'link': sUrl2, 'name': sName}
        hosters.append(hoster)
    if hosters:
        hosters.append('getHosterUrl')
    return hosters


def getHosterUrl(sUrl=False):
    return [{'streamUrl': sUrl, 'resolved': False}]


def getLinks(sUrl, movie_imdb, movie_tmdb, token, link_id):
    oRequest = cRequestHandler(sUrl)
    oRequest.addParameters('_token', token)
    oRequest.addParameters('link_id', link_id)
    oRequest.addParameters('movie_imdb', movie_imdb)
    oRequest.addParameters('movie_tmdb', movie_tmdb)
    oRequest.setRequestType(1)
    sHtmlContent = oRequest.request()
    pattern = '([^"]+)'
    isMatch, aResult = cParser().parse(sHtmlContent, pattern)
    for link in aResult:
        sUrl2 = base64.b64decode(link)
        return sUrl2
