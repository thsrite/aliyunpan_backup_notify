import multiprocessing
import os
import logging

from fastapi import FastAPI
import uvicorn as uvicorn
import yaml
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from uvicorn import Config

import aliyunpan

if __name__ == '__main__':
    alipan = aliyunpan.AliyunPan()
    filepath = os.path.join("/mnt",
                            'config.yaml')  # 文件路径,这里需要将a.yaml文件与本程序文件放在同级目录下
    with open(filepath, 'r') as f:  # 用with读取文件更好
        configs = yaml.load(f, Loader=yaml.FullLoader)  # 按字典格式读取并返回

    if bool(configs["notify"]["status"]) == True:
        # 定时服务
        _scheduler = BackgroundScheduler(timezone="Asia/Shanghai")
        try:
            if configs["notify"]["monitor"]:
                _scheduler.add_job(func=alipan.sync_aliyunpan,
                                   trigger=CronTrigger.from_crontab(str(configs["notify"]["monitor"])),
                                   name="备份监控")
            if configs["notify"]["sync"]:
                _scheduler.add_job(func=alipan.resync,
                                   trigger=CronTrigger.from_crontab(str(configs["notify"]["sync"])),
                                   name="重新同步")
        except Exception as err:
            logging.error(f"定时任务配置错误：{err}")

        # 启动任务
        if _scheduler.get_jobs():
            _scheduler.print_jobs()
            _scheduler.start()

        # App
        App = FastAPI(title='aliyunpan_notify',
                      openapi_url="/api/v1/openapi.json")

        # uvicorn服务
        Server = uvicorn.Server(Config(App, host='0.0.0.0', port=9928,
                                       reload=False, workers=multiprocessing.cpu_count()))
        # 启动服务
        Server.run()
