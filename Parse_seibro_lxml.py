#-*- coding: utf-8 -*-
from lxml import etree
import urllib2
from StringIO import StringIO
import timeit
from bs4 import BeautifulSoup


url = 'http://api.seibro.or.kr/openapi/service/StockSvc/getStkIsinByNm?ServiceKey=CJL9jdtz5gsb4z4PpjFpCDjdz/UIk8cFAGgHbJvgLEJxPWLZaTx3wIcBNPkGu/KIKsI1zAy1XtfQJLG0VV0vVg==&secnNm=' + u'한국'.encode('euc-kr') + '&pageNo=1&numOfRows=500'

# packages = html.xpath('//tr/td/a/text()') # get the text inside all "<tr><td><a ...>text</a></td></tr>"
# packages = html.xpath('//table[@class="gTable clr"]/tr/td/span/text()') # get the text inside all "<tr><td><a ...>text</a></td></tr>"
# print packages
f = urllib2.urlopen(url)
xml = f.read().decode('utf-8')
f.close()

context = etree.fromstring(xml.encode('utf-8'))
#r = context.xpath('//item/korSecnNm/text()')
i = 0
temp = etree.XML(xml.encode('utf-8'))

retlist = []
retlist1 = []
retlist2 = []

start = timeit.default_timer()

srch = etree.XPath('//item')


r = context.xpath('//item/korSecnNm/text()')
i = 0
count = 0

for elem in srch(temp):
    #print "Number: ", i
    #print "Item count:", len(srch(temp)[i])

    if len(srch(temp)[i]) == 7:
        retlist1.append(srch(temp)[i][4].text)
        retlist2.append(srch(temp)[i][6].text)
        print retlist1[count], retlist2[count]
        count = count + 1
    i = i + 1

#----------------------------------------------------------------------------------------
stop1 = timeit.default_timer()
print stop1 - start

soup = BeautifulSoup(xml, 'html.parser', from_encoding='utf-8')

i = 0

for li in soup.findAll('item'):
    i = i + 1
    retlist1.append([li.korsecnnm.string])
    if li.shotnisin == None:
        retlist2.append(['000000'])
    else:
        retlist2.append([li.shotnisin.string])


stop2 = timeit.default_timer()
print stop2 - stop1
