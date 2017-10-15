# -*- coding: utf-8 -*-
import re
from resources.lib import logger
from resources.lib.gui.gui import cGui
from resources.lib.gui.guiElement import cGuiElement
from resources.lib.handler.ParameterHandler import ParameterHandler
from resources.lib.handler.requestHandler import cRequestHandler
from resources.lib.parser import cParser

SITE_IDENTIFIER = 'dokustream_org'
SITE_NAME = 'Dokustream'
SITE_ICON = 'dokustream.png'
SITE_GLOBAL_SEARCH = False

URL_MAIN = 'http://www.doku-stream.org/'
URL_HD = URL_MAIN + 'category/hd/'
URL_TOP = URL_MAIN + 'tag/top/'
URL_GENRE = URL_MAIN + 'kategorien/'
URL_SHOW = URL_MAIN + 'serien/'
URL_SEARCH = URL_MAIN + '?s=%s'


def load():
    logger.info("Load %s" % SITE_NAME)
    oGui = cGui()
    params = ParameterHandler()
    params.setParam('sUrl', URL_MAIN)
    oGui.addFolder(cGuiElement('Dokus', SITE_IDENTIFIER, 'showEntries'), params)
    params.setParam('sUrl', URL_HD)
    oGui.addFolder(cGuiElement('HD', SITE_IDENTIFIER, 'showEntries'), params)
    params.setParam('sUrl', URL_TOP)
    oGui.addFolder(cGuiElement('Empfehlungen', SITE_IDENTIFIER, 'showEntries'), params)
    params.setParam('sUrl', URL_GENRE)
    oGui.addFolder(cGuiElement('Themen', SITE_IDENTIFIER, 'showValue'), params)
    params.setParam('sUrl', URL_SHOW)
    oGui.addFolder(cGuiElement('Serien', SITE_IDENTIFIER, 'showValue'), params)
    oGui.addFolder(cGuiElement('Suche', SITE_IDENTIFIER, 'showSearch'))
    oGui.setEndOfDirectory()


def showValue(entryUrl=False):
    oGui = cGui()
    params = ParameterHandler()
    if not entryUrl: entryUrl = params.getValue('sUrl')
    sHtmlContent = cRequestHandler(entryUrl).request()
    sPattern = 'class="entry-title">.*?<footer class="entry-meta">'
    isMatch, sHtmlContainer = cParser.parseSingleResult(sHtmlContent, sPattern)

    if not isMatch:
        oGui.showInfo('steamon', 'Es wurde kein Eintrag gefunden')
        return

    sPattern = '<a[^>]*href="([^"]+)">([^<]+)'
    isMatch, aResult = cParser.parse(sHtmlContainer, sPattern)

    if not isMatch:
        oGui.showInfo('steamon', 'Es wurde kein Eintrag gefunden')
        return

    for sUrl, sName in aResult:
        params.setParam('sUrl', sUrl)
        oGui.addFolder(cGuiElement(sName, SITE_IDENTIFIER, 'showEntries'), params)
    oGui.setEndOfDirectory()


def showEntries(entryUrl=False, sGui=False):
    oGui = sGui if sGui else cGui()
    params = ParameterHandler()
    if not entryUrl: entryUrl = params.getValue('sUrl')

    sHtmlContent = cRequestHandler(entryUrl).request()
    pattern = '<h2[^>]*class="entry-title">[^>]*<a[^>]*href="([^"]+)"[^>]*rel="bookmark">([^<]+).*?<img[^>]*src="([^"]+)'
    isMatch, aResult = cParser.parse(sHtmlContent, pattern)

    if not isMatch:
        if not sGui: oGui.showInfo('steamon', 'Es wurde kein Eintrag gefunden')
        return

    total = len(aResult)
    for sUrl, sName, sThumbnail in aResult:
        oGuiElement = cGuiElement(sName, SITE_IDENTIFIER, 'getHosterUrl')
        oGuiElement.setThumbnail(sThumbnail)
        params.setParam('entryUrl', sUrl)
        oGui.addFolder(oGuiElement, params, False, total)

    if not sGui:
        sPattern = '<a[^>]*class="nextpostslink"[^>]*rel="next"[^>]*href="([^"]+)'
        isMatchNextPage, sNextUrl = cParser.parseSingleResult(sHtmlContent, sPattern)
        if isMatchNextPage:
            params.setParam('sUrl', sNextUrl)
            oGui.addNextPage(SITE_IDENTIFIER, 'showEntries', params)
        oGui.setEndOfDirectory()


def getHosterUrl(sUrl=False):
    if not sUrl: sUrl = ParameterHandler().getValue('entryUrl')
    sHtmlContent = cRequestHandler(sUrl).request()
    try:
        hLink = re.compile('<div[^>]*class="entry-content">.*?src="([^"]+)', flags=re.I | re.M).findall(sHtmlContent)[0]
        return [{'streamUrl': hLink, 'resolved': False}]
    except:
        pass


def showSearch():
    oGui = cGui()
    sSearchText = oGui.showKeyBoard()
    if not sSearchText: return
    _search(False, sSearchText)
    oGui.setEndOfDirectory()


def _search(oGui, sSearchText):
    if not sSearchText: return
    showEntries(URL_SEARCH % sSearchText.strip(), oGui)
