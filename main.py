#-*- coding: utf-8 -*-
#
# original:    https://github.com/yukuku/telebot
# modified by: Bak Yeon O @ http://bakyeono.net
# description: http://bakyeono.net/post/2015-08-24-using-telegram-bot-api.html
# github:      https://github.com/bakyeono/using-telegram-bot-api
# githun:      https://github.com/hyunsikhwang/FnPython

# 구글 앱 엔진 라이브러리 로드
from google.appengine.api import urlfetch
from google.appengine.ext import ndb
import webapp2

# URL, JSON, 로그, 정규표현식 관련 라이브러리 로드
import urllib
import urllib2
import json
import logging
import re
import time

# 종목명 찾기 API 관련 라이브러리 로드
from urllib import urlencode, quote_plus
from urllib2 import Request, urlopen

from bs4 import BeautifulSoup
#import requests
import lxml.html
from google.appengine.api import urlfetch
#from lxml import html


# 봇 토큰, 봇 API 주소
TOKEN = '303352490:AAGLVFQbnFyviIelWVBynx98JGqd_GoVRzQ'
BASE_URL = 'https://api.telegram.org/bot' + TOKEN + '/'

# 종목명 찾기 API Key
APIKey = "CJL9jdtz5gsb4z4PpjFpCDjdz/UIk8cFAGgHbJvgLEJxPWLZaTx3wIcBNPkGu/KIKsI1zAy1XtfQJLG0VV0vVg=="

# DART API Key
DARTAPIKey = "0163d3df4b40f223395ed5e93c38e947b42b9414"

# 채권 수익률 정보 페이지
url_bondinfo = "http://sbcharts.investing.com/bond_charts/bonds_chart_60.json"

# DART JSON
DART = 'http://dart.fss.or.kr/api/search.json?auth=' + DARTAPIKey + '&page_set=100'

MarketType = {'Y':u'유가증권', 'K':u'코스닥', 'E': u'기타'}

# 봇이 응답할 명령어
CMD_START     = '/start'
CMD_STOP      = '/stop'
CMD_HELP      = '/help'
CMD_BROADCAST = '/broadcast'
CMD_INFO      = '/info'
CMD_BOND      = '/bond'
CMD_REFRESH   = '/refresh'
CMD_CLOSE     = '/close'

# 봇 사용법 & 메시지
USAGE = u"""[사용법] 아래 명령어를 메시지로 보내거나 버튼을 누르시면 됩니다.
/start   - (로봇 활성화)
/stop    - (로봇 비활성화)
/help    - (이 도움말 보여주기)
/info    - (정보 조회)
/bond    - (채권 수익률 조회)
/refresh - (공시 Refresh)
"""
MSG_START = u'봇을 시작합니다.'
MSG_STOP  = u'봇을 정지합니다.'

# 커스텀 키보드
CUSTOM_KEYBOARD = [
        [CMD_START,CMD_STOP,CMD_HELP],
        [CMD_INFO,CMD_BOND,CMD_REFRESH]
        ]

USER_KEYBOARD = []

ST_ECHO, ST_INFO, ST_BOND, ST_REFRESH = range(4)

class CommandStatus(ndb.Model):
    command_status = ndb.IntegerProperty(required=True, indexed=True, default=False,)


def CallDART(url):
    f = urllib2.urlopen(url)
    page = f.read()
    f.close()
    js = json.loads(page)
    return js


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


# 채팅별 로봇 활성화 상태
# 구글 앱 엔진의 Datastore(NDB)에 상태를 저장하고 읽음
# 사용자가 /start 누르면 활성화
# 사용자가 /stop  누르면 비활성화
class EnableStatus(ndb.Model):
    enabled = ndb.BooleanProperty(required=True, indexed=True, default=False,)

class LastSaved(ndb.Model):
    LastDate = ndb.IntegerProperty(required=True, indexed=True, default=False,)
    LastNum = ndb.IntegerProperty(required=True, indexed=True, default=False,)

def set_LastSaved(chat_id, LastDate, LastNum):
    u"""set_LastSaved: 최종 조회정보 저장
    chat_id:    (integer) 채팅 ID
    LastDate:   (integer) 최종 저장 날짜
    LastNum:    (integer) 최종 저장 일련번호
    """
    ls = LastSaved.get_or_insert(str(chat_id))
    ls.LastDate = LastDate
    ls.LastNum = LastNum
    ls.put()

def get_LastSaved(chat_id):
    u"""get_LastSaved: 최종 조회정보 반환
    return: (boolean)
    """
    ls = LastSaved.get_by_id(str(chat_id))
    if ls:
        LastInfo = []
        LastInfo = [ls.LastDate, ls.LastNum]
        return LastInfo
    return False


def set_enabled(chat_id, enabled):
    u"""set_enabled: 봇 활성화/비활성화 상태 변경
    chat_id:    (integer) 봇을 활성화/비활성화할 채팅 ID
    enabled:    (boolean) 지정할 활성화/비활성화 상태
    """
    es = EnableStatus.get_or_insert(str(chat_id))
    es.enabled = enabled
    es.put()

def get_enabled(chat_id):
    u"""get_enabled: 봇 활성화/비활성화 상태 반환
    return: (boolean)
    """
    es = EnableStatus.get_by_id(str(chat_id))
    if es:
        return es.enabled
    return False

def get_status(chat_id):
    u"""get_status: 사용 상태 반환
    return: (boolean)
    """
    cs = CommandStatus.get_by_id(str(chat_id))
    if cs:
        return cs.command_status
    return False

def get_enabled_chats():
    u"""get_enabled: 봇이 활성화된 채팅 리스트 반환
    return: (list of EnableStatus)
    """
    query = EnableStatus.query(EnableStatus.enabled == True)
    return query.fetch()

def set_status(chat_id, cmd_status):
    u"""set_status: 명령어 상태
    chat_id:    (integer) 채팅 ID
    cmd_status: (integer) 명령어 상태(info)
    """
    cs = CommandStatus.get_or_insert(str(chat_id))
    cs.command_status = cmd_status
    cs.put()

# 메시지 발송 관련 함수들
def send_msg(chat_id, text, reply_to=None, no_preview=True, keyboard=None):
    u"""send_msg: 메시지 발송
    chat_id:    (integer) 메시지를 보낼 채팅 ID
    text:       (string)  메시지 내용
    reply_to:   (integer) ~메시지에 대한 답장
    no_preview: (boolean) URL 자동 링크(미리보기) 끄기
    keyboard:   (list)    커스텀 키보드 지정
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
    u"""send_photo: 메시지 발송
    chat_id:    (integer) 메시지를 보낼 채팅 ID
    text:       (string)  메시지 내용
    reply_to:   (integer) ~메시지에 대한 답장
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
    u"""broadcast: 봇이 켜져 있는 모든 채팅에 메시지 발송
    text:       (string)  메시지 내용
    """
    for chat in get_enabled_chats():
        send_msg(chat.key.string_id(), text)

# 봇 명령 처리 함수들
def cmd_start(chat_id):
    u"""cmd_start: 봇을 활성화하고, 활성화 메시지 발송
    chat_id: (integer) 채팅 ID
    """
    set_enabled(chat_id, True)
    send_msg(chat_id, MSG_START, keyboard=CUSTOM_KEYBOARD)

def cmd_stop(chat_id):
    u"""cmd_stop: 봇을 비활성화하고, 비활성화 메시지 발송
    chat_id: (integer) 채팅 ID
    """
    set_enabled(chat_id, False)
    send_msg(chat_id, MSG_STOP)

def cmd_help(chat_id):
    u"""cmd_help: 봇 사용법 메시지 발송
    chat_id: (integer) 채팅 ID
    """
    send_msg(chat_id, USAGE, keyboard=CUSTOM_KEYBOARD)

def cmd_info(chat_id):
    u"""cmd_info: 종목 정보 조회
    chat_id: (integer) 채팅 ID
    """
    set_status(chat_id, ST_INFO)
    send_msg(chat_id, u'조회할 종목 이름을 입력하세요.')

def cmd_addquote(chat_id, text, result_list):
    u"""cmd_addquote: 종목 추가
    chat_id: (integer) 채팅 ID
    """
    USER_KEYBOARD = result_list
    send_msg(chat_id, u'종목을 선택해주십시오.\n선택 작업 종료는 /close 을 선택해주세요.', keyboard=USER_KEYBOARD)

def cmd_bond(chat_id):
    u"""cmd_bond: 채권 수익률 조회
    chat_id: (integer) 채팅 ID
    """
    BondRatesInfo = u'채권만기별 국고채 수익률 정보\n'
    BondRates = CollectBondRates(url_bondinfo)
    for itm in BondRates['current']:
        BondRatesInfo = BondRatesInfo + itm[0] + ' - ' + str(itm[1]) + '\n'
    send_msg(chat_id, BondRatesInfo)

def cmd_refresh(chat_id):
    u"""cmd_refresh: 공시 Refresh
    chat_id: (integer) 채팅 ID
    """
    # NDB 에 저장된 마지막 저장 날짜와 리스트 번호 읽어오기
    LastInfo = get_LastSaved(chat_id)
    s = "Prev %08d : %4d" % (LastInfo[0], LastInfo[1])
    send_msg(chat_id, s)

    # DART Info (API) 읽어오기
    now = time.gmtime(time.time() + 3600 * 9)
    DARTInfo = CallDART(DART)
    CurrDate = now.tm_year * 10000 + now.tm_mon * 100 + now.tm_mday
    s = "Curr %04d%02d%02d : %4d" % (now.tm_year, now.tm_mon, now.tm_mday, DARTInfo['total_count'])
    send_msg(chat_id, s)

    if LastInfo[0] == CurrDate:
        numoflist = DARTInfo['total_count'] - LastInfo[1]
    else:
        numoflist = DARTInfo['total_count']

    i = 0
    j = 0
    for el in DARTInfo['list']:
        if i <= numoflist:
            i = i + 1
            if el['crp_cls'] == "K" or el['crp_cls'] == "Y":
                j = j + 1
                s = "[%03d] " % (j) + " (" + MarketType[el['crp_cls']] + ") " + el['crp_nm'] + "(" + el['crp_cd'] + ") " + el['rpt_nm'] \
                  + "\n" + "http://dart.fss.or.kr/dsaf001/main.do?rcpNo=" + el['rcp_no']
                send_msg(chat_id, s)

    dateint = now.tm_year * 10000 + now.tm_mon * 100 + now.tm_mday
    countint = DARTInfo['total_count']
    set_LastSaved(chat_id, dateint, countint)

def cmd_close(chat_id):
    u"""cmd_close: 종목 조회 모드 종료
    chat_id: (integer) 채팅 ID
    """
    set_status(chat_id, ST_ECHO)
    send_msg(chat_id, u'종목 조회가 종료되었습니다.', keyboard=CUSTOM_KEYBOARD)

def cmd_broadcast(chat_id, text):
    u"""cmd_broadcast: 봇이 활성화된 모든 채팅에 메시지 방송
    chat_id: (integer) 채팅 ID
    text:    (string)  방송할 메시지
    """
    send_msg(chat_id, u'메시지를 방송합니다.', keyboard=CUSTOM_KEYBOARD)
    broadcast(text)

def cmd_echo(chat_id, text, reply_to):
    u"""cmd_echo: 사용자의 메시지를 따라서 답장
    chat_id:  (integer) 채팅 ID
    text:     (string)  사용자가 보낸 메시지 내용
    reply_to: (integer) 답장할 메시지 ID
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
    u"""사용자 메시지를 분석해 봇 명령을 처리
    chat_id: (integer) 채팅 ID
    text:    (string)  사용자가 보낸 메시지 내용
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
    if CMD_REFRESH == text:
        cmd_refresh(chat_id)
        return
    if get_status(chat_id) == ST_INFO:
        result_list = FindCodeAPI(APIKey, text)
        if not result_list[0]:
            send_msg(chat_id, u'종목명을 검색할 수 없습니다. 다시 확인 후 입력해주세요.')
        elif len(result_list[0]) == 1 and result_list[0][0][0] == text:
            send_msg(chat_id, result_list[0][0][0] + u' 종목(' + result_list[1][0][0] + u')이 존재합니다.')
            ValInfo = FindInfo(result_list[1][0][0])
            send_msg(chat_id, u'PER: ' + ValInfo[0] + u' 12M PER: ' + ValInfo[1] + u' PBR: ' + ValInfo[3] + u' 배당수익률: ' + ValInfo[4])
            send_photo(chat_id, 'http://comp.fnguide.com/SVO2/chartImg/01_06/PER_A' + result_list[1][0][0] + '_B_01_06.png')
            send_photo(chat_id, 'http://comp.fnguide.com/SVO2/chartImg/01_06/PBR_A' + result_list[1][0][0] + '_B_01_06.png')
        else:
            count = 0
            for li in result_list[0]:
                if li[0] == text:
                    send_msg(chat_id, u'동일한 종목이 발견되었습니다.')
                    send_msg(chat_id, text + u' 종목(' + result_list[1][count][0] + u')이 존재합니다.')
                    ValInfo = FindInfo(result_list[1][count][0])
                    send_msg(chat_id, u'PER: ' + ValInfo[0] + u' 12M PER: ' + ValInfo[1] + u' PBR: ' + ValInfo[3] + u' 배당수익률: ' + ValInfo[4])
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

# 웹 요청에 대한 핸들러 정의
# /me 요청시
class MeHandler(webapp2.RequestHandler):
    def get(self):
        urlfetch.set_default_fetch_deadline(60)
        self.response.write(json.dumps(json.load(urllib2.urlopen(BASE_URL + 'getMe'))))

# /updates 요청시
class GetUpdatesHandler(webapp2.RequestHandler):
    def get(self):
        urlfetch.set_default_fetch_deadline(60)
        self.response.write(json.dumps(json.load(urllib2.urlopen(BASE_URL + 'getUpdates'))))

# /set-wehook 요청시
class SetWebhookHandler(webapp2.RequestHandler):
    def get(self):
        urlfetch.set_default_fetch_deadline(60)
        url = self.request.get('url')
        if url:
            self.response.write(json.dumps(json.load(urllib2.urlopen(BASE_URL + 'setWebhook', urllib.urlencode({'url': url})))))

# /webhook 요청시 (텔레그램 봇 API)
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
        # 토요일이나 일요일인 경우엔 알림 중지
        if now.tm_wday == 5 or now.tm_wday == 6:
            return
        else:
            urlfetch.set_default_fetch_deadline(60)

            # NDB 에 "broadcast" id 로 저장된 마지막 저장 날짜와 리스트 번호 읽어오기
            LastInfo = get_LastSaved('broadcast')
            s = "Prev %08d : %4d" % (LastInfo[0], LastInfo[1])
            broadcast(s)

            # DART Info (API) 읽어오기
            DARTInfo = CallDART(DART)
            CurrDate = now.tm_year * 10000 + now.tm_mon * 100 + now.tm_mday
            s = "Curr %04d%02d%02d : %4d" % (now.tm_year, now.tm_mon, now.tm_mday, DARTInfo['total_count'])
            broadcast(s)

            if LastInfo[0] == CurrDate:
                numoflist = DARTInfo['total_count'] - LastInfo[1]
            else:
                numoflist = DARTInfo['total_count']

            i = 0
            j = 0   
            for el in DARTInfo['list']:
                if i <= numoflist:
                    i = i + 1
                    if el['crp_cls'] == "K" or el['crp_cls'] == "Y":
                        j = j + 1
                        s = "[%03d] " % (j) + " (" + MarketType[el['crp_cls']] + ") " + el['crp_nm'] + "(" + el['crp_cd'] + ") " + el['rpt_nm'] \
                        + "\t" + "http://dart.fss.or.kr/dsaf001/main.do?rcpNo=" + el['rcp_no']
                        broadcast(s)

            dateint = now.tm_year * 10000 + now.tm_mon * 100 + now.tm_mday
            countint = DARTInfo['total_count']
            for chat in get_enabled_chats():
                set_LastSaved('broadcast', dateint, countint)

        
# 구글 앱 엔진에 웹 요청 핸들러 지정
app = webapp2.WSGIApplication([
    ('/me', MeHandler),
    ('/updates', GetUpdatesHandler),
    ('/set-webhook', SetWebhookHandler),
    ('/webhook', WebhookHandler),
    ('/broadcast-news', WebhookHandler1),
], debug=True)
