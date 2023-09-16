import json
import logging
import time
from pathlib import Path

from aligo import Aligo

import wechat


class AliyunPan:
    # 本次文件存储路径
    __folder_json = '/Users/jiangxd/PycharmProjects/alipan_notify/floder_files.json'
    # 文件夹->文件映射关系
    __folder_files = {}
    # 本次扫描新闻界
    __new_files = []
    _ali = None
    # 定时器
    _scheduler = None

    def __get_folder_files(self, parent, file, first_flag=False):
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

            if new_flag and not first_flag:
                new_file = {
                    'name': file.name,
                    'size': file.size,
                    'time': time.strftime('%Y-%m-%d %H:%M:%S',
                                          time.strptime(file.updated_at, '%Y-%m-%dT%H:%M:%S.%fZ'))
                }
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
                    self.__get_folder_files(file2.name, file2)
                else:
                    # 判断是否新文件
                    new_flag = True

                    if sub_files:
                        for f in sub_files:
                            if str(f.get('name')) == str(file2.name):
                                new_flag = False
                                break

                    if new_flag and not first_flag:
                        new_file = {
                            'name': file2.name,
                            'size': file2.size,
                            'time': time.strftime('%Y-%m-%d %H:%M:%S',
                                                  time.strptime(file2.updated_at, '%Y-%m-%dT%H:%M:%S.%fZ'))
                        }
                        sub_files.append(new_file)
                        new_file['parent'] = file.name
                        self.__new_files.append(new_file)
                        logging.info(f"获取到新文件 {new_file}")
            if sub_files:
                self.__folder_files[file.name] = sub_files

    def sync_aliyunpan(self):
        # 第一次使用，会弹出二维码，供扫描登录
        self._ali = Aligo()
        # 获取用户信息
        user = self._ali.get_user()

        # 读取已有本地文件
        if Path(self.__folder_json).exists():
            with open(self.__folder_json, 'r') as file:
                content = file.read()
                if content:
                    self.__folder_files = json.loads(content)

        # 判断是否首次运行，首次运行不发通知
        first_flag = False
        if not self.__folder_files:
            first_flag = True

        # 获取网盘根目录文件列表
        ll = self._ali.get_file_list()
        # 遍历文件列表
        for file in ll:
            if file.name == 'backup':
                self.__get_folder_files('backup', file, first_flag)

        # 本次扫描有新文件，则发送通知
        if self.__new_files:
            # 组织msg
            new_file_msg = ""
            for index, file in enumerate(self.__new_files):
                new_file_msg += f"path {file.get('parent')} \n" \
                                f"file {file.get('name')} \n" \
                                f"time {file.get('time')} \n" \
                                f" \n"
            # 发送微信通知
            logging.info(f'准备发送新文件上传通知 {new_file_msg}')
            wc = wechat.WeChat()
            wc.send_message('文件备份通知', new_file_msg)

        # 最终写入文件
        if self.__folder_files:
            file = open(self.__folder_json, 'w')
            file.write(json.dumps(self.__folder_files))
            file.close()
