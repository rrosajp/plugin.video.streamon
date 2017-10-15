# -*- coding: utf-8 -*-
import re

from resources.lib import logger
from resources.lib.gui.gui import cGui
from resources.lib.gui.guiElement import cGuiElement
from resources.lib.handler.ParameterHandler import ParameterHandler
from resources.lib.handler.requestHandler import cRequestHandler
from resources.lib.parser import cParser

SITE_IDENTIFIER = '1kino_in'
SITE_NAME = '1Kino'
SITE_ICON = '1kino.png'

URL_MAIN = 'http://1kino.in/'
URL_KINO = 'kinofilme'
URL_FILME = 'filme'
URL_SEARCH = URL_MAIN + 'include/live.php?keyword=%s&nonce='

URL_FETCH = URL_MAIN + 'include/fetch.php'
URL_LOAD = URL_MAIN + 'include/load.php'


def load():
    logger.info("Load %s" % SITE_NAME)
    oGui = cGui()
    params = ParameterHandler()
    params.setParam('Value', URL_KINO)
    params.setParam('Page', '1')
    oGui.addFolder(cGuiElement('Kinofilme', SITE_IDENTIFIER, 'showEntries'), params)
    params.setParam('Value', URL_FILME)
    params.setParam('Page', '1')
    oGui.addFolder(cGuiElement('Filme', SITE_IDENTIFIER, 'showEntries'), params)
    oGui.addFolder(cGuiElement('Genre', SITE_IDENTIFIER, 'showGenre'), params)
    oGui.addFolder(cGuiElement('Suche', SITE_IDENTIFIER, 'showSearch'))
    oGui.setEndOfDirectory()


def showGenre():
    oGui = cGui()
    params = ParameterHandler()
    sHtmlContent = cRequestHandler(URL_MAIN).request()
    sPattern = 'Kategorie: ([^"]+)".*?href="([^"]+)">'
    isMatch, aResult = cParser.parse(sHtmlContent, sPattern)

    if not isMatch:
        oGui.showInfo('steamon', 'Es wurde kein Eintrag gefunden')
        return

    for sName, sUrl in aResult:
        params.setParam('Value', sName)
        oGui.addFolder(cGuiElement(sName, SITE_IDENTIFIER, 'showEntries'), params)
    oGui.setEndOfDirectory()


def showEntries(Value=False, Page=False, sGui=False):
    oGui = sGui if sGui else cGui()
    params = ParameterHandler()
    if not Value: Value = params.getValue('Value')
    if not Page: Page = params.getValue('Page')
    oRequest = cRequestHandler(URL_FETCH)
    oRequest.addParameters('page', Page)
    oRequest.addParameters('type', 'cat')
    oRequest.addParameters('wq', Value)
    oRequest.setRequestType(1)
    sHtmlContent = oRequest.request()

    sPattern = '<img[^>]*data-src="([^"]+).*?<div[^>]*class="ui-tile"><a[^>]*href="([^"]+).*?">([^(]+)[^>]([^)]+).*?<div[^>]*class="ui-des">([^<]+)'
    isMatch, aResult = cParser.parse(sHtmlContent, sPattern)

    if not isMatch:
        if not sGui: oGui.showInfo('steamon', 'Es wurde kein Eintrag gefunden')
        return

    total = len(aResult)
    for sThumbnail, sUrl, sName, sYear, sDesc in aResult:
        oGuiElement = cGuiElement(sName.strip(), SITE_IDENTIFIER, 'showHosters')
        oGuiElement.setThumbnail(URL_MAIN + sThumbnail)
        oGuiElement.setDescription(sDesc)
        oGuiElement.setYear(sYear)
        oGuiElement.setMediaType('movie')
        params.setParam('entryUrl', URL_MAIN + sUrl)
        params.setParam('sName', sName)
        oGui.addFolder(oGuiElement, params, False, total)

    if not sGui:
        Page = params.getValue('Page')
        Page = int(Page) + int(1)
        params.setParam('Page', Page)
        oGui.addNextPage(SITE_IDENTIFIER, 'showEntries', params)

        oGui.setView('movies')
        oGui.setEndOfDirectory()


def showHosters():
    params = ParameterHandler()
    sUrl = params.getValue('entryUrl')
    sHtmlContent = cRequestHandler(sUrl).request()

    sPattern = '<a[^>]*href="#streams"[^>]*data-mirror="([^"]+)"[^>]*data-host="([^"]+)".*?">([^"]+)</a>'
    isMatch, aResult = cParser.parse(sHtmlContent, sPattern)

    if not isMatch:
        return []
    pid = re.findall('t="(\w+)"[^>]*i="/include/load.php"', sHtmlContent)[0]
    hosters = []
    for sMirror, sHost, sName in aResult:
        oRequest = cRequestHandler(URL_LOAD)
        oRequest.addParameters('ceck', 'sk')
        oRequest.addParameters('host', sHost)
        oRequest.addParameters('mirror', sMirror)
        oRequest.addParameters('pid', pid)
        oRequest.setRequestType(1)
        sHtmlContent = oRequest.request()
        sPattern = '<iframe src="([^"]+)'
        isMatch, aResult = cParser.parse(sHtmlContent, sPattern)
        if not isMatch:
            sPattern = '<a id="stream" href="([^"]+)'
            isMatch, aResult = cParser.parse(sHtmlContent, sPattern)

        for hUrl in aResult:
            hosters.append({'link': hUrl, 'name': sName})
    if hosters:
        hosters.append('getHosterUrl')
    return hosters


def getHosterUrl(sUrl=False):
    if not sUrl: sUrl = ParameterHandler().getValue('url')
    if sUrl and not sUrl.startswith('http'):
        sUrl = URL_MAIN + sUrl
        oRequest = cRequestHandler(sUrl, caching=False)
        oRequest.request()
        sUrl = oRequest.getRealUrl()
    return [{'streamUrl': sUrl, 'resolved': False}]


def showSearchEntries(entryUrl=False, sGui=False):
    oGui = sGui if sGui else cGui()
    params = ParameterHandler()
    if not entryUrl: entryUrl = params.getValue('sUrl')
    oRequest = cRequestHandler(entryUrl, ignoreErrors=(sGui is not False))
    sHtmlContent = oRequest.request()

    sPattern = '"title":"([^"]+)","url":"([^"]+)","img":"([^"]+).*?date":"([^"]+)'
    isMatch, aResult = cParser.parse(sHtmlContent, sPattern)

    if not isMatch:
        if not sGui: oGui.showInfo('steamon', 'Es wurde kein Eintrag gefunden')
        return

    total = len(aResult)
    for sName, sUrl, sThumbnail, sYear in aResult:
        oGuiElement = cGuiElement(sName, SITE_IDENTIFIER, 'showHosters')
        oGuiElement.setMediaType('movie')
        oGuiElement.setYear(sYear)
        oGuiElement.setThumbnail(URL_MAIN + sThumbnail)
        params.setParam('entryUrl', URL_MAIN + sUrl)
        oGui.addFolder(oGuiElement, params, False, total)

    if not sGui:
        oGui.setView('movies')
        oGui.setEndOfDirectory()


def showSearch():
    oGui = cGui()
    sHtmlContent = cRequestHandler('http://1kino.in/js/live-search.js').request()
    try: nonce = re.findall('nonce=([^"]+)', sHtmlContent)[0]
    except: nonce = '273e0f8ea3'

    sSearchText = oGui.showKeyBoard()
    if not sSearchText: return
    _search(False, sSearchText, nonce)
    oGui.setEndOfDirectory()


def _search(oGui, sSearchText, nonce):
    if not sSearchText: return
    showSearchEntries(URL_SEARCH % sSearchText.strip() + nonce, oGui)
