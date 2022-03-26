# -*- coding = utf-8 -*-
# @Time : 2021/11/26 16:12
# @Author : wpz
# @File : 校园网.py
# @Software : PyCharm

import json
import sys
import time
from msvcrt import getch
from urllib import parse

import ddddocr
import execjs
import requests


def CanConnect():
    """
    当断网时访问http://1.1.1.1/时会跳转到认证页面
    返回值
    1：未断网
    0：断网
    -1：未连接网络
    """
    url = "http://1.1.1.1/"
    global ip_dict

    try:
        r = requests.get(url)
        if "wlanacip" not in r.url:
            return 1
        else:
            # 获取wlanacip和wlanuserip两个参数
            parsed = parse.urlparse(r.url)
            querys = parse.parse_qsl(str(parsed.query))
            ip_dict = dict(querys)
            ip_dict["base"] = parsed.netloc
            return 0
    except requests.exceptions.ConnectionError as e:
        if "10065" in str(e.args):  # 未连接网络
            return -1
        elif "10054" in str(e.args):  # 远程主机强迫关闭了一个现有的连接？访问过于频繁？
            return 1


def initJS():
    try:
        with open("RAS.js", "r", encoding="utf-8") as f:
            jsstr = f.read()
    except:
        print("找不到RAS.js文件或者文件出错\n正尝试从gitee上下载···", end="")
        headers = {
            'User-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36',
            'Referer': 'https://gitee.com/bailuqiao/Tainyi-campus-network/blob/main/RAS.js'
        }
        try:
            r = requests.get("https://gitee.com/bailuqiao/Tainyi-campus-network/raw/main/RAS.js", headers=headers)
        except:
            print("失败\n按任意键退出...")
            getch()
            sys.exit(0)
        with open("RAS.js", "wb") as f:
            f.write(r.content)
        print("成功")
        with open("RAS.js", "r", encoding="utf-8") as f:
            jsstr = f.read()

    return execjs.compile(jsstr)


def login(js):
    # 获取验证码并保存cookies
    session = requests.session()
    while 1:
        t = time.time()
        timestamp = int(round(t * 1000))  # 毫秒级时间戳
        url = "http://" + ip_dict["base"] + "/common/image_code.jsp?time=" + str(timestamp)  # 好像不加参数也可以
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36"}
        try:
            r = session.get(url, headers=headers)
        except requests.exceptions.ConnectionError:  # 无法访问校园网认证连接
            print("请先连接校园网\n按任意键退出······")
            input()
            sys.exit(0)

        # 验证码识别
        print("验证码识别中···")
        ocr = ddddocr.DdddOcr()
        try:
            codestr = ocr.classification(r.content)
        except:
            print("异常")
            input()

        # 调用js生成loginKey参数
        loginKey = js.call('getLoginKey', username, password, codestr)

        data = {"loginKey": loginKey,
                "wlanuserip": ip_dict["wlanuserip"],
                "wlanacip": ip_dict["wlanacip"]}

        r = session.post(f"http://{ip_dict['base']}/ajax/login", headers=headers, data=data)
        buff = json.loads(r.text)
        if buff["resultCode"] != "11063000":  # 验证码错误代号
            print("成功")
            break
        print("验证码错误，重试中")


if __name__ == "__main__":

    username = ""
    password = ""
    if username == "" or password == "":
        print("账号密码为空\n按回车退出...")
        getch()
        sys.exit(0)

    js_compile = initJS()
    ip_dict = {}
    print("运行中···")
    while 1:
        if CanConnect() == 0:  # 为0断网
            print("断网")
            login(js_compile)
        elif CanConnect() == -1:
            print("请先连接校园网")

        time.sleep(3)
