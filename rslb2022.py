#!/usr/bin/python
# -*- coding: UTF-8 -*-

import requests
import json
import base64
import hashlib
import time
import random
from PIL import Image
import threading
import tk #导入同目录题库文件

# 验证码默认保存在D盘，请确保存在D盘符
#path = 'd:/kaptcha' windows
path ='/tmp'

# 去除多余的乱码
def get_new(str):
    return str.replace("2526gt;", "").replace("2526lt;", "")\
        .replace("&amp;", "").replace("/span", "").replace("span", "")\
        .replace("&nbsp;", "").replace("/p", "").replace("p", "").replace(" ", "")\
        .replace("\n", "").replace("\r", "").replace("\t", "").replace("&lt;", "").replace("&gt;", "")\
        .replace("(", "（").replace(")", "）").replace("br/", "")


# 获取百度token
# client_id、client_secret需要自己在百度申请!!!!!!!!!!
def get_token():
    client_id = 'saWL6jnl3z4YkeqogRgkbE3G'
    client_secret = 'p1vzjrYlpNfYKi3frdZDPEGy2YADIsg5'
    base_url = 'https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id='
    host = base_url + client_id + '&client_secret=' + client_secret
    response = requests.get(host)
    if response:
        return response.json()['access_token']


# 百度OCR识别验证码
def get_code(file, token):
    request_url = "https://aip.baidubce.com/rest/2.0/ocr/v1/general_basic"
    f = open(file, 'rb')
    img = base64.b64encode(f.read())
    params = {"image": img, "language_type": "ENG"}
    access_token = token
    request_url = request_url + "?access_token=" + access_token
    headers = {'content-type': 'application/x-www-form-urlencoded'}
    response = requests.post(request_url, data=params, headers=headers)
    if response:
        try:
            return response.json()['words_result'][0]['words']
        except (IndexError, KeyError):
            return '0000'


# 获取验证码
def get_picture(session, name):
    api_picture = 'https://bw.rsbsyzx.cn/api/kaptcha'
    request = session.get(api_picture)
    picture = open(path + '-' + name + '.jpg', 'wb')
    picture.write(request.content)
    picture.close()
    img = Image.open(path + '-' + name + ".jpg")
    width = img.size[0]
    height = img.size[1]
    for i in range(0, width):
        for j in range(0, height):
            data = (img.getpixel((i, j)))
            if data[0] <= 50 and data[1] <= 50 and data[2] <= 50:
                img.putpixel((i, j), (255, 255, 255, 255))
            if data[0] >= 50 and data[1] >= 50 and data[2] >= 180:
                img.putpixel((i, j), (255, 255, 255, 255))
    img = img.convert("RGB")  # 把图片强制转成RGB
    img.save(path + '-' + name + "1.jpg")  # 保存修改像素点后的图片


# 登录
def login(session, mobile, password, verifyCode):
    m = hashlib.md5()
    m.update(password.encode(encoding='utf-8'))
    result = m.hexdigest()
    api_login = 'https://bw.rsbsyzx.cn/api/candidate/login'
    headers = {'User-Agent': 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'}
    data_login = {
        'mobile': mobile,
        'password': result,
        'verifyCode': verifyCode}
    request = session.post(api_login, headers=headers, data=data_login)
    return json.loads(request.content.decode('UTF-8'))['message']


# 自动登录：利用百度OCR识别
# 如登录失败，会重复登录，直至成功为止
def goLogin_auto(mobile, password, name):
    session = requests.session()
    get_picture(session, name)
    token = get_token()
    picture = get_code(path + '-' + name + "1.jpg", token)
    while login(session, mobile, password, picture) != '成功':
        get_picture(session, name)
        picture = get_code(path + '-' + name + "1.jpg", token)
        print('-', end='*')
    print(name + '-->登录成功')
    return session


chapterName = {'6238': '就业创业', '6239': '劳动关系', '6240': '党建理论', '6242': '人事人才', '6243': '综合服务', '6244': '社会保险'}
typeName = {'001001': '单选题', '001002': '多选题', '001003': '判断题'}


# 完成日日学：5道题目一组。如果题目答完，自动重置（不含填空题、简答题、解析题），每5题之间间隔8-15秒
def finish_day(session, chapterId, questionType, name):
    t = random.randint(8, 15)
    time.sleep(t)
    qs = session.get('https://bw.rsbsyzx.cn/api/questionPractice/listQuestions',
                     params={'chapterId': chapterId, 'questionType': questionType, 'number': '5'})
    id_len = len(json.loads(qs.content.decode('UTF-8'))['data'])
    if id_len == 5:
        id0 = json.loads(qs.content.decode('UTF-8'))['data'][0]['id']
        answer0 = json.loads(qs.content.decode('UTF-8'))['data'][0]['answer']
        id1 = json.loads(qs.content.decode('UTF-8'))['data'][1]['id']
        answer1 = json.loads(qs.content.decode('UTF-8'))['data'][1]['answer']
        id2 = json.loads(qs.content.decode('UTF-8'))['data'][2]['id']
        answer2 = json.loads(qs.content.decode('UTF-8'))['data'][2]['answer']
        id3 = json.loads(qs.content.decode('UTF-8'))['data'][3]['id']
        answer3 = json.loads(qs.content.decode('UTF-8'))['data'][3]['answer']
        id4 = json.loads(qs.content.decode('UTF-8'))['data'][4]['id']
        answer4 = json.loads(qs.content.decode('UTF-8'))['data'][4]['answer']
        answerData0 = '[{"id":"' + id0 + '","userAnswer":"' + answer0 + '","signed":1},'
        answerData1 = '{"id":"' + id1 + '","userAnswer":"' + answer1 + '","signed":1},'
        answerData2 = '{"id":"' + id2 + '","userAnswer":"' + answer2 + '","signed":1},'
        answerData3 = '{"id":"' + id3 + '","userAnswer":"' + answer3 + '","signed":1},'
        answerData4 = '{"id":"' + id4 + '","userAnswer":"' + answer4 + '","signed":1}]'
        answerData = answerData0 + answerData1 + answerData2 + answerData3 + answerData4
    elif id_len == 4:
        id0 = json.loads(qs.content.decode('UTF-8'))['data'][0]['id']
        answer0 = json.loads(qs.content.decode('UTF-8'))['data'][0]['answer']
        id1 = json.loads(qs.content.decode('UTF-8'))['data'][1]['id']
        answer1 = json.loads(qs.content.decode('UTF-8'))['data'][1]['answer']
        id2 = json.loads(qs.content.decode('UTF-8'))['data'][2]['id']
        answer2 = json.loads(qs.content.decode('UTF-8'))['data'][2]['answer']
        id3 = json.loads(qs.content.decode('UTF-8'))['data'][3]['id']
        answer3 = json.loads(qs.content.decode('UTF-8'))['data'][3]['answer']
        answerData0 = '[{"id":"' + id0 + '","userAnswer":"' + answer0 + '","signed":1},'
        answerData1 = '{"id":"' + id1 + '","userAnswer":"' + answer1 + '","signed":1},'
        answerData2 = '{"id":"' + id2 + '","userAnswer":"' + answer2 + '","signed":1},'
        answerData3 = '{"id":"' + id3 + '","userAnswer":"' + answer3 + '","signed":1}]'
        answerData = answerData0 + answerData1 + answerData2 + answerData3
    elif id_len == 3:
        id0 = json.loads(qs.content.decode('UTF-8'))['data'][0]['id']
        answer0 = json.loads(qs.content.decode('UTF-8'))['data'][0]['answer']
        id1 = json.loads(qs.content.decode('UTF-8'))['data'][1]['id']
        answer1 = json.loads(qs.content.decode('UTF-8'))['data'][1]['answer']
        id2 = json.loads(qs.content.decode('UTF-8'))['data'][2]['id']
        answer2 = json.loads(qs.content.decode('UTF-8'))['data'][2]['answer']
        answerData0 = '[{"id":"' + id0 + '","userAnswer":"' + answer0 + '","signed":1},'
        answerData1 = '{"id":"' + id1 + '","userAnswer":"' + answer1 + '","signed":1},'
        answerData2 = '{"id":"' + id2 + '","userAnswer":"' + answer2 + '","signed":1}]'
        answerData = answerData0 + answerData1 + answerData2
    elif id_len == 2:
        id0 = json.loads(qs.content.decode('UTF-8'))['data'][0]['id']
        answer0 = json.loads(qs.content.decode('UTF-8'))['data'][0]['answer']
        id1 = json.loads(qs.content.decode('UTF-8'))['data'][1]['id']
        answer1 = json.loads(qs.content.decode('UTF-8'))['data'][1]['answer']
        answerData0 = '[{"id":"' + id0 + '","userAnswer":"' + answer0 + '","signed":1},'
        answerData1 = '{"id":"' + id1 + '","userAnswer":"' + answer1 + '","signed":1}]'
        answerData = answerData0 + answerData1
    elif id_len == 1:
        id0 = json.loads(qs.content.decode('UTF-8'))['data'][0]['id']
        answer0 = json.loads(qs.content.decode('UTF-8'))['data'][0]['answer']
        answerData = '[{"id":"' + id0 + '","userAnswer":"' + answer0 + '","signed":1}]'
    else:
        pass
    if id_len != 0:
        api_get = 'https://bw.rsbsyzx.cn/api/questionPractice/saveAnswer'
        data = {'chapterId': chapterId,
                'questionType': questionType,
                'answerData': answerData}
        request = session.post(api_get, data=data)
        if json.loads(request.content.decode('UTF-8'))['code'] != 'SUCCESS':
            print(name + '-->日日学提交失败！')
    if id_len != 5:
        session.get('https://bw.rsbsyzx.cn/api/questionPractice/refreshQuestion',
                                params={'chapterId': chapterId, 'questionType': questionType})
        print(name + '-->已完成日日学-->' + chapterName[chapterId] + '-->' + typeName[questionType] + '-->' + str(id_len) + '题，并重置学习状态')
    else:
        print(name + '-->已完成日日学-->' + chapterName[chapterId] + '-->' + typeName[questionType] + '-->5题')


# 完成周周练
def finish_week(session, name):
    request_id = session.get('https://bw.rsbsyzx.cn/api/examination/listExamination',
                             params={'pageSize': '1', 'curPage': '1', 'examType': '009002'})
    week_exam_id = json.loads(request_id.content.decode('UTF-8'))['data']['rows'][0]['id']
    request_reset = session.get('https://bw.rsbsyzx.cn/api/examination/checkExamination',
                                params={'id': week_exam_id})
    if json.loads(request_reset.content.decode('UTF-8'))['code'] != 'SUCCESS':
        print(name + '-->周周练重置失败！')
    request_get = session.get('https://bw.rsbsyzx.cn/api/examination/enterExamination',
                              params={'id': week_exam_id})
    jstr = json.loads(request_get.content.decode('UTF-8'))['data']
    ids = []
    answers = []
    try:
        recordId = jstr['recordId']
        danxuans = jstr['questionTypeSummaries'][0]['questions']
        duoxuans = jstr['questionTypeSummaries'][1]['questions']
        panduans = jstr['questionTypeSummaries'][2]['questions']
        tiankons = jstr['questionTypeSummaries'][3]['questions']

        for q in danxuans:
            for question in questions:
                if q['id'] == question['id']:
                    if get_new(q['choices'][0]['content']) == question[question['answer']]:
                        ids.append(question['id'])
                        answers.append('A')
                        break
                    if get_new(q['choices'][1]['content']) == question[question['answer']]:
                        ids.append(question['id'])
                        answers.append('B')
                        break
                    if get_new(q['choices'][2]['content']) == question[question['answer']]:
                        ids.append(question['id'])
                        answers.append('C')
                        break
                    if get_new(q['choices'][3]['content']) == question[question['answer']]:
                        ids.append(question['id'])
                        answers.append('D')
                        break
        for q in duoxuans:
            for question in questions:
                if q['id'] == question['id']:
                    answers_list = []
                    answers_list2 = []
                    if 'A' in question['answer']:
                        answers_list.append(question['A'])
                    if 'B' in question['answer']:
                        answers_list.append(question['B'])
                    if 'C' in question['answer']:
                        answers_list.append(question['C'])
                    if 'D' in question['answer']:
                        answers_list.append(question['D'])
                    if 'E' in question['answer']:
                        answers_list.append(question['E'])
                    if get_new(q['choices'][0]['content']) in answers_list:
                        answers_list2.append('A')
                    if get_new(q['choices'][1]['content']) in answers_list:
                        answers_list2.append('B')
                    if get_new(q['choices'][2]['content']) in answers_list:
                        answers_list2.append('C')
                    if len(q['choices']) == 4:
                        if get_new(q['choices'][3]['content']) in answers_list:
                            answers_list2.append('D')
                    if len(q['choices']) == 5:
                        if get_new(q['choices'][3]['content']) in answers_list:
                            answers_list2.append('D')
                        if get_new(q['choices'][4]['content']) in answers_list:
                            answers_list2.append('E')
                    oo = ''
                    for ans in answers_list2:
                        oo = oo + ans + ','
                    ids.append(question['id'])
                    answers.append(oo[0:-1])
                    break
        for q in panduans:
            for question in questions:
                if q['id'] == question['id']:
                    if get_new(q['choices'][0]['content']) == question[question['answer']]:
                        ids.append(question['id'])
                        answers.append('A')
                        break
                    if get_new(q['choices'][1]['content']) == question[question['answer']]:
                        ids.append(question['id'])
                        answers.append('B')
                        break
        for q in tiankons:
            for question in questions:
                if q['id'] == question['id']:
                    ids.append(question['id'])
                    answers.append(question['answer'])
                    break
        an = '['
        for i in range(len(ids)):
            a = {'id': ids[i], 'signed': 0, 'userAnswer': answers[i]}
            answerData = json.dumps(a, ensure_ascii=False)
            an = an + answerData + ','
        an = an[0: -1] + ']'
        t = random.randint(182, 239)
        print(name + '-->为避免秒答现象，本次周周练答题将在' + str(t) + '秒后完成！不要随意关闭程序哦。')
        time.sleep(30)
        print(name + '-->已经过30秒，这才刚刚开始...')
        time.sleep(30)
        print(name + '-->已经过1分钟，请耐心等待...')
        time.sleep(30)
        print(name + '-->已经过1分30秒，马上就结束啦...')
        time.sleep(30)
        print(name + '-->已经过2分钟，请耐心等待...')
        time.sleep(30)
        print(name + '-->已经过2分30秒，马上就可以提交啦！')
        time.sleep(30)
        print(name + '-->已经过3分钟，准备提交！')
        time.sleep(t - 180)
        request_save = session.post('https://bw.rsbsyzx.cn/api/examination/submit',
                                    data={'recordId': recordId, 'answerData': an})
        if json.loads(request_save.content.decode('UTF-8'))['code'] != 'SUCCESS':
            print(name + '-->周周练提交失败！')
            print(request_save.content.decode('UTF-8'))
        print(name + '-->已完成周周练')
    except TypeError:
        print(name + '-->当日周周练已完成，无法再次答题！')


# 完成月月比_人机对抗
def finish_month(session, name):
    findIsHasAttend = session.get('https://bw.rsbsyzx.cn/api/fight/findIsHasAttend')
    hasAttend = json.loads(findIsHasAttend.content.decode('UTF-8'))['data']['hasAttend']
    fighting = json.loads(findIsHasAttend.content.decode('UTF-8'))['data']['fighting']

    if (hasAttend):
        print(name + '--->月月比今日已对战')
    else:
        againstIdStr = session.post('https://bw.rsbsyzx.cn/api/fight/martchMachine')
        againstId = json.loads(againstIdStr.content.decode('UTF-8'))['data']['againstId']
        print('againstId:' + againstId)

        questionListStr = session.get('https://bw.rsbsyzx.cn/api/fight/findRandomQuestionList',
                                      params={'platformId': '1', 'number': '10'})
        questionList = json.loads(questionListStr.content.decode('UTF-8'))['data']

        for q in questionList:
            userAnswer = q['questionBasicInfo']['answer']
            questionId = q['questionBasicInfo']['id']
            t = 100
            session.post('https://bw.rsbsyzx.cn/api/fight/saveUserAgainstRecordsDetail',
                         params={'againstRecordId': againstId, 'questionId': questionId, 'userAnswer': userAnswer,
                                 'answerDuration': t, 'againstWay': '1'})
        t = random.randint(182, 239)
        print(name + '-->为避免秒答现象，本次月月比人机对战将在' + str(t) + '秒后完成！不要随意关闭程序哦。')
        time.sleep(30)
        print(name + '-->已经过30秒，这才刚刚开始...')
        time.sleep(30)
        print(name + '-->已经过1分钟，请耐心等待...')
        time.sleep(30)
        print(name + '-->已经过1分30秒，马上就结束啦...')
        time.sleep(30)
        print(name + '-->已经过2分钟，请耐心等待...')
        time.sleep(30)
        print(name + '-->已经过2分30秒，马上就可以提交啦！')
        time.sleep(30)
        print(name + '-->已经过3分钟，准备提交！')
        time.sleep(t - 180)
        resultsStr = session.post('https://bw.rsbsyzx.cn/api/fight/calculateBattleResults',
                     params={'againstId': againstId})
        if json.loads(resultsStr.content.decode('UTF-8'))['code'] != 'SUCCESS':
            print(name + '-->月月比提交失败！')
            print(resultsStr.content.decode('UTF-8'))
        print(name + '-->已完成月月比-人机对战')


# 一个人完成日日学90题，周周练2遍，月月比1遍
def one_person(session, name):
    # 下面一共是六大类题目、三大类题型，全部做完一遍是90道题目。请根据个人需要适当删减。
    l1 =random.sample(range(0,17),2)    #不重复随机选择2组，可根据需要调整
    for x in l1:
        finish_day(session, list(chapterName)[x//3],list(typeName)[x%3], name)
    # 周周练两遍
    finish_week(session, name)
    finish_week(session, name)
    # 月月比对战1次
    finish_month(session, name)


# 定义多线程
class myThread (threading.Thread):
    def __init__(self, mobile, password, name):
        threading.Thread.__init__(self)
        self.mobile = mobile
        self.password = password
        self.name = name

    def run(self):
        print(self.name + "-->开始自动答题")
        session = goLogin_auto(self.mobile, self.password, self.name)
        one_person(session, self.name)
        print(self.name + "-->已完成答题")


# 多线程版本是同时进行多个用户的答题，不需要一个个的等待，可大幅节省程序的运行时间。
# 创建新线程 这里默认是十个用户，根据实际情况自行删减
# 这里默认密码是123456，可根据实际情况自行改动

thread1 = myThread("13967698797", "abcde12345", "Wcj")
thread2 = myThread("15824078866", "717973", "Jyz")
"""thread3 = myThread("1XXXXXXXXXX", "123456", "用户3")
thread4 = myThread("1XXXXXXXXXX", "123456", "用户4")
thread5 = myThread("1XXXXXXXXXX", "123456", "用户5")
thread6 = myThread("1XXXXXXXXXX", "123456", "用户6")
thread7 = myThread("1XXXXXXXXXX", "123456", "用户7")
thread8 = myThread("1XXXXXXXXXX", "123456", "用户8")
thread9 = myThread("1XXXXXXXXXX", "123456", "用户9")
thread0 = myThread("1XXXXXXXXXX", "123456", "用户0") """

# 开启新线程 这里对应的是上面的十个用户，根据上面的实际情况自行删减
thread1.start()
thread2.start()
""" thread3.start()
thread4.start()
thread5.start()
thread6.start()
thread7.start()
thread8.start()
thread9.start()
thread0.start() """

# 调用新线程 这里对应的是上面的十个用户，根据上面的实际情况自行删减
thread1.join()
thread2.join()
""" thread3.join()
thread4.join()
thread5.join()
thread6.join()
thread7.join()
thread8.join()
thread9.join()
thread0.join() """
print("退出线程")
