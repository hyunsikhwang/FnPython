#-*- coding: utf-8 -*-
#
# original:    https://github.com/yukuku/telebot
# modified by: Bak Yeon O @ http://bakyeono.net
# description: http://bakyeono.net/post/2015-08-24-using-telegram-bot-api.html
# github:      https://github.com/bakyeono/using-telegram-bot-api
# githun:      https://github.com/hyunsikhwang/FnPython

# κ΅¬κ?? ?± ?μ§? ?Ό?΄λΈλ¬λ¦? λ‘λ
from google.appengine.api import urlfetch
from google.appengine.ext import ndb
import webapp2

# URL, JSON, λ‘κ·Έ, ? κ·ν?? κ΄?? ¨ ?Ό?΄λΈλ¬λ¦? λ‘λ
import urllib
import urllib2
import json
import logging
import re

# μ’λͺ©λͺ? μ°ΎκΈ° API κ΄?? ¨ ?Ό?΄λΈλ¬λ¦? λ‘λ
from urllib import urlencode, quote_plus
from urllib2 import Request, urlopen

from bs4 import BeautifulSoup
#import requests
import lxml.html
from google.appengine.api import urlfetch
#from lxml import html


# λ΄? ? ?°, λ΄? API μ£Όμ
TOKEN = '303352490:AAGLVFQbnFyviIelWVBynx98JGqd_GoVRzQ'
BASE_URL = 'https://api.telegram.org/bot' + TOKEN + '/'

# μ’λͺ©λͺ? μ°ΎκΈ° API Key
APIKey = "CJL9jdtz5gsb4z4PpjFpCDjdz/UIk8cFAGgHbJvgLEJxPWLZaTx3wIcBNPkGu/KIKsI1zAy1XtfQJLG0VV0vVg=="

# μ±κΆ ??΅λ₯? ? λ³? ??΄μ§?
url_bondinfo = "http://sbcharts.investing.com/bond_charts/bonds_chart_60.json"

# λ΄μ΄ ??΅?  λͺλ Ή?΄
CMD_START     = '/start'
CMD_STOP      = '/stop'
CMD_HELP      = '/help'
CMD_BROADCAST = '/broadcast'
CMD_INFO      = '/info'
CMD_BOND      = '/bond'
CMD_CLOSE     = '/close'

# λ΄? ?¬?©λ²? & λ©μμ§?
USAGE = u"""[?¬?©λ²?] ?? λͺλ Ή?΄λ₯? λ©μμ§?λ‘? λ³΄λ΄κ±°λ λ²νΌ? ?λ₯΄μλ©? ?©??€.
/start - (λ‘λ΄ ??±?)
/stop  - (λ‘λ΄ λΉν?±?)
/help  - (?΄ ????λ§? λ³΄μ¬μ£ΌκΈ°)
/info  - (? λ³? μ‘°ν)
/bond  - (μ±κΆ ??΅λ₯? μ‘°ν)
"""
MSG_START = u'λ΄μ ???©??€.'
MSG_STOP  = u'λ΄μ ? μ§??©??€.'

# μ»€μ€??? ?€λ³΄λ
CUSTOM_KEYBOARD = [
        [CMD_START,CMD_STOP,CMD_HELP],
        [CMD_INFO,CMD_BOND]
        ]

USER_KEYBOARD = []

ST_ECHO, ST_INFO, ST_BOND = range(3)

class CommandStatus(ndb.Model):
    command_status = ndb.IntegerProperty(required=True, indexed=True, default=False,)

def FindInfo(stockcode):
    url_header = 'http://comp.fnguide.com/SVO2/ASP/SVD_main.asp?pGB=1&gicode=A'
    url_footer = '&cID=&MenuYn=Y&ReportGB=&NewMenuID=11&stkGb=&strResearchYN='

    url = url_header + stockcode + url_footer
    result = urlfetch.fetch(url)

    #html = lxml.html.parse(url)
    html = lxml.html.fromstring(result.content)

    packages = html.xpath('//div[@class="corp_group2"]/dl/dd/text()')

    STCInfo = {}
    i = 0

    for valinfo in packages:
        STCInfo[i] = valinfo
        i = i + 1

    return STCInfo


def FindCodeAPI(APIKey, stock_name):
    url = 'http://api.seibro.or.kr/openapi/service/StockSvc/getStkIsinByNm'
    queryParams = '?' + urlencode({ quote_plus('ServiceKey') : APIKey, quote_plus('secnNm') : stock_name.encode('utf-8'), quote_plus('pageNo') : '1', quote_plus(u'numOfRows') : '500' })

    request = Request(url + queryParams)
    request.get_method = lambda: 'GET'
    page = urlopen(request).read()

#    r = requests.get(url + queryParams)
#    tree = lxml.html.fromstring(r.content)
#    element1 = tree.xpath('//korSecnNm//text()')
#    element2 = tree.xpath('//')
    soup = BeautifulSoup(page, 'html.parser', from_encoding='utf-8')

    i = 0
    retlist = []
    retlist1 = []
    retlist2 = []

    for li in soup.findAll('item'):
        i = i + 1
        retlist1.append([li.korsecnnm.string])
        if li.shotnisin == None:
            retlist2.append(['000000'])
        else:
            retlist2.append([li.shotnisin.string])

    retlist = [retlist1, retlist2]
    return retlist

def MergeList(reflist):
    ml = ""
    for il in reflist:
        ml += il[0] + "\n"

    return ml


def CollectBondRates(url):
    f = urllib2.urlopen(url)
    page = f.read().decode('euc-kr', 'ignore')
    f.close()
    js = json.loads(page)
    return js


# μ±νλ³? λ‘λ΄ ??±? ??
# κ΅¬κ?? ?± ?μ§μ Datastore(NDB)? ??λ₯? ????₯?κ³? ?½?
# ?¬?©?κ°? /start ?λ₯΄λ©΄ ??±?
# ?¬?©?κ°? /stop  ?λ₯΄λ©΄ λΉν?±?
class EnableStatus(ndb.Model):
    enabled = ndb.BooleanProperty(required=True, indexed=True, default=False,)

def set_enabled(chat_id, enabled):
    u"""set_enabled: λ΄? ??±?/λΉν?±? ?? λ³?κ²?
    chat_id:    (integer) λ΄μ ??±?/λΉν?±??  μ±ν ID
    enabled:    (boolean) μ§?? ?  ??±?/λΉν?±? ??
    """
    es = EnableStatus.get_or_insert(str(chat_id))
    es.enabled = enabled
    es.put()

def get_enabled(chat_id):
    u"""get_enabled: λ΄? ??±?/λΉν?±? ?? λ°ν
    return: (boolean)
    """
    es = EnableStatus.get_by_id(str(chat_id))
    if es:
        return es.enabled
    return False

def get_status(chat_id):
    u"""get_status: ?¬?© ?? λ°ν
    return: (boolean)
    """
    cs = CommandStatus.get_by_id(str(chat_id))
    if cs:
        return cs.command_status
    return False

def get_enabled_chats():
    u"""get_enabled: λ΄μ΄ ??±?? μ±ν λ¦¬μ€?Έ λ°ν
    return: (list of EnableStatus)
    """
    query = EnableStatus.query(EnableStatus.enabled == True)
    return query.fetch()

def set_status(chat_id, cmd_status):
    u"""set_status: λͺλ Ή?΄ ??
    chat_id:    (integer) μ±ν ID
    cmd_status: (integer) λͺλ Ή?΄ ??(info)
    """
    cs = CommandStatus.get_or_insert(str(chat_id))
    cs.command_status = cmd_status
    cs.put()

# λ©μμ§? λ°μ‘ κ΄?? ¨ ?¨??€
def send_msg(chat_id, text, reply_to=None, no_preview=True, keyboard=None):
    u"""send_msg: λ©μμ§? λ°μ‘
    chat_id:    (integer) λ©μμ§?λ₯? λ³΄λΌ μ±ν ID
    text:       (string)  λ©μμ§? ?΄?©
    reply_to:   (integer) ~λ©μμ§?? ???? ?΅?₯
    no_preview: (boolean) URL ?? λ§ν¬(λ―Έλ¦¬λ³΄κΈ°) ?κΈ?
    keyboard:   (list)    μ»€μ€??? ?€λ³΄λ μ§?? 
    """
    params = {
        'chat_id': str(chat_id),
        'text': text.encode('utf-8'),
        }
    if reply_to:
        params['reply_to_message_id'] = reply_to
    if no_preview:
        params['disable_web_page_preview'] = no_preview
    if keyboard:
        reply_markup = json.dumps({
            'keyboard': keyboard,
            'resize_keyboard': True,
            'one_time_keyboard': False,
            'selective': (reply_to == True),
            })
        params['reply_markup'] = reply_markup
    try:
        urllib2.urlopen(BASE_URL + 'sendMessage', urllib.urlencode(params)).read()
    except Exception as e:
        logging.exception(e)

def send_photo(chat_id, text, reply_to=None, keyboard=None):
    u"""send_photo: λ©μμ§? λ°μ‘
    chat_id:    (integer) λ©μμ§?λ₯? λ³΄λΌ μ±ν ID
    text:       (string)  λ©μμ§? ?΄?©
    reply_to:   (integer) ~λ©μμ§?? ???? ?΅?₯
    """
    params = {
        'chat_id': str(chat_id),
        'photo': text.encode('utf-8'),
        }
    if reply_to:
        params['reply_to_message_id'] = reply_to
    if keyboard:
        params['reply_markup'] = reply_markup
    try:
        urllib2.urlopen(BASE_URL + 'sendPhoto', urllib.urlencode(params)).read()
    except Exception as e:
        logging.exception(e)


def broadcast(text):
    u"""broadcast: λ΄μ΄ μΌμ Έ ?? λͺ¨λ  μ±ν? λ©μμ§? λ°μ‘
    text:       (string)  λ©μμ§? ?΄?©
    """
    for chat in get_enabled_chats():
        send_msg(chat.key.string_id(), text)

# λ΄? λͺλ Ή μ²λ¦¬ ?¨??€
def cmd_start(chat_id):
    u"""cmd_start: λ΄μ ??±??κ³?, ??±? λ©μμ§? λ°μ‘
    chat_id: (integer) μ±ν ID
    """
    set_enabled(chat_id, True)
    send_msg(chat_id, MSG_START, keyboard=CUSTOM_KEYBOARD)

def cmd_stop(chat_id):
    u"""cmd_stop: λ΄μ λΉν?±??κ³?, λΉν?±? λ©μμ§? λ°μ‘
    chat_id: (integer) μ±ν ID
    """
    set_enabled(chat_id, False)
    send_msg(chat_id, MSG_STOP)

def cmd_help(chat_id):
    u"""cmd_help: λ΄? ?¬?©λ²? λ©μμ§? λ°μ‘
    chat_id: (integer) μ±ν ID
    """
    send_msg(chat_id, USAGE, keyboard=CUSTOM_KEYBOARD)

def cmd_info(chat_id):
    u"""cmd_info: μ’λͺ© ? λ³? μ‘°ν
    chat_id: (integer) μ±ν ID
    """
    set_status(chat_id, ST_INFO)
    send_msg(chat_id, u'μ‘°ν?  μ’λͺ© ?΄λ¦μ ?? ₯??Έ?.')

def cmd_addquote(chat_id, text, result_list):
    u"""cmd_addquote: μ’λͺ© μΆκ??
    chat_id: (integer) μ±ν ID
    """
    USER_KEYBOARD = result_list
    send_msg(chat_id, u'μ’λͺ©? ? ??΄μ£Όμ­??€.\n? ? ?? μ’λ£? /close ? ? ??΄μ£ΌμΈ?.', keyboard=USER_KEYBOARD)

def cmd_bond(chat_id):
    u"""cmd_bond: μ±κΆ ??΅λ₯? μ‘°ν
    chat_id: (integer) μ±ν ID
    """
    BondRatesInfo = u'μ±κΆλ§κΈ°λ³? κ΅?κ³ μ± ??΅λ₯? ? λ³?\n'
    BondRates = CollectBondRates(url_bondinfo)
    for itm in BondRates['current']:
        BondRatesInfo = BondRatesInfo + itm[0] + ' - ' + str(itm[1]) + '\n'
    send_msg(chat_id, BondRatesInfo)

def cmd_close(chat_id):
    u"""cmd_close: μ’λͺ© μ‘°ν λͺ¨λ μ’λ£
    chat_id: (integer) μ±ν ID
    """
    set_status(chat_id, ST_ECHO)
    send_msg(chat_id, u'μ’λͺ© μ‘°νκ°? μ’λ£???΅??€.', keyboard=CUSTOM_KEYBOARD)

def cmd_broadcast(chat_id, text):
    u"""cmd_broadcast: λ΄μ΄ ??±?? λͺ¨λ  μ±ν? λ©μμ§? λ°©μ‘
    chat_id: (integer) μ±ν ID
    text:    (string)  λ°©μ‘?  λ©μμ§?
    """
    send_msg(chat_id, u'λ©μμ§?λ₯? λ°©μ‘?©??€.', keyboard=CUSTOM_KEYBOARD)
    broadcast(text)

def cmd_echo(chat_id, text, reply_to):
    u"""cmd_echo: ?¬?©?? λ©μμ§?λ₯? ?°?Ό? ?΅?₯
    chat_id:  (integer) μ±ν ID
    text:     (string)  ?¬?©?κ°? λ³΄λΈ λ©μμ§? ?΄?©
    reply_to: (integer) ?΅?₯?  λ©μμ§? ID
    """
    send_msg(chat_id, text, reply_to=reply_to)

def cron_method(handler):
    def check_if_cron(self, *args, **kwargs):
        if self.request.headers.get('X-AppEngine-Cron') is None:
            self.error(403)
        else:
            return handler(self, *args, **kwargs)
    return check_if_cron

def process_cmds(msg):
    u"""?¬?©? λ©μμ§?λ₯? λΆμ?΄ λ΄? λͺλ Ή? μ²λ¦¬
    chat_id: (integer) μ±ν ID
    text:    (string)  ?¬?©?κ°? λ³΄λΈ λ©μμ§? ?΄?©
    """
    msg_id = msg['message_id']
    chat_id = msg['chat']['id']
    text = msg.get('text')
    if (not text):
        return
    if CMD_START == text:
        cmd_start(chat_id)
        return
    if (not get_enabled(chat_id)):
        return
    if CMD_STOP == text:
        cmd_stop(chat_id)
        return
    if CMD_HELP == text:
        cmd_help(chat_id)
        return
    if CMD_CLOSE == text:
        cmd_close(chat_id)
        return
    if CMD_INFO == text:
        cmd_info(chat_id)
        return
    if CMD_BOND == text:
        cmd_bond(chat_id)
        return
    if get_status(chat_id) == ST_INFO:
        result_list = FindCodeAPI(APIKey, text)
        if not result_list[0]:
            send_msg(chat_id, u'μ’λͺ©λͺμ κ²???  ? ??΅??€. ?€? ??Έ ? ?? ₯?΄μ£ΌμΈ?.')
        elif len(result_list[0]) == 1 and result_list[0][0][0] == text:
            send_msg(chat_id, result_list[0][0][0] + u' μ’λͺ©(' + result_list[1][0][0] + u')?΄ μ‘΄μ¬?©??€.')
            ValInfo = FindInfo(result_list[1][0][0])
            send_msg(chat_id, u'PER: ' + ValInfo[0] + u' 12M PER: ' + ValInfo[1] + u' PBR: ' + ValInfo[3] + u' λ°°λΉ??΅λ₯?: ' + ValInfo[4])
            send_photo(chat_id, 'http://comp.fnguide.com/SVO2/chartImg/01_06/PER_A' + result_list[1][0][0] + '_B_01_06.png')
            send_photo(chat_id, 'http://comp.fnguide.com/SVO2/chartImg/01_06/PBR_A' + result_list[1][0][0] + '_B_01_06.png')
        else:
            count = 0
            for li in result_list[0]:
                if li[0] == text:
                    send_msg(chat_id, u'??Ό? μ’λͺ©?΄ λ°κ²¬???΅??€.')
                    send_msg(chat_id, text + u' μ’λͺ©(' + result_list[1][count][0] + u')?΄ μ‘΄μ¬?©??€.')
                    ValInfo = FindInfo(result_list[1][count][0])
                    send_msg(chat_id, u'PER: ' + ValInfo[0] + u' 12M PER: ' + ValInfo[1] + u' PBR: ' + ValInfo[3] + u' λ°°λΉ??΅λ₯?: ' + ValInfo[4])
                    send_photo(chat_id, 'http://comp.fnguide.com/SVO2/chartImg/01_06/PER_A' + result_list[1][count][0] + '_B_01_06.png')
                    send_photo(chat_id, 'http://comp.fnguide.com/SVO2/chartImg/01_06/PBR_A' + result_list[1][count][0] + '_B_01_06.png')
                    return
                count += 1
            merge_list = MergeList(result_list[0])
            result_list[0].append([CMD_CLOSE])
            cmd_addquote(chat_id, merge_list, result_list[0])
        return
    cmd_broadcast_match = re.match('^' + CMD_BROADCAST + ' (.*)', text)
    if cmd_broadcast_match:
        cmd_broadcast(chat_id, cmd_broadcast_match.group(1))
        return
    cmd_echo(chat_id, text, reply_to=msg_id)
    return

# ?Ή ?μ²?? ???? ?Έ?€?¬ ? ?
# /me ?μ²??
class MeHandler(webapp2.RequestHandler):
    def get(self):
        urlfetch.set_default_fetch_deadline(60)
        self.response.write(json.dumps(json.load(urllib2.urlopen(BASE_URL + 'getMe'))))

# /updates ?μ²??
class GetUpdatesHandler(webapp2.RequestHandler):
    def get(self):
        urlfetch.set_default_fetch_deadline(60)
        self.response.write(json.dumps(json.load(urllib2.urlopen(BASE_URL + 'getUpdates'))))

# /set-wehook ?μ²??
class SetWebhookHandler(webapp2.RequestHandler):
    def get(self):
        urlfetch.set_default_fetch_deadline(60)
        url = self.request.get('url')
        if url:
            self.response.write(json.dumps(json.load(urllib2.urlopen(BASE_URL + 'setWebhook', urllib.urlencode({'url': url})))))

# /webhook ?μ²?? (?? κ·Έλ¨ λ΄? API)
class WebhookHandler(webapp2.RequestHandler):
    def post(self):
        urlfetch.set_default_fetch_deadline(60)
        body = json.loads(self.request.body)
        self.response.write(json.dumps(body))
        process_cmds(body['message'])

class WebhookHandler1(webapp2.RequestHandler):
    @cron_method
    def get(self):
        now = time.gmtime(time.time() + 3600 * 9)
        # ? ??Ό?΄? ?Ό??Ό?Έ κ²½μ°? ?λ¦? μ€μ??
        if now.tm_wday == 5 or now.tm_wday == 6:
            return
        else:
            urlfetch.set_default_fetch_deadline(60)
            s = '??€?Έ???€.'
            broadcast(s)

        
# κ΅¬κ?? ?± ?μ§μ ?Ή ?μ²? ?Έ?€?¬ μ§?? 
app = webapp2.WSGIApplication([
    ('/me', MeHandler),
    ('/updates', GetUpdatesHandler),
    ('/set-webhook', SetWebhookHandler),
    ('/webhook', WebhookHandler),
    ('/broadcast-news', WebhookHandler1),
], debug=True)
