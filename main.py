#-*- coding: utf-8 -*-
#
# original:    https://github.com/yukuku/telebot
# modified by: Bak Yeon O @ http://bakyeono.net
# description: http://bakyeono.net/post/2015-08-24-using-telegram-bot-api.html
# github:      https://github.com/bakyeono/using-telegram-bot-api
# githun:      https://github.com/hyunsikhwang/FnPython

# êµ¬ê?? ?•± ?—”ì§? ?¼?´ë¸ŒëŸ¬ë¦? ë¡œë“œ
from google.appengine.api import urlfetch
from google.appengine.ext import ndb
import webapp2

# URL, JSON, ë¡œê·¸, ? •ê·œí‘œ?˜„?‹ ê´?? ¨ ?¼?´ë¸ŒëŸ¬ë¦? ë¡œë“œ
import urllib
import urllib2
import json
import logging
import re

# ì¢…ëª©ëª? ì°¾ê¸° API ê´?? ¨ ?¼?´ë¸ŒëŸ¬ë¦? ë¡œë“œ
from urllib import urlencode, quote_plus
from urllib2 import Request, urlopen

from bs4 import BeautifulSoup
#import requests
import lxml.html
from google.appengine.api import urlfetch
#from lxml import html


# ë´? ?† ?°, ë´? API ì£¼ì†Œ
TOKEN = '303352490:AAGLVFQbnFyviIelWVBynx98JGqd_GoVRzQ'
BASE_URL = 'https://api.telegram.org/bot' + TOKEN + '/'

# ì¢…ëª©ëª? ì°¾ê¸° API Key
APIKey = "CJL9jdtz5gsb4z4PpjFpCDjdz/UIk8cFAGgHbJvgLEJxPWLZaTx3wIcBNPkGu/KIKsI1zAy1XtfQJLG0VV0vVg=="

# ì±„ê¶Œ ?ˆ˜?µë¥? ? •ë³? ?˜?´ì§?
url_bondinfo = "http://sbcharts.investing.com/bond_charts/bonds_chart_60.json"

# ë´‡ì´ ?‘?‹µ?•  ëª…ë ¹?–´
CMD_START     = '/start'
CMD_STOP      = '/stop'
CMD_HELP      = '/help'
CMD_BROADCAST = '/broadcast'
CMD_INFO      = '/info'
CMD_BOND      = '/bond'
CMD_CLOSE     = '/close'

# ë´? ?‚¬?š©ë²? & ë©”ì‹œì§?
USAGE = u"""[?‚¬?š©ë²?] ?•„?˜ ëª…ë ¹?–´ë¥? ë©”ì‹œì§?ë¡? ë³´ë‚´ê±°ë‚˜ ë²„íŠ¼?„ ?ˆ„ë¥´ì‹œë©? ?©?‹ˆ?‹¤.
/start - (ë¡œë´‡ ?™œ?„±?™”)
/stop  - (ë¡œë´‡ ë¹„í™œ?„±?™”)
/help  - (?´ ?„???ë§? ë³´ì—¬ì£¼ê¸°)
/info  - (? •ë³? ì¡°íšŒ)
/bond  - (ì±„ê¶Œ ?ˆ˜?µë¥? ì¡°íšŒ)
"""
MSG_START = u'ë´‡ì„ ?‹œ?‘?•©?‹ˆ?‹¤.'
MSG_STOP  = u'ë´‡ì„ ? •ì§??•©?‹ˆ?‹¤.'

# ì»¤ìŠ¤??? ?‚¤ë³´ë“œ
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


# ì±„íŒ…ë³? ë¡œë´‡ ?™œ?„±?™” ?ƒ?ƒœ
# êµ¬ê?? ?•± ?—”ì§„ì˜ Datastore(NDB)?— ?ƒ?ƒœë¥? ????¥?•˜ê³? ?½?Œ
# ?‚¬?š©?ê°? /start ?ˆ„ë¥´ë©´ ?™œ?„±?™”
# ?‚¬?š©?ê°? /stop  ?ˆ„ë¥´ë©´ ë¹„í™œ?„±?™”
class EnableStatus(ndb.Model):
    enabled = ndb.BooleanProperty(required=True, indexed=True, default=False,)

def set_enabled(chat_id, enabled):
    u"""set_enabled: ë´? ?™œ?„±?™”/ë¹„í™œ?„±?™” ?ƒ?ƒœ ë³?ê²?
    chat_id:    (integer) ë´‡ì„ ?™œ?„±?™”/ë¹„í™œ?„±?™”?•  ì±„íŒ… ID
    enabled:    (boolean) ì§?? •?•  ?™œ?„±?™”/ë¹„í™œ?„±?™” ?ƒ?ƒœ
    """
    es = EnableStatus.get_or_insert(str(chat_id))
    es.enabled = enabled
    es.put()

def get_enabled(chat_id):
    u"""get_enabled: ë´? ?™œ?„±?™”/ë¹„í™œ?„±?™” ?ƒ?ƒœ ë°˜í™˜
    return: (boolean)
    """
    es = EnableStatus.get_by_id(str(chat_id))
    if es:
        return es.enabled
    return False

def get_status(chat_id):
    u"""get_status: ?‚¬?š© ?ƒ?ƒœ ë°˜í™˜
    return: (boolean)
    """
    cs = CommandStatus.get_by_id(str(chat_id))
    if cs:
        return cs.command_status
    return False

def get_enabled_chats():
    u"""get_enabled: ë´‡ì´ ?™œ?„±?™”?œ ì±„íŒ… ë¦¬ìŠ¤?Š¸ ë°˜í™˜
    return: (list of EnableStatus)
    """
    query = EnableStatus.query(EnableStatus.enabled == True)
    return query.fetch()

def set_status(chat_id, cmd_status):
    u"""set_status: ëª…ë ¹?–´ ?ƒ?ƒœ
    chat_id:    (integer) ì±„íŒ… ID
    cmd_status: (integer) ëª…ë ¹?–´ ?ƒ?ƒœ(info)
    """
    cs = CommandStatus.get_or_insert(str(chat_id))
    cs.command_status = cmd_status
    cs.put()

# ë©”ì‹œì§? ë°œì†¡ ê´?? ¨ ?•¨?ˆ˜?“¤
def send_msg(chat_id, text, reply_to=None, no_preview=True, keyboard=None):
    u"""send_msg: ë©”ì‹œì§? ë°œì†¡
    chat_id:    (integer) ë©”ì‹œì§?ë¥? ë³´ë‚¼ ì±„íŒ… ID
    text:       (string)  ë©”ì‹œì§? ?‚´?š©
    reply_to:   (integer) ~ë©”ì‹œì§??— ????•œ ?‹µ?¥
    no_preview: (boolean) URL ??™ ë§í¬(ë¯¸ë¦¬ë³´ê¸°) ?„ê¸?
    keyboard:   (list)    ì»¤ìŠ¤??? ?‚¤ë³´ë“œ ì§?? •
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
    u"""send_photo: ë©”ì‹œì§? ë°œì†¡
    chat_id:    (integer) ë©”ì‹œì§?ë¥? ë³´ë‚¼ ì±„íŒ… ID
    text:       (string)  ë©”ì‹œì§? ?‚´?š©
    reply_to:   (integer) ~ë©”ì‹œì§??— ????•œ ?‹µ?¥
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
    u"""broadcast: ë´‡ì´ ì¼œì ¸ ?ˆ?Š” ëª¨ë“  ì±„íŒ…?— ë©”ì‹œì§? ë°œì†¡
    text:       (string)  ë©”ì‹œì§? ?‚´?š©
    """
    for chat in get_enabled_chats():
        send_msg(chat.key.string_id(), text)

# ë´? ëª…ë ¹ ì²˜ë¦¬ ?•¨?ˆ˜?“¤
def cmd_start(chat_id):
    u"""cmd_start: ë´‡ì„ ?™œ?„±?™”?•˜ê³?, ?™œ?„±?™” ë©”ì‹œì§? ë°œì†¡
    chat_id: (integer) ì±„íŒ… ID
    """
    set_enabled(chat_id, True)
    send_msg(chat_id, MSG_START, keyboard=CUSTOM_KEYBOARD)

def cmd_stop(chat_id):
    u"""cmd_stop: ë´‡ì„ ë¹„í™œ?„±?™”?•˜ê³?, ë¹„í™œ?„±?™” ë©”ì‹œì§? ë°œì†¡
    chat_id: (integer) ì±„íŒ… ID
    """
    set_enabled(chat_id, False)
    send_msg(chat_id, MSG_STOP)

def cmd_help(chat_id):
    u"""cmd_help: ë´? ?‚¬?š©ë²? ë©”ì‹œì§? ë°œì†¡
    chat_id: (integer) ì±„íŒ… ID
    """
    send_msg(chat_id, USAGE, keyboard=CUSTOM_KEYBOARD)

def cmd_info(chat_id):
    u"""cmd_info: ì¢…ëª© ? •ë³? ì¡°íšŒ
    chat_id: (integer) ì±„íŒ… ID
    """
    set_status(chat_id, ST_INFO)
    send_msg(chat_id, u'ì¡°íšŒ?•  ì¢…ëª© ?´ë¦„ì„ ?…? ¥?•˜?„¸?š”.')

def cmd_addquote(chat_id, text, result_list):
    u"""cmd_addquote: ì¢…ëª© ì¶”ê??
    chat_id: (integer) ì±„íŒ… ID
    """
    USER_KEYBOARD = result_list
    send_msg(chat_id, u'ì¢…ëª©?„ ?„ ?ƒ?•´ì£¼ì‹­?‹œ?˜¤.\n?„ ?ƒ ?‘?—… ì¢…ë£Œ?Š” /close ?„ ?„ ?ƒ?•´ì£¼ì„¸?š”.', keyboard=USER_KEYBOARD)

def cmd_bond(chat_id):
    u"""cmd_bond: ì±„ê¶Œ ?ˆ˜?µë¥? ì¡°íšŒ
    chat_id: (integer) ì±„íŒ… ID
    """
    BondRatesInfo = u'ì±„ê¶Œë§Œê¸°ë³? êµ?ê³ ì±„ ?ˆ˜?µë¥? ? •ë³?\n'
    BondRates = CollectBondRates(url_bondinfo)
    for itm in BondRates['current']:
        BondRatesInfo = BondRatesInfo + itm[0] + ' - ' + str(itm[1]) + '\n'
    send_msg(chat_id, BondRatesInfo)

def cmd_close(chat_id):
    u"""cmd_close: ì¢…ëª© ì¡°íšŒ ëª¨ë“œ ì¢…ë£Œ
    chat_id: (integer) ì±„íŒ… ID
    """
    set_status(chat_id, ST_ECHO)
    send_msg(chat_id, u'ì¢…ëª© ì¡°íšŒê°? ì¢…ë£Œ?˜?—ˆ?Šµ?‹ˆ?‹¤.', keyboard=CUSTOM_KEYBOARD)

def cmd_broadcast(chat_id, text):
    u"""cmd_broadcast: ë´‡ì´ ?™œ?„±?™”?œ ëª¨ë“  ì±„íŒ…?— ë©”ì‹œì§? ë°©ì†¡
    chat_id: (integer) ì±„íŒ… ID
    text:    (string)  ë°©ì†¡?•  ë©”ì‹œì§?
    """
    send_msg(chat_id, u'ë©”ì‹œì§?ë¥? ë°©ì†¡?•©?‹ˆ?‹¤.', keyboard=CUSTOM_KEYBOARD)
    broadcast(text)

def cmd_echo(chat_id, text, reply_to):
    u"""cmd_echo: ?‚¬?š©??˜ ë©”ì‹œì§?ë¥? ?”°?¼?„œ ?‹µ?¥
    chat_id:  (integer) ì±„íŒ… ID
    text:     (string)  ?‚¬?š©?ê°? ë³´ë‚¸ ë©”ì‹œì§? ?‚´?š©
    reply_to: (integer) ?‹µ?¥?•  ë©”ì‹œì§? ID
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
    u"""?‚¬?š©? ë©”ì‹œì§?ë¥? ë¶„ì„?•´ ë´? ëª…ë ¹?„ ì²˜ë¦¬
    chat_id: (integer) ì±„íŒ… ID
    text:    (string)  ?‚¬?š©?ê°? ë³´ë‚¸ ë©”ì‹œì§? ?‚´?š©
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
            send_msg(chat_id, u'ì¢…ëª©ëª…ì„ ê²??ƒ‰?•  ?ˆ˜ ?—†?Šµ?‹ˆ?‹¤. ?‹¤?‹œ ?™•?¸ ?›„ ?…? ¥?•´ì£¼ì„¸?š”.')
        elif len(result_list[0]) == 1 and result_list[0][0][0] == text:
            send_msg(chat_id, result_list[0][0][0] + u' ì¢…ëª©(' + result_list[1][0][0] + u')?´ ì¡´ì¬?•©?‹ˆ?‹¤.')
            ValInfo = FindInfo(result_list[1][0][0])
            send_msg(chat_id, u'PER: ' + ValInfo[0] + u' 12M PER: ' + ValInfo[1] + u' PBR: ' + ValInfo[3] + u' ë°°ë‹¹?ˆ˜?µë¥?: ' + ValInfo[4])
            send_photo(chat_id, 'http://comp.fnguide.com/SVO2/chartImg/01_06/PER_A' + result_list[1][0][0] + '_B_01_06.png')
            send_photo(chat_id, 'http://comp.fnguide.com/SVO2/chartImg/01_06/PBR_A' + result_list[1][0][0] + '_B_01_06.png')
        else:
            count = 0
            for li in result_list[0]:
                if li[0] == text:
                    send_msg(chat_id, u'?™?¼?•œ ì¢…ëª©?´ ë°œê²¬?˜?—ˆ?Šµ?‹ˆ?‹¤.')
                    send_msg(chat_id, text + u' ì¢…ëª©(' + result_list[1][count][0] + u')?´ ì¡´ì¬?•©?‹ˆ?‹¤.')
                    ValInfo = FindInfo(result_list[1][count][0])
                    send_msg(chat_id, u'PER: ' + ValInfo[0] + u' 12M PER: ' + ValInfo[1] + u' PBR: ' + ValInfo[3] + u' ë°°ë‹¹?ˆ˜?µë¥?: ' + ValInfo[4])
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

# ?›¹ ?š”ì²??— ????•œ ?•¸?“¤?Ÿ¬ ? •?˜
# /me ?š”ì²??‹œ
class MeHandler(webapp2.RequestHandler):
    def get(self):
        urlfetch.set_default_fetch_deadline(60)
        self.response.write(json.dumps(json.load(urllib2.urlopen(BASE_URL + 'getMe'))))

# /updates ?š”ì²??‹œ
class GetUpdatesHandler(webapp2.RequestHandler):
    def get(self):
        urlfetch.set_default_fetch_deadline(60)
        self.response.write(json.dumps(json.load(urllib2.urlopen(BASE_URL + 'getUpdates'))))

# /set-wehook ?š”ì²??‹œ
class SetWebhookHandler(webapp2.RequestHandler):
    def get(self):
        urlfetch.set_default_fetch_deadline(60)
        url = self.request.get('url')
        if url:
            self.response.write(json.dumps(json.load(urllib2.urlopen(BASE_URL + 'setWebhook', urllib.urlencode({'url': url})))))

# /webhook ?š”ì²??‹œ (?…”? ˆê·¸ë¨ ë´? API)
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
        # ?† ?š”?¼?´?‚˜ ?¼?š”?¼?¸ ê²½ìš°?—” ?•Œë¦? ì¤‘ì??
        if now.tm_wday == 5 or now.tm_wday == 6:
            return
        else:
            urlfetch.set_default_fetch_deadline(60)
            s = '?…Œ?Š¤?Š¸?…?‹ˆ?‹¤.'
            broadcast(s)

        
# êµ¬ê?? ?•± ?—”ì§„ì— ?›¹ ?š”ì²? ?•¸?“¤?Ÿ¬ ì§?? •
app = webapp2.WSGIApplication([
    ('/me', MeHandler),
    ('/updates', GetUpdatesHandler),
    ('/set-webhook', SetWebhookHandler),
    ('/webhook', WebhookHandler),
    ('/broadcast-news', WebhookHandler1),
], debug=True)
