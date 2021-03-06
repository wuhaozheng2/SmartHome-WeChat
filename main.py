#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import os
import web
import time
import threading
import urllib2
import hashlib
import RPi.GPIO as GPIO
from array import *
from lxml import etree
from weixin import WeiXinClient
from weixin import APIError
from weixin import AccessTokenError
from yeelink import YeeLinkClient
from yeelink import current_time


LIGHTPORT = 11
TEMPERPORT = 7
LUMPORT = 13
BODYPORT = 15
MOTORPORT = [40,38,36,35]
global flagab 
flagab = 0
global flagal 
flagal = 0
urls = (
'/weixin','WeixinInterface'
)
my_appid = 'wx2aeb8b4e9c9cf5e3'
my_secret = 'dda2b0835b67f2fa1a4babd0782b67b5'
my_yeekey = '6b9153dee4a8723ea066d90f78cb9479'
 
def _check_hash(data):
    signature=data.signature
    timestamp=data.timestamp
    nonce=data.nonce
    token="xautxaut"

    list=[token,timestamp,nonce]
    list.sort()
    sha1=hashlib.sha1()
    map(sha1.update,list)
    hashcode=sha1.hexdigest()
    
 

    if hashcode == signature:
        return True
    return False
 

def _do_event_subscribe(server, fromUser, toUser, xml):
    return server._reply_text(fromUser, toUser, u'欢迎来到智能家庭DEMO！本订阅号用于大赛测试，请点选下方菜单来测试相关功能')
    
def _do_event_unsubscribe(server, fromUser, toUser, xml):
    return server._reply_text(fromUser, toUser, u'bye!')

def _do_event_SCAN(server, fromUser, toUser, xml):
    pass

def _do_event_LOCATION(server, fromUser, toUser, xml):
    pass

def _do_event_CLICK(server, fromUser, toUser, xml):
    key = xml.find('EventKey').text
    try:
        return _weixin_click_table[key](server, fromUser, toUser, xml)
    except KeyError, e:
        print '_do_event_CLICK: %s' %e
        return server._reply_text(fromUser, toUser, u'Unknow click: '+key)

_weixin_event_table = {
    'subscribe'     :   _do_event_subscribe,
    'unsbscribe'    :   _do_event_unsubscribe,
    'SCAN'          :   _do_event_SCAN,
    'LOCATION'      :   _do_event_LOCATION,
    'CLICK'         :   _do_event_CLICK,
}


def _do_click_SNAPSHOT(server, fromUser, toUser, xml):
    data = None 
    err_msg = 'snapshot fail: '
    try:
        data = _take_snapshot('127.0.0.1', 8001, server.client)
    except Exception, e:
        err_msg += str(e)
        print '_do_click_SNAPSHOT', err_msg
        return server._reply_text(fromUser, toUser, err_msg)
    return server._reply_image(fromUser, toUser, data.media_id)

def _take_snapshot(addr, port, client):
    url = 'http://%s:%d/?action=snapshot' %(addr, port)
    req = urllib2.Request(url)
    resp = urllib2.urlopen(req, timeout = 2)
    return client.media.upload.file(type='image', pic=resp)

def _do_click_V1001_C_LEFT(server, fromUser, toUser, xml):
    GPIO.setwarnings(False) 
    GPIO.setmode(GPIO.BOARD)
    arr = [0,1,2,3];
    for p in MOTORPORT:
        GPIO.setup(p,GPIO.OUT)
    for x in range(0,50):
        for j in arr:
            time.sleep(0.01)
            for i in range(0,4):
                if i == j:            
                    GPIO.output(MOTORPORT[i],True)
                else:
                    GPIO.output(MOTORPORT[i],False)
    return server._reply_text(fromUser, toUser, u"摄像头已向左旋转45度")

def _do_click_V1001_C_RIGHT(server, fromUser, toUser, xml):
    GPIO.setwarnings(False) 
    GPIO.setmode(GPIO.BOARD)
    arr = [3,2,1,0];
    for p in MOTORPORT:
        GPIO.setup(p,GPIO.OUT)
    for x in range(0,50):
        for j in arr:
            time.sleep(0.01)
            for i in range(0,4):
                if i == j:            
                    GPIO.output(MOTORPORT[i],True)
                else:
                    GPIO.output(MOTORPORT[i],False)
    return server._reply_text(fromUser, toUser, u"摄像头已向右旋转45度")

def _do_click_V1001_TEMPERATURES(server, fromUser, toUser, xml):
    data=[]
    j=0
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BOARD)
    time.sleep(1)

    def delay(i):
        a=0
        for j in range(i):
            a+1
    GPIO.setup(TEMPERPORT,GPIO.OUT)
    GPIO.output(TEMPERPORT,GPIO.LOW)
    time.sleep(0.02)
    GPIO.output(TEMPERPORT,GPIO.HIGH)
    GPIO.setup(TEMPERPORT, GPIO.IN)

    GPIO.setup(TEMPERPORT,GPIO.IN)
    while GPIO.input(TEMPERPORT) == GPIO.LOW:
        continue

    while GPIO.input(TEMPERPORT) == GPIO.HIGH:
        continue

    while j<40:
        k=0
        while GPIO.input(TEMPERPORT) == GPIO.LOW:
            continue
    
        while GPIO.input(TEMPERPORT) == GPIO.HIGH:
            k+=1
            if k>100:break
        if k<8:
            data.append(0)
        else:
            data.append(1)
        j+=1

    humidity_bit=data[0:8]
    humidity_point_bit=data[8:16]
    temperature_bit=data[16:24]
    temperature_point_bit=data[24:32]
    check_bit=data[32:40]

    humidity=0
    humidity_point=0
    temperature=0
    temperature_point=0
    check=0

    for i in range(8):
        humidity+=humidity_bit[i]*2**(7-i)
        humidity_point+=humidity_point_bit[i]*2**(7-i)
        temperature+=temperature_bit[i]*2**(7-i)
        temperature_point+=temperature_point_bit[i]*2**(7-i)
        check+=check_bit[i]*2**(7-i)

    tmp=humidity+humidity_point+temperature+temperature_point
    if check==tmp:
        reply_temp = "室内温度: %d℃\n室内湿度: %d%%" %(temperature, humidity)
        return server._reply_text(fromUser, toUser, reply_temp)
        
    else:
        print "something is worong the humidity,humidity_point,temperature,temperature_point,check is",humidity,humidity_point,temperature,temperature_point,check
        return server._reply_text(fromUser, toUser, u"请保持数据线接触良好")
            

def _do_click_V1001_LED_ON(server, fromUser, toUser, xml):
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(LIGHTPORT,GPIO.OUT)
    GPIO.output(LIGHTPORT,GPIO.HIGH)
    return server._reply_text(fromUser, toUser, u"电灯已开")

def _do_click_V1001_LED_OFF(server, fromUser, toUser, xml):
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(LIGHTPORT,GPIO.OUT)
    GPIO.output(LIGHTPORT,GPIO.LOW)
    return server._reply_text(fromUser, toUser, u"电灯已关")
	
def _do_click_V1001_AUTOSAFE(server, fromUser, toUser, xml):
    return _do_change_ALARM(server, fromUser, toUser, xml)
    
def _do_click_V1001_AUTOLED(server, fromUser, toUser, xml):
    return _do_change_LIGHT(server, fromUser, toUser, xml)
    
def _do_click_V1001_HELP(server, fromUser, toUser, xml):
    return server._reply_text(fromUser, toUser, u'''本DEMO展示了智能家庭的运作情况 ''')


    
_weixin_click_table = {
    
    'V1001_SNAPSHOT'        :   _do_click_SNAPSHOT,
    'V1001_C_LEFT'          :   _do_click_V1001_C_LEFT,
    'V1001_C_RIGHT'         :   _do_click_V1001_C_RIGHT,
    'V1001_TEMPERATURES'    :   _do_click_V1001_TEMPERATURES,
    'V1001_LED_ON'          :   _do_click_V1001_LED_ON,
    'V1001_LED_OFF'         :   _do_click_V1001_LED_OFF,
    'V1001_HELP'            :   _do_click_V1001_HELP,
    'V1001_AUTOSAFE'        :   _do_click_V1001_AUTOSAFE,
    'V1001_AUTOLED'         :   _do_click_V1001_AUTOLED
	
}



def _do_change_LIGHT(server, fromUser, toUser, xml):
    global flagal 
    if flagal == 0:
        try:
            al = threading.Thread(target=_auto_control_light)
            al.setDaemon(True)
            al.start()
            flagal = 1
            return server._reply_text(fromUser, toUser, u"自动光控已开启")
        except:
            print "Error: unable to start thread"
            flagal = 0
            return server._reply_text(fromUser, toUser, u"自动光控没有成功开启")
    else:
        flagal = 0
        return server._reply_text(fromUser, toUser, u"自动光控已关闭")

def _do_change_ALARM(server, fromUser, toUser, xml):
    global flagab 
    if flagab == 0:
        try:
            ab = threading.Thread(target=_auto_control_body)
            ab.setDaemon(True)
            ab.start()
            flagab = 1
            return server._reply_text(fromUser, toUser, u"检测报警已开启")
        except:
            print "Error: unable to start thread"
            flagab = 0
            return server._reply_text(fromUser, toUser, u"检测报警没有成功开启")
    else:
        flagab = 0
        return server._reply_text(fromUser, toUser, u"检测报警已关闭")
        

def _auto_control_light():
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BOARD) 
    GPIO.setup(LUMPORT,GPIO.IN)
    GPIO.setup(LIGHTPORT,GPIO.OUT)

    wc = WeiXinClient(my_appid, my_secret, fc=True, path='/tmp')
    wc.request_access_token()
    rjson = wc.user.get._get(next_openid=None)
    count = rjson.count
    id_list = rjson.data.openid
    while count < rjson.total:
        rjson = wc.user.get._get(next_openid=rjson.next_openid)
        count += rjson.count
        id_list.extend(rjson.openid)

    print id_list
    while flagal == 1:

        inputValue = GPIO.input(LUMPORT)
        if(inputValue==0):
#            print("THE LED IS OFF NOW")
            GPIO.output(LIGHTPORT,GPIO.LOW)

        else:
#            print("THE LED IS ON NOW")
            GPIO.output(LIGHTPORT,GPIO.HIGH)

            
        time.sleep(1.0)
	

def _auto_control_body():
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BOARD) 
    GPIO.setup(BODYPORT,GPIO.IN)

    wc = WeiXinClient(my_appid, my_secret, fc=True, path='/tmp')
    wc.request_access_token()
    rjson = wc.user.get._get(next_openid=None)
    count = rjson.count
    id_list = rjson.data.openid
    while count < rjson.total:
        rjson = wc.user.get._get(next_openid=rjson.next_openid)
        count += rjson.count
        id_list.extend(rjson.openid)
    
    while flagab == 1:
        print "alarm is working"
        inputValue = GPIO.input(BODYPORT)
        if(inputValue!=0):
            for uid in id_list:
                content = '{"touser":"%s", "msgtype":"text", "text":{ "content":"注意！可能有人闯进了您的房间！"}}' %uid
                #print
                try:
                    print wc.message.custom.send.post(body=content)
                except APIError, e:
                    print e, uid

            url = 'http://127.0.0.1:8001/?action=snapshot'
            req = urllib2.Request(url)
            resp = urllib2.urlopen(req, timeout = 2)
            rjson = wc.media.upload.file(type='image', pic=resp)
            #print rjson
            for uid in id_list:
                content = '{"touser":"%s", "msgtype":"image", ' \
                    '"image":{ "media_id":"%s"}}' % (uid, rjson.media_id)
                try:
                    print wc.message.custom.send.post(body=content)
                except APIError, e:
                    print e, uid

        time.sleep(5.0)



   
class WeixinInterface:
 
    def __init__(self):
        self.app_root = os.path.dirname(__file__)
        self.templates_root = os.path.join(self.app_root, 'templates')
        self.render = web.template.render(self.templates_root)
        self.client = WeiXinClient(my_appid, my_secret, fc=True, path='/tmp')
        self.client.request_access_token()
        self.yee = YeeLinkClient(my_yeekey)
        
 
    def _recv_text(self, fromUser, toUser, xml):
        content = xml.find('Content').text
        reply_msg = content
        return self._reply_text(fromUser, toUser, u'我还不能理解你说的话:' + reply_msg)
        

    def _recv_event(self, fromUser, toUser, xml):
        event = xml.find('Event').text
        try:
            return _weixin_event_table[event](self, fromUser, toUser, xml)
        except KeyError, e:
            print '_recv_event: %s' %e
            return server._reply_text(fromUser, toUser, u'Unknow event: '+event)

    def _recv_image(self, fromUser, toUser, xml):
        url = xml.find('PicUrl').text
        req = urllib2.Request(url)
        try:
            resp = urllib2.urlopen(req, timeout = 2)
            print self.yee.image.upload('361437', '27360', fd = resp)
        except urllib2.HTTPError, e:
            print e
            return self._reply_text(fromUser, toUser, u'上传图片失败！')
        view = 'http://api.yeelink.net/devices/361437/'
        return self._reply_text(fromUser, toUser, u'图片已收到已上传到此地址:'+view)

    def _recv_voice(self, fromUser, toUser, xml):
        return self.render.reply_text(fromUser,toUser,int(time.time()),u"接收声音处理的功能正在开发中")

    def _recv_video(self, fromUser, toUser, xml):
        return self.render.reply_text(fromUser,toUser,int(time.time()),u"接收视频处理的功能正在开发中")

    def _recv_location(self, fromUser, toUser, xml):
        return self.render.reply_text(fromUser,toUser,int(time.time()),u"接收位置处理的功能正在开发中")

    def _recv_link(self, fromUser, toUser, xml):
        return self.render.reply_text(fromUser,toUser,int(time.time()),u"接收链接处理的功能正在开发中")

    def _reply_text(self, toUser, fromUser, msg):
        return self.render.reply_text(toUser, fromUser, int(time.time()),msg)

    def _reply_image(self, toUser, fromUser, media_id):
        return self.render.reply_image(toUser, fromUser, int(time.time()), media_id)

    def _reply_news(self, toUser, fromUser, title, descrip, picUrl, hqUrl):
        return self.render.reply_news(toUser, fromUser, int(time.time()), title, descrip, picUrl, hqUrl)


    def GET(self):

	data = web.input()
        if _check_hash(data):
            return data.echostr

        
    def POST(self):        
        str_xml = web.data()
        xml = etree.fromstring(str_xml)
        msgType=xml.find("MsgType").text
        fromUser=xml.find("FromUserName").text
        toUser=xml.find("ToUserName").text
        
        if msgType == 'text':
            return self._recv_text(fromUser, toUser, xml)
	    
        if msgType == 'event':
            return self._recv_event(fromUser, toUser, xml)
	    
        if msgType == 'image':
            return self._recv_image(fromUser, toUser, xml)
	   
        if msgType == 'voice':
            return self._recv_voice(fromUser, toUser, xml)
	    
        if msgType == 'video':
            return self._recv_video(fromUser, toUser, xml)
	    
        if msgType == 'location':
            return self._recv_location(fromUser, toUser, xml)
	    
        if msgType == 'link':
            return self._recv_link(fromUser, toUser, xml)
	    
        else:
            return self._reply_text(fromUser, toUser, u'Unknow msg:' + msgType)


application = web.application(urls, globals())

if __name__ == "__main__":
    application.run()
