# -*- coding: utf-8 -*-
from resources.lib.gui.gui import cGui
from resources.lib.gui.guiElement import cGuiElement
from resources.lib.handler.requestHandler import cRequestHandler
from resources.lib.parser import cParser
from resources.lib import logger
from resources.lib.handler.ParameterHandler import ParameterHandler
from resources.lib.config import cConfig

SITE_IDENTIFIER = 'flimmerstube_com'
SITE_NAME = 'Flimmerstube'
SITE_ICON = 'flimmerstube.png'
SITE_GLOBAL_SEARCH = False

URL_MAIN_GER = 'http://flimmerstube.com'
URL_MAIN_ENG = 'http://flimmerstube.do.am'
URL_MOVIE_GER = URL_MAIN_GER + '/video/vic/alle_filme'
URL_MOVIE_ENG = URL_MAIN_ENG + '/video/vic/alle_filme'
URL_SEARCH = '/shv'

def load():
    logger.info("Load %s" % SITE_NAME)
    oGui = cGui()
    params = ParameterHandler()

    sLanguage = _getPrefLanguage()

    if sLanguage == '0' or sLanguage == '2':
        params.setParam('sBaseUrl', URL_MAIN_GER)
        params.setParam('sUrl', URL_MOVIE_GER)
        oGui.addFolder(cGuiElement('Deutsche Horrorfilme', SITE_IDENTIFIER, 'showEntries'), params)
        params.setParam('sBaseUrl', URL_MAIN_GER)
        params.setParam('sUrl', URL_MOVIE_GER)
        oGui.addFolder(cGuiElement('Genre (DE)', SITE_IDENTIFIER, 'showGenresList'), params)
    if sLanguage == '1' or sLanguage == '2':
        params.setParam('sBaseUrl', URL_MAIN_ENG)
        params.setParam('sUrl', URL_MOVIE_ENG)
        oGui.addFolder(cGuiElement('English Horror Movie', SITE_IDENTIFIER, 'showEntries'), params)
        params.setParam('sBaseUrl', URL_MAIN_ENG)
        params.setParam('sUrl', URL_MOVIE_ENG)
        oGui.addFolder(cGuiElement('Genre (EN)', SITE_IDENTIFIER, 'showGenresList'), params)

    oGui.addFolder(cGuiElement('Suche', SITE_IDENTIFIER, 'showSearch'))
    oGui.setEndOfDirectory()

def showGenresList():
    oGui = cGui()
    params = ParameterHandler()
    sBaseUrl = params.getValue('sBaseUrl')
    sHtmlContent = cRequestHandler(params.getValue('sUrl')).request()
    aResult = cParser().parse(sHtmlContent, '<a[^>]class=[^>]catName[^>][^>]href="([^"]+)"[^>]>([^"]+)</a>')
    if aResult[0] and aResult[1][0]:
        total = len (aResult[1])
        for sUrl, sName in aResult[1]:
            params.setParam('sUrl', sBaseUrl + sUrl)
            oGui.addFolder(cGuiElement((sName), SITE_IDENTIFIER, 'showEntries'), params, True, total)
    oGui.setEndOfDirectory()

def showEntries(entryUrl = False, sGui = False, sSearchText = None, sBaseUrl = None, isInternalSearch = False):
    oGui = sGui if sGui else cGui()
    params = ParameterHandler()
    if not entryUrl: entryUrl = params.getValue('sUrl')
    if not sBaseUrl: sBaseUrl = params.getValue('sBaseUrl')
    oRequest = cRequestHandler(entryUrl, ignoreErrors = (isInternalSearch == False))
    if sSearchText:
        oRequest.addParameters('query', sSearchText)
        oRequest.setRequestType(1)
    sHtmlContent = oRequest.request()
    pattern = '<div[^>]class="ve-screen"[^>]title="([^"(]+)[^>]([^")]+).*?url[^>]([^")]+).*?<a[^>]href="([^">]+)'
    aResult = cParser().parse(sHtmlContent, pattern)

    if aResult[0] and aResult[1][0]:
        total = len (aResult[1])
        for sName, sJahr, sThumbnail, sUrl in aResult[1]:
            oGuiElement = cGuiElement(sName, SITE_IDENTIFIER, 'showHosters')
            oGuiElement.setThumbnail(sThumbnail if sThumbnail.startswith("http") else sBaseUrl + sThumbnail)
            oGuiElement.setYear(sJahr)
            params.setParam('sBaseUrl', sBaseUrl)
            params.setParam('entryUrl', sBaseUrl + sUrl)
            oGui.addFolder(oGuiElement, params, False, total)

    if not sGui:
        pattern = 'onclick="spages[^>][^>]([^"]+)[^>][^>];return[^>]false;"><span>&raquo;</span></a></span></td></tr></table>.*?location.href=[^>]([^"]+)[^>][^>]page[^>]'
        aResult = cParser().parse(sHtmlContent, pattern)
        if aResult[0] and aResult[1][0]:
            for sNr, Url in aResult[1]:
                params.setParam('sBaseUrl', sBaseUrl)
                params.setParam('sUrl', sBaseUrl + Url + sNr)
                oGui.addNextPage(SITE_IDENTIFIER, 'showEntries', params)

        oGui.setView('movies')
        oGui.setEndOfDirectory()

def showHosters():
    oParams = ParameterHandler()
    sUrl = oParams.getValue('entryUrl')
    sHtmlContent = cRequestHandler(sUrl).request()
    sPattern = 'src=[^>]"([^"]+)"\s'
    aResult = cParser().parse(sHtmlContent, sPattern)
    hosters = []
    if aResult[1]:
        for sUrl in aResult[1]:
            hoster = {}
            hoster['link'] = sUrl
            hoster['name'] = sUrl
            hosters.append(hoster)
    if hosters:
        hosters.append('getHosterUrl')
    return hosters

def getHosterUrl(sUrl = False):
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

def _getPrefLanguage():
    sLanguage = cConfig().getSetting('prefLanguage')
    sLanguage = sLanguage if sLanguage != '' else '2'
    return sLanguage

def _search(oGui, sSearchText):
    if not sSearchText: return
    sLanguage = _getPrefLanguage()
    isInternalSearch = (oGui == False)

    if isInternalSearch:
        oGui = cGui()

    if sLanguage == '0' or sLanguage == '2':
        showEntries(URL_MOVIE_GER + URL_SEARCH, oGui, sSearchText, URL_MAIN_GER, isInternalSearch)
    if sLanguage == '1' or sLanguage == '2':
        showEntries(URL_MOVIE_ENG + URL_SEARCH, oGui, sSearchText, URL_MAIN_ENG, isInternalSearch)

    if isInternalSearch:
        oGui.setView('movies')
        oGui.setEndOfDirectory()
