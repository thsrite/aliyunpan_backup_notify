import datetime
import json
import logging
import os
import time
from pathlib import Path

import yaml
from aligo import Aligo

import wechat

logger = logging.getLogger()


class AliyunPan:
    def __init__(self):
        filepath = os.path.join("/mnt", 'config.yaml')
        with open(filepath, 'r') as f:  # 用with读取文件更好
            configs = yaml.load(f, Loader=yaml.FullLoader)  # 按字典格式读取并返回

        self.REFRESH_TOKEN = configs["notify"]["refresh_token"] or None
        self.NOTIFY_PATH = str(configs["notify"]["notify_path"])

    # 本次文件存储路径
    __folder_json = '/mnt/folder_files.json'
    # 文件夹->文件映射关系
    __folder_files = {}
    # 本次扫描新闻界
    __new_files = []
    _ali = None
    # 定时器
    _scheduler = None

    def __get_folder_files(self, parent, file, first_flag):
        '''
        获取文件夹下级文件存储
        :param parent:
        :param file:
        :return:
        '''
        parent_file_id = None
        if file and file.type == 'folder':
            parent_file_id = file.file_id
        if file and file.type == 'file':
            sub_files = self.__folder_files.get(parent) or []

            # 判断是否新文件
            new_flag = True

            if sub_files:
                for f in sub_files:
                    if str(f.get('name')) == str(file.name):
                        new_flag = False
                        break
            update_date = datetime.datetime.strptime(file.updated_at,
                                                     '%Y-%m-%dT%H:%M:%S.%fZ') + datetime.timedelta(hours=8)
            new_file = {
                'name': file.name,
                'size': file.size,
                'time': update_date.strftime('%Y-%m-%d %H:%M:%S')
            }
            if first_flag:
                sub_files.append(new_file)

            if new_flag and not first_flag:
                sub_files.append(new_file)
                new_file['parent'] = parent
                self.__new_files.append(new_file)
            if sub_files:
                self.__folder_files[file.name] = sub_files

        files = self._ali.get_file_list(parent_file_id=parent_file_id)
        if files:
            sub_files = self.__folder_files.get(parent) or []
            for file2 in files:
                if file2.type == 'folder':
                    self.__get_folder_files(file2.name, file2, first_flag)
                else:
                    # 判断是否新文件
                    new_flag = True

                    if sub_files:
                        for f in sub_files:
                            if str(f.get('name')) == str(file2.name):
                                new_flag = False
                                break
                    update_date = datetime.datetime.strptime(file2.updated_at,
                                                             '%Y-%m-%dT%H:%M:%S.%fZ') + datetime.timedelta(hours=8)
                    new_file = {
                        'name': file2.name,
                        'size': file2.size,
                        'time': update_date.strftime('%Y-%m-%d %H:%M:%S')
                    }
                    if first_flag:
                        sub_files.append(new_file)

                    if new_flag and not first_flag:
                        sub_files.append(new_file)
                        new_file['parent'] = file.name
                        self.__new_files.append(new_file)
                        logger.info(f"获取到新文件 {new_file}")
            if sub_files:
                self.__folder_files[file.name] = sub_files

    def resync(self):
        # 本次文件存储路径
        if Path(self.__folder_json).exists():
            os.remove(self.__folder_json)
            logger.info(f"开始删除本地文件 {self.__folder_json}")
        self.sync_aliyunpan()

    @staticmethod
    def str_filesize(size: Union[str, float, int], pre: int = 2) -> str:
        """
        将字节计算为文件大小描述（带单位的格式化后返回）
        """
        if size is None:
            return ""
        size = re.sub(r"\s|B|iB", "", str(size), re.I)
        if size.replace(".", "").isdigit():
            try:
                size = float(size)
                d = [(1024 - 1, 'K'), (1024 ** 2 - 1, 'M'), (1024 ** 3 - 1, 'G'), (1024 ** 4 - 1, 'T')]
                s = [x[0] for x in d]
                index = bisect.bisect_left(s, size) - 1
                if index == -1:
                    return str(size) + "B"
                else:
                    b, u = d[index]
                return str(round(size / (b + 1), pre)) + u
            except ValueError:
                return ""
        if re.findall(r"[KMGTP]", size, re.I):
            return size
        else:
            return size + "B"

    def sync_aliyunpan(self):
        '''
        同步阿里云文件
        '''
        logger.info("同步阿里云文件")
        self.__new_files = []

        # 第一次使用，会弹出二维码，供扫描登录
        self._ali = Aligo(level=logging.INFO, refresh_token=self.REFRESH_TOKEN)
        # 获取用户信息
        user = self._ali.get_user()
        logger.info(user)

        # 判断是否首次运行，首次运行不发通知
        first_flag = True

        # 读取已有本地文件
        if Path(self.__folder_json).exists():
            with open(self.__folder_json, 'r') as file:
                content = file.read()
                if content:
                    self.__folder_files = json.loads(content)
                    first_flag = False

        # 获取网盘根目录文件列表
        ll = self._ali.get_file_list()
        # 遍历文件列表
        for file in ll:
            if file.name == self.NOTIFY_PATH:
                self.__get_folder_files(self.NOTIFY_PATH, file, first_flag)

        # 本次扫描有新文件，则发送通知
        if not first_flag and self.__new_files:
            # 组织msg
            new_file_msg = ""
            for index, file in enumerate(self.__new_files):
                new_file_msg += f"备份文件 {file.get('name')} {self.str_filesize(file.get('size'))}\n" \
                                f"备份时间 {file.get('time')} \n" \
                                f" \n"
            # 发送微信通知
            logger.info(f'准备发送新文件上传通知 {new_file_msg}')
            wc = wechat.WeChat()
            wc.send_message('文件备份通知', new_file_msg)
        else:
            logger.info(f'未发现新上传文件')

        # 最终写入文件
        if self.__folder_files:
            logger.info(f"开始写入本地文件 {self.__folder_json}")
            file = open(self.__folder_json, 'w')
            file.write(json.dumps(self.__folder_files))
            file.close()
        else:
            logger.warning(f"未获取到文件列表")
