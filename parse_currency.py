import json
import urllib2

url_quote = "http://api.fixer.io/latest?symbols=USD,KRW"

def GetCurrency(url):
    f = urllib2.urlopen(url)
    page = f.read().decode('euc-kr', 'ignore')
    f.close()
    js = json.loads(page)
    return js

StockInfo = CollectCurrency(url_quote)

for itm in StockInfo['rates']:
    print itm
