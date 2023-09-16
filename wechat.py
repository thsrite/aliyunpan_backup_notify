import logging

import requests
import yaml
import os


class WeChat():
    def __init__(self):
        filepath = os.path.join("/mnt", 'config.yaml')
        with open(filepath, 'r') as f:  # 用with读取文件更好
            configs = yaml.load(f, Loader=yaml.FullLoader)  # 按字典格式读取并返回

        self.CORP_ID = str(configs["wechat"]["corp_id"])  # 企业号的标识
        self.SECRET = str(configs["wechat"]["secret"])  # 管理组凭证密钥
        self.AGENT_ID = int(configs["wechat"]["agent_id"])  # 应用ID
        self.TO_USER = str(configs["wechat"]["to_user"])  # 应用ID
        self.token = self.get_token()

    def get_token(self):
        url = "https://qyapi.weixin.qq.com/cgi-bin/gettoken"
        data = {
            "corpid": self.CORP_ID,
            "corpsecret": self.SECRET
        }
        req = requests.get(url=url, params=data)
        res = req.json()
        if res['errmsg'] == 'ok':
            return res["access_token"]
        else:
            return res

    def send_message(self, title, text):
        url = "https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token=%s" % self.token
        image_url = "https://raw.githubusercontent.com/thsrite/aliyundrive-checkin/main/aliyunpan.jpg"
        if text:
            text = text.replace("\n\n", "\n")
        req_json = {
            "touser": self.TO_USER,
            "msgtype": "news",
            "agentid": self.AGENT_ID,
            "news": {
                "articles": [
                    {
                        "title": title,
                        "description": text,
                        "picurl": image_url,
                        "url": ''
                    }
                ]
            }
        }
        req = requests.post(url=url, json=req_json)
        res = req.json()
        if res['errmsg'] == 'ok':
            logging.info("send wechat msg successed")
            return "send message sucessed"
        else:
            return res
