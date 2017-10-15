# -*- coding: utf-8 -*-

import json
import threading
from resources.lib.gui.gui import cGui
from resources.lib.gui.guiElement import cGuiElement
from resources.lib.handler.requestHandler import cRequestHandler
from resources.lib.parser import cParser
from resources.lib import logger
from resources.lib.handler.ParameterHandler import ParameterHandler

SITE_IDENTIFIER = 'video4k_to'
SITE_NAME = 'Video4k'
SITE_ICON = 'video4k.png'

URL_REQUEST = 'http://video4k.to/request'

DEFAULT_REQUEST_PARAMS = dict(sEcho=1, iColumns=1, sColumns="", iDisplayStart=0, iDisplayLength=50, mDataProp_0=0,
                              mDataProp_1=1, mDataProp_2=2, mDataProp_3=3, mDataProp_4=4, sSearch="", bRegex="false",
                              sSearch_0="", bRegex_0="false", bSearchable_0="true", sSearch_1="", bRegex_1="false",
                              bSearchable_1="true", sSearch_2=" ", bRegex_2="false", bSearchable_2="true",
                              sSearch_3="", bRegex_3="false", bSearchable_3="true", sSearch_4="", bRegex_4="false",
                              bSearchable_4="true", iSortCol_0="0", sSortDir_0="asc", iSortingCols=1,
                              bSortable_0="false", bSortable_1="true", bSortable_2="false", bSortable_3="false",
                              bSortable_4="true", type="movies", filter="")

QUALITY_ENUM = {0:'LOW', 1:'OKAY', 2:'GOOD'}

def load():
    logger.info("Load %s" % SITE_NAME)
    oGui = cGui()
    params = ParameterHandler()

    params.setParam('type', 'movies')
    oGui.addFolder(cGuiElement('Alle Filme', SITE_IDENTIFIER, 'showEntries'), params)
    params.setParam('type', 'cinema')
    oGui.addFolder(cGuiElement('Kino Filme', SITE_IDENTIFIER, 'showEntries'), params)
    params.setParam('type', 'series')
    oGui.addFolder(cGuiElement('Serien', SITE_IDENTIFIER, 'showEntries'), params)
    oGui.addFolder(cGuiElement('Suche', SITE_IDENTIFIER, 'showSearch'))
    oGui.setEndOfDirectory()

def showEntries(sGui = False, sSearchText = None):
    oGui = sGui if sGui else cGui()
    oParams = ParameterHandler()

    oRequest = cRequestHandler(URL_REQUEST, ignoreErrors = (sGui is not False))
    for key in DEFAULT_REQUEST_PARAMS:
        oRequest.addParameters(key, DEFAULT_REQUEST_PARAMS[key])

    oRequest.addParameters('type', oParams.getValue('type'))

    if oParams.getValue('iDisplayStart'):
        oRequest.addParameters('iDisplayStart', oParams.getValue('iDisplayStart'))

    if sSearchText:
        oRequest.addParameters('sSearch', sSearchText)
        oRequest.addParameters('type', '')
    oRequest.setRequestType(1)
    sHtmlContent = oRequest.request()

    isMatch, aResult = cParser().parse(sHtmlContent, '#tt(\d*).*?">(.*?)<')

    if not isMatch:
        if not sGui: oGui.showInfo('steamon','Es wurde kein Eintrag gefunden')
        return

    threads = []
    for mId, sName in aResult:
        t = threading.Thread(target=_addEntry, args=(oGui, sName, mId), name=sName)
        threads += [t]
        t.start()
    for count, t in enumerate(threads):
        t.join()

    if not sGui:
        maxEntries = json.loads(sHtmlContent).items()[3][1]
        if maxEntries > int(oParams.getValue('iDisplayStart')) and maxEntries > 50:
            oParams.setParam('iDisplayStart', int(oParams.getValue('iDisplayStart')) + 50)
            oGui.addNextPage(SITE_IDENTIFIER, 'showEntries', oParams)

        oGui.setEndOfDirectory()

def _addEntry(oGui, sName, mId):
    oParams = ParameterHandler()
    oParams.setParam('id', mId)
    info = loadInformation(mId)

    isFolder = False

    if info:
        isFolder = info[4] is not False
        oGuiElement = cGuiElement(sName, SITE_IDENTIFIER, 'showSeasons' if info[4] else 'showHosters')
        oGuiElement.setTitle(info[5])
        oGuiElement.setDescription(info[0])
        oGuiElement.setLanguage(info[3])
        oGuiElement.setThumbnail(info[1])
        oGuiElement.setYear(info[2])
        oParams.setParam('lang', info[3])
        oGui.addFolder(oGuiElement, oParams, bIsFolder=isFolder, isHoster=not isFolder)

def showSeasons():
    oGui = cGui()
    oParams = ParameterHandler()

    info = loadInformation(oParams.getValue('id'))

    if info and info[4]is not False:
        total = len (info[4])
        for sSeason in info[4]:
            oGuiElement = cGuiElement('Staffel ' + sSeason, SITE_IDENTIFIER, 'showEpisode')
            oGuiElement.setTVShowTitle(info[5])
            oGuiElement.setSeason(sSeason)
            oGuiElement.setMediaType('season')
            oGuiElement.setDescription(info[0])
            oGuiElement.setLanguage(info[3])
            oGuiElement.setThumbnail(info[1])
            oGuiElement.setYear(info[2])
            oParams.setParam('season', sSeason)
            oGui.addFolder(oGuiElement, oParams, bIsFolder=True, iTotal=total)

    oGui.setView('seasons')
    oGui.setEndOfDirectory()

def showEpisode():
    oGui = cGui()
    oParams = ParameterHandler()
    sSeason = oParams.getValue('season')
    info = loadInformation(oParams.getValue('id'))

    if info and info[4]is not False:
        total = len (info[4][sSeason])
        for sEpisode in info[4][sSeason]:
            oGuiElement = cGuiElement('Episode ' + str(sEpisode), SITE_IDENTIFIER, 'showHosters')
            oGuiElement.setTVShowTitle(info[5])
            oGuiElement.setSeason(sSeason)
            oGuiElement.setEpisode(sEpisode)
            oGuiElement.setMediaType('episode')
            oGuiElement.setDescription(info[0])
            oGuiElement.setLanguage(info[3])
            oGuiElement.setThumbnail(info[1])
            oGuiElement.setYear(info[2])
            oParams.setParam('episode', sEpisode)
            oGui.addFolder(oGuiElement, oParams, bIsFolder=False, iTotal=total)

    oGui.setView('episodes')
    oGui.setEndOfDirectory()


def loadInformation(mID = None):

    if not mID:
        return

    oRequest = cRequestHandler(URL_REQUEST)

    oRequest.addParameters('mID', mID)
    oRequest.setRequestType(1)

    sHtmlContent = oRequest.request()

    if not sHtmlContent:
        return

    jContent = json.loads(sHtmlContent)
    
    plot = jContent[0]['plot']
    year = jContent[0]['year']
    name = jContent[0]['name']
    cover = '' if jContent[0]['cover'] == '//static.video4k.to/covers/' else ('http:' + jContent[0]['cover'])
    language = jContent[0]['languages'][0]['symbol'] if jContent[0]['languages'] else '' # later fix this because if there are two lang we should pick the correct one
    seasons = jContent[0]['seasons'] if 'seasons' in jContent[0] else False

    return [plot, cover, year, language, seasons, name]

def showHosters():
    oParams = ParameterHandler()

    oRequest = cRequestHandler(URL_REQUEST)
    oRequest.addParameters('mID', oParams.getValue('id'))
    oRequest.addParameters('raw', 'true')
    oRequest.addParameters('language', oParams.getValue('lang'))
    if oParams.getValue('season'):
        oRequest.addParameters('season', oParams.getValue('season'))
        oRequest.addParameters('episode', oParams.getValue('episode'))
    sHtmlContent = oRequest.request()

    if not sHtmlContent:
        return []

    jContent = json.loads(sHtmlContent)

    if not jContent[1]:
        return []

    hosters = []
    for ohoster in jContent[1].items():
        sName = ohoster[1]['name']

        for links in ohoster[1]['links']:
            hoster = dict()
            hoster['link'] = links['URL']
            hoster['name'] = sName
            if links['quality'] in QUALITY_ENUM:
                hoster['displayedName'] = '[%s] %s' % (QUALITY_ENUM[links['quality']], sName)
            hoster['quality'] = links['quality']
            hosters.append(hoster)

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
    showEntries(oGui, sSearchText)
