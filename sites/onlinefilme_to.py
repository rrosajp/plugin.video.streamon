# -*- coding: utf-8 -*-
from resources.lib import logger
from resources.lib.gui.gui import cGui
from resources.lib.gui.guiElement import cGuiElement
from resources.lib.handler.ParameterHandler import ParameterHandler
from resources.lib.handler.requestHandler import cRequestHandler
from resources.lib.parser import cParser
import base64

SITE_IDENTIFIER = 'onlinefilme_to'
SITE_NAME = 'OnlineFilme'
SITE_ICON = 'onlinefilme.png'
 
URL_MAIN = 'http://onlinefilme.to/'
URL_Filme = URL_MAIN + 'filme-online/'
URL_Serien = URL_MAIN + 'serie-online/'
URL_SEARCH = URL_MAIN + 'suche/%s'


def load():
    logger.info("Load %s" % SITE_NAME)
    oGui = cGui()
    params = ParameterHandler()
    params.setParam('valueType', 'filme')
    params.setParam('sUrl', URL_Filme)
    oGui.addFolder(cGuiElement('Filme', SITE_IDENTIFIER, 'showContentMenu'), params)
    params.setParam('valueType', 'serie')
    params.setParam('sUrl', URL_Serien)
    oGui.addFolder(cGuiElement('Serien', SITE_IDENTIFIER, 'showContentMenu'), params)
    oGui.addFolder(cGuiElement('Suche', SITE_IDENTIFIER, 'showSearch'))
    oGui.setEndOfDirectory()


def showContentMenu():
    oGui = cGui()
    params = ParameterHandler()
    baseURL = params.getValue('sUrl')
    params.setParam('sUrl', baseURL + 'newest')
    oGui.addFolder(cGuiElement('Newest', SITE_IDENTIFIER, 'showEntries'), params)
    params.setParam('sUrl', baseURL + 'most-viewed')
    oGui.addFolder(cGuiElement('most viewed', SITE_IDENTIFIER, 'showEntries'), params)
    params.setParam('sUrl', baseURL + 'highest-rated')
    oGui.addFolder(cGuiElement('highest rated', SITE_IDENTIFIER, 'showEntries'), params)
    params.setParam('sUrl', baseURL + 'most-discussed')
    oGui.addFolder(cGuiElement('most discussed', SITE_IDENTIFIER, 'showEntries'), params)
    params.setParam('sUrl', URL_MAIN)
    oGui.addFolder(cGuiElement('Genre', SITE_IDENTIFIER, 'showGenresList'), params)
    oGui.setEndOfDirectory()


def showGenresList(entryUrl=False):
    oGui = cGui()
    params = ParameterHandler()
    if not entryUrl: entryUrl = params.getValue('sUrl')
    valueType = params.getValue('valueType')
    sHtmlContent = cRequestHandler(entryUrl).request()
    pattern = '<li>[^<]*<a[^>]*href="([^"]+%s-online[^"]+)"[^>]*><strong>([^<]+)</strong>' % valueType
    isMatch, aResult = cParser.parse(sHtmlContent, pattern)

    if not isMatch:
        oGui.showInfo('streamon', 'Es wurde kein Eintrag gefunden')
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
    pattern = 'hover-link">.*?</div></div></div></div></a></li></ul>'
    isMatch, sContainer = cParser().parseSingleResult(sHtmlContent, pattern)

    if not isMatch:
        if not sGui: oGui.showInfo('streamon', 'Es wurde kein Eintrag gefunden')
        return

    pattern = 'href="([^"]+).*?original=".*?([^"]+).*?flagHolderDiv">.*?'
    pattern += "alt='([^']+).*?"
    pattern += 'title"><h2>([^<]+).*?left">([^<]+)'
    isMatch, aResult = cParser().parse(sContainer, pattern)

    if not isMatch:
        if not sGui: oGui.showInfo('streamon', 'Es wurde kein Eintrag gefunden')
        return

    total = len(aResult)
    for sUrl, sThumbnail, sLang, sName, sYear in aResult:
        isTvshow = True if "serie" in sUrl else False
        oGuiElement = cGuiElement(sName, SITE_IDENTIFIER, 'showEpisodes' if isTvshow else 'showHosters')
        oGuiElement.setMediaType('tvshow' if isTvshow else 'movie')
        oGuiElement.setLanguage(sLang)
        oGuiElement.setThumbnail(URL_MAIN + sThumbnail)
	oGuiElement.setFanart(URL_MAIN + sThumbnail)
        oGuiElement.setYear(sYear)
        oGuiElement.setMediaType('tvshow' if isTvshow else 'movie')
        params.setParam('TVShowTitle', sName)
        params.setParam('entryUrl', sUrl)
        oGui.addFolder(oGuiElement, params, isTvshow, total)
    if not sGui:
        isMatchNextPage, sNextUrl = cParser().parseSingleResult(sHtmlContent, "class='arrow'><a[^>]*href='([^']+)'>&raquo")
        if isMatchNextPage:
            params.setParam('sUrl', sNextUrl)
        oGui.addNextPage(SITE_IDENTIFIER, 'showEntries', params)
        oGui.setView('tvshows' if 'serie' in entryUrl else 'movies')
        oGui.setEndOfDirectory()


def showEpisodes():
    oGui = cGui()
    params = ParameterHandler()
    sTVShowTitle = params.getValue('TVShowTitle')
    entryUrl = params.getValue('entryUrl')
    oRequest = cRequestHandler(entryUrl)
    sHtmlContent = oRequest.request()
    pattern = '<dd[^>]class="accordion-navigation"><a[^>]href=".*?"><strong>([^"]+)</strong>'
    isMatch, aResult = cParser.parse(sHtmlContent, pattern)

    if not isMatch:
        oGui.showInfo('streamon', 'Es wurde kein Eintrag gefunden')
        return

    total = len(aResult)
    for sName in aResult:
        oGuiElement = cGuiElement(sName, SITE_IDENTIFIER, 'showHosters')
        oGuiElement.setTVShowTitle(sTVShowTitle)
        oGuiElement.setMediaType('episode')
        params.setParam('sEpisode', sName)
        oGui.addFolder(oGuiElement, params, False, total)
    oGui.setView('episodes')
    oGui.setEndOfDirectory()


def getLinks():
    params = ParameterHandler()
    sUrl = params.getValue('entryUrl')
    sEpisode = params.getValue('sEpisode')
    sHtmlContent = cRequestHandler(sUrl).request()
    if sEpisode:
	pattern = "<strong>%s</strong>.*?</div>.*?<br>" % sEpisode
	isMatch, sHtmlContainer = cParser.parseSingleResult(sHtmlContent, pattern)
	pattern = '>([^<]+)</span></form>.*?true"[^>]title="([^"]+)"></div>.*?right"'
	pattern += "><a[^>]href='([^']+)"
	isMatch, aResult = cParser.parse(sHtmlContainer, pattern)
    else:
	pattern = '>([^"]+)</span></form>.*?true"[^>]title="([^"]+).*?</span></div>.*?'
	pattern += "<a[^>]href='([^']+)"
	isMatch, aResult = cParser().parse(sHtmlContent, pattern)
    return aResult


def showHosters():
    aResult = getLinks()
    hosters = []
    for sName, sLang, sUrl in aResult:
	oRequest = cRequestHandler(sUrl, caching=False)
	oRequest.request()
        hoster = {'link': oRequest.getRealUrl(), 'name': sName + ' ' + sLang}
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
    sSearchText = base64.b64encode('search_term=%s&search_type=0&search_where=0&search_rating_start=1&search_rating_end=10&search_year_from=1900' % sSearchText)
    showEntries(URL_SEARCH % sSearchText.strip(), oGui)
