#-*- coding: utf-8 -*-
from lxml import etree
import urllib2
from StringIO import StringIO

url = 'http://api.seibro.or.kr/openapi/service/StockSvc/getStkIsinByNm?ServiceKey=CJL9jdtz5gsb4z4PpjFpCDjdz/UIk8cFAGgHbJvgLEJxPWLZaTx3wIcBNPkGu/KIKsI1zAy1XtfQJLG0VV0vVg==&secnNm=' + u'한국'.encode('euc-kr') + '&pageNo=1&numOfRows=500'

# packages = html.xpath('//tr/td/a/text()') # get the text inside all "<tr><td><a ...>text</a></td></tr>"
# packages = html.xpath('//table[@class="gTable clr"]/tr/td/span/text()') # get the text inside all "<tr><td><a ...>text</a></td></tr>"
# print packages
f = urllib2.urlopen(url)
xml = f.read().decode('utf-8')
f.close()

context = etree.fromstring(xml.encode('utf-8'))
r = context.xpath('//korSecnNm//text()')


for elem in r:
    print elem
    i=i+1
