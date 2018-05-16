# -*- coding: utf-8 -*-
from resources.lib.gui.gui import cGui
from resources.lib.gui.guiElement import cGuiElement
from resources.lib.handler.requestHandler import cRequestHandler
from resources.lib.parser import cParser
from resources.lib import logger
from resources.lib.handler.ParameterHandler import ParameterHandler

from resources.lib.cCFScrape import cCFScrape
import re, json, base64

# Plugin-Eigenschaften
SITE_IDENTIFIER = 'hdfilme_tv'
SITE_NAME = 'HDfilme'
SITE_ICON = 'hdfilme.png'

# Basis-URL's
URL_MAIN = 'http://hdfilme.tv/'
URL_MOVIES = URL_MAIN + 'movie-movies?'
URL_SHOWS = URL_MAIN + 'movie-series?'
URL_SEARCH = URL_MAIN + 'movie-search?key=%s'
URL_GETLINK = URL_MAIN + 'movie/getlink/'

# Parameter für die Sortierung
URL_PARMS_ORDER_UPDATE = 'sort=top'
URL_PARMS_ORDER_UPDATE_ASC = URL_PARMS_ORDER_UPDATE + '&sort_type=asc'
URL_PARMS_ORDER_YEAR = 'sort=year'
URL_PARMS_ORDER_YEAR_ASC = URL_PARMS_ORDER_YEAR + '&sort_type=asc'
URL_PARMS_ORDER_NAME = 'sort=name'
URL_PARMS_ORDER_NAME_ASC = URL_PARMS_ORDER_NAME + '&sort_type=asc'
URL_PARMS_ORDER_VIEWS = 'sort=view'
URL_PARMS_ORDER_VIEWS_ASC = URL_PARMS_ORDER_VIEWS + '&sort_type=asc'
URL_PARMS_ORDER_IMDB = 'sort=imdb'
URL_PARMS_ORDER_IMDB_ASC = URL_PARMS_ORDER_IMDB + '&sort_type=asc'
URL_PARMS_ORDER_HDRATE = 'sort=rate'
URL_PARMS_ORDER_HDRATE_ASC = URL_PARMS_ORDER_HDRATE + '&sort_type=asc'

QUALITY_ENUM = {'240': 0, '360': 1, '480': 2, '720': 3, '1080': 4}


def load():
    # Logger-Eintrag
    logger.info("Load %s" % SITE_NAME)

    # GUI-Element erzeugen
    oGui = cGui()

    # ParameterHandler erzeugen
    params = ParameterHandler()

    # Einträge anlegen
    params.setParam('sUrl', URL_MOVIES)
    oGui.addFolder(cGuiElement('Filme', SITE_IDENTIFIER, 'showContentMenu'), params)
    params.setParam('sUrl', URL_SHOWS)
    oGui.addFolder(cGuiElement('Serien', SITE_IDENTIFIER, 'showContentMenu'), params)
    oGui.addFolder(cGuiElement('Suche', SITE_IDENTIFIER, 'showSearch'))

    # Liste abschließen
    oGui.setEndOfDirectory()


def showContentMenu():
    # GUI-Element erzeugen
    oGui = cGui()

    # ParameterHandler erzeugen
    params = ParameterHandler()

    # Basis-URL ermitteln (Filme oder Serien)
    baseURL = params.getValue('sUrl')

    # Einträge anlegen
    params.setParam('sUrl', baseURL + URL_PARMS_ORDER_UPDATE)
    oGui.addFolder(cGuiElement('Neu hinzugefügt', SITE_IDENTIFIER, 'showEntries'), params)
    params.setParam('sUrl', baseURL + URL_PARMS_ORDER_YEAR)
    oGui.addFolder(cGuiElement('Herstellungsjahr', SITE_IDENTIFIER, 'showEntries'), params)
    params.setParam('sUrl', baseURL + URL_PARMS_ORDER_NAME_ASC)
    oGui.addFolder(cGuiElement('Alphabetisch', SITE_IDENTIFIER, 'showEntries'), params)
    params.setParam('sUrl', baseURL + URL_PARMS_ORDER_VIEWS)
    oGui.addFolder(cGuiElement('Top Aufrufe', SITE_IDENTIFIER, 'showEntries'), params)
    params.setParam('sUrl', baseURL + URL_PARMS_ORDER_IMDB)
    oGui.addFolder(cGuiElement('IMDB Punkt', SITE_IDENTIFIER, 'showEntries'), params)
    params.setParam('sUrl', baseURL + URL_PARMS_ORDER_HDRATE)
    oGui.addFolder(cGuiElement('Bewertung HDFilme.tv', SITE_IDENTIFIER, 'showEntries'), params)
    params.setParam('sUrl', baseURL)
    oGui.addFolder(cGuiElement('Genre', SITE_IDENTIFIER, 'showGenreList'), params)

    # Liste abschließen
    oGui.setEndOfDirectory()


def showGenreList():
    # GUI-Element erzeugen
    oGui = cGui()

    # ParameterHandler erzeugen
    params = ParameterHandler()

    # URL vom ParameterHandler ermitteln
    entryUrl = params.getValue('sUrl')

    # Movie-Seite laden
    sHtmlContent = cRequestHandler(entryUrl).request()

    # Select für Generes-Container
    pattern = '<select[^>]*name="category"[^>]*>(.*?)</select[^>]*>'

    # Regex parsen
    isMatch, sContainer = cParser.parseSingleResult(sHtmlContent, pattern)

    # Nichts gefunden? => raus hier
    if not isMatch:
        logger.debug("genre regex not matched")
        return

    # Filter für Genres
    pattern = '<option[^>]*value="(\d[^ ]*)"[^>]*>(.*?)</option[>]'

    # Regex parsen
    isMatch, aResult = cParser.parse(sContainer, pattern)

    # Nichts gefunden? => raus hier
    if not isMatch:
        logger.debug("value regex not matched")
        return

    # Alle Genres durchlaufen und Liste erzeugen
    for sID, sGenre in sorted(aResult, key=lambda k: k[1]):
        params.setParam('sUrl', entryUrl + 'category=' + sID + '&country=&order_f=last_update')
        oGui.addFolder(cGuiElement(sGenre.strip(), SITE_IDENTIFIER, 'showEntries'), params)

    # Liste abschließen
    oGui.setEndOfDirectory()


def showEntries(entryUrl=False, sGui=False):
    # GUI-Element erzeugen wenn nötig
    oGui = sGui if sGui else cGui()

    # ParameterHandler erzeugen
    params = ParameterHandler()

    # URL ermitteln falls nicht übergeben
    if not entryUrl: entryUrl = params.getValue('sUrl')

    # Aktuelle Seite ermitteln und ggf. URL anpassen
    iPage = int(params.getValue('page'))

    # Daten ermitteln
    oRequest = cRequestHandler(entryUrl + '&page=' + str(iPage) if iPage > 0 else entryUrl,
                               ignoreErrors=(sGui is not False))
    sHtmlContent = oRequest.request()

    # Filter out the main section
    pattern = '<ul class="products row">(.*?)</ul>'
    isMatch, aMainContents = cParser.parse(sHtmlContent, pattern)

    # Funktion verlassen falls keine Daten ermittelt werden konnten
    if not isMatch:
        if not sGui: oGui.showInfo('streamon', 'Es wurde kein Eintrag gefunden')
        return

    # Gefundenen Bereiche zusammenführen (tritt z.b bei der Suche auf)
    sMainContent = ''
    for content in aMainContents:
        sMainContent += content

    # Funktion verlassen falls keine Daten ermittelt werden konnten
    if not sMainContent:
        if not sGui: oGui.showInfo('streamon', 'Es wurde kein Eintrag gefunden')
        return

    # URL ermitteln
    pattern = '<div[^>]*class="box-product clearfix"[^>]*>\s*?'
    pattern += '<a[^>]*href="([^"]*)"[^>]*>.*?'

    # Thumbnail ermitteln
    pattern += '<img[^>]*src="([^"]*)"[^>]*>.*?'

    # Prüfung auf Episoden-Einträge
    pattern += '(?:<div[^>]*class="episode"[^>]*>([^"]*)</div>.*?)?'

    # Name ermitteln
    pattern += '<div[^>]*class="popover-title"[^>]*>.*?'
    pattern += '<span[^>]*class="name"[^>]*>([^<>]*)</span>.*?'

    # Beschreibung ermitteln
    pattern += '<div[^>]*class="popover-content"[^>]*>.*?<p>([^<]+)</p>'

    # HTML parsen
    isMatch, aResult = cParser.parse(sMainContent, pattern)

    # Kein Einträge gefunden? => Raus hier
    if not isMatch:
        if not sGui: oGui.showInfo('streamon', 'Es wurde kein Eintrag gefunden')
        return

    # Listengröße ermitteln
    total = len(aResult)

    # Alle Ergebnisse durchlaufen
    for sUrl, sThumbnail, sEpisodeNrs, sName, sDesc in aResult:
        # Bei Filmen das Jahr vom Title trennen
        aYear = re.compile("(.*?)\((\d*)\)").findall(sName)
        iYear = False
        for name, year in aYear:
            sName = name
            iYear = year
            break

        # prüfen ob der Eintrag ein Serie/Staffel ist
        isTvshow = True if sEpisodeNrs else False

        # Listen-Eintrag erzeugen
        sUIElementName = sName

        if URL_PARMS_ORDER_YEAR in entryUrl:
            sUIElementName += ' (' + str(iYear) + ')'

        oGuiElement = cGuiElement(sUIElementName, SITE_IDENTIFIER, 'showHosters')

        # Bei Serien Title anpassen
        res = re.search('(.*?)\s(?:staf+el|s)\s*(\d+)', sName, re.I)
        if res:
            oGuiElement.setTVShowTitle(res.group(1))
            oGuiElement.setTitle('%s - Staffel %s' % (res.group(1), int(res.group(2))))
            params.setParam('sSeason', int(res.group(2)))
        elif not res and isTvshow:
            oGuiElement.setTVShowTitle(sName)
            oGuiElement.setTitle('%s - Staffel %s' % (sName, "1"))
            params.setParam('sSeason', "1")

        # Thumbnail und Beschreibung für Anzeige anpassen
        sThumbnail = sThumbnail.replace('_thumb', '')
        sThumbnail = cCFScrape.createUrl(sThumbnail, oRequest)

        # Falls vorhanden Jahr ergänzen
        if iYear:
            oGuiElement.setYear(iYear)

        # Eigenschaften setzen und Listeneintrag hinzufügen
        oGuiElement.setThumbnail(sThumbnail)
        oGuiElement.setMediaType('tvshow' if isTvshow else 'movie')
        oGuiElement.setDescription(sDesc)
        params.setParam('entryUrl', sUrl)
        params.setParam('sName', sName)
        params.setParam('sThumbnail', sThumbnail)
        params.setParam('isTvshow', isTvshow)
        oGui.addFolder(oGuiElement, params, isTvshow, total)

    # Nur ausführen wenn das Gui-Element Plugin intern ist
    if not sGui:
        # Pattern um die Aktuelle Seite zu ermitteln
        # pattern = '<ul[^>]*class="pagination[^>]*>.*?'
        # pattern += '<li[^>]*class="\s*active\s*"[^>]*>.*?</li>.*?<a[^>]*>(\d*)</a>.*?</ul>'

        # Seite parsen
        # isMatch, sPageNr = cParser.parse(sHtmlContent, pattern)

        sPageNr = int(params.getValue('page'))
        if sPageNr == 0:
            sPageNr = 2
        else:
            sPageNr += 1

        # TODO: Fallunterscheidung entfernt, weil hdfilme die pagination unzuverlässig anzeigt
        # Falls ein Ergebniss gefunden wurden "Next-Page" ergänzen
        # if isMatch:
        params = ParameterHandler()
        params.setParam('page', int(sPageNr))
        params.setParam('sUrl', entryUrl)
        oGui.addNextPage(SITE_IDENTIFIER, 'showEntries', params)

        # Liste abschließen und View setzen
        oGui.setView('tvshows' if URL_SHOWS in entryUrl else 'movies')
        oGui.setEndOfDirectory()


def showHosters():
    # ParameterHandler erzeugen
    params = ParameterHandler()

    # URL Anpassen um die Stream und nicht die Infos zu bekommen
    entryUrl = params.getValue('entryUrl').replace("-info", "-stream")

    # Seite abrufen
    sHtmlContent = cRequestHandler(entryUrl).request()

    # Prüfen ob Episoden gefunden werden
    pattern = '<a[^>]*episode="([^"]*)"[^>]*href="([^"]*)"[^>]*>([^<]*)<\/a'
    isMatch, aResult = cParser.parse(sHtmlContent, pattern)

    # Prüfen ob Einträge vorliegen
    if not isMatch:
        return

    # Ermitteln ob es sich um eine Serie handelt
    isTvshowEntry = params.getValue('isTvshow')

    # Falls Episoden gefunden worden => Episodenauswahl vorschalten
    if isTvshowEntry == 'True':
        showEpisodes(aResult, params)
    else:
        return getHosters(entryUrl)


def showEpisodes(aResult, params):
    # GUI-Element erzeugen wenn nötig
    oGui = cGui()

    # Variable für Ansicht vorbereiten
    sTVShowTitle = params.getValue('TVShowTitle')
    sName = params.getValue('sName')
    sThumbnail = params.getValue('sThumbnail')
    sSeason = params.getValue('sSeason')

    # Listengröße ermitteln
    total = len(aResult)

    # Alle Folgen durchlaufen und Einträge erzeugen
    for iEpisode, sUrl, sEpisodeTitle in aResult:
        sName = 'Folge ' + sEpisodeTitle.strip()
        sEpisodeTitle = sEpisodeTitle.strip()
        oGuiElement = cGuiElement(sName, SITE_IDENTIFIER, 'getHosters')
        oGuiElement.setMediaType('episode')
        oGuiElement.setTVShowTitle(sTVShowTitle)
        oGuiElement.setSeason(sSeason)
        oGuiElement.setEpisode(iEpisode)
        oGuiElement.setThumbnail(sThumbnail)
        params.setParam('sEpisodeTitle', sEpisodeTitle)
        params.setParam('sUrl', sUrl)
        params.setParam('sName', sName)
        oGui.addFolder(oGuiElement, params, False, total)

    # Ansicht auf "Episoden" setze
    oGui.setView('episodes')

    # Liste abschließen
    oGui.setEndOfDirectory()


def getHosters(sUrl=False):
    # ParameterHandler erzeugen 
    params = ParameterHandler()

    # URL und Name ermitteln falls nicht übergeben
    sUrl = sUrl if sUrl else params.getValue('sUrl')

    # Seite abrufen
    sHtmlContent = cRequestHandler(sUrl).request()

    # Servername und Episoden pro Server ermitteln
    pattern = "<ul[^>]*class=['\"]list-inline list-film['\"][^>]*>.*?([a-zA-Z0-9_ ]+)</div>(.*?)</ul>"
    isMatch, aResult = cParser.parse(sHtmlContent, pattern)

    # Hosterliste initialisieren
    hosters = []

    # Prüfen ob Server ermittelt werden konnte 
    if isMatch:
        # Prüfen ob eine direkte-Episode gewünscht ist
        aMatches = re.compile("episode=(\d+)$").findall(sUrl)

        # gewünsche Episode ermitteln wenn möglich
        sEpisode = "1" if not aMatches else aMatches[0]

        # Server-Block durchlaufen
        for sServername, sInnerHtml in aResult:
            # Alle Links für diesen Server ermitteln 
            isMatch, aResult = cParser.parse(sInnerHtml, "href=['\"]([^'\"]*)['\"][^>]*>")
            
            # Keine Links gefunden? => weiter machen 
            if not isMatch:
                continue

            # Alle Links durchlaufen
            for singleUrl in aResult:
                # Link auf korrekte Episode prüfen
                aMatches = re.compile("episode=(%s)$" % sEpisode).findall(singleUrl)

                # Wurde ein Link gefunden? => Einträge zur Gesamtliste hinzufügen
                if aMatches:
                    res = re.search("(\d+)-stream(?:\?episode=(\d+))?", singleUrl, re.I)
                    if res:
                        hosters.extend(_getHostFromUrl(res.group(1), res.group(2), sServername))

    # Sind Hoster vorhanden? => Nachfolgefunktion ergänzen
    if hosters:
        hosters.append('play')
    return hosters


def _getHostFromUrl(sID, sEpisode, sServername):
    # Seite abrufen
    sHtmlContent = cRequestHandler(URL_GETLINK + sID + '/' + sEpisode).request()
    sHtmlContent = base64.b64decode(str(sHtmlContent))

    if sHtmlContent is None:
        logger.info("result string is none")
        return []

    try:
        getLinkResponseJson = json.loads(sHtmlContent)
    except (ValueError, TypeError):
        logger.debug("could not decode server response")
        return []

    if 'playinfo' not in getLinkResponseJson:
        logger.info("no playable sources")
        return []

    hosters = []

    for playableEntry in getLinkResponseJson['playinfo']:
        hoster = dict()
        quality = playableEntry["label"]
        url = playableEntry["file"]
        label = sServername + ' - ' + quality
        if quality in QUALITY_ENUM:
            hoster['quality'] = QUALITY_ENUM[quality]
        hoster['link'] = url
        hoster['name'] = label
        hoster['resolveable'] = True
        hosters.append(hoster)

    return hosters

def play(sUrl=False):
    # ParameterHandler erzeugen
    oParams = ParameterHandler()

    # URL ermitteln falls nicht übergeben
    if not sUrl: sUrl = oParams.getValue('url')

    # Array mit einem Eintrag für Hosterliste erzeugen (sprich direkt abspielen)
    results = []
    ref = oParams.getValue('entryUrl').replace("-info", "-stream")
    result = {'streamUrl':  sUrl + '|Referer=' + ref + '|User-Agent=Mozilla/5.0 (Windows NT 6.3; rv:36.0) Gecko/20100101 Firefox/36.0', 'resolved': True}
    results.append(result)

    # Ergebniss zurückliefern
    return results

# Sucher über UI
def showSearch():
    # Gui-Elemet erzeugen
    oGui = cGui()

    # Tastatur anzeigen und Eingabe ermitteln
    sSearchText = oGui.showKeyBoard()

    # Keine Eingabe? => raus hier
    if not sSearchText: return

    # Suche durchführen
    _search(False, sSearchText)

    # Liste abschließen und View setzen
    oGui.setView()
    oGui.setEndOfDirectory()

# Such-Funktion (z.b auch für Globale-Suche)
def _search(oGui, sSearchText):
    # Keine Eingabe? => raus hier
    if not sSearchText: return

    # Unnötigen Leerzeichen entfernen
    sSearchText = sSearchText.strip()

    # URL-Übergeben und Ergebniss anzeigen
    showEntries(URL_SEARCH % sSearchText, oGui)
