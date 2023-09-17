import logging

import requests
import yaml
import os

logging.basicConfig(filename="alipan_wechat", format='%(asctime)s - %(name)s - %(levelname)s -%(module)s:  %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S ',
                    level=logging.INFO)
logger = logging.getLogger()
KZT = logging.StreamHandler()
KZT.setLevel(logging.DEBUG)
logger.addHandler(KZT)


class WeChat():
    def __init__(self):
        filepath = os.path.join("/mnt", 'config.yaml')
        with open(filepath, 'r') as f:  # 用with读取文件更好
            configs = yaml.load(f, Loader=yaml.FullLoader)  # 按字典格式读取并返回

        self.CORP_ID = str(configs["wechat"]["corp_id"])  # 企业号的标识
        self.SECRET = str(configs["wechat"]["secret"])  # 管理组凭证密钥
        self.AGENT_ID = int(configs["wechat"]["agent_id"])  # 应用ID
        self.TO_USER = str(configs["wechat"]["to_user"])  # 应用ID
        self.PROXY_URL = configs["wechat"]["proxy_url"] or "https://qyapi.weixin.qq.com"  # 微信代理
        self.IMAGE_URL = configs["wechat"][
                             "image_url"] or "https://raw.githubusercontent.com/thsrite/aliyundrive-checkin/main/aliyunpan.jpg"  # 代理图片
        self.token = self.get_token()

    def get_token(self):
        url = f"{self.PROXY_URL}/cgi-bin/gettoken"
        data = {
            "corpid": self.CORP_ID,
            "corpsecret": self.SECRET
        }
        req = requests.get(url=url, params=data)
        res = req.json()
        if res['errcode'] == 0:
            return res["access_token"]
        else:
            logger.error(f"获取 access_token 失败，错误信息：{res}")
            return res

    def send_message(self, title, text):
        url = f"{self.PROXY_URL}/cgi-bin/message/send?access_token=%s" % self.token
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
                        "picurl": self.IMAGE_URL,
                        "url": ''
                    }
                ]
            }
        }
        req = requests.post(url=url, json=req_json)
        res = req.json()
        if res['errcode'] == 0:
            logger.info("send wechat msg successed")
            return "send message sucessed"
        else:
            logger.error(f"发送 {title} 失败，错误信息：{res}")
            return res
