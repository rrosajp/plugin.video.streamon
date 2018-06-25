# -*- coding: utf-8 -*-
from __future__ import division
import urllib, urllib2, re, sys
from time import sleep
from urlparse import urlparse
from resources.lib import logger

def checkpart(s, sens):
    number = 0
    p = 0
    if sens == 1:
        pos = 0
    else:
        pos = len(s) - 1

    try:
        while 1:
            c = s[pos]

            if ((c == '(') and (sens == 1)) or ((c == ')') and (sens == -1)):
                p = p + 1
            if ((c == ')') and (sens == 1)) or ((c == '(') and (sens == -1)):
                p = p - 1
            if (c == '+') and (p == 0) and (number > 1):
                break

            number += 1
            pos = pos + sens
    except:
        pass
    if sens == 1:
        return s[:number], number
    else:
        return s[-number:], number


def parseInt(s):
    offset = 1 if s[0] == '+' else 0
    chain = s.replace('!+[]', '1').replace('!![]', '1').replace('[]', '0').replace('(', 'str(')[offset:]

    if '/' in chain:
        val = chain.split('/')
        links, sizeg = checkpart(val[0], -1)
        rechts, sized = checkpart(val[1], 1)

        if rechts.startswith('+') or rechts.startswith('-'):
            rechts = rechts[1:]
        gg = eval(links)
        dd = eval(rechts)
        chain = val[0][:-sizeg] + str(gg) + '/' + str(dd) + val[1][sized:]
    val = float(eval(chain))
    return val


class cCFScrape:
    def resolve(self, url, cookie_jar, user_agent):
        Domain = re.sub(r'https*:\/\/([^/]+)(\/*.*)', '\\1', url)
        headers = {'User-agent': user_agent, 'Referer': url, 'Host': Domain,
                   'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                   'Content-Type': 'text/html; charset=utf-8'}

        try:
            cookie_jar.load(ignore_discard=True)
        except Exception as e:
            logger.info(e)

        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookie_jar))
        request = urllib2.Request(url)
        for key in headers:
            request.add_header(key, headers[key])

        try:
            response = opener.open(request)
        except urllib2.HTTPError as e:
            response = e
			
        if response.code != 503:
            return response

        body = response.read()
        cookie_jar.extract_cookies(response, request)
        cCFScrape.__checkCookie(cookie_jar)
        parsed_url = urlparse(url)
        submit_url = "%s://%s/cdn-cgi/l/chk_jschl" % (parsed_url.scheme, parsed_url.netloc)
        params = {}

        try:
            params["jschl_vc"] = re.search(r'name="jschl_vc" value="(\w+)"', body).group(1)
            params["pass"] = re.search(r'name="pass" value="(.+?)"', body).group(1)
            js = self._extract_js(body, parsed_url.netloc)
        except:
            return None

        params["jschl_answer"] = js
        sParameters = urllib.urlencode(params, True)
        request = urllib2.Request("%s?%s" % (submit_url, sParameters))
        for key in headers:
            request.add_header(key, headers[key])
        sleep(5)

        try:
            response = opener.open(request)
        except urllib2.HTTPError as e:
            response = e
        return response

    @staticmethod
    def __checkCookie(cookieJar):
        for entry in cookieJar:
            if entry.expires > sys.maxint:
                entry.expires = sys.maxint

    @staticmethod
    def _extract_js(htmlcontent, domain):
        line1 = re.findall('var s,t,o,p,b,r,e,a,k,i,n,g,f, (.+?)={"(.+?)":\+*(.+?)};', htmlcontent)
        varname = line1[0][0] + '.' + line1[0][1]
        calc = parseInt(line1[0][2])
        AllLines = re.findall(';' + varname + '([*\-+])=([^;]+)', htmlcontent)

        for aEntry in AllLines:
            calc = eval(format(calc, '.17g') + str(aEntry[0]) + format(parseInt(aEntry[1]), '.17g'))
        rep = calc + len(domain)
        return format(rep, '.10f')

    @staticmethod
    def createUrl(sUrl, oRequest):
        parsed_url = urlparse(sUrl)
        netloc = parsed_url.netloc[4:] if parsed_url.netloc.startswith('www.') else parsed_url.netloc
        cfId = oRequest.getCookie('__cfduid', '.' + netloc)
        cfClear = oRequest.getCookie('cf_clearance', '.' + netloc)

        if cfId and cfClear and 'Cookie=Cookie:' not in sUrl:
            delimiter = '&' if '|' in sUrl else '|'
            sUrl = sUrl + delimiter + "Cookie=Cookie: __cfduid=" + cfId.value + "; cf_clearance=" + cfClear.value

        if 'User-Agent=' not in sUrl:
            delimiter = '&' if '|' in sUrl else '|'
            sUrl += delimiter + "User-Agent=" + oRequest.getHeaderEntry('User-Agent')
        return sUrl
