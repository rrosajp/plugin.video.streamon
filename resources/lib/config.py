import sys
import xbmc
import xbmcplugin
from resources.lib import common

class cConfig:

    def __check(self):
        try:
            import xbmcaddon           
            self.__bIsDharma = True            
        except ImportError:
            self.__bIsDharma = False

    def __init__(self):
        self.__check()

        if (self.__bIsDharma):
            import xbmcaddon
            self.__oSettings = xbmcaddon.Addon(common.addonID)
            self.__aLanguage = self.__oSettings.getLocalizedString


    def isDharma(self):
        return self.__bIsDharma
        

    def showSettingsWindow(self):
        if (self.__bIsDharma):
            self.__oSettings.openSettings()
        else:
            try:		
                xbmcplugin.openSettings( sys.argv[ 0 ] )
            except:
                pass

    def getSetting(self, sName, default=''):
        if (self.__bIsDharma):
            result = self.__oSettings.getSetting(sName)

            if result:
                return result
            else:
                return default
        else:
            try:                
                return xbmcplugin.getSetting(sName)
            except:
                return default

    def getLocalizedString(self, sCode):
        if (self.__bIsDharma):
            return self.__aLanguage(sCode)
        else:
            try:		
                 return xbmc.getLocalizedString(sCode)
            except:
                return ''