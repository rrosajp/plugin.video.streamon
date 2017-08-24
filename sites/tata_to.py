# -*- coding: utf-8 -*-
import base64, json, re, common
from resources.lib import logger
from resources.lib.cCFScrape import cCFScrape
from resources.lib.gui.gui import cGui
from resources.lib.gui.guiElement import cGuiElement
from resources.lib.handler.ParameterHandler import ParameterHandler
from resources.lib.handler.requestHandler import cRequestHandler
from resources.lib.parser import cParser

SITE_IDENTIFIER = 'tata_to'
SITE_NAME = 'Tata'
SITE_ICON = 'tata.png'

URL_MAIN = 'http://www.tata.to/'
URL_MOVIES = URL_MAIN + 'filme'
URL_SHOWS = URL_MAIN + 'tv'
URL_SEARCH = URL_MAIN + 'filme?&suche=%s&type=alle'

URL_PARMS_ORDER_ALL = '?&order=alle'
URL_PARMS_ORDER_ID = '?&order=neueste'
URL_PARMS_ORDER_MOSTVIEWED = '?&order=ansichten'
URL_PARMS_ORDER_MOSTRATED = '?&order=ratingen'
URL_PARMS_ORDER_TOPIMDB = '?&order=imdb'
URL_PARMS_ORDER_RELEASEDATE = '?&order=veröffentlichung'

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
    params.setParam('valueType', 'land')
    oGui.addFolder(cGuiElement('Land', SITE_IDENTIFIER, 'showValueList'), params)
    params.setParam('sUrl', baseURL)
    params.setParam('valueType', 'veröffentlichung')
    oGui.addFolder(cGuiElement('Veröffentlichung', SITE_IDENTIFIER, 'showValueList'), params)
    oGui.setEndOfDirectory()


def showValueList():
    oGui = cGui()
    params = ParameterHandler()
    entryUrl = params.getValue('sUrl')
    valueType = params.getValue('valueType')
    sHtmlContent = _getRequestHandler(entryUrl).request()
    pattern = '<input[^>]*name="%s[[]]"[^>]*value="(.*?)"[^>]*>(.*?)</' % valueType
    isMatch, aResult = cParser.parse(sHtmlContent, pattern)

    if not isMatch:
        return

    for sID, sName in aResult:
        params.setParam('sUrl', entryUrl + '?&' + valueType + '[]=' + sID)
        oGui.addFolder(cGuiElement(sName.strip(), SITE_IDENTIFIER, 'showEntries'), params)
    oGui.setEndOfDirectory()


def showEntries(entryUrl=False, sGui=False):
    oGui = sGui if sGui else cGui()
    params = ParameterHandler()
    if not entryUrl: entryUrl = params.getValue('sUrl')
    oRequest = _getRequestHandler(entryUrl, ignoreErrors=(sGui is not False))
    sHtmlContent = oRequest.request()
    pattern = '<div[^>]*class="ml-item-content"[^>]*>.*?'  # start element
    pattern += '<a[^>]*href="([^"]*)"[^>]*>.*?'  # url
    pattern += '(?:<span[^>]*class="quality-label (\w+)"[^>]*>.*?)?'  # quality
    pattern += '<img[^>]*src="([^"]*)"[^>]*>.*?'  # thumbnail
    pattern += '(?:<span[^>]*class="season-label"[^>]*>.*?<span[^>]*class="el-num"[^>]*>\s+(\d+)\s+</span>.*?)?'  # season
    pattern += '</a>.*?'  # end link
    pattern += '<h\d+>(.*?)</h\d+>.*?'  # title
    pattern += '(?:<span[^>]*class="[^"]*glyphicon-time[^"]*"[^>]*></span>[^\d]*(\d+) min[^<]*</li>.*?)?'  # duration
    pattern += '(?:<span[^>]*class="[^"]*glyphicon-calendar[^"]*"[^>]*></span>(.*?)</li>.*?)'  # year
    pattern += '(?:<p>IMDb:</p>([^<]*)</li>.*?)'  # imdb
    pattern += '(?:<div[^>]*class="caption-description"[^>]*>(.*?)</div>.*?)'  # description
    isMatch, aResult = cParser.parse(sHtmlContent, pattern)

    if not isMatch:
        if not sGui: oGui.showInfo('streamon', 'Es wurde kein Eintrag gefunden')
        return

    total = len(aResult)
    for sUrl, sQuality, sThumbnail, sSeason, sName, sDuration, sYear, sImdb, sDesc in aResult:
        isTvshow = True if sSeason else False
        sName = sName.strip()
        sThumbnail = cCFScrape.createUrl(sThumbnail, oRequest)
        oGuiElement = cGuiElement(sName, SITE_IDENTIFIER, 'showHosters')
        res = re.search('(.*?)\s(?:staf+el|s)\s*(\d+)', sName, re.I)
        if res:
            sName = res.group(1)
            sSeason = res.group(2)
            isTvshow = True
            oGuiElement.setTVShowTitle(sName)
            oGuiElement.setFunction('showEpisodes')
            oGuiElement.setTitle('%s - Staffel %s' % (sName, sSeason))
            params.setParam('sSeason', sSeason)
        oGuiElement.setYear(sYear)
        oGuiElement.setThumbnail(sThumbnail)
        oGuiElement.setMediaType('tvshow' if isTvshow else 'movie')
        oGuiElement.setDescription(sDesc)
        oGuiElement.addItemValue('rating', sImdb)
        if sDuration:
            oGuiElement.addItemValue('duration', int(sDuration) * 60)
        params.setParam('sUrl', sUrl)
        params.setParam('sName', sName)
        params.setParam('sThumbnail', sThumbnail)
        oGui.addFolder(oGuiElement, params, isTvshow, total)

    if not sGui:
        sPattern = '<li[^>]*class="active".*?<a[^>]*href="([^"]*)"[^>]*>\d+</a>'
        isMatch, sPageUrl = cParser.parseSingleResult(sHtmlContent, sPattern)
        if isMatch:
            params.setParam('sUrl', sPageUrl)
            oGui.addNextPage(SITE_IDENTIFIER, 'showEntries', params)
        oGui.setView('tvshows' if '/tv' in entryUrl else 'movies')
        oGui.setEndOfDirectory()


def showEpisodes():
    oGui = cGui()
    params = ParameterHandler()
    entryUrl = params.getValue('sUrl')
    sTVShowTitle = params.getValue('TVShowTitle')
    sThumbnail = params.getValue('sThumbnail')
    sSeason = params.getValue('sSeason')
    sHtmlContent = _getRequestHandler(entryUrl).request()
    isMatch, aResult = cParser.parse(sHtmlContent, '<li[^>].*?<a[^>]*href="([^"]*)"[^>]*>(\d+)</a>')

    if not isMatch:
        oGui.showInfo('streamon', 'Es wurde kein Eintrag gefunden')
        return

    total = len(aResult)
    for sUrl, iEpisode in aResult:
        sName = 'Folge ' + str(iEpisode)
        oGuiElement = cGuiElement(sName, SITE_IDENTIFIER, 'showHosters')
        oGuiElement.setMediaType('episode')
        oGuiElement.setTVShowTitle(sTVShowTitle)
        oGuiElement.setSeason(sSeason)
        oGuiElement.setEpisode(iEpisode)
        oGuiElement.setThumbnail(sThumbnail)
        params.setParam('sUrl', sUrl)
        params.setParam('sName', sName)
        oGui.addFolder(oGuiElement, params, False, total)
    oGui.setView('episodes')
    oGui.setEndOfDirectory()

def showHosters(sUrl=False):
    params = ParameterHandler()
    sUrl = sUrl if sUrl else params.getValue('sUrl')
    sHtmlContent = _getRequestHandler(sUrl).request()
    pattern = "<div[^>]*data-url='([^']*)'[^>]*>"
    isMatch, sStreamUrl = cParser.parseSingleResult(sHtmlContent, pattern)
    hosters = []
    if isMatch:
        oRequestHandler = _getRequestHandler(sStreamUrl)
        oRequestHandler.addHeaderEntry('Referer', sUrl)
        sJson = oRequestHandler.request()

        if not sJson:
            return []
        data = json.loads(base64.decodestring(sJson))
        if "playinfo" in data:
            if isinstance(data["playinfo"], list):
                for urlData in data["playinfo"]:
                    hoster = dict()
                    hoster['link'] = urlData["link_mp4"]
                    hoster['name'] = urlData["quality"]
                    if urlData["quality"] in QUALITY_ENUM:
                        hoster['quality'] = QUALITY_ENUM[urlData["quality"]]
                    hoster['resolveable'] = True
                    hosters.append(hoster)
            else:
                hoster = dict()
                hoster['link'] = data["playinfo"]
                hoster['name'] = SITE_NAME
                hoster['resolveable'] = True
                hosters.append(hoster)
    if hosters:
        hosters.append('play')
    return hosters


def play(sUrl=False):
    oParams = ParameterHandler()
    if not sUrl: sUrl = oParams.getValue('url')
    return [{'streamUrl': sUrl.replace('embed.html', 'index.m3u8') + '|User-Agent=' + common.FF_USER_AGENT, 'resolved': True}]


def _getRequestHandler(sUrl, ignoreErrors=False):
    sUrl = sUrl.replace('https:', 'http:').replace('\/', '/')
    oRequest = cRequestHandler(sUrl, ignoreErrors=ignoreErrors)
    return oRequest


def showSearch():
    oGui = cGui()
    sSearchText = oGui.showKeyBoard()
    if not sSearchText: return
    _search(False, sSearchText)
    oGui.setEndOfDirectory()


def _search(oGui, sSearchText):
    if not sSearchText: return
    showEntries(URL_SEARCH % sSearchText.strip(), oGui)
