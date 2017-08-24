# -*- coding: utf-8 -*-
from resources.lib.gui.gui import cGui
from resources.lib.gui.guiElement import cGuiElement
from resources.lib.handler.requestHandler import cRequestHandler
from resources.lib.parser import cParser
from resources.lib import logger
from resources.lib.handler.ParameterHandler import ParameterHandler

SITE_IDENTIFIER = 'filme-streamz_com'
SITE_NAME = 'FilmeStreamz'
SITE_ICON = 'filme-streamz.png'

URL_MAIN = 'http://www.filme-streamz.com/'
URL_Filme = URL_MAIN + 'categorie/2/filme-im-stream-stream-p1.html'
URL_Erfolgreichste = URL_MAIN + '/categorie/6/Erfolgreichste-Filmreihen-stream-stream-p1.html'
URL_Kino = URL_MAIN + '/categorie/7/Neuerscheinungen-stream-p1.html'
URL_SEARCH = URL_MAIN + '/?s=%s'


def load():
    logger.info("Load %s" % SITE_NAME)
    oGui = cGui()
    params = ParameterHandler()
    params.setParam('sUrl', URL_MAIN)
    oGui.addFolder(cGuiElement('Alle Filme', SITE_IDENTIFIER, 'showEntries'), params)
    params.setParam('sUrl', URL_Filme)
    oGui.addFolder(cGuiElement('Filme', SITE_IDENTIFIER, 'showEntries'), params)
    params.setParam('sUrl', URL_Erfolgreichste)
    oGui.addFolder(cGuiElement('Erfolgreichste Filmreihen', SITE_IDENTIFIER, 'showEntries'), params)
    params.setParam('sUrl', URL_Kino)
    oGui.addFolder(cGuiElement('Kinofilme / Neuerscheinungen', SITE_IDENTIFIER, 'showEntries'), params)
    oGui.addFolder(cGuiElement('Genre', SITE_IDENTIFIER, 'showGenresList'), params)
    oGui.addFolder(cGuiElement('Suche', SITE_IDENTIFIER, 'showSearch'))
    oGui.setEndOfDirectory()


def showGenresList():
    oGui = cGui()
    params = ParameterHandler()
    sHtmlContent = cRequestHandler(URL_MAIN).request()
    aResult = cParser().parse(sHtmlContent, '<li><a href="([^"]+)" class="rightsidemenu cat">([^"<]+)<')
    if aResult[0] and aResult[1][0]:
        total = len(aResult[1])
        for sUrl, sName in aResult[1]:
            params.setParam('sUrl', URL_MAIN + sUrl)
            oGui.addFolder(cGuiElement((sName), SITE_IDENTIFIER, 'showEntries'), params, True, total)
    oGui.setEndOfDirectory()


def showEntries(entryUrl=False, sGui=False):
    oGui = sGui if sGui else cGui()
    params = ParameterHandler()
    if not entryUrl: entryUrl = params.getValue('sUrl')
    sHtmlContent = cRequestHandler(entryUrl, ignoreErrors = (sGui is not False)).request()
    pattern = 'class="list_film.*?img src="([^"]+).*?\s=\s\'([^\']+).*?>([^"(]+).*?\(([^")]+)'
    aResult = cParser().parse(sHtmlContent, pattern)

    if aResult[0] and aResult[1][0]:
        total = len(aResult[1])
        for sThumbnail, sUrl, sName, sJahr in aResult[1]:
            oGuiElement = cGuiElement(sName, SITE_IDENTIFIER, 'showHosters')
            oGuiElement.setThumbnail(sThumbnail)
            oGuiElement.setYear(sJahr)
            oGuiElement.setMediaType('movie')
            params.setParam('entryUrl', URL_MAIN + sUrl)
            oGui.addFolder(oGuiElement, params, False, total)

    if not sGui:
        pattern = '"><a href="([^"]+)"([^>]+)?>&raquo;'
        aResult = cParser().parse(sHtmlContent, pattern)
        if aResult[0] and aResult[1][0] and 'void' not in aResult[1][0][0]:
            params.setParam('sUrl', URL_MAIN + aResult[1][0][0])
            oGui.addNextPage(SITE_IDENTIFIER, 'showEntries', params)
        oGui.setView('movies')
        oGui.setEndOfDirectory()


def showHosters():
    oParams = ParameterHandler()
    sUrl = oParams.getValue('entryUrl')
    sHtmlContent = cRequestHandler(sUrl).request()
    sPattern = '<a[^>]*href="([^"]+)"[^>]*target="videoPlayer"[^>]*class="[^"]*sinactive[^"]*"[^>]*>\s*<img[^>]*src="\/images\/([^"]+)\.\w{1,3}"[^>]*>\s*</a>'
    aResult = cParser().parse(sHtmlContent, sPattern)
    hosters = []
    if aResult[1]:
        for sUrl, sName in aResult[1]:
            hoster = {}
            hoster['link'] = sUrl
            hoster['name'] = sName.title()
            hosters.append(hoster)
    if hosters:
        hosters.append('getHosterUrl')
    return hosters


def getHosterUrl(sUrl=False):
    if not sUrl: sUrl = ParameterHandler().getValue('url')
    results = []
    result = {}

    # resolve redirect
    if not sUrl.startswith("http"):
        oRequestHandler = cRequestHandler(URL_MAIN + sUrl)
        oRequestHandler.request()
        sUrl = oRequestHandler.getRealUrl()

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
    showEntries(URL_SEARCH % sSearchText.strip(), oGui)
