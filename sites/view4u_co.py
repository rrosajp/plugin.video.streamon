# -*- coding: utf-8 -*-
from resources.lib.gui.gui import cGui
from resources.lib.gui.guiElement import cGuiElement
from resources.lib.handler.requestHandler import cRequestHandler
from resources.lib.parser import cParser
from resources.lib import logger
from resources.lib.handler.ParameterHandler import ParameterHandler

SITE_IDENTIFIER = 'view4u_co'
SITE_NAME = 'View4U'
SITE_ICON = 'view4u.png'

URL_MAIN = 'http://view4u.co/'
URL_Kinofilme = URL_MAIN + 'load/25'
URL_FILME_HD = URL_MAIN + 'load/32'
URL_SERIEN = URL_MAIN + 'board/serien/5'
URL_TVSHOWS = URL_MAIN + 'board/serien/4'
URL_SEARCH = URL_MAIN + 'search/?q=%s'

def load():
    logger.info("Load %s" % SITE_NAME)
    oGui = cGui()
    params = ParameterHandler()
    params.setParam('sUrl', URL_Kinofilme)
    oGui.addFolder(cGuiElement('Kinofilme', SITE_IDENTIFIER, 'showEntries'), params)
    params.setParam('sUrl', URL_FILME_HD)
    oGui.addFolder(cGuiElement('Filme in HD', SITE_IDENTIFIER, 'showEntries'), params)
    params.setParam('sUrl', URL_SERIEN)
    oGui.addFolder(cGuiElement('Serien', SITE_IDENTIFIER, 'showEntries'), params)
    params.setParam('sUrl', URL_TVSHOWS)
    oGui.addFolder(cGuiElement('TV-Shows', SITE_IDENTIFIER, 'showEntries'), params)
    params.setParam('sUrl', URL_Kinofilme)
#    params.setParam('valueType', 'vert_nav')
    oGui.addFolder(cGuiElement('Genre', SITE_IDENTIFIER, 'showValueList'))
    oGui.addFolder(cGuiElement('Suche', SITE_IDENTIFIER, 'showSearch'))
    oGui.setEndOfDirectory()

def showValueList():
    oGui = cGui()
    params = ParameterHandler()
    valueType = params.getValue('valueType')

    sHtmlContent = cRequestHandler(URL_Kinofilme).request()
    sPattern = '<ul[^>]*class="vert_nav">.*?</a></li>[^>]*</ul>' #% valueType # will hier noch "filme nach jahr" eibauen

    isMatch, strContainer = cParser.parseSingleResult(sHtmlContent, sPattern)

    if isMatch:
        sPattern = '<a[^>]*href="([^"]+)"[^>]*>([^<]*)</a>'
        isMatch, aResult = cParser.parse(strContainer, sPattern)

    if not isMatch:
        oGui.showInfo('streamon','Es wurde kein Eintrag gefunden')
        return

    for sUrl, sName in aResult:
        params.setParam('sUrl',URL_MAIN + sUrl)
        oGui.addFolder(cGuiElement(sName, SITE_IDENTIFIER, 'showEntries'), params)
    oGui.setEndOfDirectory()

def showEntries(entryUrl = False, sGui = False):
    oGui = sGui if sGui else cGui()
    params = ParameterHandler()
    if not entryUrl: entryUrl = params.getValue('sUrl')
    sHtmlContent = cRequestHandler(entryUrl, ignoreErrors = (sGui is not False)).request()
    if not sGui:
        pattern = '<div class="s_poster"> <a href="([^"]+)"><img src="([^"]+).*?">([^<]+)</a></h2>.*?">([^<]+)</a></li>.*?shortstory_bottom">([^<]+)'
    else:
        pattern = 'poster">[^>]*<a[^>]*href="([^"]+)"><img[^>]*src="([^"]+).*?">([^"]+)</a></h2>.*?shortstory_bottom">([^<]+)'
    isMatch, aResult = cParser.parse(sHtmlContent, pattern)

    if not isMatch:
        if not sGui: oGui.showInfo('streamon','Es wurde kein Eintrag gefunden')
        return

    total = len (aResult)
    for sUrl, sThumbnail, sName, sYear, sDescription in aResult:
        isTvshow = True if "serie" in entryUrl or "show" in sUrl else False
        oGuiElement = cGuiElement(sName, SITE_IDENTIFIER, 'showHosters')
        oGuiElement.setThumbnail(URL_MAIN + sThumbnail)
        oGuiElement.setDescription(sDescription)
        oGuiElement.setYear(sYear)
        oGuiElement.setMediaType('tvshow' if isTvshow else 'movie')        
        params.setParam('isTvshow', isTvshow)
        params.setParam('entryUrl', URL_MAIN + sUrl)        
        oGui.addFolder(oGuiElement, params, False, total)

    if not sGui:
        sPattern = 'class="swchItemA1"[^>]*>.*?</b>\s*<a[^>]*href="([^"]+)"'
        isMatchNextPage, sNextUrl = cParser.parseSingleResult(sHtmlContent, sPattern)
        if isMatchNextPage:
            params.setParam('sUrl', URL_MAIN + sNextUrl)
            oGui.addNextPage(SITE_IDENTIFIER, 'showEntries', params)

        oGui.setView('tvshows' if "serie" in entryUrl or "show" in entryUrl else 'movies')
        oGui.setEndOfDirectory()

def showHosters():
    oParams = ParameterHandler()
    sUrl = oParams.getValue('entryUrl')
    isTvshowEntry = oParams.getValue('isTvshow')
    sHtmlContent = cRequestHandler(sUrl).request()
    if isTvshowEntry == 'True':
        sPattern = '"> <a href="([^"]+)"> <img src=".*?//.*?/.*?/([^.]+)' # serie/shows
    else:
        sPattern = '> <img alt="" src=".*?//.*?/.*?/([^"]+).png.*?<a target="_blank" href="([^"]+)' # Movies

    isMatch, aResult = cParser.parse(sHtmlContent, sPattern)

    if not isMatch:
        return []

    hosters = []
    for sName, sUrl in aResult:
        hoster = {}
        if isTvshowEntry == 'True':
            hoster['name'] = sUrl
            hoster['link'] = sName
        else:
            hoster['name'] = sName
            hoster['link'] = sUrl
        hosters.append(hoster)
    if hosters:
        hosters.append('getHosterUrl')
    return hosters

def getHosterUrl(sUrl = False):
    oParams = ParameterHandler()
    if not sUrl: sUrl = oParams.getValue('url')
    return [{'streamUrl': sUrl, 'resolved': False}]

def showSearchEntries(entryUrl = False, sGui = False):
    oGui = sGui if sGui else cGui()
    params = ParameterHandler()
    if not entryUrl: entryUrl = params.getValue('sUrl')
    sHtmlContent = cRequestHandler(entryUrl, ignoreErrors = (sGui is not False)).request()
    pattern = 'poster">[^>]*<a[^>]*href="([^"]+)"><img[^>]*src="([^"]+).*?">([^"]+)</a></h2>.*?shortstory_bottom">([^<]+)'
    isMatch, aResult = cParser.parse(sHtmlContent, pattern)

    if not isMatch:
        return

    total = len (aResult)
    for sUrl, sThumbnail, sName, sDescription in aResult:
        oGuiElement = cGuiElement(sName, SITE_IDENTIFIER, 'showHosters')
        oGuiElement.setThumbnail(URL_MAIN + sThumbnail)
        oGuiElement.setDescription(sDescription)
        params.setParam('entryUrl', sUrl)
        oGui.addFolder(oGuiElement, params, False, total)

def showSearch():
    oGui = cGui()
    sSearchText = oGui.showKeyBoard()
    if not sSearchText: return
    _search(False, sSearchText)
    oGui.setEndOfDirectory()

def _search(oGui, sSearchText):
    if not sSearchText: return
    showSearchEntries(URL_SEARCH % sSearchText.strip(), oGui)
