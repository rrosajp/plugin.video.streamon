# -*- coding: utf-8 -*-
import re, sys
from binascii import unhexlify, hexlify
from resources.lib import cookie_helper, logger, pyaes, jsunpacker
from resources.lib.gui.gui import cGui
from resources.lib.gui.guiElement import cGuiElement
from resources.lib.handler.ParameterHandler import ParameterHandler
from resources.lib.handler.requestHandler import cRequestHandler
from resources.lib.parser import cParser
from resources.lib.util import cUtil

SITE_IDENTIFIER = 'foxx_to'
SITE_NAME = 'Foxx'
SITE_ICON = 'foxx.png'

URL_MAIN = 'http://foxx.to/'
URL_FILME = URL_MAIN + 'film'
URL_SERIE = URL_MAIN + 'serie'
URL_SEARCH = URL_MAIN + 'wp-json/dooplay/search/?keyword=%s&nonce='

QUALITY_ENUM = {'240p': 0, '360p': 1, '480p': 2, '720p': 3, '1080p': 4, '240': 0, '360': 1, '480': 2, '720': 3, '1080': 4}


def load():
    params = ParameterHandler()
    oGui = cGui()
    params.setParam('sUrl', URL_FILME)
    oGui.addFolder(cGuiElement('Filme', SITE_IDENTIFIER, 'showEntries'), params)
    params.setParam('sUrl', URL_SERIE)
    oGui.addFolder(cGuiElement('Serien', SITE_IDENTIFIER, 'showEntries'), params)
    params.setParam('sUrl', URL_MAIN)
    oGui.addFolder(cGuiElement('Genres', SITE_IDENTIFIER, 'showGenres'), params)
    oGui.addFolder(cGuiElement('Suche', SITE_IDENTIFIER, 'showSearch'))
    oGui.setEndOfDirectory()


def showGenres():
    oGui = cGui()
    params = ParameterHandler()
    sHtmlContent = __getContent(URL_MAIN)
    sPattern = 'Filme</a><ul[^>]*class="sub-menu">.*?</ul></li><li[^>]*id'
    isMatch, sHtmlContainer = cParser.parseSingleResult(sHtmlContent, sPattern)

    if not isMatch:
        oGui.showInfo('streamon', 'Es wurde kein Eintrag gefunden')
        return

    sPattern = '<a[^>]*href="([^"]+)".*?>([^"]+)</a>'
    isMatch, aResult = cParser.parse(sHtmlContainer, sPattern)

    if not isMatch:
        oGui.showInfo('streamon', 'Es wurde kein Eintrag gefunden')
        return

    for sUrl, sName in aResult:
        sName = sName.replace('&#8211; ', '')
        params.setParam('sUrl', sUrl)
        oGui.addFolder(cGuiElement(sName.strip(), SITE_IDENTIFIER, 'showEntries'), params)
    oGui.setEndOfDirectory()


def showEntries(entryUrl=False, sGui=False):
    oGui = sGui if sGui else cGui()
    params = ParameterHandler()
    if not entryUrl: entryUrl = params.getValue('sUrl')
    sHtmlContent = __getContent(entryUrl)
    sPattern = '<div[^>]*class="poster">.*?<img[^>]*src="([^"]+).*?<a[^>]*href="([^"]+)">([^<]+).*?(?:<span>([^<]+)?).*?<div[^>]*class="texto">([^<]+)'
    isMatch, aResult = cParser.parse(sHtmlContent, sPattern)

    if not isMatch:
        if not sGui: oGui.showInfo('streamon', 'Es wurde kein Eintrag gefunden')
        return

    total = len(aResult)
    for sThumbnail, sUrl, sName, sYear, sDesc in aResult:
        sThumbnail = re.sub('-\d+x\d+\.', '.', sThumbnail)
        isTvshow = True if "serie" in sUrl else False
        if sThumbnail and not sThumbnail.startswith('http'):
            sThumbnail = URL_MAIN + sThumbnail
        oGuiElement = cGuiElement(sName, SITE_IDENTIFIER, 'showSeasons' if isTvshow else 'showHosters')
        oGuiElement.setMediaType('tvshow' if isTvshow else 'movie')
        oGuiElement.setThumbnail(sThumbnail)
        if sYear:
            oGuiElement.setYear(sYear)
        oGuiElement.setDescription(sDesc)
        sUrl = cUtil.quotePlus(sUrl)
        params.setParam('entryUrl', sUrl)
        params.setParam('sName', sName)
        params.setParam('sThumbnail', sThumbnail)
        oGui.addFolder(oGuiElement, params, isTvshow, total)

    if not sGui:
        sPattern = '"next"[^>]*href="([^"]+)'
        isMatchNextPage, sNextUrl = cParser.parseSingleResult(sHtmlContent, sPattern)
        if isMatchNextPage:
            params.setParam('sUrl', sNextUrl)
            oGui.addNextPage(SITE_IDENTIFIER, 'showEntries', params)
        oGui.setView('tvshows' if 'serie' in sUrl else 'movies')
        oGui.setEndOfDirectory()


def showSeasons():
    oGui = cGui()
    params = ParameterHandler()
    sUrl = params.getValue('entryUrl')
    sThumbnail = params.getValue('sThumbnail')
    sTVShowTitle = params.getValue('sName')
    sHtmlContent = __getContent(sUrl)
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

    pattern = '<a[^>]*href="([^"]+)"[^>]*>\s*<img src="([^"]+).*?<div[^>]*class="numerando">[^-]*-\s*(\d+)\s*?</div>.*?<a[^>]*>([^<]*)</a>'
    isMatch, aResult = cParser.parse(sContainer, pattern)

    if not isMatch:
        oGui.showInfo('streamon', 'Es wurde kein Eintrag gefunden')
        return

    total = len(aResult)
    for sUrl, sThumbnail, sEpisodeNr, sName in aResult:
        oGuiElement = cGuiElement("%s - %s" % (sEpisodeNr, sName.strip()), SITE_IDENTIFIER, 'showHosters')
        oGuiElement.setTVShowTitle(sTVShowTitle)
        oGuiElement.setSeason(sSeasonNr)
        oGuiElement.setEpisode(sEpisodeNr)
        sThumbnail = re.sub('-\d+x\d+\.', '.', sThumbnail)
        oGuiElement.setThumbnail(sThumbnail)
        oGuiElement.setMediaType('episode')
        params.setParam('entryUrl', sUrl.strip())
        oGui.addFolder(oGuiElement, params, False, total)
    oGui.setView('seasons')
    oGui.setEndOfDirectory()


def showHosters():
    oParams = ParameterHandler()
    sUrl = oParams.getValue('entryUrl')
    sHtmlContent = __getContent(sUrl)
    sPattern = 'src="([^"]+)"[^>]*frameborder'  # url
    aResult = cParser().parse(sHtmlContent, sPattern)
    hosters = []
    if aResult[1]:
        for hUrl in aResult[1]:
            if 'view.php' in hUrl:
                oRequest = cRequestHandler(hUrl, ignoreErrors=True)
                sHtmlContent = oRequest.request()
                aResult = cParser.parse(sHtmlContent, '"file":"([^"]+).*?label":"([^"]+)')
                for sUrl, sQuality in aResult[1]:
                    sQuality = sQuality.lower()
                    hoster = {'link': sUrl, 'name': sQuality, 'quality': QUALITY_ENUM[sQuality]}
                    hosters.append(hoster)

            if 'rapidvideo' in hUrl:
                oRequest = cRequestHandler(hUrl, ignoreErrors=True)
                oRequest.addHeaderEntry('Referer', sUrl)
                sHtmlContent = oRequest.request()
                aResult = cParser.parse(sHtmlContent, '<a[^>]*href="([^"]+)">.*?">([^<]+)')
                for sUrl, sQuality in aResult[1]:
                    sQuality = sQuality.lower()
                    hoster = {'link': sUrl, 'name': 'Rapidvideo ' + sQuality, 'quality': QUALITY_ENUM[sQuality]}
                    hosters.append(hoster)

            if 'wp-embed.php' in hUrl:
                oRequest = cRequestHandler(hUrl, ignoreErrors=True)
                oRequest.addHeaderEntry('Referer', sUrl)
                sHtmlContent = oRequest.request()
                aResult = cParser.parse(sHtmlContent, '{file: "([^"]+).*?label: "([^"]+)')
                for sUrl, sQuality in aResult[1]:
                    sQuality = sQuality.lower()
                    hoster = {'link': sUrl, 'name': sQuality, 'quality': QUALITY_ENUM[sQuality]}
                    hosters.append(hoster)

            if 'play' in hUrl:
                oRequest = cRequestHandler(hUrl, ignoreErrors=True)
                oRequest.addHeaderEntry('Referer', sUrl)
                sHtmlContent = oRequest.request()
                isMatch, aResult = cParser.parse(sHtmlContent, '(eval\s*\(function.*?)</script>')
                if isMatch:
                    for packed in aResult:
                        try:
                            sHtmlContent += jsunpacker.unpack(packed)
                        except:
                            pass

                    isMatch, aResult = cParser.parse(sHtmlContent, 'file":"([^"]+)","label":"([^"]+)"')
                    for sUrl, sQuality in aResult:
                        sQuality = sQuality.lower()
                        hoster = {'link': sUrl, 'name': sQuality, 'quality': QUALITY_ENUM[sQuality]}
                        hosters.append(hoster)

            if 'youtube' in hUrl:
                hoster = {'link': hUrl, 'name': 'Youtube [Trailer]'}
                hosters.append(hoster)

    if hosters:
        hosters.append('getHosterUrl')
    return hosters


def getHosterUrl(sUrl=False):
    if not sUrl: sUrl = ParameterHandler().getValue('url')
    results = []
    result = {'streamUrl': sUrl}
    if 'rapidvideo' in sUrl:
        result['resolved'] = False
    elif'youtube' in sUrl:
        result['resolved'] = False
    else:
        result['resolved'] = True
    results.append(result)
    return results


def str_to_utf8(s):
    if '\\u00c4' in s:
        s = s.replace("\\u00c4", "Ä")
    if '\\u00e4' in s:
        s = s.replace("\\u00e4", "ä")
    if '\\u00d6' in s:
        s = s.replace("\\u00d6", "Ö")
    if '\\u00f6' in s:
        s = s.replace("\\u00f6", "ö")
    if '\\u00dc' in s:
        s = s.replace("\\u00dc", "Ü")
    if '\\u00fc' in s:
        s = s.replace("\\u00fc", "ü")
    if '\\u00df' in s:
        s = s.replace("\\u00df", "ß")
    return s


def showSearchEntries(entryUrl=False, sGui=False):
    oGui = sGui if sGui else cGui()
    params = ParameterHandler()
    if not entryUrl: entryUrl = params.getValue('sUrl')
    sHtmlContent = __getContent(entryUrl)
    sPattern = '"title":"([^"]+)","url":"([^"]+)","img":"([^"]+).*?date":"([^"]+)'
    isMatch, aResult = cParser.parse(sHtmlContent, sPattern)

    if not isMatch:
        if not sGui: oGui.showInfo('streamon', 'Es wurde kein Eintrag gefunden')
        return

    total = len(aResult)
    for sName, sUrl, sThumbnail, sYear in aResult:
        sThumbnail = sThumbnail.replace('\\/', '/').replace('\/', '/')
        sUrl = sUrl.replace('\\/', '/').replace('\/', '/')
        sThumbnail = re.sub('-\d+x\d+\.', '.', sThumbnail)
        if sThumbnail and not sThumbnail.startswith('http'):
            sThumbnail = URL_MAIN + sThumbnail
        isTvshow = True if "serie" in sUrl else False
        sName = str_to_utf8(sName)
        oGuiElement = cGuiElement(sName, SITE_IDENTIFIER, 'showSeasons' if isTvshow else 'showHosters')
        oGuiElement.setMediaType('tvshow' if isTvshow else 'movie')
        oGuiElement.setThumbnail(sThumbnail)
        oGuiElement.setYear(sYear)
        sUrl = cUtil.quotePlus(sUrl)
        params.setParam('entryUrl', sUrl)
        params.setParam('sName', sName)
        params.setParam('sThumbnail', sThumbnail)
        oGui.addFolder(oGuiElement, params, isTvshow, total)

    if not sGui:
        sPattern = "span[^>]*class=[^>]*current[^>]*>.*?</span><a[^>]*href='([^']+)"
        isMatchNextPage, sNextUrl = cParser.parseSingleResult(sHtmlContent, sPattern)
        if isMatchNextPage:
            params.setParam('sUrl', sNextUrl)
            oGui.addNextPage(SITE_IDENTIFIER, 'showEntries', params)
        oGui.setView('tvshows' if 'serie' in sUrl else 'movies')
        oGui.setEndOfDirectory()


def showSearch():
    oGui = cGui()
    sHtmlContent = __getContent(URL_MAIN)
    try:
        nonce = re.findall('nonce":"([^"]+)', sHtmlContent)[0]
    except:
        nonce = '5d12d0fa54'

    sSearchText = oGui.showKeyBoard()
    if not sSearchText: return
    _search(False, sSearchText, nonce)
    oGui.setEndOfDirectory()


def _search(oGui, sSearchText, nonce):
    if not sSearchText: return
    showSearchEntries(URL_SEARCH % sSearchText.strip() + nonce, oGui)


''' BLAZINGFAST bypass '''


def __getContent(sUrl):
    request = cRequestHandler(sUrl, caching=False, ignoreErrors=True)
    return __unprotect(request)


def __unprotect(initialRequest):
    parser = cParser()
    content = initialRequest.request()
    if 'Blazingfast.io' not in content:
        return content
    pattern = 'xhr\.open\("GET","([^,]+),'
    match = parser.parse(content, pattern)
    if not match[0]:
        return False
    urlParts = match[1][0].split('"')
    sid = '1200'
    url = '%s%s%s%s' % (URL_MAIN[:-1], urlParts[0], sid, urlParts[2])
    request = cRequestHandler(url, caching=False)
    request.addHeaderEntry('Referer', initialRequest.getRequestUri())
    content = request.request()
    if not check(content):
        return content  # even if its false its probably not the right content, we'll see
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


COOKIE_NAME = 'BLAZINGFAST-WEB-PROTECT'


def check(content):
    """
    returns True if there seems to be a protection
    """
    return COOKIE_NAME in content


# not very robust but lazieness...
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
