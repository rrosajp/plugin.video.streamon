# -*- coding: utf-8 -*-
import json
from resources.lib import logger
from resources.lib.config import cConfig
from resources.lib.gui.gui import cGui
from resources.lib.gui.guiElement import cGuiElement
from resources.lib.handler.ParameterHandler import ParameterHandler
from resources.lib.handler.requestHandler import cRequestHandler
from resources.lib.parser import cParser

SITE_IDENTIFIER = 'ddl_me'
SITE_NAME = 'DirectDownLoad'
SITE_ICON = 'ddl.png'
SITE_SETTINGS = '<setting default="de.ddl.me" enable="!eq(-2,false)" id="ddl_me-domain" label="30051" type="labelenum" values="de.ddl.me|en.ddl.me" />'

oConfig = cConfig()
DOMAIN = oConfig.getSetting('ddl_me-domain')

URL_MAIN = 'http://' + DOMAIN
URL_SEARCH = URL_MAIN + '/search_99/?q='
URL_MOVIES = URL_MAIN + '/moviez'
URL_SHOWS = URL_MAIN + '/episodez'
URL_TOP100 = URL_MAIN + '/top100/cover/'

PARMS_GENRE_ALL = "_00"

PARMS_SORT_LAST_UPDATE = "_0"
PARMS_SORT_BLOCKBUSTER = "_1"
PARMS_SORT_IMDB_RATING = "_2"
PARMS_SORT_YEAR = "_3"


def load():
    logger.info("Load %s" % SITE_NAME)
    oGui = cGui()
    params = ParameterHandler()

    params.setParam('sUrl', URL_MOVIES)
    params.setParam('sTop100Type', 'movies')
    oGui.addFolder(cGuiElement('Filme', SITE_IDENTIFIER, 'showContentMenu'), params)
    params.setParam('sUrl', URL_SHOWS)
    params.setParam('sTop100Type', 'tv')
    oGui.addFolder(cGuiElement('Serien', SITE_IDENTIFIER, 'showContentMenu'), params)
    params.setParam('sUrl', URL_TOP100 + 'total/all/')
    oGui.addFolder(cGuiElement('Hall of Fame', SITE_IDENTIFIER, 'showEntries'), params)
    oGui.addFolder(cGuiElement('Suche', SITE_IDENTIFIER, 'showSearch'))
    oGui.setEndOfDirectory()


def showContentMenu():
    oGui = cGui()
    params = ParameterHandler()
    baseURL = params.getValue('sUrl')

    oGui.addFolder(cGuiElement('Top 100', SITE_IDENTIFIER, 'showTop100Menu'), params)
    params.setParam('sUrl', baseURL + PARMS_GENRE_ALL + PARMS_SORT_LAST_UPDATE)
    oGui.addFolder(cGuiElement('Letztes Update', SITE_IDENTIFIER, 'showEntries'), params)
    params.setParam('sUrl', baseURL + PARMS_GENRE_ALL + PARMS_SORT_BLOCKBUSTER)
    oGui.addFolder(cGuiElement('Blockbuster', SITE_IDENTIFIER, 'showEntries'), params)
    params.setParam('sUrl', baseURL + PARMS_GENRE_ALL + PARMS_SORT_IMDB_RATING)
    oGui.addFolder(cGuiElement('IMDB Rating', SITE_IDENTIFIER, 'showEntries'), params)
    params.setParam('sUrl', baseURL + PARMS_GENRE_ALL + PARMS_SORT_YEAR)
    oGui.addFolder(cGuiElement('Jahr', SITE_IDENTIFIER, 'showEntries'), params)
    params.setParam('sUrl', baseURL + PARMS_GENRE_ALL + PARMS_SORT_LAST_UPDATE)
    oGui.addFolder(cGuiElement('Genre', SITE_IDENTIFIER, 'showGenreList'), params)
    oGui.setEndOfDirectory()


def showTop100Menu():
    oGui = cGui()
    params = ParameterHandler()

    params.setParam('sUrl', URL_TOP100 + 'today/' + params.getValue('sTop100Type'))
    oGui.addFolder(cGuiElement('Heute', SITE_IDENTIFIER, 'showEntries'), params)
    params.setParam('sUrl', URL_TOP100 + 'month/' + params.getValue('sTop100Type'))
    oGui.addFolder(cGuiElement('Monat', SITE_IDENTIFIER, 'showEntries'), params)
    oGui.setEndOfDirectory()


def showGenreList():
    oGui = cGui()
    params = ParameterHandler()
    sHtmlContent = cRequestHandler(params.getValue('sUrl')).request()
    sPattern = '<i[^>]*class="genre.*?<span>Genre</span>'
    isMatch, sHtmlContainer = cParser.parseSingleResult(sHtmlContent, sPattern)

    if not isMatch:
        oGui.showInfo('streamon', 'Es wurde kein Eintrag gefunden')
        return

    sPattern = '<a[^>]*href="([^"]+)".*?i>([^<]+)'
    isMatch, aResult = cParser.parse(sHtmlContainer, sPattern)

    if not isMatch:
        oGui.showInfo('streamon', 'Es wurde kein Eintrag gefunden')
        return

    for sUrl, sTitle in aResult:
        params.setParam('sUrl', URL_MAIN + sUrl)
        oGui.addFolder(cGuiElement(sTitle.strip(), SITE_IDENTIFIER, 'showEntries'), params)
    oGui.setEndOfDirectory()


def showEntries(entryUrl=False, sGui=False):
    oGui = sGui if sGui else cGui()
    params = ParameterHandler()
    if not entryUrl: entryUrl = params.getValue('sUrl')
    sHtmlContent = cRequestHandler(entryUrl, ignoreErrors=(sGui is not False)).request()
    pattern = "div[^>]*class='iwrap type_(\d*).*?"  # smType
    pattern += "<a[^>]*title='([^']*)'*[^>]*href='([^']*)'*>.*?"  # title / url
    pattern += "<img[^>]*src='([^']*)'[^>]*>.*?"  # thumbnail

    isMatch, aResult = cParser.parse(sHtmlContent, pattern)

    if not isMatch:
        if not sGui: oGui.showInfo('streamon', 'Es wurde kein Eintrag gefunden')
        return

    total = len(aResult)
    for smType, sName, sUrl, sThumbnail in aResult:
        isTvshow = True if "1" in smType else False
        oGuiElement = cGuiElement(sName, SITE_IDENTIFIER, 'showAllSeasons' if isTvshow else 'showHosters')
        oGuiElement.setMediaType('tvshow' if isTvshow else 'movie')
        oGuiElement.setThumbnail(sThumbnail)
        params.setParam('entryUrl', URL_MAIN + sUrl)
        params.setParam('sName', sName)
        params.setParam('sThumbnail', sThumbnail)
        oGui.addFolder(oGuiElement, params, isTvshow, total)

    if not sGui:
        aResult = cParser.parse(sHtmlContent, "<a[^>]class='active'.*?<a[^>]href='([^']*)'[^>]*>\d+<[^>]*>")
        if aResult[0] and aResult[1][0]:
            params.setParam('sUrl', URL_MAIN + aResult[1][0])
            oGui.addNextPage(SITE_IDENTIFIER, 'showEntries', params)

        oGui.setView('tvshows' if 'download_1' in entryUrl else 'movies')
        oGui.setEndOfDirectory()


def showAllSeasons():
    oGui = cGui()
    params = ParameterHandler()

    sUrl = params.getValue('entryUrl')

    sHtmlContent = cRequestHandler(sUrl).request()
    aResult = cParser().parse(sHtmlContent, "var[ ]subcats[ ]=[ ](.*?);")  # json for hoster

    if not aResult[0] or not aResult[1][0]:
        oGui.showInfo('streamon', 'Es wurde kein Eintrag gefunden')
        return

    data = json.loads(aResult[1][0])
    seasons = []
    for key, value in data.items():
        SeasonsNr = int(value['info']['staffel'])
        if SeasonsNr not in seasons:
            seasons.append(SeasonsNr)

    sThumbnail = params.getValue('sThumbnail')
    sName = params.getValue('sName')

    seasons = sorted(seasons)
    total = len(seasons)
    for iSeason in seasons:
        oGuiElement = cGuiElement()
        oGuiElement.setSiteName(SITE_IDENTIFIER)
        oGuiElement.setFunction('showAllEpisodes')
        oGuiElement.setTitle("Staffel " + str(iSeason))
        oGuiElement.setTVShowTitle(sName)
        oGuiElement.setSeason(iSeason)
        oGuiElement.setMediaType('season')
        oGuiElement.setThumbnail(sThumbnail)

        # oOutParms.setParam('entryUrl', sUrl)
        # oOutParms.setParam('sName', sName)
        # oOutParms.setParam('sThumbnail', sThumbnail)
        # oOutParms.setParam('iSeason', iSeason)
        # oOutParms.setParam('sJson', aResult[1][0])
        # whole json through parameters is not a good idea
        oGui.addFolder(oGuiElement, params, iTotal=total)
    oGui.setView('seasons')
    oGui.setEndOfDirectory()


def showAllEpisodes():
    oGui = cGui()

    params = ParameterHandler()
    iSeason = int(params.getValue('season'))
    sThumbnail = params.getValue('sThumbnail')
    url = params.getValue('entryUrl')

    # 2nd request of json should cached so no problem, 
    # temp file for json would be another option
    sHtmlContent = cRequestHandler(url).request()
    aResult = cParser().parse(sHtmlContent, "var[ ]subcats[ ]=[ ](.*?);")
    if not aResult[0] or not aResult[1][0]:
        return

    episodes = {}
    data = json.loads(aResult[1][0])
    for key, value in data.items():
        SeasonsNr = int(value['info']['staffel'])
        if SeasonsNr != iSeason:
            continue
        episodeNr = int(value['info']['nr'])
        if episodeNr not in episodes.keys():
            episodes.update({episodeNr: key})

    for iEpisodesNr, sEpisodesID in episodes.items():
        oGuiElement = cGuiElement()
        oGuiElement.setSiteName(SITE_IDENTIFIER)
        oGuiElement.setFunction('showHosters')
        epiName = data[sEpisodesID]['info']['name'].encode('utf-8')
        epiName = epiName.split("»")[0].strip()
        oGuiElement.setTitle(str(iEpisodesNr) + " - " + epiName)
        # oGuiElement.setTVShowTitle(sName)
        # oGuiElement.setSeason(iSeason)
        oGuiElement.setEpisode(iEpisodesNr)
        oGuiElement.setMediaType('episode')
        oGuiElement.setThumbnail(sThumbnail)
        params.setParam('sJsonID', sEpisodesID)
        oGui.addFolder(oGuiElement, params, bIsFolder=False)

    oGui.setView('episodes')
    oGui.setEndOfDirectory()


def showHosters():
    params = ParameterHandler()
    sHtmlContent = cRequestHandler(params.getValue('entryUrl')).request()
    aResult = cParser().parse(sHtmlContent, "var[ ]subcats[ ]=[ ](.*?);")
    if not aResult[0]: return []

    hosters = []
    data = json.loads(aResult[1][0])
    sJsonID = params.getValue('sJsonID')
    if not sJsonID:
        sJsonID = data.keys()[0]
    partCount = 1  # fallback for series (because they get no MultiParts)
    if '1' in data[sJsonID]:
        partCount = int(data[sJsonID]['1'])
    for jHoster in data[sJsonID]['links']:
        for jHosterEntry in data[sJsonID]['links'][jHoster]:
            if jHosterEntry[5] != 'stream': continue
            hoster = {}
            if partCount > 1:
                hoster['displayedName'] = jHoster + ' - Part ' + jHosterEntry[0]
            hoster['link'] = jHosterEntry[3]
            hoster['name'] = jHoster
            hosters.append(hoster)

    if len(hosters) > 0:
        hosters.append('getHosterUrl')
    return hosters


def getHosterUrl(sUrl=False):
    if not sUrl: sUrl = ParameterHandler().getValue('url')
    results = []
    result = {'streamUrl': sUrl, 'resolved': False}
    results.append(result)
    return results


def _stripTitle(sName):
    sName = sName.replace("- Serie", "")
    sName = sName.replace("(English)", "")
    sName = sName.replace("(Serie)", "")
    return sName.strip()


def showSearch():
    oGui = cGui()
    sSearchText = oGui.showKeyBoard()
    if not sSearchText: return
    _search(False, sSearchText)
    oGui.setEndOfDirectory()


def _search(oGui, sSearchText):
    if not sSearchText: return
    showEntries(URL_SEARCH + sSearchText.strip(), oGui)
