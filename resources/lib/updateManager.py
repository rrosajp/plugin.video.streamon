# -*- coding: utf-8 -*-
import urllib
import os
import json
import zipfile
import logger
import xbmc
from resources.lib.common import addonPath, profilePath
from resources.lib.download import cDownload

## Installation path.
ROOT_DIR = addonPath
ADDON_DIR = os.path.abspath(os.path.join(ROOT_DIR, '..'))
streamon_DIRNAME = os.path.basename(ROOT_DIR)


## URLRESOLVER
REMOTE_URLRESOLVER_COMMITS = "https://api.github.com/repos/jsergio123/script.module.urlresolver/commits/master"
REMOTE_URLRESOLVER_DOWNLOADS = "https://github.com/jsergio123/script.module.urlresolver/archive/master.zip"

## streamon
REMOTE_streamon_COMMITS = "https://api.github.com/repos/xstreamon/plugin.video.streamon/commits/master"
REMOTE_streamon_NIGHTLY = "https://github.com/xstreamon/plugin.video.streamon/archive/master.zip"

## Filename of the update File.
LOCAL_NIGHTLY_VERSION = os.path.join(profilePath, "nightly_commit_sha")
LOCAL_RESOLVER_VERSION = os.path.join(profilePath, "resolver_commit_sha")
LOCAL_FILE_NAME_streamon = 'update_streamon.zip'
LOCAL_FILE_NAME_RESOLVER = 'update_urlresolver.zip'


def streamonUpdate():
    logger.info("streamon streamonUpdate")
    commitXML = _getXmlString(REMOTE_streamon_COMMITS)
    if commitXML:
        commitUpdate(commitXML, LOCAL_NIGHTLY_VERSION, REMOTE_streamon_NIGHTLY, ROOT_DIR, "Updating streamon", LOCAL_FILE_NAME_streamon)
    else:
        from resources.lib.gui.gui import cGui
        cGui().showError('streamon', 'Fehler beim streamon-Update.', 5)

def urlResolverUpdate():
    logger.info("streamon urlResolverUpdate")

    urlResolverPaths = []
    for child in os.listdir(ADDON_DIR):
        if not child.lower().startswith('script.module.urlresolver'): continue
        resolver_path = os.path.join(ADDON_DIR, child)
        if os.path.isdir(resolver_path):
            urlResolverPaths.append(resolver_path)

    if len(urlResolverPaths) > 1:
        from resources.lib.gui.gui import cGui
        cGui().showError('streamon', 'Es ist mehr als ein URLResolver installiert. Bitte löschen!', 5)
        logger.info("Its more the one URLResolver installed!")
        return
    elif len(urlResolverPaths) < 1:
        from resources.lib.gui.gui import cGui
        cGui().showError('streamon', 'Es wurde kein URLResolver gefunden!', 5)
        logger.info("No URLResolver installed/found!")
        return

    commitXML = _getXmlString(REMOTE_URLRESOLVER_COMMITS)
    if commitXML:
        commitUpdate(commitXML, LOCAL_RESOLVER_VERSION, REMOTE_URLRESOLVER_DOWNLOADS, urlResolverPaths[0], "Updating URLResolver", LOCAL_FILE_NAME_RESOLVER)
    else:
        from resources.lib.gui.gui import cGui
        cGui().showError('streamon', 'Fehler beim URLResolver-Update.', 5)

def commitUpdate(onlineFile, offlineFile, downloadLink, LocalDir, Title, localFileName):
    try:
        jsData = json.loads(onlineFile)
        if not os.path.exists(offlineFile) or open(offlineFile).read() != jsData['sha']:
            update(LocalDir, downloadLink, Title, localFileName)
            open(offlineFile, 'w').write(jsData['sha'])
    except Exception as e:
        logger.info("Ratelimit reached")
        logger.info(e)

def update(LocalDir, REMOTE_PATH, Title, localFileName):
    logger.info(Title + " from: " + REMOTE_PATH)

    cDownload().download(REMOTE_PATH, localFileName, False, Title)

    updateFile = zipfile.ZipFile(os.path.join(profilePath, localFileName))

    removeFilesNotInRepo(updateFile, LocalDir)

    for index, n in enumerate(updateFile.namelist()):
        if n[-1] != "/":
            dest = os.path.join(LocalDir, "/".join(n.split("/")[1:]))
            destdir = os.path.dirname(dest)
            if not os.path.isdir(destdir):
                os.makedirs(destdir)
            data = updateFile.read(n)
            if os.path.exists(dest):
                os.remove(dest)
            f = open(dest, 'wb')
            f.write(data)
            f.close()
    updateFile.close()
    xbmc.executebuiltin("XBMC.UpdateLocalAddons()")
    logger.info("Update Successful")

def removeFilesNotInRepo(updateFile, LocalDir):
    ignored_files = ['settings.xml']
    updateFileNameList = [i.split("/")[-1] for i in updateFile.namelist()]

    for root, dirs, files in os.walk(LocalDir):
        if ".git" in root or "pydev" in root or ".idea" in root:
            continue
        else:
            for file in files:
                if file in ignored_files:
                    continue
                if file not in updateFileNameList:
                    os.remove(os.path.join(root, file))

def _getXmlString(xml_url):
    try:
        xmlString = urllib.urlopen(xml_url).read()
        if "sha" in json.loads(xmlString):
            return xmlString
        else:
            logger.info("Update-URL incorrect")
    except Exception as e:
        logger.info(e)

