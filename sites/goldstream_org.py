# -*- coding: utf-8 -*-
from resources.lib.gui.gui import cGui
from resources.lib.gui.guiElement import cGuiElement
from resources.lib.handler.requestHandler import cRequestHandler
from resources.lib.parser import cParser
from resources.lib import logger
from resources.lib.handler.ParameterHandler import ParameterHandler
from resources.lib.config import cConfig

SITE_IDENTIFIER = 'goldstream_org'
SITE_NAME = 'Goldstream'
SITE_ICON = 'goldstream.png'

URL_MAIN = 'http://goldstream.org/'
URL_Kinofilme = URL_MAIN + 'Stream/kinofilme/'
URL_Filme = URL_MAIN + 'Stream/filme/'
URL_ADULT = URL_MAIN + '/Stream/xxx/'
URL_SEARCH =  URL_MAIN + '?s=%s'
URL_SERIES = URL_MAIN + 'serien/'

URL_GENRES_LIST = {'Abenteuer' : 'Stream/filme/abenteuer', 'Action' : 'Stream/filme/action', 'Animation' : 'Stream/filme/animation', 'Dokumentation' : 'Stream/filme/dokumentation',
                'Drama' : 'Stream/filme/drama',  'Family' : 'Stream/filme/family',  'Historie' : 'Stream/filme/historie',  'Horror' : 'Stream/filme/horror',
                'Komödie' : 'Stream/filme/komoedie',  'Krimi' : 'Stream/filme/krimi',  'Lovestory' : 'Stream/filme/lovestory',  'Musical' : 'Stream/filme/musical',
                'Science Fiction' : 'Stream/filme/science-fiction', 'Thriller' : 'Stream/filme/thriller', 'Western' : 'Stream/filme/western', 'Erotik' : 'Stream/filme/erotik'}

def load():
    logger.info("Load %s" % SITE_NAME)
    oGui = cGui()
    params = ParameterHandler()
    params.setParam('sUrl', URL_Kinofilme)
    oGui.addFolder(cGuiElement('Kinofilme', SITE_IDENTIFIER, 'showEntries'), params)
    params.setParam('sUrl', URL_Filme)
    oGui.addFolder(cGuiElement('Alle Filme', SITE_IDENTIFIER, 'showEntries'), params)
    oGui.addFolder(cGuiElement('Genre', SITE_IDENTIFIER, 'showGenresList'), params)
    oGui.addFolder(cGuiElement('Serien', SITE_IDENTIFIER, 'showSeries'))
    if showAdult():
        params.setParam('sUrl', URL_ADULT)
        oGui.addFolder(cGuiElement('XXX', SITE_IDENTIFIER, 'showEntries'), params)
    oGui.addFolder(cGuiElement('Suche', SITE_IDENTIFIER, 'showSearch'))
    oGui.setEndOfDirectory()

def showAdult():
    oConfig = cConfig()
    if oConfig.getSetting('showAdult')=='true':
        return True
    return False

def showGenresList():
    oGui = cGui()
    if not showAdult():
        del URL_GENRES_LIST['Erotik']
    for key in sorted(URL_GENRES_LIST):
        params = ParameterHandler()
        params.setParam('sUrl', (URL_MAIN + URL_GENRES_LIST[key]))
        oGui.addFolder(cGuiElement(key, SITE_IDENTIFIER, 'showEntries'), params)
    oGui.setEndOfDirectory()

def showSeries():# Danke Lynx187
    oGui = cGui()
    params = ParameterHandler()
    sHtmlContent = cRequestHandler(URL_SERIES).request()
    pattern = '<h3>([^<]+)</h3>\s*<p>\|.+?</p>'
    aResult = cParser().parse(sHtmlContent, pattern)
    if not aResult[0]:
        oGui.showInfo('steamon','Es wurde kein Eintrag gefunden')
        return
    total = len(aResult[1])
    for name in aResult[1]:
        oGuiElement = cGuiElement(name, SITE_IDENTIFIER, 'showSeasons')
        oGuiElement.setMediaType('tvshow')
        oGuiElement.setTVShowTitle(name)
        params.setParam('selectedShow', name)
        oGui.addFolder(oGuiElement, params, True, total)
    oGui.setView('tvshows')
    oGui.setEndOfDirectory()

def showSeasons():# Danke Lynx187
    oGui = cGui()
    params = ParameterHandler()
    selectedShow = params.getValue('selectedShow')
    sHtmlContent = cRequestHandler(URL_SERIES).request()
    pattern = '<h3>%s</h3>\s*<p>\|(.*?)</p>' % selectedShow
    aResult = cParser().parse(sHtmlContent, pattern)
    pattern =  'href="([^"]+)">([^<]+)<'
    aResult = cParser().parse(aResult[1][0], pattern)
    if not aResult[0]:
        oGui.showInfo('steamon','Es wurde kein Eintrag gefunden')
        return
    total = len(aResult[1])
    for link, name in aResult[1]:
        oGuiElement = cGuiElement(name, SITE_IDENTIFIER, 'showEntries')
        oGuiElement.setSeason(name.split(' ')[-1])
        oGuiElement.setMediaType('season')
        params.setParam('sUrl', link)
        oGui.addFolder(oGuiElement, params, True, total)
    oGui.setView('seasons')
    oGui.setEndOfDirectory()

def showEntries(entryUrl = False, sGui = False):
    oGui = sGui if sGui else cGui()
    params = ParameterHandler()
    if not entryUrl: entryUrl = params.getValue('sUrl')
    isSeason = params.exist('season')
    sHtmlContent = cRequestHandler(entryUrl, ignoreErrors = (sGui is not False)).request()
    pattern = '<h2[^>]*class="entry-title"[^>]*><a[^>]*href="([^"]+)[^>]*rel="bookmark"[^>]*>(.*?)</a></h2>.*?' # link / title
    pattern += '<p><p>(.*?)</p>' # Description
    parser = cParser()
    aResult = parser.parse(sHtmlContent, pattern)
    
    if not aResult[0]:
        if not sGui: oGui.showInfo('steamon','Es wurde kein Eintrag gefunden')
        return
    
    episodePattern = '(.+?)\sStaffel\s([\d]+)\sEpisode\s([\d]+)'
    total = len(aResult[1])
    for sEntryUrl, sName, sDescription in aResult[1]:
        oGuiElement = cGuiElement(sName, SITE_IDENTIFIER, 'showHosters')
        aResult = parser.parse(sName, episodePattern)
        if aResult[0]:
            sTVShowTitle, sSeason, sEpisode = aResult[1][0]
            oGuiElement.setTVShowTitle(sTVShowTitle)
            oGuiElement.setSeason(sSeason)
            oGuiElement.setEpisode(sEpisode)
            oGuiElement.setMediaType('episode')
        else:
            oGuiElement.setMediaType('movie')
        oGuiElement.setDescription(sDescription)
        params.setParam('entryUrl', sEntryUrl)
        oGui.addFolder(oGuiElement, params, False, total)

    if not sGui:
        pattern = '<div[^>]*class="right"><a[^>]*href="([^"]+)"[^>]*>'
        aResult = parser.parse(sHtmlContent, pattern)
        if aResult[0] and aResult[1][0]:
            params.setParam('sUrl', aResult[1][0])
            oGui.addNextPage(SITE_IDENTIFIER, 'showEntries', params)

        oGui.setView('episodes' if isSeason else 'movies')
        oGui.setEndOfDirectory()
        return

def showHosters():
    oParams = ParameterHandler()
    sUrl = oParams.getValue('entryUrl')
    sHtmlContent = cRequestHandler(sUrl).request()
    sPattern = '<a[^>]title=".*?Stream[^>].*?"[^>]href="([^"]+).*?blank">([^"]+)[^>]</a>' # url / hostername
    aResult = cParser().parse(sHtmlContent, sPattern)
    hosters = []
    if aResult[1]:
        for sUrl, sName in aResult[1]:
            hoster = {}
            hoster['link'] = sUrl
            hoster['name'] = sName
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

def _search(oGui, sSearchText):
    if not sSearchText: return
    showEntries(URL_SEARCH % sSearchText.strip(), oGui)
