# -*- coding: utf-8 -*-
import re
from resources.lib import logger
from resources.lib.gui.gui import cGui
from resources.lib.gui.guiElement import cGuiElement
from resources.lib.handler.ParameterHandler import ParameterHandler
from resources.lib.handler.requestHandler import cRequestHandler
from resources.lib.parser import cParser
from resources.lib.util import cUtil

SITE_IDENTIFIER = 'movie2k_ag'
SITE_NAME = 'Movie2k AG'
SITE_ICON = 'movie2k_ag.png'

URL_MAIN = 'http://movie2k.ag/'
URL_MOVIE = URL_MAIN + '%s'
URL_SEARCH = '&keyword=%s'
URL_Hoster = 'http://www.vodlocker.to/embed/movieStreams/?id=%s'


def load():
    logger.info("Load %s" % SITE_NAME)
    oGui = cGui()
    params = ParameterHandler()
    params.setParam('sUrl', URL_MOVIE % 'releases')
    oGui.addFolder(cGuiElement('Neue Filme', SITE_IDENTIFIER, 'showEntries'), params)
    params.setParam('sUrl', URL_MOVIE % 'featured')
    oGui.addFolder(cGuiElement('Kinofilme', SITE_IDENTIFIER, 'showEntries'), params)
    params.setParam('sUrl', URL_MOVIE % 'views')
    oGui.addFolder(cGuiElement('Beliebte Filme', SITE_IDENTIFIER, 'showEntries'), params)
    params.setParam('sUrl', URL_MOVIE % 'updates')
    oGui.addFolder(cGuiElement('Updates', SITE_IDENTIFIER, 'showEntries'), params)
    params.setParam('sUrl', URL_MOVIE % 'rating')
    oGui.addFolder(cGuiElement('Top IMDB', SITE_IDENTIFIER, 'showEntries'), params)
    oGui.addFolder(cGuiElement('Genre', SITE_IDENTIFIER, 'showGenre'))
    oGui.addFolder(cGuiElement('Suche', SITE_IDENTIFIER, 'showSearch'))
    oGui.setEndOfDirectory()


def showGenre():
    oGui = cGui()
    params = ParameterHandler()
    sHtmlContent = cRequestHandler(URL_MAIN).request()
    sPattern = '">Genres</a>.*?</ul>'
    isMatch, sHtmlContainer = cParser.parseSingleResult(sHtmlContent, sPattern)

    if not isMatch:
        oGui.showInfo('streamon', 'Es wurde kein Eintrag gefunden')
        return

    isMatch, aResult = cParser.parse(sHtmlContainer, "<a[^>]*href='([^']+)'>([^<]+)")

    if not isMatch:
        oGui.showInfo('streamon', 'Es wurde kein Eintrag gefunden')
        return

    for sUrl, sName in aResult:
        print sUrl
        print 'viper'
        params.setParam('sUrl', sUrl)
        oGui.addFolder(cGuiElement(sName, SITE_IDENTIFIER, 'showEntries'), params)
    oGui.setEndOfDirectory()


def showEntries(entryUrl=False, sGui=False):
    oGui = sGui if sGui else cGui()
    params = ParameterHandler()
    if not entryUrl: entryUrl = params.getValue('sUrl')
    oRequest = cRequestHandler(entryUrl, ignoreErrors=(sGui is not False))
    oRequest.addHeaderEntry('Referer', entryUrl)
    sHtmlContent = oRequest.request()

    pattern = '<a[^>]*class="clip-link".*?title="([^"]+).*?href="([^"]+).*?(?:<img src="([^"]+).*?<span>([^<]+)?)'
    isMatch, aResult = cParser.parse(sHtmlContent, pattern)

    if not isMatch:
        if not sGui: oGui.showInfo('streamon', 'Es wurde kein Eintrag gefunden')
        return

    total = len(aResult)
    for sName, sUrl, sThumbnail, sDesc in aResult:
        sYear = re.compile("(.*?)\((\d*)\)").findall(sName)

        for name, year in sYear:
            sName = name
            sYear = year
            break

        sID = re.compile('-(\d+)[^>]htm').findall(sUrl)[0]
        oGuiElement = cGuiElement(sName, SITE_IDENTIFIER, 'showHosters')
        oGuiElement.setThumbnail(sThumbnail)
        if sDesc:
            oGuiElement.setDescription(sDesc)
        if sYear:
            oGuiElement.setYear(sYear)
        params.setParam('sUrl', URL_Hoster % sID)
        oGui.addFolder(oGuiElement, params, False, total)

    if not sGui:
        isMatchNextPage, sNextUrl = cParser.parseSingleResult(sHtmlContent, '<a[^>]*href="([^"]+)">&gt')
        if isMatchNextPage:
            params.setParam('sUrl', cUtil.cleanse_text(sNextUrl))
            oGui.addNextPage(SITE_IDENTIFIER, 'showEntries', params)
        oGui.setView('movies')
        oGui.setEndOfDirectory()


def showHosters():
    sUrl = ParameterHandler().getValue('sUrl')
    sHtmlContent = cRequestHandler(sUrl).request()

    sPattern = "<a[^>]*href='([^']+)'(?:[^>]*player.*?, \"([^\"]+)\")?.*?<span[^>]*class='?url'?[^>]*>(.*?)</span>"
    isMatch, aResult = cParser().parse(sHtmlContent, sPattern)

    hosters = []
    if isMatch:
        for sHref, sEmbeded, sName in aResult:
            hoster = {'link': (sEmbeded if sEmbeded else sHref), 'name': sName}
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
    sHtmlContent = cRequestHandler(URL_MAIN).request()
    try:
        nonce = re.findall('data-key="([^"]+)', sHtmlContent)[0]
    except:
        nonce = '4164OPTZ98adf546874s4'
    showSearchEntries(URL_MAIN + '?c=movie&m=quickSearch&key=' + nonce + URL_SEARCH % sSearchText.strip(), oGui)


def showSearchEntries(entryUrl=False, sGui=False):
    oGui = sGui if sGui else cGui()
    params = ParameterHandler()
    if not entryUrl: entryUrl = params.getValue('sUrl')
    oRequest = cRequestHandler(entryUrl, ignoreErrors=(sGui is not False))
    oRequest.addHeaderEntry('X-Requested-With', 'XMLHttpRequest')
    sHtmlContent = oRequest.request()

    pattern = 'id":"([^"]+)","title":"([^"]+)'
    isMatch, aResult = cParser.parse(sHtmlContent, pattern)

    total = len(aResult)
    for sID, sName in aResult:
        oGuiElement = cGuiElement(sName, SITE_IDENTIFIER, 'showHosters')
        params.setParam('sUrl', URL_Hoster % sID)
        oGui.addFolder(oGuiElement, params, False, total)
    if not sGui:
        oGui.setEndOfDirectory()
