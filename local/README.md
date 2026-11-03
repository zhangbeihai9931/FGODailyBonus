# 本地自动化（Windows）

让电脑每天自动触发一次云端签到，全程不用手工操作。

## 原理

```
Windows 计划任务（每天 03:00）
  └─ daily_task.py
       ├─ trigger.py：改 heartbeat.txt 并提交 → GitHub 收到 push → 立刻跑签到
       └─ 推送失败时：在本地直接执行 main.py（兜底）
```

GitHub 自带的 cron 常年延迟 3~4 小时甚至丢失，而 push 事件是实时的（实测 1 秒内触发），
所以用「主动推送」当主触发器。

## 配置

1. 把 `env.example` 复制为 `env.txt`，填上自己的值（`env.txt` 已被 .gitignore 排除）

   ```
   GITHUB_OWNER=你的用户名
   GITHUB_REPO=FGODailyBonus
   GITHUB_TOKEN=ghp_xxx        # 需要有 repo 权限
   GAME_USERIDS=...
   GAME_AUTHKEYS=...
   GAME_SECRETKEYS=...
   GAME_VERCODE=48a1e86...
   ```

2. 在仓库根目录创建虚拟环境并装依赖

   ```bat
   python -m venv .venv
   .venv\Scripts\pip install -r requirements.txt
   ```

3. 注册计划任务

   ```powershell
   powershell -ExecutionPolicy Bypass -File .\install_task.ps1 -Time 03:00
   ```

## 日常

| 想做什么 | 怎么做 |
|---|---|
| 改运行时间 | 重新跑 `install_task.ps1 -Time 07:30` |
| 立刻触发一次 | `python daily_task.py` |
| 只推心跳不签到 | `python trigger.py` |
| 检查配置 | `python trigger.py --check` |
| 看运行记录 | `logs\自动化记录.txt` |

## 注意

- 电脑关机或未登录时会跳过，下次开机由 StartWhenAvailable 自动补跑
- `env.txt` 含凭证，**不要提交**；仓库里只放 `env.example`
- 每次运行会在仓库里产生一条 `heartbeat` 提交
