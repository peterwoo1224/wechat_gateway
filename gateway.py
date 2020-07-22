#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Time    : 2020/7/21 5:08 下午
# @Author  : wlb
# @File    : gateway.py
# @Software: PyCharm


from wsgiref.simple_server import make_server
import re
import requests
import json
import os
import logging
from logging.handlers import TimedRotatingFileHandler

# 定义日志
LOG_FILE = "./wechat_alert.log"
logger = logging.getLogger()
logger.setLevel(logging.INFO)
fh = TimedRotatingFileHandler(LOG_FILE, when='D', interval=1, backupCount=30)
datefmt = '%Y-%m-%d %H:%M:%S'
format_str = '%(asctime)s %(levelname)s %(message)s '
formatter = logging.Formatter(format_str, datefmt)
fh.setFormatter(formatter)
logger.addHandler(fh)

os.chdir(os.path.split(os.path.realpath(__file__))[0])

# 读取配置文件
def parse_account(file):
    with open(file, 'r', encoding='utf-8') as f:
        conf_data = json.load(f)
    # 读取字典内kye为weixin的值
    weixin = [(d['CorpId'], d['AgentId'], d['Secret']) for d in conf_data['weixin']]
    for item in weixin:
        CorpId = item[0]
        AgentId = item[1]
        Secret = item[2]

    # 读取users的值并转换成列表以|符号隔开(微信字段定义对个值以|符号隔开)
    users_list = []
    for k, v in conf_data.items():
        if k == "users":
            for s, r in v[0].items():
                users_list.append(r)
    Users = '|'.join(users_list)

    return CorpId, AgentId, Secret, Users

# 获取token并写入到access_token.json文件
def access_token(CorpId, Secret):
    url = "https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid=" + CorpId + "&corpsecret=" + Secret
    response = requests.request("GET", url)
    if response.json()['errcode'] != 0:
        print("获取token出错，服务已停止，请排查后再启动！")
        return False
    else:
        access_token = response.json()['access_token']
        with open('./access_token.json', 'w') as file:
            file.write(response.text)
            file.close()
        return access_token


# 定义函数，参数是函数的两个参数，都是python本身定义的，默认就行了。
def application(environ, start_response):
    # 定义文件请求的类型和当前请求成功的code
    start_response('200 OK', [('Content-Type', 'application/json')])
    # environ是当前请求的所有数据，包括Header和URL，body
    request_body = environ["wsgi.input"].read(int(environ.get("CONTENT_LENGTH", 0)))
    # byte 转 str
    json_str = request_body.decode('utf-8')
    # 单引号转双引号, json.loads 必须使用双引号
    json_str = re.sub('\'', '\"', json_str)
    # POST请求中的data部分（注意：key值必须双引号）
    json_dict = json.loads(json_str)
    # 调用wechat发送data中的msg字段
    wechat(json_dict["msg"])
    # 调试 输出字典
    #print(json_dict["msg"])
    return [json.dumps(json_dict).encode()]

# 告警主程序
def wechat(data):
    # 组成post请求连接
    url = "https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token=" + Token
    post_url = url
    logging.info(post_msg(post_url, data))


# 完成告警信息
def post_msg(post_url, msg):

    headers = {'Content-Type': 'application/json'}
    post_data = {
        "touser": Users,
        "msgtype": "text",
        "agentid": "1000002",
        "text":
            {
                "content": msg
            },
        "safe": 0,
        "enable_id_trans": 0,
        "enable_duplicate_check": 0,
        "duplicate_check_interval": 1800
    }
    post_json = json.dumps(post_data)
    r = requests.post(post_url, headers=headers, data=post_json)
    return r.text


if __name__ == '__main__':
    # 读取配置文件
    (CorpId, AgentId, Secret, Users) = parse_account('config.json')
    Token = access_token(CorpId, Secret)
    port = 6088
    httpd = make_server("0.0.0.0", port, application)
    # 判断获取token是否成功，否则停止服务
    if Token == False:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass
        httpd.server_close()
    # 服务启动监听
    print("serving http on port {0}...".format(str(port)))
    #httpd.serve_forever()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()

    # curl http://127.0.0.1:6088 -X POST -d '{"msg": "world"}' --header "Content-Type: application/json"
