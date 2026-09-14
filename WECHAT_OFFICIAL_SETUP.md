# 微信公众号模板消息接入

本项目使用微信官方 `api.weixin.qq.com` 接口，不模拟个人微信登录。支持已开通模板消息权限的认证服务号，以及用于开发验证的微信公众平台测试账号。

## 微信后台准备

1. 登录微信公众平台。正式服务号需确认已认证，并在“广告与服务/模板消息”中具备模板消息权限。若只是个人自用验证，可进入“公众平台测试账号”。
2. 让接收消息的微信扫码关注该服务号或测试号，记录后台显示的 OpenID。
3. 新增模板，内容必须与下方完全对应：

   ```text
   {{title.DATA}}

   {{content.DATA}}

   {{remark.DATA}}
   ```

4. 记录 AppID、AppSecret、模板 ID 和接收者 OpenID。AppSecret 属于高敏感凭据，不要写进 Git、聊天或命令行参数。
5. 正式服务号若启用了接口 IP 白名单，把实际运行服务器的固定出口公网 IP 加入白名单。

正式服务号的模板消息只能用于符合微信规则的服务通知。若后台没有模板消息权限，不能通过代码绕过；客服消息也有用户交互后的时间窗口限制。

## 项目配置

复制 `config.wechat.example.yml` 为被 Git 忽略的 `config.wechat.local.yml`，填入上述四项和微博 Cookie。服务器部署时可将该文件作为容器内 `/mnt/config.yml` 只读挂载。公众号消息不能直接内嵌微博图片，但点击消息可打开原微博页面。

切换通道后先使用临时状态文件执行一次受控测试；确认微信收到后再沿用正式 `data/weibo_state.json`。不要删除正式状态，否则下一次只会重新建立基线。

配置完成后先检查配置：

```powershell
.\.venv\Scripts\python.exe .\scripts\preflight.py .\config.wechat.local.yml
```

只有在明确同意接收一条测试消息后，才运行：

```powershell
.\.venv\Scripts\python.exe .\scripts\send_wechat_test.py .\config.wechat.local.yml
```
