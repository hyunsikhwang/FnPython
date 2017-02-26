import json
import urllib2

url_quote = "http://api.fixer.io/latest?symbols=USD,KRW"

def GetCurrency(url):
    f = urllib2.urlopen(url)
    page = f.read().decode('euc-kr', 'ignore')
    f.close()
    js = json.loads(page)
    return js

CurrencyInfo = GetCurrency(url_quote)
i = 0

for itm in CurrencyInfo['rates']:
    print itm[1][0]
