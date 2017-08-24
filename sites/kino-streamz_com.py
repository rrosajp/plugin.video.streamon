# -*- coding: utf-8 -*-
from resources.lib.gui.gui import cGui
from resources.lib.gui.guiElement import cGuiElement
from resources.lib.handler.requestHandler import cRequestHandler
from resources.lib.parser import cParser
from resources.lib import logger
from resources.lib.handler.ParameterHandler import ParameterHandler

SITE_IDENTIFIER = 'kino-streamz_com'
SITE_NAME = 'KinoStreamz'
SITE_ICON = 'kino-streamz.png'

URL_MAIN = 'http://kino-streamz.com/'
URL_Filme = URL_MAIN + 'categorie/2/filme-stream-p1.html'
URL_Kino = URL_MAIN + 'categorie/8/kinofilme-2016-online-stream-p1.html'
URL_GENRE = URL_MAIN + 'genre'
URL_SEARCH = URL_MAIN + '?q=%s'

def load():
    logger.info("Load %s" % SITE_NAME)
    oGui = cGui()
    params = ParameterHandler()
    params.setParam('sUrl', URL_Kino)
    oGui.addFolder(cGuiElement('Kinofilme', SITE_IDENTIFIER, 'showEntries'), params)
    params.setParam('sUrl', URL_Filme)
    oGui.addFolder(cGuiElement('Filme', SITE_IDENTIFIER, 'showEntries'), params)
    oGui.addFolder(cGuiElement('Genre', SITE_IDENTIFIER, 'showGenresList'), params)
    oGui.addFolder(cGuiElement('Suche', SITE_IDENTIFIER, 'showSearch'))
    oGui.setEndOfDirectory()

def showGenresList():
    oGui = cGui()
    params = ParameterHandler()
    sHtmlContent = cRequestHandler(URL_GENRE).request()
    aResult = cParser().parse(sHtmlContent, '<a[^>]class="list-group-item"[^>]href="([^"]+)"><span[^>]class="badge">([^"<]+)</span>([^"<]+)')
    if aResult[0] and aResult[1][0]:
        total = len(aResult[1])
        for sUrl, sNr ,sName in aResult[1]:
            params.setParam('sUrl', URL_MAIN + sUrl)
            oGui.addFolder(cGuiElement((sName + ' (' + sNr + ')'), SITE_IDENTIFIER, 'showEntries'), params, True, total)
    oGui.setEndOfDirectory()

def showEntries(entryUrl=False, sGui=False):
    oGui = sGui if sGui else cGui()
    params = ParameterHandler()
    if not entryUrl: entryUrl = params.getValue('sUrl')
    sHtmlContent = cRequestHandler(entryUrl, ignoreErrors = (sGui is not False)).request()
    pattern = '">([^"]+)</div><a[^>]href="([^"]+)-([^"]+)-stream.*?src="([^"]+)"></a>[^>].*?">([^"<]+)'
    aResult = cParser().parse(sHtmlContent, pattern)

    if aResult[0] and aResult[1][0]:
        total = len(aResult[1])
        for sDesc, sUrl, sYear, sThumbnail, sName in aResult[1]:
            oGuiElement = cGuiElement(sName, SITE_IDENTIFIER, 'showHosters')
            oGuiElement.setThumbnail(sThumbnail.decode('utf-8').encode('utf-8'))
            oGuiElement.setDescription(sDesc)
            oGuiElement.setYear(sYear)
            params.setParam('sName', sName)
            params.setParam('entryUrl', URL_MAIN + sUrl + '-' + sYear + '-stream')
            oGui.addFolder(oGuiElement, params, False, total)

    if not sGui:
        pattern = '"><a[^>]href="([^"]+)"([^>]+)?>&raquo;'
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
    sPattern = '<tr[^>]*class="mygt"[^>]*>\s*<td[^>]*>\s*<img[^>]*src="\/images\/([^"]+)\.\w{1,3}"[^>]*>\s*' # name
    sPattern += '</td>\s*<td[^>]*>\s*<img[^>]*src="[^"]*\/play.png"[^>]*onclick=".*?\'([^\']+)\'\)"[^>]*>' # url
    aResult = cParser.parse(sHtmlContent, sPattern)
    hosters = []
    if aResult[1]:
        for sName, sUrl in aResult[1]:
            if sUrl.startswith('/hd/'): continue
            hosters.append({'link': sUrl, 'name': sName.title()})
    if hosters:
        hosters.append('getHosterUrl')
    return hosters

def getHosterUrl(sUrl=False):
    if not sUrl: sUrl = ParameterHandler().getValue('url')
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
    showEntries(URL_SEARCH % sSearchText.strip(), oGui)
