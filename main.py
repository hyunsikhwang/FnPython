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

# 종목명 찾기 API 관련 라이브러리 로드
from urllib import urlencode, quote_plus
from urllib2 import Request, urlopen

from bs4 import BeautifulSoup

# 봇 토큰, 봇 API 주소
TOKEN = '303352490:AAGLVFQbnFyviIelWVBynx98JGqd_GoVRzQ'
BASE_URL = 'https://api.telegram.org/bot' + TOKEN + '/'

# 종목명 찾기 API Key
APIKey = "CJL9jdtz5gsb4z4PpjFpCDjdz/UIk8cFAGgHbJvgLEJxPWLZaTx3wIcBNPkGu/KIKsI1zAy1XtfQJLG0VV0vVg=="

# 봇이 응답할 명령어
CMD_START     = '/start'
CMD_STOP      = '/stop'
CMD_HELP      = '/help'
CMD_BROADCAST = '/broadcast'
CMD_INFO      = '/info'
CMD_CLOSE     = '/close'

# 봇 사용법 & 메시지
USAGE = u"""[사용법] 아래 명령어를 메시지로 보내거나 버튼을 누르시면 됩니다.
/start - (로봇 활성화)
/stop  - (로봇 비활성화)
/help  - (이 도움말 보여주기)
/info  - (정보 조회)
"""
MSG_START = u'봇을 시작합니다.'
MSG_STOP  = u'봇을 정지합니다.'

# 커스텀 키보드
CUSTOM_KEYBOARD = [
        [CMD_START],
        [CMD_STOP],
        [CMD_HELP],
        [CMD_INFO],
        ]

USER_KEYBOARD = []

ST_ECHO, ST_INFO = range(2)

class CommandStatus(ndb.Model):
    command_status = ndb.IntegerProperty(required=True, indexed=True, default=False,)

def FindCodeAPI(APIKey, stock_name):
    url = 'http://api.seibro.or.kr/openapi/service/StockSvc/getStkIsinByNm'
    queryParams = '?' + urlencode({ quote_plus('ServiceKey') : APIKey, quote_plus('secnNm') : stock_name.encode('utf-8'), quote_plus('pageNo') : '1', quote_plus(u'numOfRows') : '200' })

    request = Request(url + queryParams)
    request.get_method = lambda: 'GET'
    page = urlopen(request).read()

    soup = BeautifulSoup(page, 'html.parser', from_encoding='utf-8')

    i = 0
    retlist = []
    retlist1 = []
    retlist2 = []

    for li in soup.findAll('item'):
        i = i + 1
        retlist1.append([li.korsecnnm.string])
        if li.shotnisin.string == None:
            li.shotnisin.string = ''
        retlist2.append([li.shotnisin.string])

    retlist = [retlist1, retlist2]
    return retlist

def MergeList(reflist):
    ml = ""
    for il in reflist:
        ml += il[0] + "\n"

    return ml

# 채팅별 로봇 활성화 상태
# 구글 앱 엔진의 Datastore(NDB)에 상태를 저장하고 읽음
# 사용자가 /start 누르면 활성화
# 사용자가 /stop  누르면 비활성화
class EnableStatus(ndb.Model):
    enabled = ndb.BooleanProperty(required=True, indexed=True, default=False,)

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
    if get_status(chat_id) == ST_INFO:
        result_list = FindCodeAPI(APIKey, text)
        if not result_list[0]:
            send_msg(chat_id, u'종목명을 검색할 수 없습니다. 다시 확인 후 입력해주세요.')
        elif len(result_list[0]) == 1 and result_list[0][0][0] == text:
            send_msg(chat_id, result_list[0][0][0] + u' 종목(' + result_list[1][0][0] + u')이 존재합니다.')
        else:
            count = 0
            for li in result_list[0]:
                if li[0] == text:
                    send_msg(chat_id, u'동일한 종목이 발견되었습니다.')
                    send_msg(chat_id, text + u' 종목(' + result_list[1][count][0] + u')이 존재합니다.')
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

# 구글 앱 엔진에 웹 요청 핸들러 지정
app = webapp2.WSGIApplication([
    ('/me', MeHandler),
    ('/updates', GetUpdatesHandler),
    ('/set-webhook', SetWebhookHandler),
    ('/webhook', WebhookHandler),
], debug=True)
