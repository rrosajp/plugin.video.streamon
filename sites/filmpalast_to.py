# -*- coding: utf-8 -*-
# Reimplimented from LaryLooses plugin.video.filmpalast_to addon
import json
import re

from resources.lib import logger
from resources.lib.gui.gui import cGui
from resources.lib.gui.guiElement import cGuiElement
from resources.lib.handler.ParameterHandler import ParameterHandler
from resources.lib.handler.requestHandler import cRequestHandler
from resources.lib.parser import cParser

SITE_IDENTIFIER = 'filmpalast_to'
SITE_NAME = 'FilmPalast'
SITE_ICON = 'filmpalast.png'

URL_MAIN = 'http://filmpalast.to/'
URL_STREAM = URL_MAIN + 'stream/%d/1'
URL_MOVIES_NEW = URL_MAIN + 'movies/new/'
URL_MOVIES_TOP = URL_MAIN + 'movies/top/'
URL_SHOWS_NEW = URL_MAIN + 'serien/view/'
URL_SEARCH = URL_MAIN + 'search/title/'

def load():
    logger.info("Load %s" % SITE_NAME)
    oGui = cGui()
    oGui.addFolder(cGuiElement('Filme', SITE_IDENTIFIER, 'showMovieMenu'))
    oGui.addFolder(cGuiElement('Serien', SITE_IDENTIFIER, 'showSeriesMenu'))
    oGui.addFolder(cGuiElement('Suche', SITE_IDENTIFIER, 'showSearch'))
    oGui.setEndOfDirectory()


def showMovieMenu():
    oGui = cGui()
    params = ParameterHandler()
    params.setParam('sUrl', URL_MOVIES_NEW)
    oGui.addFolder(cGuiElement('Neue Filme', SITE_IDENTIFIER, 'showEntries'), params)
    params.setParam('sUrl', URL_MOVIES_TOP)
    oGui.addFolder(cGuiElement('Top Filme', SITE_IDENTIFIER, 'showEntries'), params)
    params.setParam('sUrl', URL_MOVIES_NEW)
    oGui.addFolder(cGuiElement('Genre', SITE_IDENTIFIER, 'showGenre'), params)
    params.setParam('sUrl', URL_MOVIES_NEW)
    oGui.addFolder(cGuiElement('A-Z', SITE_IDENTIFIER, 'showAlphaNumeric'), params)
    oGui.setEndOfDirectory()


def showSeriesMenu():
    oGui = cGui()
    params = ParameterHandler()
    params.setParam('sUrl', URL_SHOWS_NEW)
    oGui.addFolder(cGuiElement('Neue Episoden', SITE_IDENTIFIER, 'showEntries'), params)
    params.setParam('sUrl', URL_SHOWS_NEW)
    oGui.addFolder(cGuiElement('A-Z', SITE_IDENTIFIER, 'showAlphaNumeric'), params)
    oGui.setEndOfDirectory()


def showGenre():
    oGui = cGui()
    params = ParameterHandler()
    parser = cParser()

    sHtmlContent = cRequestHandler(params.getValue('sUrl')).request()
    pattern = '<section[^>]*id="genre">(.*?)</section>' # container
    isMatch, sContainer = parser.parseSingleResult(sHtmlContent, pattern)

    if not isMatch: 
        return

    pattern = '<a[^>]*href="([^"]*)">[ ]*([^<]*)</a>' # url / title
    isMatch, aResult = parser.parse(sContainer, pattern)

    if not isMatch: 
        return

    for sUrl, sName in aResult:
        params.setParam('sUrl', __checkUrl(sUrl))
        oGui.addFolder(cGuiElement(sName.strip(), SITE_IDENTIFIER, 'showEntries'), params)
    oGui.setEndOfDirectory()


def showAlphaNumeric():
    oGui = cGui()
    params = ParameterHandler()
    parser = cParser()

    sHtmlContent = cRequestHandler(params.getValue('sUrl')).request()
    pattern = '<section[^>]*id="movietitle">(.*?)</section>' # container
    isMatch, sContainer = parser.parseSingleResult(sHtmlContent, pattern)

    if not isMatch: 
        return

    pattern = '<a[^>]*href="([^"]*)">[ ]*([^<]*)</a>'
    isMatch, aResult = parser.parse(sContainer, pattern)

    if not isMatch: 
        return

    for sUrl, sName in aResult:
        params.setParam('sUrl', __checkUrl(sUrl))
        params.setParam('showEpisodes', 'True')
        oGui.addFolder(cGuiElement(sName, SITE_IDENTIFIER, 'showEntries'), params)
    oGui.setEndOfDirectory()


def showEntries(entryUrl = False, sGui = False):
    oGui = sGui if sGui else cGui()
    params = ParameterHandler()
    if not entryUrl: entryUrl = params.getValue('sUrl')

    isTvshow = True if 'serien/' in entryUrl else False
    showEpisodes = True if params.getValue('showEpisodes') == 'True' else False

    sView = 'movies'
    sMediaType = 'movie'
    if isTvshow and showEpisodes:
        sView = 'tvshows'
        sMediaType = 'tvshow'
    elif isTvshow and not showEpisodes:
        sView = 'episodes'
        sMediaType = 'episode'
    
    sHtmlContent = cRequestHandler(entryUrl, ignoreErrors = (sGui is not False)).request()
    pattern = '<a[^>]*href="([^"]*)"[^>]*title="([^"]*)"[^>]*>[^<]*' # link / title
    pattern +='<img[^>]*src=["\']([^"\']*)["\'][^>]*class="cover-opacity"[^>]*>' # thumbnail
    parser = cParser()
    isMatch, aResult = parser.parse(sHtmlContent, pattern)

    if not isMatch: 
        if not sGui: oGui.showInfo('streamon','Es wurde kein Eintrag gefunden')
        return

    for sUrl, sName, sThumbnail in aResult:
        sFunction = "showSeasons" if isTvshow and showEpisodes else "showHosters"
        sThumbnail = __checkUrl(sThumbnail)

        oGuiElement = cGuiElement(sName, SITE_IDENTIFIER, sFunction)
        oGuiElement.setMediaType(sMediaType)
        oGuiElement.setThumbnail(sThumbnail)
        if isTvshow:
            res = re.search('(.*?) S(\d+)\s?E(\d+)',sName)
            if res:
                oGuiElement.setTVShowTitle(res.group(1))
                if showEpisodes:
                    sName = res.group(1)
                    oGuiElement.setTitle(res.group(1))
                else:
                    oGuiElement.setTitle('%s - Staffel %s / Episode %s' % (res.group(1),int(res.group(2)),int(res.group(3))))
                    oGuiElement.setEpisode(res.group(2))
                    oGuiElement.setSeason(res.group(3))
        
        oParams = ParameterHandler()
        oParams.setParam('Thumbnail', sThumbnail)
        oParams.setParam('sName', sName)
        oParams.setParam('entryUrl', __checkUrl(sUrl))
        oGui.addFolder(oGuiElement, oParams, bIsFolder = (isTvshow and showEpisodes))

    if not sGui:
        pattern = '<a[^>]*class="[^"]*pageing[^"]*"[^>]*href=\'([^\']*)\'[^>]*>[^\d+-]'
        isMatch, sUrl = parser.parseSingleResult(sHtmlContent, pattern)
        if isMatch:
            params.setParam('sUrl', sUrl)
            oGui.addNextPage(SITE_IDENTIFIER, 'showEntries', params)

        oGui.setView(sView)
        oGui.setEndOfDirectory()


def showSeasons():
    oGui = cGui()
    oParams = ParameterHandler()

    sUrl = oParams.getValue('entryUrl')
    sThumbnail = oParams.getValue("Thumbnail")
    sName = oParams.getValue('sName')
    sHtmlContent = cRequestHandler(sUrl).request()

    sPattern = '<a[^>]*class="staffTab"[^>]*data-sid="(\d+)"[^>]*>' # container
    parser = cParser()
    isMatch, aResult = parser.parse(sHtmlContent, sPattern)

    if not isMatch: 
        oGui.showInfo('streamon','Es wurde kein Eintrag gefunden')
        return

    total = len(aResult)
    for iSeason in aResult:
        oGuiElement = cGuiElement("Staffel " + str(iSeason),SITE_IDENTIFIER, 'showEpisodes')
        oGuiElement.setTVShowTitle(sName)
        oGuiElement.setSeason(iSeason)
        oGuiElement.setMediaType('season')
        oGuiElement.setThumbnail(sThumbnail)
        oGui.addFolder(oGuiElement, oParams, iTotal = total)

    oGui.setView('seasons')
    oGui.setEndOfDirectory()


def showEpisodes():
    oGui = cGui()
    oParams = ParameterHandler()

    sUrl = oParams.getValue('entryUrl')
    sThumbnail = oParams.getValue("Thumbnail")
    sSeason = oParams.getValue('season')
    sShowName = oParams.getValue('TVShowTitle')
    sHtmlContent = cRequestHandler(sUrl).request()
    
    parser = cParser()
    sPattern = '<div[^>]*class="staffelWrapperLoop[^"]*"[^>]*data-sid="%s">(.*?)</div></li></ul></div>' % sSeason
    isMatch, sContainer = parser.parseSingleResult(sHtmlContent, sPattern)

    if not isMatch: 
        oGui.showInfo('streamon','Es wurde kein Eintrag gefunden')
        return

    sPattern = '<a[^>]*href="([^"]*)"[^>]*class="getStaffelStream"[^>]*>.*?<small>([^>]*?)</small>'
    parser = cParser()
    isMatch, aResult = parser.parse(sContainer, sPattern)
    
    total = len(aResult)
    for sEpisodeUrl, sTitle in aResult:
        oGuiElement = cGuiElement(sTitle, SITE_IDENTIFIER, "showHosters")
        oGuiElement.setThumbnail(sThumbnail)
        oGuiElement.setTVShowTitle(sShowName)
        #oGuiElement.setEpisode(sEpisodeNr)
        oGuiElement.setSeason(sSeason)
        oGuiElement.setMediaType('episode')
        oParams.setParam('entryUrl', sEpisodeUrl)
        oGui.addFolder(oGuiElement, oParams, bIsFolder=False, iTotal=total)

    oGui.setView('episodes')
    oGui.setEndOfDirectory()


def showHosters():
    params = ParameterHandler()
    oRequest = cRequestHandler(params.getValue('entryUrl'))
    sHtmlContent = oRequest.request()

    pattern = 'class="hostName"[^>]*>([^<>]+)(.+?)currentStreamLinks'
    aResult = cParser().parse(sHtmlContent, pattern)

    if cParser().parse(aResult[1][0][1], 'small')[0]:
        linkPattern = 'data-id="(\d*).*?small>(.*?)<'

        aResults = []
        for host in aResult[1]:
            aHost = []
            aHost.append(host[0])
            aHost.append(cParser().parse(host[1], linkPattern))
            aResults.append(aHost)

        if not aResults[0]:
            return

        hosters = []
        for aHosters in aResults:
            for parts in aHosters[1][1]:
                hoster = dict()
                if not parts[0]: continue
                hoster['link'] = parts[0]
                hoster['name'] = aHosters[0]
                if hoster['name'].lower() == "openload hd":
                    hoster['name'] = "OpenLoad"
                hoster['displayedName'] = aHosters[0] + ' - ' + parts[1]
                hosters.append(hoster)

    else:
        pattern = '<p[^>]*class="hostName"[^>]*>([^<>]+)</p>.*?'
        pattern += '<a[^>]*class="[^"]*stream-src[^"]*"[^>]*data-id="([^"]+)"[^>]*>'
        aResult = cParser().parse(sHtmlContent, pattern)
        hosters = []

        for sHost, iId in aResult[1]:
            hoster = dict()
            if not iId: continue
            hoster['link'] = iId
            hoster['name'] = sHost
            if hoster['name'].lower() == "openload hd":
                hoster['name'] = "OpenLoad"
            hoster['displayedName'] = sHost
            hosters.append(hoster)

    if hosters:
        hosters.append('getHosterUrl')
    return hosters


def getHosterUrl(sUrl = False):
    oParams = ParameterHandler()
    if not sUrl:
        sUrl = oParams.getValue('url')
    results = []
    result = {}
    result['streamUrl'] = __getSource(sUrl)
    result['resolved'] = False
    results.append(result)
    return results


def showSearch():
    sSearchText = cGui().showKeyBoard()
    if not sSearchText: return
    _search(False, sSearchText)


def _search(oGui, sSearchText):
    if not sSearchText: return
    showEntries(URL_SEARCH + sSearchText, oGui)


def __checkUrl(url):
    url = url.replace('https:', 'http:')
    return url if 'http:' in url else URL_MAIN + url


def __getSource(id):
    oRequest = cRequestHandler(URL_STREAM % int(id))
    oRequest.addParameters('streamID', id)
    oRequest.addHeaderEntry('Origin', URL_MAIN)
    oRequest.addHeaderEntry('Host', 'filmpalast.to')
    oRequest.addHeaderEntry('X-Requested-With', 'XMLHttpRequest')
    sJson = oRequest.request()
    if sJson:
        data = json.loads(sJson)
        if 'error' in data and int(data['error']) == 0 and 'url' in data:
            return data['url']
        if 'msg' in data:
            logger.info("Get link failed: '%s'" % data['msg'])
    return False
