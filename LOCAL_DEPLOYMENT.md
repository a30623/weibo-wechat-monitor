# 微博更新到个人微信：本机部署说明

本目录基于 `nfe-w/aio-dynamic-push`，用于个人、非商业地监控一个微博博主的公开原创及转发微博，并通过 Server酱 Turbo 通知个人微信。上游基线 commit 记录在 `UPSTREAM_COMMIT`。

## 文件位置

- 私密配置：`config.local.yml`（已被 Git 和 Docker 构建上下文排除）
- 可提交模板：`config.example.yml`
- 持久去重状态：`data/weibo_state.json`
- 日志：`logs/monitor.stdout.log`、`logs/monitor.stderr.log`
- 进程号：`run/monitor.pid`

上游接口在本机匿名验证时返回未登录业务状态，因此当前部署需要 Cookie。本机任务使用 `api_mode: desktop`，Cookie 来自已登录的 `weibo.com` 请求。建议使用微博小号；不要在聊天、命令行参数或可提交文件中保存 Cookie。

## 首次配置和验证

1. 把 `config.local.yml` 中 `<WEIBO_UID>` 换成数字 UID，把 `<SERVERCHAN_SENDKEY>` 换成 SendKey，并把 `<WEIBO_COOKIE>` 换成 Cookie。该文件不可提交。当前 `desktop` 模式的 Cookie 获取方式：浏览器登录 `https://weibo.com`，按 F12 打开 Network 后刷新，选中同域请求，只把 Request Headers 中的 `cookie` 值写入该字段；关闭开发者工具，不要复制到聊天。
2. 解析主页并验证公开读取：

   ```powershell
   # 只解析 UID（可先用它填写 config.local.yml）
   .\.venv\Scripts\python.exe .\scripts\resolve_weibo.py '<微博主页链接>' --uid-only

   # 私密配置填好后，用其中 Cookie 验证最新公开微博
   .\.venv\Scripts\python.exe .\scripts\resolve_weibo.py '<微博主页链接>' --config .\config.local.yml
   ```

3. 检查配置（不会输出密钥）：

   ```powershell
   .\.venv\Scripts\python.exe .\scripts\preflight.py .\config.local.yml
   ```

4. 只在首次部署时发送一次获准的测试消息：

   ```powershell
   .\.venv\Scripts\python.exe .\scripts\send_deployment_test.py .\config.local.yml
   ```

## 日常运行

在项目根目录执行：

```powershell
# 启动
powershell -ExecutionPolicy Bypass -File .\scripts\start.ps1

# 停止
powershell -ExecutionPolicy Bypass -File .\scripts\stop.ps1

# 重启
powershell -ExecutionPolicy Bypass -File .\scripts\restart.ps1

# 状态
powershell -ExecutionPolicy Bypass -File .\scripts\status.ps1

# 持续查看日志（Ctrl+C 仅停止查看，不停止服务）
powershell -ExecutionPolicy Bypass -File .\scripts\logs.ps1
```

这是普通用户进程，不会自行注册系统服务或 Windows 计划任务。重启 Windows 后需手动运行启动命令；如需开机自启，应先确认后再创建系统级任务。

Docker/Compose 可用的机器也可执行 `docker compose up -d --build`；`compose.yml` 不发布端口，私密配置只读挂载，`data/` 持久挂载，重启策略为 `unless-stopped`。

## 修改监控对象和间隔

编辑私密配置中的 `uid_list`。默认 `intervals_second: 300`、`jitter_seconds: 30`，即每次约 270–330 秒。修改后执行重启命令。更换博主时，应先停止服务，备份并移走旧 `data/weibo_state.json`，然后启动；首次成功读取只建立新基线，不推送历史。

## 凭据失效

Server酱 SendKey 失效时：停止服务，在 `config.local.yml` 更换 `send_key`，运行配置检查；只有需要再次验证通道且明确同意再发一条测试消息时，才运行通道测试脚本。微博 Cookie 失效时，在浏览器登录 `https://weibo.com`，只将同域请求头中的 Cookie 写入私密配置 `cookie` 字段，然后重启。日志不会输出配置值、请求头或带 SendKey 的 URL 路径。

## 数据备份和恢复

停止服务后备份 `config.local.yml` 与整个 `data/` 目录。恢复时放回相同路径，确认仅当前用户可读，然后启动。不要删除正式状态文件来排障，否则下一次会重新建立基线；虽然不会批量推送历史，但会重置已见记录。

## 更新上游

先停止并备份私密配置及 `data/`，然后执行：

```powershell
git fetch origin
git log --oneline HEAD..origin/master
```

先审阅上游差异，尤其是依赖、网络请求、配置和容器文件，再将本地安全与持久化补丁迁移到新基线并运行测试。不要盲目覆盖 `config.local.yml` 或 `data/`，并更新 `UPSTREAM_COMMIT`。

## 健康检查

`scripts/status.ps1` 应显示 `RUNNING`；`logs/monitor.stderr.log` 应约每 270–330 秒出现一次查询活动，且没有连续请求错误；`data/weibo_state.json` 应存在并在发现新微博后更新。可用 `Get-Item .\data\weibo_state.json` 查看修改时间，不要把正式状态内容复制到公开位置。

## GitHub Actions 无服务器运行

`.github/workflows/weibo-monitor.yml` 每 5 分钟触发一次，并随机等待 0–30 秒后执行单次检查。仓库中只包含可公开的程序文件；私密值必须配置成仓库 Actions Secrets：`WEIBO_UID`、`WEIBO_COOKIE`、`SERVERCHAN_SENDKEY`。工作流运行时才生成被忽略的 `config.local.yml`，不会输出凭据内容。

云端去重状态保存在独立的 `monitor-state` 分支。第一次成功运行在该分支建立基线，不推送历史微博；后续运行读取同一状态，只有发现新微博并成功推送后才更新。不要删除该分支，否则下一次运行会重新建立基线。

在仓库的 Actions 页面查看 `Weibo monitor`：绿色运行记录表示检查成功；也可以用 `Run workflow` 手动检查。云端验证完成后应停止本机进程，避免本机和云端同时监控。GitHub 的计划任务可能延迟，并且公开仓库长期无活动时可能被自动停用，需要定期查看 Actions 页面。
