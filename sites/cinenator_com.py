# -*- coding: utf-8 -*-
from binascii import unhexlify, hexlify
from resources.lib import cookie_helper, logger, pyaes
from resources.lib.gui.gui import cGui
from resources.lib.gui.guiElement import cGuiElement
from resources.lib.handler.ParameterHandler import ParameterHandler
from resources.lib.handler.requestHandler import cRequestHandler
from resources.lib.parser import cParser
from resources.lib.util import cUtil
import sys, re

SITE_IDENTIFIER = 'cinenator_com'
SITE_NAME = 'Cinenator'
SITE_ICON = 'cinenator.png'

URL_MAIN = 'http://www.cinenator.com/'
URL_FILME = URL_MAIN + 'filme/'
URL_SERIE = URL_MAIN + 'kategorien/serien/'
URL_SEARCH = URL_MAIN + '?s=%s'


def load():
    logger.info("Load %s" % SITE_NAME)
    oGui = cGui()
    params = ParameterHandler()
    params.setParam('sUrl', URL_FILME)
    oGui.addFolder(cGuiElement('Filme', SITE_IDENTIFIER, 'showEntries'), params)
    params.setParam('sUrl', URL_SERIE)
    oGui.addFolder(cGuiElement('Serien', SITE_IDENTIFIER, 'showEntries'), params)
    params.setParam('Value', 'Genres')
    oGui.addFolder(cGuiElement('Genres', SITE_IDENTIFIER, 'showValue'), params)
    params.setParam('Value', 'Release Year')
    oGui.addFolder(cGuiElement('Erscheinungsjahr', SITE_IDENTIFIER, 'showValue'), params)
    oGui.addFolder(cGuiElement('Suche', SITE_IDENTIFIER, 'showSearch'))
    oGui.setEndOfDirectory()


def showValue():
    oGui = cGui()
    params = ParameterHandler()
    sHtmlContent = __getContent(URL_MAIN)
    pattern = '<h2>%s</h2>.*?<div[^>]*class' % params.getValue('Value')
    isMatch, sHtmlContainer = cParser.parseSingleResult(sHtmlContent, pattern)
    pattern = '<a[^>]*href="([^"]+)".*?>([^"]+)</a>'
    isMatch, aResult = cParser.parse(sHtmlContainer, pattern)
    if not isMatch:
        oGui.showInfo('streamon', 'Es wurde kein Eintrag gefunden')
        return
    for sUrl, sName in aResult:
        params.setParam('sUrl', sUrl)
        oGui.addFolder(cGuiElement(cUtil.cleanse_text(sName), SITE_IDENTIFIER, 'showEntries'), params)
    oGui.setEndOfDirectory()


def showEntries(entryUrl=False, sGui=False):
    oGui = sGui if sGui else cGui()
    params = ParameterHandler()
    if not entryUrl: entryUrl = params.getValue('sUrl')
    sHtmlContent = __getContent(entryUrl)
    pattern = '<div[^>]*class="poster">.*?<img[^>]*src="([^"]+).*?<a[^>]*href="([^"]+)">([^<]+).*?(?:<span>([^<]+)?).*?<div[^>]*class="texto">([^<]+)'
    isMatch, aResult = cParser.parse(sHtmlContent, pattern)
    if not isMatch:
        pattern = '<div[^>]*class="search_page_form">.*?</div></div></div>'
        isMatch, sHtmlContainer = cParser.parseSingleResult(sHtmlContent, pattern)
        if not isMatch:
            if not sGui: oGui.showInfo('streamon', 'Es wurde kein Eintrag gefunden')
            return
        pattern = '<img[^>]*src="([^"]+).*?<a[^>]*href="([^"]+)">([^<]+)</a>.*?(?:<span[^>]*class="year">([^<]+)?).*?<p>([^<]+)'
        isMatch, aResult = cParser.parse(sHtmlContainer, pattern)
    if not isMatch:
        if not sGui: oGui.showInfo('streamon', 'Es wurde kein Eintrag gefunden')
        return
    total = len(aResult)
    for sThumbnail, sUrl, sName, sYear, sDesc in aResult:
        sThumbnail = re.sub('-\d+x\d+\.', '.', sThumbnail)
        isTvshow = True if "serien" in sUrl else False
        oGuiElement = cGuiElement(sName, SITE_IDENTIFIER, 'showSeasons' if isTvshow else 'showHosters')
        oGuiElement.setMediaType('tvshow' if isTvshow else 'movie')
        oGuiElement.setThumbnail(sThumbnail)
        if sYear:
            oGuiElement.setYear(sYear)
        oGuiElement.setDescription(sDesc)
        params.setParam('entryUrl', sUrl)
        params.setParam('sName', sName)
        params.setParam('sThumbnail', sThumbnail)
        oGui.addFolder(oGuiElement, params, isTvshow, total)
    if not sGui:
        pattern = '<link[^>]*rel="next"[^>]*href="([^"]+)"'
        isMatchNextPage, sNextUrl = cParser.parseSingleResult(sHtmlContent, pattern)
        if isMatchNextPage:
            params.setParam('sUrl', sNextUrl)
            oGui.addNextPage(SITE_IDENTIFIER, 'showEntries', params)
        oGui.setView('tvshows' if 'serien' in entryUrl else 'movies')
        oGui.setEndOfDirectory()


def showSeasons():
    oGui = cGui()
    params = ParameterHandler()
    entryUrl = params.getValue('entryUrl')
    sThumbnail = params.getValue('sThumbnail')
    sTVShowTitle = params.getValue('sName')
    sHtmlContent = __getContent(entryUrl)
    pattern = '<span[^>]*class="se-t[^"]*"[^>]*>(\d+)</span>'
    isMatch, aResult = cParser.parse(sHtmlContent, pattern)

    if not isMatch:
        oGui.showInfo('streamon', 'Es wurde kein Eintrag gefunden')
        return

    total = len(aResult)
    for sSeasonNr in aResult:
        oGuiElement = cGuiElement("Staffel " + sSeasonNr, SITE_IDENTIFIER, 'showEpisodes')
        oGuiElement.setMediaType('season')
        oGuiElement.setTVShowTitle(sTVShowTitle)
        oGuiElement.setSeason(sSeasonNr)
        oGuiElement.setThumbnail(sThumbnail)
        params.setParam('sSeasonNr', int(sSeasonNr))
        oGui.addFolder(oGuiElement, params, True, total)
    oGui.setView('seasons')
    oGui.setEndOfDirectory()


def showEpisodes():
    oGui = cGui()
    params = ParameterHandler()
    sTVShowTitle = params.getValue('TVShowTitle')
    entryUrl = params.getValue('entryUrl')
    sSeasonNr = params.getValue('sSeasonNr')
    sHtmlContent = __getContent(entryUrl)
    pattern = '<span[^>]*class="se-t[^"]*">%s</span>.*?<ul[^>]*class="episodios"[^>]*>(.*?)</ul>' % sSeasonNr
    isMatch, sContainer = cParser.parseSingleResult(sHtmlContent, pattern)

    if not isMatch:
        oGui.showInfo('streamon', 'Es wurde kein Eintrag gefunden')
        return

    pattern = '<a[^>]*href="([^"]+)"[^>]*>\s*(?:<img[^>]*src="([^"]+)?).*?<div[^>]*class="numerando">[^-]*-\s*(\d+)\s*?</div>.*?<a[^>]*>([^<]*)</a>'
    isMatch, aResult = cParser.parse(sContainer, pattern)

    if not isMatch:
        oGui.showInfo('streamon', 'Es wurde kein Eintrag gefunden')
        return

    total = len(aResult)
    for sUrl, sThumbnail, sEpisodeNr, sName in aResult:
        oGuiElement = cGuiElement(sName.strip(), SITE_IDENTIFIER, 'showHosters')
        oGuiElement.setTVShowTitle(sTVShowTitle)
        oGuiElement.setSeason(sSeasonNr)
        oGuiElement.setEpisode(sEpisodeNr)
        if sThumbnail:
            sThumbnail = re.sub('-\d+x\d+\.', '.', sThumbnail)
            oGuiElement.setThumbnail(sThumbnail)
        oGuiElement.setMediaType('episode')
        params.setParam('entryUrl', sUrl.strip())
        oGui.addFolder(oGuiElement, params, False, total)
    oGui.setView('episodes')
    oGui.setEndOfDirectory()


def showHosters():
    params = ParameterHandler()
    sUrl = params.getValue('entryUrl')
    sHtmlContent = __getContent(sUrl)
    pattern = '<a[^>]*class="link_a"[^>]*href="([^"]+).*?domain=([^"]+).*?</td><td>([^<]+)</td><td>([^<]+)</td><td>'
    aResult = cParser().parse(sHtmlContent, pattern)
    hosters = []
    for sUrl, sName, sQuali, sLang in aResult[1]:
        if not 'filecrypt' in sName:
            if not 'depfile' in sName:
                hoster = {'link': sUrl, 'name': sName}
                hosters.append(hoster)
    if hosters:
        hosters.append('getHosterUrl')
    return hosters


def getHosterUrl(sUrl=False):
    sHtmlContent = __getContent(sUrl)
    hLink = re.compile('><a[^>]*href="([^"]+)">', flags=re.I | re.M).findall(sHtmlContent)[0]
    return [{'streamUrl': cUtil.cleanse_text(hLink), 'resolved': False}]


def showSearch():
    oGui = cGui()
    sSearchText = oGui.showKeyBoard()
    if not sSearchText: return
    _search(False, sSearchText)
    oGui.setEndOfDirectory()


def _search(oGui, sSearchText):
    if not sSearchText: return
    showEntries(URL_SEARCH % sSearchText.strip(), oGui)


''' BLAZINGFAST bypass '''
def __getContent(sUrl):
    request = cRequestHandler(sUrl, caching = False)
    return __unprotect(request)


def __unprotect(initialRequest):
    content = initialRequest.request()
    if 'Blazingfast.io' not in content:
        return content
    pattern = 'xhr\.open\("GET","([^,]+),'
    match = cParser.parse(content, pattern)
    if not match[0]:
        return False
    urlParts = match[1][0].split('"')
    sid = '1200'
    url = '%s%s%s%s' % (URL_MAIN[:-1], urlParts[0], sid, urlParts[2])
    request = cRequestHandler(url, caching=False)
    request.addHeaderEntry('Referer', initialRequest.getRequestUri())
    content = request.request()
    if not check(content):
        return content
    cookie = getCookieString(content)
    if not cookie:
        return False
    initialRequest.caching = False
    name, value = cookie.split(';')[0].split('=')
    cookieData = dict((k.strip(), v.strip()) for k, v in (item.split("=") for item in cookie.split(";")))
    cookie = cookie_helper.create_cookie(name, value, domain=cookieData['domain'], expires=sys.maxint, discard=False)
    initialRequest.setCookie(cookie)
    content = initialRequest.request()
    return content


def check(content):
    return 'BLAZINGFAST-WEB-PROTECT' in content


def getCookieString(content):
    vars = re.findall('toNumbers\("([^"]+)"', content)
    if not vars:
        logger.info('vars not found')
        return False
    value = _decrypt(vars[2], vars[0], vars[1])
    if not value:
        logger.info('value decryption failed')
        return False
    pattern = '"%s=".*?";([^"]+)"' % COOKIE_NAME
    cookieMeta = re.findall(pattern, content)
    if not cookieMeta:
        logger.info('cookie meta not found')
    cookie = "%s=%s;%s" % (COOKIE_NAME, value, cookieMeta[0])
    return cookie


def _decrypt(msg, key, iv):
    msg = unhexlify(msg)
    key = unhexlify(key)
    iv = unhexlify(iv)
    if len(iv) != 16:
        logger.info("iv length is" + str(len(iv)) + " must be 16.")
        return False
    decrypter = pyaes.Decrypter(pyaes.AESModeOfOperationCBC(key, iv))
    plain_text = decrypter.feed(msg)
    plain_text += decrypter.feed()
    f = hexlify(plain_text)
    return f

    if 'User-Agent=' not in sUrl:
        delimiter = '&' if '|' in sUrl else '|'
        sUrl += delimiter + "User-Agent=" + oRequest.getHeaderEntry('User-Agent')
    return sUrl
