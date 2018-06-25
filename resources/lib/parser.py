import re


class cParser:
    @staticmethod
    def parseSingleResult(sHtmlContent, sPattern):
        aMatches = re.compile(sPattern).findall(sHtmlContent)
        if len(aMatches) == 1:
            aMatches[0] = cParser.__replaceSpecialCharacters(aMatches[0])
            return True, aMatches[0]
        return False, aMatches

    @staticmethod
    def __replaceSpecialCharacters(sString):
        return sString.replace('\\/', '/')

    @staticmethod
    def parse(sHtmlContent, sPattern, iMinFoundValue=1, ignoreCase=False):
        if ignoreCase:
            aMatches = re.compile(sPattern, re.DOTALL | re.I).findall(sHtmlContent)
        else:
            aMatches = re.compile(sPattern, re.DOTALL).findall(sHtmlContent)
        if len(aMatches) >= iMinFoundValue:
            return True, aMatches
        return False, aMatches

    @staticmethod
    def replace(sPattern, sReplaceString, sValue):
        return re.sub(sPattern, sReplaceString, sValue)

    @staticmethod
    def escape(sValue):
        return re.escape(sValue)

    @staticmethod
    def getNumberFromString(sValue):
        sPattern = "\d+"
        aMatches = re.findall(sPattern, sValue)
        if (len(aMatches) > 0):
            return int(aMatches[0])
        return 0
