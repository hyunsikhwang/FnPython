import json
import urllib2

url_quote = "http://sbcharts.investing.com/bond_charts/bonds_chart_60.json"

def CollectPrices(url):
    f = urllib2.urlopen(url)
    page = f.read().decode('euc-kr', 'ignore')
    f.close()
    js = json.loads(page)
    return js

StockInfo = CollectPrices(url_quote)

for itm in StockInfo['current']:
    print itm

