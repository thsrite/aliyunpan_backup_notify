主要用于检测每天备份文件是否正确上传至云盘

```
config.yaml

notify:
 # 是否开始服务
  status: true
  # 检测周期
  monitor: '0 9 * * *'
  # 删除文件重新同步周期
  sync: '0 21 * * *'
  # 检测云盘文件夹（一级文件夹）
  notify_path: 'backup'
  # 阿里云盘refresh_token
  refresh_token: ''

# 微信通知配置
wechat:
  # 企业id
  corp_id: ""
  # 应用密钥
  secret: ""
  # 应用id
  agent_id: ""
  # 不知道就填@all
  to_user: ""
  # 微信代理服务器，不填用官方
  proxy_url: ""
  # 微信消息图片，不填用默认
  image_url: ""
```
```
docker run -d --name alipan_notify
-v <config.yaml父路径>:/mnt
-v <config.yaml父路径>:/aligo.json:/root/.aligo/aligo.json
thsrite/alipan-nofity:latest
```
