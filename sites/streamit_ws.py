# -*- coding: utf-8 -*-
from resources.lib.gui.gui import cGui
from resources.lib.gui.guiElement import cGuiElement
from resources.lib.handler.requestHandler import cRequestHandler
from resources.lib.parser import cParser
from resources.lib import logger
from resources.lib.handler.ParameterHandler import ParameterHandler
from resources.lib.cCFScrape import cCFScrape
import re

SITE_IDENTIFIER = 'streamit_ws'
SITE_NAME = 'StreamIt'
SITE_ICON = 'streamit.png'

URL_MAIN = 'http://streamit.ws/'
URL_SERIELINKS = 'http://streamit.ws/lade_episode.php'
URL_Kinofilme = URL_MAIN + 'kino'
URL_Filme = URL_MAIN + 'film'
URL_SERIES = URL_MAIN + 'serie'
URL_GENRES_FILM = URL_MAIN + 'genre-filme'
URL_GENRES_SERIE = URL_MAIN + 'genre-serien'
URL_SEARCH = URL_MAIN + 'suche.php?s=%s'


def load():
    logger.info("Load %s" % SITE_NAME)
    oGui = cGui()
    params = ParameterHandler()
    params.setParam('sUrl', URL_Kinofilme)
    oGui.addFolder(cGuiElement('Kino Filme', SITE_IDENTIFIER, 'showEntries'), params)
    params.setParam('sUrl', URL_Filme)
    oGui.addFolder(cGuiElement('Filme', SITE_IDENTIFIER, 'showEntries'), params)
    params.setParam('sUrl', URL_GENRES_FILM)
    oGui.addFolder(cGuiElement('Film Genre', SITE_IDENTIFIER, 'showGenre'), params)
    params.setParam('sUrl', URL_SERIES)
    oGui.addFolder(cGuiElement('Serien', SITE_IDENTIFIER, 'showEntries'), params)
    params.setParam('sUrl', URL_GENRES_SERIE)
    oGui.addFolder(cGuiElement('Serien Genre', SITE_IDENTIFIER, 'showGenre'), params)
    oGui.addFolder(cGuiElement('Suche', SITE_IDENTIFIER, 'showSearch'))
    oGui.setEndOfDirectory()


def showGenre():
    oGui = cGui()
    params = ParameterHandler()
    entryUrl = params.getValue('sUrl')
    sHtmlContent = cRequestHandler(entryUrl).request()
    isMatch, aResult = cParser().parse(sHtmlContent, '<h3 class="title">Alle Kategorien</h3>.*?</ul><div class="clear">')

    if isMatch:
        sHtmlContent = aResult[0]

    pattern = '<a[^>]href="([^"]+)"[^>]*>([^<]+)</a>([^<]+)'  # url / title / Nr
    isMatch, aResult = cParser().parse(sHtmlContent, pattern)

    for sUrl, sTitle, Nr in aResult:
        params.setParam('sUrl', URL_MAIN + sUrl)
        oGui.addFolder(cGuiElement(sTitle + Nr, SITE_IDENTIFIER, 'showEntries'), params)
    oGui.setEndOfDirectory()


def showEntries(entryUrl=False, sGui=False):
    oGui = sGui if sGui else cGui()
    params = ParameterHandler()
    if not entryUrl: entryUrl = params.getValue('sUrl')

    iPage = int(params.getValue('page'))
    if iPage > 0:
        entryUrl = entryUrl + ('&' if '?' in entryUrl else '?') + 'page=' + str(iPage)

    oRequestHandler = cRequestHandler(entryUrl, ignoreErrors=(sGui is not False))
    sHtmlContent = oRequestHandler.request()
    pattern = '<a[^>]*href="([^"]+)" title="([^"]+)"><img src="([^"]+)" alt="'
    isMatch, aResult = cParser().parse(sHtmlContent, pattern)

    if not isMatch:
        if not sGui: oGui.showInfo('streamon', 'Es wurde kein Eintrag gefunden')
        return

    total = len(aResult)
    for sUrl, sName, sThumbnail in aResult:
        isTvshow = True if "serie" in sUrl else False
        oGuiElement = cGuiElement(sName, SITE_IDENTIFIER, 'showSeasons' if isTvshow else 'showHosters')
        if sThumbnail.startswith('/'):
            sThumbnail = URL_MAIN + sThumbnail
        sThumbnail = cCFScrape().createUrl(sThumbnail, oRequestHandler)
        oGuiElement.setThumbnail(sThumbnail)
        oGuiElement.setMediaType('tvshow' if isTvshow else 'movie')
        params.setParam('entryUrl', URL_MAIN + sUrl)
        params.setParam('sName', sName)
        params.setParam('Thumbnail', sThumbnail)
        oGui.addFolder(oGuiElement, params, isTvshow, total)
    if not sGui:
        isMatch, strPage = cParser().parseSingleResult(sHtmlContent, '<a[^>]*class="next page-numbers"[^>]*href="[^>]*page=([^"]+)">Next &raquo;')
        if isMatch:
            params.setParam('page', int(strPage))
            oGui.addNextPage(SITE_IDENTIFIER, 'showEntries', params)
        oGui.setView('tvshows' if 'serie' in entryUrl else 'movies')
        oGui.setEndOfDirectory()


def showSeasons():
    oGui = cGui()
    params = ParameterHandler()
    sUrl = params.getValue('entryUrl')
    sThumbnail = params.getValue("Thumbnail")
    sName = params.getValue('sName')
    sHtmlContent = cRequestHandler(sUrl).request()
    sPattern = '<select[^>]*class="staffelauswahl"[^>]*>(.*?)</select>'  # container
    isMatch, strContainer = cParser().parseSingleResult(sHtmlContent, sPattern)

    if isMatch:
        sPattern = '<option[^>]*value="(.*?)"[^>]*>(.*?)</option>'  # container
        isMatch, aResult = cParser().parse(strContainer, sPattern)

    if not isMatch:
        oGui.showInfo('streamon', 'Es wurde kein Eintrag gefunden')
        return

    total = len(aResult)
    for iSeason, sTitle in aResult:
        oGuiElement = cGuiElement("Staffel " + str(iSeason), SITE_IDENTIFIER, 'showEpisodes')
        oGuiElement.setTVShowTitle(sName)
        oGuiElement.setSeason(iSeason)
        oGuiElement.setMediaType('season')
        oGuiElement.setThumbnail(sThumbnail)
        oGui.addFolder(oGuiElement, params, True, total)
    oGui.setView('seasons')
    oGui.setEndOfDirectory()


def showEpisodes():
    oGui = cGui()
    params = ParameterHandler()
    sUrl = params.getValue('entryUrl')
    sThumbnail = params.getValue("Thumbnail")
    sSeason = params.getValue('season')
    sShowName = params.getValue('TVShowTitle')
    sHtmlContent = cRequestHandler(sUrl).request()
    sPattern = '<a[^>]*href="#(s%se(\d+))"[^>]*>(.*?)</a>' % sSeason
    isMatch, aResult = cParser().parse(sHtmlContent, sPattern)

    if not isMatch:
        oGui.showInfo('streamon', 'Es wurde kein Eintrag gefunden')
        return

    result, imdb = cParser().parseSingleResult(sHtmlContent, 'IMDB\s?=\s?\'(\d+)')

    total = len(aResult)
    for sEpisodeUrl, sEpisodeNr, sEpisodeTitle in aResult:
        res = re.search('%s (.*)' % sEpisodeNr, sEpisodeTitle)
        if res:
            sEpisodeTitle = '%s - %s' % (sEpisodeNr, res.group(1))
        oGuiElement = cGuiElement(sEpisodeTitle, SITE_IDENTIFIER, "showHosters")
        oGuiElement.setThumbnail(sThumbnail)
        oGuiElement.setTVShowTitle(sShowName)
        oGuiElement.setEpisode(sEpisodeNr)
        oGuiElement.setSeason(sSeason)
        oGuiElement.setMediaType('episode')
        params.setParam('entryUrl', sUrl)
        params.setParam('val', sEpisodeUrl)
        params.setParam('IMDB', imdb)
        oGui.addFolder(oGuiElement, params, False, total)
    oGui.setView('episodes')
    oGui.setEndOfDirectory()


def showHosters():
    params = ParameterHandler()
    sUrl = params.getValue('entryUrl')
    oRequestHandler = cRequestHandler(sUrl)

    if params.getValue('val'):
        oRequestHandler = cRequestHandler(URL_SERIELINKS)
        oRequestHandler.addParameters('val', params.getValue('val'))
        oRequestHandler.addParameters('IMDB', params.getValue('IMDB'))
        oRequestHandler.setRequestType(1)

    sHtmlContent = oRequestHandler.request()
    hosters = []
    isMatch, sContainer = cParser().parseSingleResult(sHtmlContent, '<select[^>]*class="sel_quali"[^>]*>(.*?)</select>')  # filter main content if needed

    if not isMatch:
        return hosters

    isMatch, aResult = cParser().parse(sContainer, '<option[^>]*\((?:[^>]*quality/(\d+)\.png)?[^>]*id="(\w+)"[^>]*>(.*?)</option>')  # filter main content if needed

    if not isMatch:
        return hosters

    for sQulityNr, sID, sQulityTitle in aResult:
        sPattern = '<div[^>]*class="mirrors\w+"[^>]*id="%s">(.*?)</div></div>' % sID
        isMatchMirrors, sMirrorContainer = cParser().parse(sHtmlContent, sPattern)

        if not isMatchMirrors:
            continue

        isMatchUrls, aResultMirrors = cParser().parse(sMirrorContainer[0], '<a[^>]*href="([^"]+)"[^>]*>.*?name="save"[^>]*value="(.*?)"[^>]*/>')

        if not isMatchUrls:
            continue

        for sUrl, sName in aResultMirrors:
            hoster = {'name': sName.strip(), 'displayedName': '[%s] %s' % (sQulityTitle, sName.strip()),
                      'quality': sQulityNr if sQulityNr else '0', 'link': URL_MAIN + sUrl}
            hosters.append(hoster)

    if hosters:
        hosters.append('getHosterUrl')
    return hosters


def getHosterUrl(sUrl=False):
    sHtmlContent = cRequestHandler(sUrl).request()
    isMatch, redirectUrl = cParser().parseSingleResult(sHtmlContent, 'none"><a[^>]*href="([^"]+)')
    return [{'streamUrl': redirectUrl, 'resolved': False}]


def showSearch():
    oGui = cGui()
    sSearchText = oGui.showKeyBoard()
    if not sSearchText: return
    _search(False, sSearchText)
    oGui.setEndOfDirectory()


def _search(oGui, sSearchText):
    if not sSearchText: return
    showEntries(URL_SEARCH % sSearchText.strip(), oGui)
