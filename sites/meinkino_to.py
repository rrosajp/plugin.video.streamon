# -*- coding: utf-8 -*-
from resources.lib.gui.gui import cGui
from resources.lib.gui.guiElement import cGuiElement
from resources.lib.handler.requestHandler import cRequestHandler
from resources.lib.parser import cParser
from resources.lib import logger
from resources.lib.handler.ParameterHandler import ParameterHandler
from urlparse import urlparse
import json, re

SITE_IDENTIFIER = 'meinkino_to'
SITE_NAME = 'MeinKino'
SITE_ICON = 'meinkino.png'

URL_MAIN = 'http://meinkino.to/'
URL_MOVIES = URL_MAIN + 'filter?type=filme'
URL_SHOWS = URL_MAIN + 'filter?type=tv'
URL_SEARCH = URL_MAIN + 'filter?suche=%s&type=alle'
URL_GET_URL = URL_MAIN + 'geturl/'

URL_PARMS_ORDER_ID = '&order=neueste'
URL_PARMS_ORDER_MOSTVIEWED = '&order=ansichten'
URL_PARMS_ORDER_MOSTRATED = '&order=ratingen'
URL_PARMS_ORDER_TOPIMDB = '&order=imdb'
URL_PARMS_ORDER_RELEASEDATE = '&order=veröffentlichung'


QUALITY_ENUM = {'240': 0, '360': 1, '480': 2, '720': 3, '1080': 4}

def load():
   logger.info("Load %s" % SITE_NAME)
   
   oGui = cGui()
   params = ParameterHandler()

   params.setParam('sUrl', URL_MOVIES)
   oGui.addFolder(cGuiElement('Filme', SITE_IDENTIFIER, 'showContentMenu'), params)
   params.setParam('sUrl', URL_SHOWS)
   oGui.addFolder(cGuiElement('Serien', SITE_IDENTIFIER, 'showContentMenu'), params)
   oGui.addFolder(cGuiElement('Suche', SITE_IDENTIFIER, 'showSearch'))
   oGui.setEndOfDirectory()


def showContentMenu():
    oGui = cGui()
    params = ParameterHandler()
    baseURL = params.getValue('sUrl')

    params.setParam('sUrl', baseURL + URL_PARMS_ORDER_ID)
    oGui.addFolder(cGuiElement('Neuste', SITE_IDENTIFIER, 'showEntries'), params)
    params.setParam('sUrl', baseURL + URL_PARMS_ORDER_MOSTVIEWED)
    oGui.addFolder(cGuiElement('Am häufigsten gesehen', SITE_IDENTIFIER, 'showEntries'), params)
    params.setParam('sUrl', baseURL + URL_PARMS_ORDER_MOSTRATED)
    oGui.addFolder(cGuiElement('Am meisten bewertet', SITE_IDENTIFIER, 'showEntries'), params)
    params.setParam('sUrl', baseURL + URL_PARMS_ORDER_TOPIMDB)
    oGui.addFolder(cGuiElement('Top IMDb', SITE_IDENTIFIER, 'showEntries'), params)
    params.setParam('sUrl', baseURL + URL_PARMS_ORDER_RELEASEDATE)
    oGui.addFolder(cGuiElement('Veröffentlichungsdatum', SITE_IDENTIFIER, 'showEntries'), params)
    params.setParam('sUrl', baseURL)
    params.setParam('valueType', 'genre')
    oGui.addFolder(cGuiElement('Genre', SITE_IDENTIFIER, 'showValueList'), params)
    params.setParam('sUrl', baseURL)
    params.setParam('valueType', 'staat')
    oGui.addFolder(cGuiElement('Land', SITE_IDENTIFIER, 'showValueList'), params)
    params.setParam('sUrl', baseURL)
    params.setParam('valueType', 'veroeffentlichung')
    oGui.addFolder(cGuiElement('Veröffentlichung', SITE_IDENTIFIER, 'showValueList'), params)

    oGui.setEndOfDirectory()


def showValueList():
    oGui = cGui()
    params = ParameterHandler()
    entryUrl = params.getValue('sUrl')
    valueType = params.getValue('valueType')

    sHtmlContent = cRequestHandler(entryUrl).request()
    sPattern = '<select[^>]*name="%s\[\]"[^>]*>(.*?)</select>' % valueType # container#
    logger.info("sPattern %s" % sPattern)
    isMatch, strContainer = cParser.parseSingleResult(sHtmlContent, sPattern)

    if isMatch: 
        sPattern = '<option[^>]*value="(.*?)"[^>]*>(.*?)</option>' # container
        isMatch, aResult = cParser.parse(strContainer, sPattern)

    if not isMatch:
        return

    for sID, sName in aResult:
        params.setParam('sUrl',entryUrl + '&' + valueType + '[]=' + sID)
        oGui.addFolder(cGuiElement(sName.strip(), SITE_IDENTIFIER, 'showEntries'), params)
    oGui.setEndOfDirectory()


def showEntries(entryUrl = False, sGui = False):
    oGui = sGui if sGui else cGui()
    params = ParameterHandler()
    if not entryUrl: entryUrl = params.getValue('sUrl')
    sHtmlContent = cRequestHandler(entryUrl, ignoreErrors = (sGui is not False)).request()
    pattern = '<a[^>]*href="([^"]+)id([^"]+)"[^>]*class="ml-name">(.*?)<\/a.*?img*[^>]src="([^"]+).*?</a> ,([^<]+)'
    isMatch, aResult = cParser.parse(sHtmlContent, pattern)

    if not isMatch:
        if not sGui: oGui.showInfo('steamon','Es wurde kein Eintrag gefunden')
        return

    total = len (aResult)
    for sUrl, sId, sName, sThumbnail, sYear in aResult:
        isTvshow = True if "staffel" in sUrl else False
        oGuiElement = cGuiElement(sName, SITE_IDENTIFIER, "showHosters")
        oGuiElement.setThumbnail(sThumbnail)
        oGuiElement.setYear(sYear)
        oGuiElement.setMediaType('tvshow' if isTvshow else 'movie')

        if isTvshow:
            res = re.search('(.*?)\s(?:staf+el|s)\s*(\d+)', sName, re.I)
            if res:
                sName = res.group(1)
            logger.info(sName)
            oGuiElement.setTVShowTitle(sName)
            oGuiElement.setTitle('%s - Staffel %s' % (sName, res.group(2)))
            params.setParam('sSeason', res.group(2))

        params.setParam('entryUrl', sUrl + 'id' + sId if isTvshow else URL_GET_URL + sId)
        params.setParam('sThumbnail', sThumbnail)
        params.setParam('isTvshow', isTvshow)
        oGui.addFolder(oGuiElement, params, isTvshow, total)

    if not sGui:
        isMatchNextPage, sNextUrl = cParser.parseSingleResult(sHtmlContent, '<link[^>]*rel="next"[^>]*href="([^"]+)')
        if isMatchNextPage:
            params.setParam('sUrl', sNextUrl)
            oGui.addNextPage(SITE_IDENTIFIER, 'showEntries', params)

        oGui.setView('tvshows' if 'staffel' in entryUrl else 'movies')
        oGui.setEndOfDirectory()

def showHosters():
    params = ParameterHandler()
    entryUrl = params.getValue('entryUrl')
    isTvshowEntry = params.getValue('isTvshow')

    if isTvshowEntry == 'True':
        sHtmlContent = cRequestHandler(entryUrl).request()
        isMatch, aResult = cParser.parse(sHtmlContent, 'stream-id([^"]+)">([^<]+)')
        if isMatch:
            showEpisodes(aResult, params)
    else:
        return getHosters(entryUrl)

def showEpisodes(aResult, params):
    oGui = cGui()

    sTVShowTitle = params.getValue('TVShowTitle')
    sThumbnail = params.getValue('sThumbnail')
    sSeason = params.getValue('sSeason')

    total = len (aResult)
    for sId, iEpisode in aResult:
        sName = 'Folge ' + str(iEpisode)
        oGuiElement = cGuiElement(sName, SITE_IDENTIFIER, 'getHosters')
        oGuiElement.setMediaType('episode')
        oGuiElement.setTVShowTitle(sTVShowTitle)
        oGuiElement.setSeason(sSeason)
        oGuiElement.setEpisode(iEpisode)
        oGuiElement.setThumbnail(sThumbnail)
        params.setParam('entryUrl', URL_GET_URL + sId)
        params.setParam('sName', sName)
        oGui.addFolder(oGuiElement, params, False, total)

    oGui.setView('episodes')
    oGui.setEndOfDirectory()

def getHosters(sUrl=False):
    params = ParameterHandler()
    sUrl = sUrl if sUrl else params.getValue('entryUrl')
    oRequest = cRequestHandler(sUrl)
    oRequest.addHeaderEntry("X-Requested-With","XMLHttpRequest")
    oRequest.setRequestType(1)
    sJson = oRequest.request()
    
    if not sJson:
        return []

    hosters = []
    data = json.loads(sJson)

    # add main link
    if isinstance(data["url"], list):
        for urlData in data["url"]:
            hosters.append(__getHosterFromList(urlData))
    else:
        hosters.append(__getHosterEntry(data["url"]))

    # add alternative links
    if 'alternative' in data:
        for urlData in data["alternative"]:
            hosterData = data["alternative"][urlData]
            if isinstance(hosterData, list):
                for urlHosterData in hosterData:
                    hosters.append(__getHosterFromList(urlHosterData))
            else:
                hosters.append(__getHosterEntry(hosterData, urlData))

    if hosters:
        hosters.append('getHosterUrl')
    return hosters

def __getHosterFromList(urlData, hostername=False):
    if not hostername:
        parsed_url = urlparse(urlData["link_mp4"])
        hostername = parsed_url.netloc

    hoster = dict()
    hoster['link'] = urlData["link_mp4"]
    hoster['name'] = hostername
    if urlData["quality"] in QUALITY_ENUM:
        hoster['quality'] = QUALITY_ENUM[urlData["quality"]]
    hoster['displayedName'] = '%sP (%s)' % (urlData["quality"], hostername)
    return hoster

def __getHosterEntry(sUrl, hostername=False):
    if not hostername:
        parsed_url = urlparse(sUrl)
        hostername = parsed_url.netloc

    hoster = dict()
    hoster['link'] = sUrl
    hoster['name'] = hostername
    hoster['displayedName'] = hostername.title()
    return hoster

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