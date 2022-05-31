# !/usr/bin/env python
# coding=utf-8
import requests
import time
import json
import sys
import pytz
import datetime
import re
import random
from io import StringIO

# Python版本 3.6, 该脚本仅供分享交流和学习, 不允许用于任何非法途径, 否则后果自负, 作者对此不承担任何责任
# 20210124更新: 添加WPS小程序会员群集结功能 (如需仅执行群集结功能, 请将执行方法由'index.main_handler'更改为'index.wps_massing' ); 添加并优化企业微信推送功能; 优化推送逻辑
# 请依次修改 25-32行中的需要修改的部分内容以实现推送功能
# 请依次修改 36-37, 42, 44, 46行中的需要修改的部分内容以实现签到功能
# 邀请用户签到可以额外获得会员, 每日可邀请最多10个用户, 已预置了12个小号用于接受邀请和会员群集结功能, 49-72行invite_sid信息可选删改
# 如群集结失败,请在相应49-72行处修改或相应位置前后增加invite_sid信息, 修改时注意逗号及保留双引号

# 参考以下代码解决https访问警告
# from requests.packages.urllib3.exceptions import InsecureRequestWarning,InsecurePlatformWarning
# requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
# requests.packages.urllib3.disable_warnings(InsecurePlatformWarning)

# 初始化信息
pusher = 1 # SERVER酱填1, 企业微信推送填2(推荐使用)
SCKEY = 'SCU171200T8386a5521ff72f0b970604b9f8a24a5360856697e5ba7'
corpid = '*********填写企业ID*************(保留引号)'
agentid = '*********填写应用AgentId*************(保留引号)'
corpsecret = '*********填写应用Secret*************(保留引号)'
pushusr = '@all' # 企业微信推送用户,默认'@all'为应用全体用户
img_url = 'https://s3.ax1x.com/2021/01/23/s7GOTP.png' # 微信图文消息提醒图片地址
wxpusher_type = 2 # 企业微信推送文本消息填1, 图文消息填2(推荐选择)
data = {
    "wps_checkin": [
        {
            "name": "我的签到",
            "sid": "V02SpmG7RE5Tu2BR4wG0IgNUwlQ73Kg00a01b422001fb4d004"
        }
    ]
}
# 是否显示WPS小程序邀请和会员群集结成功信息, 是填1, 否填0
success_info = 1 
# 指定WPS小程序被有效邀请人数
invite_limit = 10
# 指定有效参与群集结人数, 减少因多余人数参与集结导致的invite_sid资源不足
mass_limit = 5 
# 这12个账号被邀请,且参与WPS会员群集结,如群集结失败, 请修改以下sid, 修改时注意逗号及保留双引号
invite_sid = [
            {"name": "公共用户1",
            "sid": "V02S2UBSfNlvEprMOn70qP3jHPDqiZU00a7ef4a800341c7c3b"},
            {"name": "公共用户2",
            "sid": "V02SWIvKWYijG6Rggo4m0xvDKj1m7ew00a8e26d3002508b828"},
            {"name": "公共用户3",
            "sid": "V02Sr3nJ9IicoHWfeyQLiXgvrRpje6E00a240b890023270f97"},
            {"name": "公共用户4",
            "sid": "V02SBsNOf4sJZNFo4jOHdgHg7-2Tn1s00a338776000b669579"},
            {"name": "公共用户5",
            "sid": "V02S2oI49T-Jp0_zJKZ5U38dIUSIl8Q00aa679530026780e96"},
            {"name": "公共用户6",
            "sid": "V02ShotJqqiWyubCX0VWTlcbgcHqtSQ00a45564e002678124c"},
            {"name": "公共用户7",
            "sid": "V02SFiqdXRGnH5oAV2FmDDulZyGDL3M00a61660c0026781be1"},
            {"name": "公共用户8",
            "sid": "V02S7tldy5ltYcikCzJ8PJQDSy_ElEs00a327c3c0026782526"},
            {"name": "公共用户9",
            "sid": "V02SPoOluAnWda0dTBYTXpdetS97tyI00a16135e002684bb5c"},
            {"name": "公共用户10",
            "sid": "V02Sb8gxW2inr6IDYrdHK_ywJnayd6s00ab7472b0026849b17"},
            {"name": "公共用户11",
            "sid": "V02SwV15KQ_8n6brU98_2kLnnFUDUOw00adf3fda0026934a7f"},
            {"name": "公共用户12",
            "sid": "V02SC1mOHS0RiUBxeoA8NTliH2h2NGc00a803c35002693584d"}
]

# 初始化日志
sio = StringIO('WPS签到日志\n\n')
sio.seek(0, 2)  # 将读写位置移动到结尾
dio = StringIO('')
#dio.seek(0, 2)
s = requests.session()
tz = pytz.timezone('Asia/Shanghai')
nowtime = datetime.datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
sio.write("---"+nowtime+"---\n\n")

# 微信推送
def pushWechat(desp,nowtime):
    ssckey = SCKEY
    send_url='https://sc.ftqq.com/' + ssckey + '.send'
    if '失败' in desp :
        params = {
            'text': 'WPS签到提醒' + nowtime,
            'desp': desp
            }
    else:
        params = {
            'text': 'WPS签到提醒' + nowtime,
            'desp': desp
            }
    requests.post(send_url,params=params)

class WXPusher:
    def __init__(self, usr=None, digest=None, desp=None):
        self.base_url = 'https://qyapi.weixin.qq.com/cgi-bin/gettoken?'
        self.req_url = 'https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token='
        self.media_url = 'https://qyapi.weixin.qq.com/cgi-bin/media/upload?access_token={access_token}&type=file'
        self.corpid = corpid     # 填写企业ID
        self.corpsecret = corpsecret     # 应用Secret
        self.agentid = int(agentid)          # 填写应用ID，是个整型常数,就是应用AgentId
        if usr is None:
            usr = '@all'
        self.usr = usr
        if '失败' in desp:
            self.title = 'WPS签到失败提醒'
        else:
            self.title = 'WPS签到提醒'
        self.msg = desp
        self.digest = digest
        content = self.msg
        content = content.replace('\n          ---', '\n<code>          ---')
        content = content.replace('---↓\n', '---↓</code>\n')
        self.content = '<pre>' + content + '</pre>'  # content.replace('\n','<br/>')

    def get_access_token(self):
        urls = self.base_url + 'corpid=' + self.corpid + '&corpsecret=' + self.corpsecret
        resp = requests.get(urls).json()
        access_token = resp['access_token']
        return access_token

    # 上传临时素材,返回素材id
    def get_ShortTimeMedia(self):
        url = self.media_url
        ask_url = url.format(access_token=self.get_access_token())
        f = requests.get(img_url).content
        r = requests.post(ask_url, files={'file': f}, json=True)
        return json.loads(r.text)['media_id']

    def send_message(self):
        data = self.get_message()
        req_urls = self.req_url + self.get_access_token()
        res = requests.post(url=req_urls, data=data)
        print(res.text)

    def get_message(self):
        if wxpusher_type == 1:
            data = {
                "touser": self.usr,
                "toparty": "@all",
                "totag": "@all",
                "msgtype": "text",
                "agentid": self.agentid,
                "text": {
                    "content": self.msg
                },
                "safe": 0,
                "enable_id_trans": 0,
                "enable_duplicate_check": 0,
                "duplicate_check_interval": 1800
            }
        elif wxpusher_type == 2:

            data = {
                "touser": self.usr,
                "toparty": "@all",
                "totag": "@all",
                "msgtype": "mpnews",
                "agentid": self.agentid,
                "mpnews": {
                    "articles": [
                        {
                            "title": self.title,
                            "thumb_media_id": self.get_ShortTimeMedia(),  # 填写图片media_id
                            "author": "WPS推送助手",
                            "content_source_url": "",
                            "content": self.content,
                            "digest": self.digest
                        }
                    ]
                },
                "safe": 0,
                "enable_id_trans": 0,
                "enable_duplicate_check": 0,
                "duplicate_check_interval": 1800
            }
        data = json.dumps(data)
        return data

# WPS客户端签到，每周三天会员左右，需手动兑换


def wps_client_clockin(sid):
    sio.write("          ---wps PC客户端签到---↓\n\n")
    if len(sid) == 0:
        sio.write("签到失败: 用户sid为空, 请重新输入\n\n")
        return 0
    elif "*" in sid or sid[0] != "V":
        sio.write("签到失败: 用户sid错误, 请重新输入\n\n")
        return 0
    url = "https://vipapi.wps.cn/wps_clock/v1"
    headers = {
        "Cookie": "wps_sid=" + sid,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2486.0 Safari/537.36 Edge/13.10586"
    }
    data = {
        'double': 0
    }
    req = requests.get(url, headers=headers)
    if not ("msg" in req.text):
        # 判断wps_sid是否失效
        sio.write("wps_sid无效")
        return 0
    else:
        if(json.loads(req.text)["result"] == "ok"):
            req = requests.post(url, headers=headers, data=data)
            if json.loads(req.text)["result"] == "ok":
                sio.write('客户端签到成功，请手动去客户端兑换时长\n')
                return 1
            else:
                if json.loads(req.text)["data"] == "ClockAgent":
                    sio.write('你已经签到过了\n')
                else:
                    sio.write('未知错误:' + json.loads(req.text)["data"] + '\n')
                return 0
        else:
            if json.loads(req.text)["result"] == "UserNotLogin":
                sio.write('您貌似没有在电脑上登陆过\n')
            else:
                sio.write('未知错误:' + json.loads(req.text)["result"] + '\n')
            return 0

# WPS简历助手稻壳会员签到


def wps_miniapp_sign(sid):
    sio.write("\n\n          ---WPS简历助手小程序签到---↓\n\n")
    if len(sid) == 0:
        sio.write("签到失败: 用户sid为空, 请重新输入\n\n")
        return 0
    elif "*" in sid or sid[0] != "V":
        sio.write("签到失败: 用户sid错误, 请重新输入\n\n")
        return 0
    url = "https://vipapi.wps.cn/miniapp_sign_in/v1/user/sign_in"
    headers = {
        "sid": sid,
    }
    req = requests.post(url, headers=headers)
    if not ("msg" in req.text):
        # 判断wps_sid是否失效
        sio.write("wps_sid无效")
        return 0
    else:
        if(json.loads(req.text)["result"] == "ok"):
            sio.write('WPS简历助手小程序签到成功（签到七天给5天会员）\n')
            return 1
        else:
            sio.write('未知错误:' + json.loads(req.text)["msg"] + '\n')
            return 0


# wps网页签到
def wps_webpage_clockin(sid: str):
    sio.write("\n          ---wps网页签到---↓\n\n")
    if len(sid) == 0:
        sio.write("签到失败: 用户sid为空, 请重新输入\n\n")
        return 0
    elif "*" in sid or sid[0] != "V":
        sio.write("签到失败: 用户sid错误, 请重新输入\n\n")
        return 0

    url = "https://vip.wps.cn/sign/v2"
    headers = {
        "Cookie": "wps_sid=" + sid,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2486.0 Safari/537.36 Edge/13.10586"
    }
    data = {
        "platform": "8",
        "captcha_pos": "137.00431974731889, 36.00431593261568",
        "img_witdh": "275.164",
        "img_height": "69.184"
    }  # 带验证坐标的请求
    data0 = {"platform": "8"}  # 不带验证坐标的请求
    yz_url = "https://vip.wps.cn/checkcode/signin/captcha.png?platform=8&encode=0&img_witdh=275.164&img_height=69.184"

    req = requests.post(url=url, headers=headers, data=data)
    if not ("msg" in req.text):
        # 判断wps_sid是否失效
        sio.write("wps_sid无效")
        return 0
    else:
        sus = json.loads(req.text)["result"]  # 第一次：不带验证码的请求结果
        sio.write("免验证签到-->" + sus + '\n')  # 判断第一次请求
        if sus == "error":
            for n in range(50):
                requests.get(url=yz_url, headers=headers)
                req = requests.post(url=url, headers=headers, data=data)
                sus = json.loads(req.text)["result"]
                sio.write(str(n + 1) + "尝试验证签到-->" + sus + "\n")
                time.sleep(random.randint(0, 5)/10)
                if sus == "ok":
                    break
        sio.write("最终签到结果-->" + sus + '\n')
        return 1

# wps网页任务提示


def wps_webpage_taskreward(sid: str):
    tasklist_url = 'https://vipapi.wps.cn/task_center/task/list'
    r = s.post(tasklist_url, headers={'sid': sid})
    if len(r.history) != 0:
        if r.history[0].status_code == 302:
            sio.write("任务检查失败: 用户sid错误, 请重新输入\n\n")
            return 0
    resp = json.loads(r.text)
    # 完善账户信息任务检查
    resplist = ([resp['data']['1']['task'], resp['data']['2']['task'],
                 resp['data']['3']['task']])
    statustask = 1
    for i in range(len(resplist)):
        checkinformation(resplist[i], sid)

# 检查wps网页任务提示信息


def checkinformation(information, sid):
    for i in range(len(information)):
        if information[i]['status'] == 0:
            fetchMission_url = 'https://vipapi.wps.cn/task_center/task/receive_task'
            r = s.post(fetchMission_url, data={'id': information[i]['id']}, headers={'sid': sid})
            resp = json.loads(r.text)
            sio.write("任务{} “{}”领取情况: {}\n\n".format(information[i]['id'], information[i]['taskName'], resp['msg']))
        elif information[i]['status'] == 1:
            sio.write("任务{} “{}”未完成".format(information[i]['id'], information[i]['taskName']))
            if len(information[i]['prizes']) > 0:
                sio.write(",手动完成可获得")
                for j in range(len(information[i]['prizes'])):
                    sio.write("{}{}{} ".format(
                        information[i]['prizes'][j]['name'], information[i]['prizes'][j]['num'], information[i]['prizes'][j]['size']))
            sio.write("\n\n")
        elif information[i]['status'] == 2:
            sio.write("任务{} “{}”已完成".format(information[i]['id'], information[i]['taskName']))
            if len(information[i]['prizes']) > 0:
                sio.write(",可获得")
                for j in range(len(information[i]['prizes'])):
                    sio.write("{}{}{} ".format(
                        information[i]['prizes'][j]['name'], information[i]['prizes'][j]['num'], information[i]['prizes'][j]['size']))
            fetchReward_url = 'https://vipapi.wps.cn/task_center/task/receive_reward'
            s.post(fetchReward_url, data={'id': information[i]['id']}, headers={'sid': sid})
            sio.write("已自动为您领取奖励\n\n")
        else:
            pass

# Docer网页签到


def docer_webpage_clockin(sid: str):
    sio.write("\n\n          ---稻壳网页签到---↓\n\n")
    docer_url = 'https://zt.wps.cn/2018/docer_check_in/api/checkin_today'
    r = s.post(docer_url, headers={'sid': sid})
    if len(r.history) != 0:
        if r.history[0].status_code == 302:
            sio.write("签到失败: 用户sid错误, 请重新输入\n\n")
            return 0
    resp = json.loads(r.text)
    if resp['result'] == 'ok':
        sio.write("签到信息: {}\n\n".format(r.text))
        return 1
    elif resp['msg'] == 'recheckin':
        sio.write('签到信息: 重复签到\n\n')
        return 1

# Docer网页补签


def docer_webpage_earlyclockin(sid, checkinEarly_times, checkinrecord, max_days):
    now = datetime.datetime.now(tz)
    this_month_start = datetime.datetime(now.year, now.month, 1).date()
    checkin_Earliestdate = datetime.datetime.strptime(checkinrecord[0]['checkin_date'], '%Y-%m-%d').date()
    for i in range(checkinEarly_times):
        if checkin_Earliestdate.day > this_month_start.day:
            checkin_date = checkin_Earliestdate - datetime.timedelta(days=(i+1))
            checkin_date = datetime.datetime.strptime(str(checkin_date), '%Y-%m-%d').strftime('%Y%m%d')
            checkinEarly_url = 'https://zt.wps.cn/2018/docer_check_in/api/checkin_early'
            s.post(checkinEarly_url, data={'date': checkin_date}, headers={'sid': sid})
        else:
            if i == 0:
                sio.write('无需补签\n\n')
                return max_days
            else:
                sio.write('使用补签卡{}张\n\n'.format(i))
                checinRecord_url = 'https://zt.wps.cn/2018/docer_check_in/api/checkin_record'
                r = s.get(checinRecord_url, headers={'sid': sid})
                resp = json.loads(r.text)
                sio.write('补签后连续签到: {}天\n\n'.format(resp['data']['max_days']))
                return resp['data']['max_days']
    sio.write('使用补签卡{}张\n\n'.format(i))
    checinRecord_url = 'https://zt.wps.cn/2018/docer_check_in/api/checkin_record'
    r = s.get(checinRecord_url, headers={'sid': sid})
    resp = json.loads(r.text)
    sio.write('补签后连续签到: {}天\n\n'.format(resp['data']['max_days']))
    return resp['data']['max_days']

# Docer网页领取礼物


def docer_webpage_giftReceive(sid, max_days):
    userinfo_url = 'https://vip.wps.cn/userinfo'
    r = s.get(userinfo_url, headers={'sid': sid})
    resp = json.loads(r.text)
    memberid = [0]
    if len(resp['data']['vip']['enabled']) > 0:
        for i in range(len(resp['data']['vip']['enabled'])):
            memberid.append(resp['data']['vip']['enabled'][i]['memberid'])
    rewardRecord_url = 'https://zt.wps.cn/2018/docer_check_in/api/reward_record'
    rewardReceive_url = 'https://zt.wps.cn/2018/docer_check_in/api/receive_reward'
    r = s.get(rewardRecord_url, headers={'sid': sid})
    resp = json.loads(r.text)
    rewardRecord_list = resp['data']
    if len(rewardRecord_list) > 0:
        for i in rewardRecord_list:
            if i['reward_type'] == 'vip' or i['reward_type'] == 'code':
                if int(i['limit_days']) <= max_days and int(i['limit_vip']) in memberid and i['status'] == 'unreceived':
                    r1 = s.post(rewardReceive_url, data={'reward_id': i['id'], 'receive_from': 'pc_client'}, headers={'sid': sid})
                    sio.write('领取礼物: {} '.format(i['reward_name']))
                    if 'reward_info' in r1.text:
                        resp1 = json.loads(r1.text)
                        sio.write('礼物信息: {}'.format(resp1['data']['reward_info']))
                    else:
                        sio.write('领取信息: {}'.format(r1.text))
                    sio.write('\n\n')
                elif i['status'] == 'received':
                    sio.write('已领取礼物: {} '.format(i['reward_name']))
                    if 'reward_info' in i:
                        sio.write('礼物信息: {}'.format(i['reward_info']))
                    sio.write('\n\n')

# wps小程序签到


def wps_miniprogram_clockin(sid: str):
    sio.write("\n\n          ---wps小程序签到---↓\n\n")
    if len(sid) == 0:
        sio.write("签到失败: 用户sid为空, 请重新输入\n\n")
        return 0
    elif "*" in sid or sid[0] != "V":
        sio.write("签到失败: 用户sid错误, 请重新输入\n\n")
        return 0
    # 打卡签到
    clockin_url = 'http://zt.wps.cn/2018/clock_in/api/clock_in'
    r = s.get(clockin_url, headers={'sid': sid})
    if len(r.history) != 0:
        if r.history[0].status_code == 302:
            sio.write("签到失败: 用户sid错误, 请重新输入\n\n")
            return 0
    resp = json.loads(r.text)
    # 判断是否已打卡
    if resp['msg'] == '已打卡':
        sio.write("签到信息: {}\n\n".format(r.text))
        return 1
    # 判断是否绑定手机
    elif resp['msg'] == '未绑定手机':
        sio.write('签到失败: 未绑定手机, 请绑定手机后重新运行签到\n\n')
        return 0
    # 判断是否重新报名
    elif resp['msg'] == '前一天未报名':
        sio.write('前一天未报名\n\n')
        signup_url = 'http://zt.wps.cn/2018/clock_in/api/sign_up'
        r = s.get(signup_url, headers={'sid': sid})
        resp = json.loads(r.text)
        if resp['result'] == 'ok':
            sio.write('报名信息: 已自动报名, 报名后第二天签到\n\n')
            return 1
        else:
            sio.write('报名失败: 请手动报名, 报名后第二天签到\n\n')
            return 0
    # 打卡签到需要参加活动
    elif resp['msg'] == '答题未通过':
        getquestion_url = 'http://zt.wps.cn/2018/clock_in/api/get_question?member=wps'
        r = s.get(getquestion_url, headers={'sid': sid})
        answer_set = {
            'WPS会员全文检索',
            '100G',
            'WPS会员数据恢复',
            'WPS会员PDF转doc',
            'WPS会员PDF转图片',
            'WPS图片转PDF插件',
            '金山PDF转WORD',
            'WPS会员拍照转文字',
            '使用WPS会员修复',
            'WPS全文检索功能',
            '有，且无限次',
            '文档修复'
        }
        resp = json.loads(r.text)
        # sio.write(resp['data']['multi_select'])
        # 只做单选题 multi_select==1表示多选题
        while resp['data']['multi_select'] == 1:
            r = s.get(getquestion_url, headers={'sid': sid})
            resp = json.loads(r.text)
            # sio.write('选择题类型: {}'.format(resp['data']['multi_select']))
        answer_id = 3
        for i in range(4):
            opt = resp['data']['options'][i]
            if opt in answer_set:
                answer_id = i+1
                break
        sio.write("选项: {}\n\n".format(resp['data']['options']))
        sio.write("选择答案: {}\n\n".format(answer_id))
        # 提交答案
        answer_url = 'http://zt.wps.cn/2018/clock_in/api/answer?member=wps'
        r = s.post(answer_url, headers={'sid': sid}, data={'answer': answer_id})
        resp = json.loads(r.text)
        # 答案错误
        if resp['msg'] == 'wrong answer':
            sio.write("答案不对, 挨个尝试\n\n")
            for i in range(4):
                r = s.post(answer_url, headers={'sid': sid}, data={'answer': i+1})
                resp = json.loads(r.text)
                sio.write(i+1)
                if resp['result'] == 'ok':
                    sio.write(r.text)
                    break
        # 打卡签到
        clockin_url = 'http://zt.wps.cn/2018/clock_in/api/clock_in?member=wps'
        r = s.get(clockin_url, headers={'sid': sid})
        sio.write("签到信息: {}\n\n".format(r.text))
        return 1
    elif resp['msg'] == 'ParamData Empty':
        sio.write('签到失败信息: {}\n\n'.format(r.text))
        signup_url = 'http://zt.wps.cn/2018/clock_in/api/sign_up'
        r = s.get(signup_url, headers={'sid': sid})
        sio.write('签到接口失效, 请手动打卡\n\n')
        return 1
    elif resp['msg'] == '不在打卡时间内':
        sio.write('签到失败: 不在打卡时间内\n\n')
        signup_url = 'http://zt.wps.cn/2018/clock_in/api/sign_up'
        r = s.get(signup_url, headers={'sid': sid})
        resp = json.loads(r.text)
        if resp['result'] == 'ok':
            sio.write('已自动报名, 报名后请设置在规定时间内签到\n\n')
            return 1
        else:
            sio.write('报名失败: 请手动报名, 报名后第二天签到\n\n')
            return 0
    # 其他错误
    elif resp['result'] == 'error':
        sio.write('签到失败信息: {}\n\n'.format(r.text))
        signup_url = 'http://zt.wps.cn/2018/clock_in/api/sign_up'
        r = s.get(signup_url, headers={'sid': sid})
        resp = json.loads(r.text)
        if resp['result'] == 'ok':
            sio.write('已自动报名, 报名后请设置在规定时间内签到\n\n')
            return 1
        else:
            sio.write('报名失败: 请手动报名, 报名后第二天签到\n\n')
            return 0

# wps小程序接受邀请


def wps_miniprogram_invite(sid: list, invite_userid: int) -> None:
    invite_url = 'http://zt.wps.cn/2018/clock_in/api/invite'
    k = 0
    for index in range(len(sid)):
        if k < invite_limit:
            headers = {
                'sid': sid[index]['sid'],
                'alipayMiniMark': 'T6Or5GIV5k2cBGWJgNuzVdkKB78d3U3Mq3wlWqOKf9UIfwg0bUdCWtnNrWFwXydtEo820U7tQ1Gx3xB7Mqdkzb8njgl1/FQC2u7M0HGrKhc='
            }
            time.sleep(2 + random.random())
            r = s.post(
                invite_url, 
                headers=headers, 
                data={
                    'invite_userid': invite_userid,
                    'client': 'alipay',
                    'client_code': '040ce6c23213494c8de9653e0074YX30'
            })
            if r.status_code == 200:
                try:
                    resp = json.loads(r.text)
                    if resp['result'] == 'ok':
                        if success_info == 1:
                            sio.write("邀请对象: {}, Result: {}\n\n".format(sid[index]['name'], resp['msg']))
                        k += 1
                    else:
                        sio.write("邀请对象: {}, Result: {}\n\n".format(sid[index]['name'], resp['msg']))
                except:
                    resp = r.text[:25]
                    sio.write("邀请对象: {}, Result: ID已失效\n\n".format(sid[index]['name']))
            else:
                sio.write("邀请对象: {}, 状态码: {},\n\n 请求信息{}\n\n".format(sid[index]['name'], r.status_code, r.text[:25]))
        else:
            break
    return k


# wps会员群集结开团
def wps_massing_group(sid):
    massing_url = 'https://zt.wps.cn/2020/massing/api'
    r = s.post(massing_url, headers={'sid': sid})
    resp = json.loads(r.text)
    code = ''
    if resp['result'] == "error" and resp['msg'] == "up to limit":
        sio.write("今日集结次数已达到上限,请明日再来\n\n")
    elif resp['data'] and resp['data']['code']:
        code = resp['data']['code']
        sio.write("开团成功, code: " + code + '\n\n')
    else:
        r1 = s.get(massing_url, headers={'sid': sid})
        resp1 = json.loads(r1.text)
        if 'latest_record' in resp1['data']:
            code = resp1['data']['latest_record']['code']
            sio.write("开团成功, code: " + code + '\n\n')
        else:
            sio.write(resp['msg'] + '\n\n')
    return code

# wps会员群集结参团


def wps_massing_join(code, sid):
    massing_url = 'https://zt.wps.cn/2020/massing/api'
    k = 1
    for index in range(len(sid)):
        if k < mass_limit:
            headers = {
                'sid': sid[index]['sid']
            }
            r = s.post(massing_url, data={'code': code}, headers=headers)
            if r.status_code == 200:
                try:
                    resp = json.loads(r.text)
                    if resp['result'] == 'error':
                        sio.write("参团对象: {}, Result: {}\n\n".format(sid[index]['name'], resp['msg']))
                    elif resp['result'] == 'ok':
                        if success_info == 1:
                            sio.write("参团对象: {}, Result: {}\n\n".format(sid[index]['name'], resp['result']))
                        k += 1
                except:
                    resp = r.text[:25]
                    sio.write("参团对象: {}, Result: ID已失效\n\n".format(sid[index]['name']))
            else:
                sio.write("参团对象ID={}, 状态码: {},\n\n  请求信息: {}\n\n".format(sid[index]['name'], r.status_code, r.text[:25]))
        else:
            break
    return k

# wps会员群集结信息


def wps_massing_info(sid, c):
    massing_url = 'https://zt.wps.cn/2020/massing/api'
    r = s.get(massing_url, headers={'sid': sid})
    resp = json.loads(r.text)
    time = 0
    if resp['result'] == "ok" and resp['data'] and resp['data']['reward']:
        reward = resp['data']['reward']
        time = reward['time']
        if time != 0 and c == 1:
            sio.write('今日集结' + str(reward['time']) + '次,共集结' + str(reward['total_time']) + '次;\n\n获得' + str(reward['member']) + '天会员,' + str(reward['drive']) + 'M空间\n\n')
        if 'latest_record' in resp['data'] and c == 2:
            create_time = resp['data']['latest_record']['create_time']
            ts2str_url = 'https://api.a76yyyy.cn/time?function=timestamp2str'
            r1 = s.post(ts2str_url, data={'params1': str(int(create_time)+1800)})
            resp1 = json.loads(r1.text)
            sio.write("下次集结开团时间:" + resp1['data'] + '\n\n')
    else:
        sio.write("sid已失效,请重新获取sid\n\n")
    return time

# 主函数


def main():
    # sio.write("\n            ===模拟WPS签到===")
    sid = data['wps_checkin']

    for item in sid:
        sio.write("---为{}签到---↓\n\n".format(item['name']))
        dio.write("{}签到摘要↓\n\n".format(item['name']))

        b0 = wps_webpage_clockin(item['sid'])
        if b0 == 1:
            # 获取当前网页签到信息
            dio.write("wps网页签到成功\n\n")
            taskcenter_url = 'https://vipapi.wps.cn/task_center/task/summary'
            r = s.post(taskcenter_url, headers={'sid': item['sid']})
            resp = json.loads(r.text)
            if resp['data']['taskNum'] < 12:
                wps_webpage_taskreward(item['sid'])
            r = s.post(taskcenter_url, headers={'sid': item['sid']})
            resp = json.loads(r.text)
            sio.write('已领取积分: {}\n\n'.format(resp['data']['wpsIntegral']))
            sio.write('已领取会员: {}天\n\n'.format(resp['data']['member']))
            sio.write('已完成任务: {}项\n\n'.format(resp['data']['taskNum']))
        else:
            dio.write("wps网页签到失败\n\n")
            desp = sio.getvalue()
            digest = dio.getvalue()
            if digest[-2:] == '\n\n':
                digest = digest[0:-2]

        b0 = wps_client_clockin(item['sid'])
        if b0 == 1:
            # 获取当前网页签到信息
            dio.write("wps PC客户端签到成功\n\n")
        else:
            dio.write("wps PC客户端签到失败\n\n")

        # WPS简历助手小程序
        b0 = wps_miniapp_sign(item['sid'])
        if b0 == 1:
            # 获取当前网页签到信息
            dio.write("WPS简历助手小程序签到成功\n\n")
        else:
            dio.write("WPS简历助手小程序签到失败\n\n")

        b1 = docer_webpage_clockin(item['sid'])
        if b1 == 1:
            checinRecord_url = 'https://zt.wps.cn/2018/docer_check_in/api/checkin_record'
            r = s.get(checinRecord_url, headers={'sid': item['sid']})
            resp = json.loads(r.text)
            sio.write('本期连续签到: {}天\n\n'.format(resp['data']['max_days']))
            checkinEarlytimes_url = 'https://zt.wps.cn/2018/docer_check_in/api/checkin_early_times'
            r1 = s.get(checkinEarlytimes_url, headers={'sid': item['sid']})
            resp1 = json.loads(r1.text)
            sio.write('拥有补签卡: {}张\n\n'.format(resp1['data']))
            max_days = resp['data']['max_days']
            if resp1['data'] > 0 and len(resp['data']['records']) > 0:
                max_days = docer_webpage_earlyclockin(item['sid'], resp1['data'], resp['data']['records'], max_days)
            if len(resp['data']['records']) > 0:
                docer_webpage_giftReceive(item['sid'], max_days)
            dio.write("稻壳网页签到成功\n\n")
        else:
            dio.write("稻壳网页签到失败\n\n")

        b2 = wps_miniprogram_clockin(item['sid'])
        if b2 == 1:
            # 获取小程序当前会员奖励信息
            member_url = 'https://zt.wps.cn/2018/clock_in/api/get_data?member=wps'
            r = s.get(member_url, headers={'sid': item['sid']})
            # 累计在小程序打卡中获得会员天数
            total_add_day = re.search('"total_add_day":(\d+)', r.text).group(1)
            sio.write('小程序打卡中累计获得会员: {}天\n\n'.format(total_add_day))
            dio.write("小程序打卡成功\n\n")
        else:
            dio.write("小程序打卡失败\n\n")

        # wps签到邀请
        sio.write("\n\n          ---wps小程序邀请---↓\n\n")
        sio.write("为{}邀请\n\n".format(item['name']))
        userinfo_url = 'https://vip.wps.cn/userinfo'
        r = s.get(userinfo_url, headers={'sid': item['sid']})
        resp = json.loads(r.text)
        if type(resp['data']['userid']) == int:
            k = wps_miniprogram_invite(invite_sid, resp['data']['userid'])
            sio.write('邀请完成，成功邀请{}人\n\n'.format(k))
            dio.write('小程序成功邀请{}人\n\n'.format(k))
        else:
            sio.write("邀请失败: 用户ID错误, 请检查用户sid\n\n")
            dio.write("小程序邀请失败\n\n")

        # 获取当前用户信息
        sio.write('\n\n          ---当前用户信息---↓\n\n')
        summary_url = 'https://vip.wps.cn/2019/user/summary'
        r = s.post(summary_url, headers={'sid': item['sid']})
        resp = json.loads(r.text)
        sio.write('会员积分:{}\n\n"稻米数量":{}\n\n'.format(resp['data']['integral'], resp['data']['wealth']))
        userinfo_url = 'https://vip.wps.cn/userinfo'
        r = s.get(userinfo_url, headers={'sid': item['sid']})
        resp = json.loads(r.text)
        if len(resp['data']['vip']['enabled']) > 0:
            sio.write('会员信息:\n\n')
            for i in range(len(resp['data']['vip']['enabled'])):
                sio.write('"类型":{}, "过期时间":{}\n\n'.format(resp['data']['vip']['enabled'][i]['name'], datetime.datetime.fromtimestamp(
                    resp['data']['vip']['enabled'][i]['expire_time']).strftime("%Y--%m--%d %H:%M:%S")))
                dio.write('"类型":{}, "过期时间":{}\n\n'.format(resp['data']['vip']['enabled'][i]['name'],
                                                          datetime.datetime.fromtimestamp(resp['data']['vip']['enabled'][i]['expire_time']).strftime("%Y/%m/%d")))

    desp = sio.getvalue()
    digest = dio.getvalue()
    if digest[-2:] == '\n\n':
        digest = digest[0:-2]
    if pusher == 1:
        pushWechat(desp, nowtime)
    elif pusher == 2:
        desp = desp.replace('\n\n', '\n')
        digest = digest.replace('\n\n', '\n')
        push = WXPusher(pushusr, digest, desp)
        push.send_message()
    print(desp)
    return desp


def main_handler(event, context):
    return main()


if __name__ == '__main__':
    main()
