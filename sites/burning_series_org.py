# -*- coding: utf-8 -*-
from resources.lib.gui.gui import cGui
from resources.lib.gui.guiElement import cGuiElement
from resources.lib.handler.requestHandler import cRequestHandler
from resources.lib.handler.ParameterHandler import ParameterHandler
from resources.lib import logger
import string
import json
import random
import xbmcgui
from resources.lib.bs_finalizer import *

# "Global" variables
SITE_IDENTIFIER = 'burning_series_org'
SITE_NAME = 'BurningSeries'
SITE_ICON = 'burning_series.png'

URL_MAIN = 'https://www.bs.to/api/'
URL_COVER = 'https://bs.to/public/img/cover/%s.jpg|encoding=gzip'

# Mainmenu
def load():
    logger.info("Load %s" % SITE_NAME)
    oGui = cGui()
    oGui.addFolder(cGuiElement('Alle Serien', SITE_IDENTIFIER, 'showSeries'))
    oGui.addFolder(cGuiElement('A-Z', SITE_IDENTIFIER, 'showCharacters'))
    oGui.addFolder(cGuiElement('Genre', SITE_IDENTIFIER, 'showGenres'))
    oGui.addFolder(cGuiElement('Zufall', SITE_IDENTIFIER, 'showRandom'))
    oGui.addFolder(cGuiElement('Suche', SITE_IDENTIFIER, 'showSearch'))
    oGui.setEndOfDirectory()

### Mainmenu entries

# Show all series in a big list
def showSeries():
    oGui = cGui()
    oParams = ParameterHandler()
    sChar = oParams.getValue('char')
    if sChar: sChar = sChar.lower()
    series = _getJsonContent("series")
    if not series:
        oGui.showInfo('streamon', 'Es wurde kein Eintrag gefunden')
        return
    total = len(series)
    for serie in series:
        sTitle = serie["series"].encode('utf-8')
        if sChar:
            if sChar == '#':
                if sTitle[0].isalpha(): continue
            elif sTitle[0].lower() != sChar: continue
        guiElement = cGuiElement(sTitle, SITE_IDENTIFIER, 'showSeasons')
        if oParams.getValue('specific') == 'Season':
            guiElement.setFunction('randomSeason')
        guiElement.setMediaType('tvshow')
        guiElement.setThumbnail(URL_COVER % serie["id"])
        # Load series description by iteration through the REST-Api (slow)
        #sDesc = _getJsonContent("series/%d/1" % int(serie['id']))
        #guiElement.setDescription(sDesc['series']['description'].encode('utf-8'))
        #sStart = str(sDesc['series']['start'])
        #if sStart != 'None':
        #   guiElement.setYear(int(sDesc['series']['start']))
        oParams.addParams({'seriesID' : str(serie["id"]), 'Title' : sTitle})
        oGui.addFolder(guiElement, oParams, iTotal = total)

    oGui.setView('tvshows')
    oGui.setEndOfDirectory()

# Show an alphabetic list 'A-Z' prepended by '#' for alphanumeric series
def showCharacters():
    oGui = cGui()
    oParams = ParameterHandler()
    oGuiElement = cGuiElement('#', SITE_IDENTIFIER, 'showSeries')
    oParams.setParam('char', '#')
    oGui.addFolder(oGuiElement, oParams)
    for letter in string.uppercase[:26]:
        oGuiElement = cGuiElement(letter, SITE_IDENTIFIER, 'showSeries')
        oParams.setParam('char', letter)
        oGui.addFolder(oGuiElement, oParams)
    oGui.setEndOfDirectory()

# Show a list of all available genres
def showGenres():
    oGui = cGui()
    oParams = ParameterHandler()
    sGenre = oParams.getValue('genreID')
    genres = _getJsonContent("series:genre")
    if not genres:
        oGui.showInfo('streamon', 'Es wurde kein Eintrag gefunden')
        return
    total = len(genres)
    for genre in sorted(genres):
        genreID = str(genres[genre]["id"])

        if not sGenre:
            guiElement = cGuiElement(genre.encode('utf-8'), SITE_IDENTIFIER, 'showGenres')
            oParams.setParam('genreID', genreID)
            oGui.addFolder(guiElement, oParams, iTotal=total)
        else:
            if genreID != sGenre: continue

            for serie in genres[genre]["series"]:
                sTitle = serie["name"].encode('utf-8')
                guiElement = cGuiElement(sTitle, SITE_IDENTIFIER, 'showSeasons')
                guiElement.setMediaType('tvshow')
                guiElement.setThumbnail(URL_COVER % serie["id"])
                oParams.addParams({'seriesID': str(serie["id"]), 'Title': sTitle})
                oGui.addFolder(guiElement, oParams, iTotal=total)

    if sGenre:
        oGui.setView('tvshows')
    oGui.setEndOfDirectory()

# Show the search dialog, return/abort on empty input
def showSearch():
    oGui = cGui()
    sSearchText = oGui.showKeyBoard()
    if not sSearchText: return
    _search(False, sSearchText)
    oGui.setView('tvshows')
    oGui.setEndOfDirectory()

### Helper functions

# Load a JSON object
def _getJsonContent(urlPart, ignoreErrors = False):
    request = cRequestHandler(URL_MAIN + urlPart, ignoreErrors=ignoreErrors)
    mod_request(request, urlPart)
    content = request.request()
    if content:
        aJson = json.loads(content)
        if 'error' in aJson:
            logger.info("API-Error: %s" % aJson)
            if not ignoreErrors:
                if 'unauthorized' in aJson and aJson['unauthorized'] == 'timestamp':
                    xbmcgui.Dialog().ok('streamon', 'Fehler bei API-Abfrage:','','System-Zeit ist nicht korrekt.')
                else:
                    xbmcgui.Dialog().ok('streamon', 'Fehler bei API-Abfrage:','',str(aJson))
            return []
        else:
            return aJson
    else:
        return []

# Search for series using the requested string sSearchText
def _search(sGui, sSearchText):
    oGui = sGui if sGui else cGui()
    params = ParameterHandler()
    series = _getJsonContent("series", ignoreErrors = (sGui is not False))
    if not series:
        if not sGui: oGui.showInfo('streamon', 'Es wurde kein Eintrag gefunden')
        return
    total = len(series)
    sSearchText = sSearchText.lower()
    for serie in series:
        sTitle = serie["series"].encode('utf-8')
        if sTitle.lower().find(sSearchText) == -1: continue
        guiElement = cGuiElement(sTitle, SITE_IDENTIFIER, 'showSeasons')
        guiElement.setMediaType('tvshow')
        guiElement.setThumbnail(URL_COVER % serie["id"])
        params.addParams({'seriesID' : str(serie["id"]), 'Title' : sTitle})
        oGui.addFolder(guiElement, params, iTotal = total)

# Show a list of seasons for a requested series, and movies if available
def showSeasons():
    oGui = cGui()
    params = ParameterHandler()
    sTitle = params.getValue('Title')
    seriesId = params.getValue('seriesID')

    logger.info("%s: show seasons of '%s' " % (SITE_NAME, sTitle))

    data = _getJsonContent("series/%s/1" % seriesId)

    if not data:
        oGui.showInfo('streamon', 'Es wurde kein Eintrag gefunden')
        return

    rangeStart = not int(data["series"]["movies"])
    total = int(data["series"]["seasons"])
    for i in range(rangeStart, total + 1):
        seasonNum = str(i)
        if i is 0:
            seasonTitle = 'Film(e)'
            dialogType = 'showCinemaMovies'
        else:
            seasonTitle = '%s - Staffel %s' %(sTitle, seasonNum)
            if params.getValue('specific') == 'Episode':
                dialogType = 'randomEpisode'
            else:
                dialogType = 'showEpisodes'
        guiElement = cGuiElement(seasonTitle, SITE_IDENTIFIER, dialogType)
        guiElement.setMediaType('season')
        guiElement.setSeason(seasonNum)
        guiElement.setTVShowTitle(sTitle)
        guiElement.setDescription(data["series"]["description"])
        guiElement.setThumbnail(URL_COVER % data["series"]["id"])
        params.setParam('Season', seasonNum)
        oGui.addFolder(guiElement, params, iTotal = total)
    oGui.setView('seasons')
    oGui.setEndOfDirectory()

# Show episodes of a requested season for a series
def showEpisodes():
    oGui = cGui()
    oParams = ParameterHandler()
    sShowTitle = oParams.getValue('Title')
    seriesId = oParams.getValue('seriesID')
    sSeason = oParams.getValue('Season')

    logger.info("%s: show episodes of '%s' season '%s' " % (SITE_NAME, sShowTitle, sSeason))

    data = _getJsonContent("series/%s/%s" % (seriesId, sSeason))

    if not data:
        oGui.showInfo('streamon', 'Es wurde kein Eintrag gefunden')
        return

    total = len(data['epi'])
    for episode in data['epi']:
        title = "%d - " % int(episode['epi'])
        if episode['german']:
            title += episode['german'].encode('utf-8')
        else:
            title += episode['english'].encode('utf-8')
        guiElement = cGuiElement(title, SITE_IDENTIFIER, 'showHosters')
        guiElement.setMediaType('episode')
        guiElement.setSeason(data['season'])
        guiElement.setEpisode(episode['epi'])
        guiElement.setTVShowTitle(sShowTitle)
        guiElement.setThumbnail(URL_COVER % data["series"]["id"])
        guiElement.setDescription(data["series"]["description"])
        oParams.setParam('EpisodeNr', episode['epi'])
        oGui.addFolder(guiElement, oParams, bIsFolder = False, iTotal = total)
    oGui.setView('episodes')
    oGui.setEndOfDirectory()

def showCinemaMovies():
    oGui = cGui()
    oParams = ParameterHandler()
    seriesId = oParams.getValue('seriesID')

    data = _getJsonContent("series/%s/0" % (seriesId))

    if not data:
        oGui.showInfo('streamon', 'Es wurde kein Eintrag gefunden')
        return

    total = len(data['epi'])
    for movie in data['epi']:
        if movie['german']:
            title = movie['german'].encode('utf-8')
        else:
            title = movie['english'].encode('utf-8')
        guiElement = cGuiElement(title, SITE_IDENTIFIER, 'showHosters')
        guiElement.setMediaType('movie')
        guiElement.setTitle(title)
        guiElement.setThumbnail(URL_COVER % data["series"]["id"])
        guiElement.setDescription(data["series"]["description"])
        oParams.setParam('EpisodeNr', movie['epi'])
        oGui.addFolder(guiElement, oParams, bIsFolder = False, iTotal = total)
    oGui.setView('movies')
    oGui.setEndOfDirectory()
    
def showRandom():
    oGui = cGui()
    oParams = ParameterHandler()

    oGui.addFolder(cGuiElement('Zufällige Serie', SITE_IDENTIFIER, 'randomSerie'))
    oParams.setParam('specific', 'Season')
    oGui.addFolder(cGuiElement('Zufällige Staffel', SITE_IDENTIFIER, 'randomSeason'), oParams)
    oParams.setParam('specific', 'Episode')
    oGui.addFolder(cGuiElement('Zufällige Episode', SITE_IDENTIFIER, 'randomEpisode'), oParams)

    oGui.setEndOfDirectory()

def randomSerie():
    oGui = cGui()
    oParams = ParameterHandler()
    series = _getJsonContent('series')
    if not series:
        oGui.showInfo('streamon', 'Es wurde kein Eintrag gefunden')
        return
    serie = random.choice(series)
    sTitle = serie["series"].encode('utf-8')
    guiElement = cGuiElement(sTitle, SITE_IDENTIFIER, 'showSeasons')
    guiElement.setMediaType('tvshow')
    guiElement.setThumbnail(URL_COVER % serie["id"])
    oParams.addParams({'seriesID': str(serie["id"]), 'Title': sTitle})
    oGui.addFolder(guiElement, oParams, iTotal=1)
    oGui.setView('tvshows')
    oGui.setEndOfDirectory()

def randomSeason():
    oGui = cGui()
    oParams = ParameterHandler()
    if oParams.getValue('specific') == 'Season' and not oParams.getValue('seriesID'):
        showSeries()
        return

    data = _getJsonContent("series/%s/1" % oParams.getValue('seriesID'))
    if not data:
        oGui.showInfo('streamon', 'Es wurde kein Eintrag gefunden')
        return

    seasons = int(data["series"]["seasons"])+1

    randomSeason = random.randint(1, seasons)

    seasonNum = str(randomSeason)
    seasonTitle = '%s - Staffel %s' % (oParams.getValue('Title'), seasonNum)
    dialogType = 'showEpisodes'
    guiElement = cGuiElement(seasonTitle, SITE_IDENTIFIER, dialogType)
    guiElement.setMediaType('season')
    guiElement.setSeason(seasonNum)
    guiElement.setTVShowTitle(oParams.getValue('Title'))
    guiElement.setDescription(data["series"]["description"])

    oParams.setParam('Season', seasonNum)
    guiElement.setThumbnail(URL_COVER % data["series"]["id"])
    oGui.addFolder(guiElement, oParams, iTotal=1)
    oGui.setView('seasons')
    oGui.setEndOfDirectory()

def randomEpisode():
    oGui = cGui()
    oParams = ParameterHandler()
    if oParams.getValue('specific') == 'Episode' and not oParams.getValue('seriesID'):
        showSeries()
        return
    elif oParams.getValue('seriesID') and not oParams.getValue('Season'):
        showSeasons()
        return
    else:
        series = {'id': oParams.getValue('seriesID'), 'series': oParams.getValue('Title')}

    season = _getJsonContent("series/%s/1" % series['id'])
    if not season:
        oGui.showInfo('streamon', 'Es wurde kein Eintrag gefunden')
        return
    randomEpisodeNr = (random.choice(season['epi']))['epi']
    randomEpisode = filter(lambda person: person['epi'] == randomEpisodeNr, season['epi'])[0]

    Title = season['series']['series'].encode('utf-8') + ' - Staffel ' + str(season['season']) + ' - '
    if randomEpisode['german']:
        Title += randomEpisode['german'].encode('utf-8')
    else:
        Title += randomEpisode['english'].encode('utf-8')

    guiElement = cGuiElement(Title, SITE_IDENTIFIER, 'showHosters')
    guiElement.setMediaType('episode')
    guiElement.setEpisode(randomEpisodeNr)
    guiElement.setSeason(season['season'])
    guiElement.setTVShowTitle(series['series'])
    guiElement.setThumbnail(URL_COVER % int(season['series']['id']))
    guiElement.setDescription(season["series"]["description"])
    oParams.setParam('EpisodeNr', randomEpisodeNr)
    oParams.setParam('seriesID', season['series']['id'])
    oParams.setParam('Season', season['season'])
    oGui.addFolder(guiElement, oParams, bIsFolder=False, iTotal=1)

    oGui.setView('episodes')
    oGui.setEndOfDirectory()
 
# Show a hoster dialog for a requested episode
def showHosters():
    oParams= ParameterHandler()
    seriesId = oParams.getValue('seriesID')
    season = oParams.getValue('Season')
    episode = oParams.getValue('EpisodeNr')

    data = _getJsonContent("series/%s/%s/%s" % (seriesId, season, episode))

    if not data:
        return []

    hosters = []
    for link in data['links']:
        hoster = dict()
        hoster['link'] = URL_MAIN + 'watch/' + link['id']
        hoster['name'] = link['hoster']
        if hoster['name'] == "OpenLoadHD":
            hoster['name'] = "OpenLoad"
        hoster['displayedName'] = link['hoster']
        hosters.append(hoster)
    if hosters:
        hosters.append('getHosterUrl')
    return hosters

# Load a url for a requested host
def getHosterUrl(sUrl = False):
    oParams = ParameterHandler()
    if not sUrl: sUrl = oParams.getValue('url')
    data = _getJsonContent(sUrl.replace(URL_MAIN, ''))

    if not data:
        return []

    results = []
    result = {}
    if data['fullurl'].startswith('http'):
        result['streamUrl'] = data['fullurl']
    else:
        result['streamID'] = data['url']
        result['host'] = data['hoster']
        if result['host'] == "OpenLoadHD":
            result['host'] = "OpenLoad"
    result['resolved'] = False
    results.append(result)
    return results
