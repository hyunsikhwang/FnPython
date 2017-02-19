import lxml.html

#url = 'http://comp.fnguide.com/SVO2/ASP/SVD_main.asp?pGB=1&gicode=A026960&cID=&MenuYn=Y&ReportGB=&NewMenuID=11&stkGb=&strResearchYN='
url = 'http://comp.fnguide.com/SVO2/ASP/SVD_Invest.asp?pGB=1&gicode=A026960&cID=&MenuYn=Y&ReportGB=&NewMenuID=105&stkGb=701'

html = lxml.html.parse(url)
# packages = html.xpath('//tr/td/a/text()') # get the text inside all "<tr><td><a ...>text</a></td></tr>"
# packages = html.xpath('//table[@class="gTable clr"]/tr/td/span/text()') # get the text inside all "<tr><td><a ...>text</a></td></tr>"
# print packages

packages = html.xpath('//tr[@id="p_grid1_4"]/td/text()')
# test = html.xpath("//tr/td/a/@href")

A = {}
i = 0

for stname in packages:
    A[i] = stname
    # A[i] = stname[-6:]
    print A[i]
    i = i + 1
