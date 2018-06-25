# -*- coding: utf-8 -*-
import sys
import urllib

import xbmc
import xbmcgui
import xbmcplugin

from resources.lib import common
from resources.lib.config import cConfig
from resources.lib.gui.contextElement import cContextElement
from resources.lib.gui.guiElement import cGuiElement
from resources.lib.handler.ParameterHandler import ParameterHandler


#import xbmcaddon
#from sys import path
#from xbmc import translatePath

#traktPath = xbmcaddon.Addon(id = 'script.trakt').getAddonInfo('path')
#print traktPath
#path.append(translatePath(traktPath))
#import traktapi
#watchedList = traktapi.traktAPI().getWatchedEpisodeLibrary()
#print watchedList

class cGui:
    '''
    This class "abstracts" a list of xbmc listitems.
    '''

    def __init__(self):
        try:
            self.pluginHandle = int( sys.argv[ 1 ] )
        except :
            self.pluginHandle = 0
        try:
            self.pluginPath = sys.argv[0]
        except:
            self.pluginPath = ''
        self.isMetaOn = cConfig().getSetting('metahandler')=='true'
        if cConfig().getSetting('metaOverwrite')=='true':
           self.metaMode = 'replace'
        else:
           self.metaMode = 'add'

        #for globalSearch or alterSearch
        self.globalSearch = False
        self._collectMode = False
        self._isViewSet = False
        self.searchResults = []



    def addFolder(self, oGuiElement, outParams='', bIsFolder = True, iTotal = 0, isHoster = False):
        '''
        add GuiElement to Gui, adds listitem to a list
        '''
        # abort xbmc list creation if user requests abort
        if xbmc.abortRequested:
            self.setEndOfDirectory(False)
            raise RuntimeError('UserAborted')
        # store result in list if we searched global for other sources
        if  self._collectMode:
            import copy
            self.searchResults.append({'guiElement':oGuiElement,'params':copy.deepcopy(outParams),'isFolder':bIsFolder})
            return

        if not oGuiElement._isMetaSet and self.isMetaOn and oGuiElement._mediaType:
            imdbID = outParams.getValue('imdbID')
            if imdbID:
                oGuiElement.getMeta(oGuiElement._mediaType, imdbID, mode = self.metaMode)
            else:
                oGuiElement.getMeta(oGuiElement._mediaType, mode = self.metaMode)

        sItemUrl = self.__createItemUrl(oGuiElement, bIsFolder, outParams)
        oListItem = self.createListItem(oGuiElement) 
        if not bIsFolder and cConfig().getSetting('hosterSelect') == 'List':
            bIsFolder = True
        if isHoster:
            bIsFolder = False
        oListItem = self.__createContextMenu(oGuiElement, oListItem, bIsFolder, sItemUrl, outParams)
                 
        if not bIsFolder:
            oListItem.setProperty('IsPlayable', 'true')        
        xbmcplugin.addDirectoryItem(self.pluginHandle, sItemUrl, oListItem, isFolder = bIsFolder, totalItems = iTotal)
        

    def addNextPage(self, site, function, oParams='', totalPages = 0):
        '''
        inserts a standard "next page" button into a listing 
        '''
        guiElement = cGuiElement('>>>',site,function)
        self.addFolder(guiElement, oParams)
        
        
    def createListItem(self, oGuiElement):
        '''
        creates a standard xbmcgui.listitem from the GuiElement
        '''
        itemValues= oGuiElement.getItemValues()
        itemTitle = oGuiElement.getTitle()
        infoString = ''
        if oGuiElement._sLanguage != '':
            infoString += ' (%s)' % oGuiElement._sLanguage
        if oGuiElement._sSubLanguage != '':
            infoString += ' *Sub: %s*' % oGuiElement._sSubLanguage
        if oGuiElement._sQuality != '':
            infoString += ' [%s]' % oGuiElement._sQuality
        if self.globalSearch:
            infoString += ' %s' % oGuiElement.getSiteName() 
        if infoString:
            infoString = '[I]%s[/I]' % infoString
        itemValues['title'] = itemTitle + infoString
         
        oListItem = xbmcgui.ListItem(itemTitle + infoString, oGuiElement.getTitleSecond(), oGuiElement.getIcon(), oGuiElement.getThumbnail())
        oListItem.setInfo(oGuiElement.getType(), itemValues)     
        oListItem.setProperty('fanart_image', oGuiElement.getFanart())
        oListItem.setArt({ 'poster': oGuiElement.getThumbnail()})
        aProperties = oGuiElement.getItemProperties()
        if len(aProperties)>0:
            for sPropertyKey in aProperties.keys():
                oListItem.setProperty(sPropertyKey, aProperties[sPropertyKey])
        return oListItem
        

    def __createContextMenu(self, oGuiElement, oListItem, bIsFolder, sItemUrl, oOutputParams=''):
        aContextMenus = []
        if len(oGuiElement.getContextItems()) > 0:
          for oContextItem in oGuiElement.getContextItems():
            oOutputParameterHandler = oContextItem.getOutputParameterHandler()
            sParams = oOutputParameterHandler.getParameterAsUri()                
            sTest = "%s?site=%s&function=%s&%s" % (self.pluginPath, oContextItem.getFile(), oContextItem.getFunction(), sParams)                
            aContextMenus+= [ ( oContextItem.getTitle(), "XBMC.RunPlugin(%s)" % (sTest,),)]

        itemValues = oGuiElement.getItemValues()

        oContextItem = cContextElement()
        oContextItem.setTitle("Info")
        aContextMenus+= [ ( oContextItem.getTitle(), "XBMC.Action(Info)",)]

        #search for alternative source
        oContextItem.setTitle("Weitere Quellen")
        searchParams = {}
        searchParams['searchTitle'] = oGuiElement.getTitle()
        if 'imdb_id' in itemValues:
            searchParams['searchImdbID'] = itemValues['imdb_id']
        aContextMenus+= [ ( oContextItem.getTitle(), "XBMC.Container.Update(%s?function=searchAlter&%s)" % (self.pluginPath, urllib.urlencode(searchParams),),)]
     
        if 'imdb_id' in itemValues and 'title' in itemValues:
            metaParams = {} 
            if itemValues['title']:
                metaParams['title'] = oGuiElement.getTitle()
            if 'mediaType' in itemValues and itemValues['mediaType']:
                metaParams['mediaType'] = itemValues['mediaType']
            elif 'TVShowTitle' in itemValues and itemValues['TVShowTitle']:
                metaParams['mediaType'] = 'tvshow'
            else:
                metaParams['mediaType'] = 'movie'
            if 'season' in itemValues and itemValues['season'] and int(itemValues['season'])>0:
                metaParams['season'] = itemValues['season']
                metaParams['mediaType'] = 'season'
            if ( 'episode' in itemValues and itemValues['episode'] and int(itemValues['episode'])>0
                and 'season' in itemValues and itemValues['season'] and int(itemValues['season']) ):
                metaParams['episode'] = itemValues['episode']
                metaParams['mediaType'] = 'episode'
            # if an imdb id is available we can mark this element as seen/unseen in the metahandler
            if itemValues['imdb_id']:
                metaParams['imdbID'] = itemValues['imdb_id']
                if itemValues['overlay'] == '7':
                    oContextItem.setTitle("Als ungesehen markieren")
                else:
                    oContextItem.setTitle("Als gesehen markieren")
                aContextMenus+= [ ( oContextItem.getTitle(), "XBMC.RunPlugin(%s?function=changeWatched&%s)" % (self.pluginPath, urllib.urlencode(metaParams),),)]
            # if year is set we can search reliably for metainfos via metahandler
            if 'year' in itemValues and itemValues['year']:
                metaParams['year'] = itemValues['year']
            oContextItem.setTitle("Suche Metainfos")
            aContextMenus+= [ ( oContextItem.getTitle(), "XBMC.RunPlugin(%s?function=updateMeta&%s)" % (self.pluginPath, urllib.urlencode(metaParams),),)]
        # context options for movies or episodes
        if not bIsFolder:
            oContextItem.setTitle("add to Playlist")     
            aContextMenus+= [ ( oContextItem.getTitle(), "XBMC.RunPlugin(%s&playMode=enqueue)" % (sItemUrl,),)]
            oContextItem.setTitle("download")
            aContextMenus+= [ ( oContextItem.getTitle(), "XBMC.RunPlugin(%s&playMode=download)" % (sItemUrl,),)]
            if cConfig().getSetting('jd_enabled') == 'true':
                oContextItem.setTitle("send to JDownloader")
                aContextMenus+= [ ( oContextItem.getTitle(), "XBMC.RunPlugin(%s&playMode=jd)" % (sItemUrl,),)]   
            if cConfig().getSetting('jd2_enabled') == 'true':
                oContextItem.setTitle("send to JDownloader2")
                aContextMenus+= [ ( oContextItem.getTitle(), "XBMC.RunPlugin(%s&playMode=jd2)" % (sItemUrl,),)]   
            if cConfig().getSetting('pyload_enabled') == 'true':
                oContextItem.setTitle("send to PyLoad")     
                aContextMenus+= [ ( oContextItem.getTitle(), "XBMC.RunPlugin(%s&playMode=pyload)" % (sItemUrl,),)]
            if cConfig().getSetting('hosterSelect')=='Auto':
                oContextItem.setTitle("select hoster")     
                aContextMenus+= [ ( oContextItem.getTitle(), "XBMC.RunPlugin(%s&playMode=play&manual=1)" % (sItemUrl,),)]
        oListItem.addContextMenuItems(aContextMenus)
        #oListItem.addContextMenuItems(aContextMenus, True)  
        return oListItem
        

    def setEndOfDirectory(self, success = True):
        '''
        mark the listing as completed, this is mandatory
        '''

        if not self._isViewSet:
            self.setView('files')

        xbmcplugin.setPluginCategory(self.pluginHandle, "")
        # add some sort methods, these will be available in all views         
        xbmcplugin.addSortMethod(self.pluginHandle, xbmcplugin.SORT_METHOD_UNSORTED)
        xbmcplugin.addSortMethod(self.pluginHandle, xbmcplugin.SORT_METHOD_VIDEO_RATING)
        xbmcplugin.addSortMethod(self.pluginHandle, xbmcplugin.SORT_METHOD_LABEL)       
        xbmcplugin.addSortMethod(self.pluginHandle, xbmcplugin.SORT_METHOD_DATE)
        xbmcplugin.addSortMethod(self.pluginHandle, xbmcplugin.SORT_METHOD_PROGRAM_COUNT)
        xbmcplugin.addSortMethod(self.pluginHandle, xbmcplugin.SORT_METHOD_VIDEO_RUNTIME)
        xbmcplugin.addSortMethod(self.pluginHandle, xbmcplugin.SORT_METHOD_GENRE) 
          
        xbmcplugin.endOfDirectory(self.pluginHandle, success)
        
 
    def setView(self, content='movies'):
        '''
        set the listing to a certain content, makes special views available
        sets view to the viewID which is selected in streamon settings

        see http://mirrors.xbmc.org/docs/python-docs/stable/xbmcplugin.html#-setContent
        (seasons is also supported but not listed)
        '''
        content = content.lower()
        supportedViews = ['files', 'songs', 'artists', 'albums', 'movies', 'tvshows', 'seasons', 'episodes', 'musicvideos']

        if content in supportedViews:
            self._isViewSet = True
            xbmcplugin.setContent(self.pluginHandle, content)
        if cConfig().getSetting('auto-view')=='true' and content:
            viewId = cConfig().getSetting(content+'-view')
            if viewId:
                xbmc.executebuiltin("Container.SetViewMode(%s)" % viewId)
        


    def updateDirectory(self):
        '''
        update the current listing
        '''
        xbmc.executebuiltin("Container.Refresh")
        

    def __createItemUrl(self, oGuiElement, bIsFolder, oOutputParameterHandler=''):
        if (oOutputParameterHandler == ''):
            oOutputParameterHandler = ParameterHandler()
       
        itemValues = oGuiElement.getItemValues()
        if 'imdb_id' in itemValues and itemValues['imdb_id']:
            oOutputParameterHandler.setParam('imdbID',itemValues['imdb_id'])
        if 'TVShowTitle' in itemValues and itemValues['TVShowTitle']:
            oOutputParameterHandler.setParam('TVShowTitle',itemValues['TVShowTitle'])
        if 'season' in itemValues and itemValues['season'] and int(itemValues['season'])>0:
            oOutputParameterHandler.setParam('season',itemValues['season'])
        if 'episode' in itemValues and itemValues['episode'] and float(itemValues['episode'])>0:
            oOutputParameterHandler.setParam('episode',itemValues['episode'])
        #TODO change this, it can cause bugs it influencec the params for the following listitems
        if not bIsFolder:
            oOutputParameterHandler.setParam('MovieTitle',oGuiElement.getTitle())
            
            thumbnail = oGuiElement.getThumbnail()
            if thumbnail:
                oOutputParameterHandler.setParam('thumb',thumbnail)

            if oGuiElement._mediaType:
                oOutputParameterHandler.setParam('mediaType', oGuiElement._mediaType)
            elif 'TVShowTitle' in itemValues and itemValues['TVShowTitle']:
                oOutputParameterHandler.setParam('mediaType','tvshow')
            if 'season' in itemValues and itemValues['season'] and int(itemValues['season'])>0:
                oOutputParameterHandler.setParam('mediaType','season')
            if 'episode' in itemValues and itemValues['episode'] and float(itemValues['episode'])>0:
                oOutputParameterHandler.setParam('mediaType','episode')
                                             
        sParams = oOutputParameterHandler.getParameterAsUri()
        if len(oGuiElement.getFunction()) == 0:
            sItemUrl = "%s?site=%s&title=%s&%s" % (self.pluginPath, oGuiElement.getSiteName(), urllib.quote_plus(oGuiElement.getTitle()), sParams)
        else:
            sItemUrl = "%s?site=%s&function=%s&title=%s&%s" % (self.pluginPath, oGuiElement.getSiteName(), oGuiElement.getFunction(), urllib.quote_plus(oGuiElement.getTitle()), sParams)
            if not bIsFolder:
                sItemUrl += '&playMode=play'
        return sItemUrl       


    @staticmethod
    def showKeyBoard(sDefaultText = ""):
        # Create the keyboard object and display it modal
        oKeyboard = xbmc.Keyboard(sDefaultText)
        oKeyboard.doModal()    
        # If key board is confirmed and there was text entered return the text
        if oKeyboard.isConfirmed():
          sSearchText = oKeyboard.getText()
          if len(sSearchText) > 0:
            return sSearchText
        return False
        

    @staticmethod
    def showNumpad(defaultNum = "", numPadTitle="Choose page"):
        defaultNum = str(defaultNum)
        dialog = xbmcgui.Dialog()
        num = dialog.numeric(0, numPadTitle, defaultNum)
        return num
        
    @staticmethod
    def openSettings():
        cConfig().showSettingsWindow()

    @staticmethod
    def showNofication(sTitle, iSeconds=0):
        if (iSeconds == 0):
          iSeconds = 1000
        else:
          iSeconds = iSeconds * 1000  
        xbmc.executebuiltin("Notification(%s,%s,%s,%s)" % (cConfig().getLocalizedString(30308), (cConfig().getLocalizedString(30309) % str(sTitle)), iSeconds, common.addon.getAddonInfo('icon')))

    @staticmethod
    def showError(sTitle, sDescription, iSeconds = 0):
        if iSeconds == 0:
          iSeconds = 1000
        else:
          iSeconds = iSeconds * 1000
        xbmc.executebuiltin("Notification(%s,%s,%s,%s)" % (str(sTitle), (str(sDescription)), iSeconds, common.addon.getAddonInfo('icon')))

    @staticmethod
    def showInfo(sTitle, sDescription, iSeconds=0):
        if (iSeconds == 0):
            iSeconds = 1000
        else:
            iSeconds = iSeconds * 1000
        xbmc.executebuiltin("Notification(%s,%s,%s,%s)" % (str(sTitle), (str(sDescription)), iSeconds, common.addon.getAddonInfo('icon')))
