#-*- coding: utf-8 -*-
#
# original:    https://github.com/yukuku/telebot
# modified by: Bak Yeon O @ http://bakyeono.net
# description: http://bakyeono.net/post/2015-08-24-using-telegram-bot-api.html
# github:      https://github.com/bakyeono/using-telegram-bot-api
# githun:      https://github.com/hyunsikhwang/FnPython

# 구�?? ?�� ?���? ?��?��브러�? 로드
from google.appengine.api import urlfetch
from google.appengine.ext import ndb
import webapp2

# URL, JSON, 로그, ?��규표?��?�� �??�� ?��?��브러�? 로드
import urllib
import urllib2
import json
import logging
import re

# 종목�? 찾기 API �??�� ?��?��브러�? 로드
from urllib import urlencode, quote_plus
from urllib2 import Request, urlopen

from bs4 import BeautifulSoup
#import requests
import lxml.html
from google.appengine.api import urlfetch
#from lxml import html


# �? ?��?��, �? API 주소
TOKEN = '303352490:AAGLVFQbnFyviIelWVBynx98JGqd_GoVRzQ'
BASE_URL = 'https://api.telegram.org/bot' + TOKEN + '/'

# 종목�? 찾기 API Key
APIKey = "CJL9jdtz5gsb4z4PpjFpCDjdz/UIk8cFAGgHbJvgLEJxPWLZaTx3wIcBNPkGu/KIKsI1zAy1XtfQJLG0VV0vVg=="

# 채권 ?��?���? ?���? ?��?���?
url_bondinfo = "http://sbcharts.investing.com/bond_charts/bonds_chart_60.json"

# 봇이 ?��?��?�� 명령?��
CMD_START     = '/start'
CMD_STOP      = '/stop'
CMD_HELP      = '/help'
CMD_BROADCAST = '/broadcast'
CMD_INFO      = '/info'
CMD_BOND      = '/bond'
CMD_CLOSE     = '/close'

# �? ?��?���? & 메시�?
USAGE = u"""[?��?���?] ?��?�� 명령?���? 메시�?�? 보내거나 버튼?�� ?��르시�? ?��?��?��.
/start - (로봇 ?��?��?��)
/stop  - (로봇 비활?��?��)
/help  - (?�� ?��???�? 보여주기)
/info  - (?���? 조회)
/bond  - (채권 ?��?���? 조회)
"""
MSG_START = u'봇을 ?��?��?��?��?��.'
MSG_STOP  = u'봇을 ?���??��?��?��.'

# 커스??? ?��보드
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


# 채팅�? 로봇 ?��?��?�� ?��?��
# 구�?? ?�� ?��진의 Datastore(NDB)?�� ?��?���? ????��?���? ?��?��
# ?��?��?���? /start ?��르면 ?��?��?��
# ?��?��?���? /stop  ?��르면 비활?��?��
class EnableStatus(ndb.Model):
    enabled = ndb.BooleanProperty(required=True, indexed=True, default=False,)

def set_enabled(chat_id, enabled):
    u"""set_enabled: �? ?��?��?��/비활?��?�� ?��?�� �?�?
    chat_id:    (integer) 봇을 ?��?��?��/비활?��?��?�� 채팅 ID
    enabled:    (boolean) �??��?�� ?��?��?��/비활?��?�� ?��?��
    """
    es = EnableStatus.get_or_insert(str(chat_id))
    es.enabled = enabled
    es.put()

def get_enabled(chat_id):
    u"""get_enabled: �? ?��?��?��/비활?��?�� ?��?�� 반환
    return: (boolean)
    """
    es = EnableStatus.get_by_id(str(chat_id))
    if es:
        return es.enabled
    return False

def get_status(chat_id):
    u"""get_status: ?��?�� ?��?�� 반환
    return: (boolean)
    """
    cs = CommandStatus.get_by_id(str(chat_id))
    if cs:
        return cs.command_status
    return False

def get_enabled_chats():
    u"""get_enabled: 봇이 ?��?��?��?�� 채팅 리스?�� 반환
    return: (list of EnableStatus)
    """
    query = EnableStatus.query(EnableStatus.enabled == True)
    return query.fetch()

def set_status(chat_id, cmd_status):
    u"""set_status: 명령?�� ?��?��
    chat_id:    (integer) 채팅 ID
    cmd_status: (integer) 명령?�� ?��?��(info)
    """
    cs = CommandStatus.get_or_insert(str(chat_id))
    cs.command_status = cmd_status
    cs.put()

# 메시�? 발송 �??�� ?��?��?��
def send_msg(chat_id, text, reply_to=None, no_preview=True, keyboard=None):
    u"""send_msg: 메시�? 발송
    chat_id:    (integer) 메시�?�? 보낼 채팅 ID
    text:       (string)  메시�? ?��?��
    reply_to:   (integer) ~메시�??�� ????�� ?��?��
    no_preview: (boolean) URL ?��?�� 링크(미리보기) ?���?
    keyboard:   (list)    커스??? ?��보드 �??��
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
    u"""send_photo: 메시�? 발송
    chat_id:    (integer) 메시�?�? 보낼 채팅 ID
    text:       (string)  메시�? ?��?��
    reply_to:   (integer) ~메시�??�� ????�� ?��?��
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
    u"""broadcast: 봇이 켜져 ?��?�� 모든 채팅?�� 메시�? 발송
    text:       (string)  메시�? ?��?��
    """
    for chat in get_enabled_chats():
        send_msg(chat.key.string_id(), text)

# �? 명령 처리 ?��?��?��
def cmd_start(chat_id):
    u"""cmd_start: 봇을 ?��?��?��?���?, ?��?��?�� 메시�? 발송
    chat_id: (integer) 채팅 ID
    """
    set_enabled(chat_id, True)
    send_msg(chat_id, MSG_START, keyboard=CUSTOM_KEYBOARD)

def cmd_stop(chat_id):
    u"""cmd_stop: 봇을 비활?��?��?���?, 비활?��?�� 메시�? 발송
    chat_id: (integer) 채팅 ID
    """
    set_enabled(chat_id, False)
    send_msg(chat_id, MSG_STOP)

def cmd_help(chat_id):
    u"""cmd_help: �? ?��?���? 메시�? 발송
    chat_id: (integer) 채팅 ID
    """
    send_msg(chat_id, USAGE, keyboard=CUSTOM_KEYBOARD)

def cmd_info(chat_id):
    u"""cmd_info: 종목 ?���? 조회
    chat_id: (integer) 채팅 ID
    """
    set_status(chat_id, ST_INFO)
    send_msg(chat_id, u'조회?�� 종목 ?��름을 ?��?��?��?��?��.')

def cmd_addquote(chat_id, text, result_list):
    u"""cmd_addquote: 종목 추�??
    chat_id: (integer) 채팅 ID
    """
    USER_KEYBOARD = result_list
    send_msg(chat_id, u'종목?�� ?��?��?��주십?��?��.\n?��?�� ?��?�� 종료?�� /close ?�� ?��?��?��주세?��.', keyboard=USER_KEYBOARD)

def cmd_bond(chat_id):
    u"""cmd_bond: 채권 ?��?���? 조회
    chat_id: (integer) 채팅 ID
    """
    BondRatesInfo = u'채권만기�? �?고채 ?��?���? ?���?\n'
    BondRates = CollectBondRates(url_bondinfo)
    for itm in BondRates['current']:
        BondRatesInfo = BondRatesInfo + itm[0] + ' - ' + str(itm[1]) + '\n'
    send_msg(chat_id, BondRatesInfo)

def cmd_close(chat_id):
    u"""cmd_close: 종목 조회 모드 종료
    chat_id: (integer) 채팅 ID
    """
    set_status(chat_id, ST_ECHO)
    send_msg(chat_id, u'종목 조회�? 종료?��?��?��?��?��.', keyboard=CUSTOM_KEYBOARD)

def cmd_broadcast(chat_id, text):
    u"""cmd_broadcast: 봇이 ?��?��?��?�� 모든 채팅?�� 메시�? 방송
    chat_id: (integer) 채팅 ID
    text:    (string)  방송?�� 메시�?
    """
    send_msg(chat_id, u'메시�?�? 방송?��?��?��.', keyboard=CUSTOM_KEYBOARD)
    broadcast(text)

def cmd_echo(chat_id, text, reply_to):
    u"""cmd_echo: ?��?��?��?�� 메시�?�? ?��?��?�� ?��?��
    chat_id:  (integer) 채팅 ID
    text:     (string)  ?��?��?���? 보낸 메시�? ?��?��
    reply_to: (integer) ?��?��?�� 메시�? ID
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
    u"""?��?��?�� 메시�?�? 분석?�� �? 명령?�� 처리
    chat_id: (integer) 채팅 ID
    text:    (string)  ?��?��?���? 보낸 메시�? ?��?��
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
            send_msg(chat_id, u'종목명을 �??��?�� ?�� ?��?��?��?��. ?��?�� ?��?�� ?�� ?��?��?��주세?��.')
        elif len(result_list[0]) == 1 and result_list[0][0][0] == text:
            send_msg(chat_id, result_list[0][0][0] + u' 종목(' + result_list[1][0][0] + u')?�� 존재?��?��?��.')
            ValInfo = FindInfo(result_list[1][0][0])
            send_msg(chat_id, u'PER: ' + ValInfo[0] + u' 12M PER: ' + ValInfo[1] + u' PBR: ' + ValInfo[3] + u' 배당?��?���?: ' + ValInfo[4])
            send_photo(chat_id, 'http://comp.fnguide.com/SVO2/chartImg/01_06/PER_A' + result_list[1][0][0] + '_B_01_06.png')
            send_photo(chat_id, 'http://comp.fnguide.com/SVO2/chartImg/01_06/PBR_A' + result_list[1][0][0] + '_B_01_06.png')
        else:
            count = 0
            for li in result_list[0]:
                if li[0] == text:
                    send_msg(chat_id, u'?��?��?�� 종목?�� 발견?��?��?��?��?��.')
                    send_msg(chat_id, text + u' 종목(' + result_list[1][count][0] + u')?�� 존재?��?��?��.')
                    ValInfo = FindInfo(result_list[1][count][0])
                    send_msg(chat_id, u'PER: ' + ValInfo[0] + u' 12M PER: ' + ValInfo[1] + u' PBR: ' + ValInfo[3] + u' 배당?��?���?: ' + ValInfo[4])
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

# ?�� ?���??�� ????�� ?��?��?�� ?��?��
# /me ?���??��
class MeHandler(webapp2.RequestHandler):
    def get(self):
        urlfetch.set_default_fetch_deadline(60)
        self.response.write(json.dumps(json.load(urllib2.urlopen(BASE_URL + 'getMe'))))

# /updates ?���??��
class GetUpdatesHandler(webapp2.RequestHandler):
    def get(self):
        urlfetch.set_default_fetch_deadline(60)
        self.response.write(json.dumps(json.load(urllib2.urlopen(BASE_URL + 'getUpdates'))))

# /set-wehook ?���??��
class SetWebhookHandler(webapp2.RequestHandler):
    def get(self):
        urlfetch.set_default_fetch_deadline(60)
        url = self.request.get('url')
        if url:
            self.response.write(json.dumps(json.load(urllib2.urlopen(BASE_URL + 'setWebhook', urllib.urlencode({'url': url})))))

# /webhook ?���??�� (?��?��그램 �? API)
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
        # ?��?��?��?��?�� ?��?��?��?�� 경우?�� ?���? 중�??
        if now.tm_wday == 5 or now.tm_wday == 6:
            return
        else:
            urlfetch.set_default_fetch_deadline(60)
            s = '?��?��?��?��?��?��.'
            broadcast(s)

        
# 구�?? ?�� ?��진에 ?�� ?���? ?��?��?�� �??��
app = webapp2.WSGIApplication([
    ('/me', MeHandler),
    ('/updates', GetUpdatesHandler),
    ('/set-webhook', SetWebhookHandler),
    ('/webhook', WebhookHandler),
    ('/broadcast-news', WebhookHandler1),
], debug=True)
