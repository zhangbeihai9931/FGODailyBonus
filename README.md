# FGODailyBonus

Fate/Grand Order 每日自动签到。跑在 GitHub Actions 上，也可以在自己的 Windows 电脑上定时跑。

fork 自 [hexstr/FGODailyBonus](https://github.com/hexstr/FGODailyBonus)，在原版基础上做了这些修复与增强：

- 修复 `private_key.pem` 无法被新版 OpenSSL 解析（`ASN.1 parsing error`）
- 修复 Telegram 推送因 Markdown 解析失败报 400
- 修复日志上传因鉴权缺失报 422
- 支持**私有日志仓库**（改用 GitHub API 读写，不再依赖公开的 raw 地址）
- 玩家昵称改为**加盐哈希**，日志中不可反推
- 断网时自动使用本地 `cfg.json` 缓存

> **风险提示**：本项目通过官方 API 自动完成登录。FGO 已启用 Play Integrity / App Check，
> 非官方客户端行为可能被标记账号，导致之后在手机 App 上登录出现 `99-` 开头的错误。
> **使用后果自负。**

---

## 快速开始（GitHub Actions）

1. Fork 本仓库，或把代码导入你自己的仓库
2. 新建一个**日志仓库**，建议命名为 `FGODailyBonusLog`（可以设为 private）
3. 在日志仓库里新建 `cfg.json`，内容：

   ```json
   {"global": {"appVer": "2.54.0", "assetbundleFolder": "trb3ulHJR4lI/", "dataServerFolderCrc": 610168911, "dataVer": 1419, "dateVer": 1655046000}}
   ```

   > 这只是初始值，脚本每次运行都会向游戏服务器核对版本，发现过期会自动更新并写回。

4. 生成 GitHub Personal Access Token（`repo` 权限即可；
   如果你还想用 API 修改 `.github/workflows/`，需要额外勾选 `workflow`）
5. 在本仓库 `Settings → Secrets and variables → Actions` 里添加下方 Secrets
6. 打开 `Actions` 页面，启用工作流

### 需要的 Secrets

| Secret | 说明 |
|---|---|
| `GAME_USERIDS` | 账号 id，多个用英文逗号分隔 |
| `GAME_AUTHKEYS` | 认证 key，与 userId 一一对应 |
| `GAME_SECRETKEYS` | 密钥，与 userId 一一对应 |
| `GAME_VERCODE` | 固定值，见下 |
| `GAME_USERAGENT` | 伪装 UA，不需要就填 `nullvalue` |
| `TELEGRAM_BOT_TOKEN` | 可选；不需要通知填 `nullvalue` |
| `TELEGRAM_ADMIN_ID` | 可选；不需要通知填 `nullvalue` |
| `VERY_IMPORTANT_NAME` | 你的 GitHub 用户名 |
| `VERY_IMPORTANT_TOKEN` | 上一步生成的 PAT |
| `NAME_SALT` | 可选。自定义昵称哈希盐，见「隐私」一节 |

`GAME_VERCODE` 固定填：

```
48a1e86bdbb80b4795204d447cfc073ce21b132a5bd5b096cb919830b1d3b93e
```

---

## 本地运行（Windows）

```bat
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt

set userIds=你的userId
set authKeys=你的authKey
set secretKeys=你的secretKey
set verCode=48a1e86bdbb80b4795204d447cfc073ce21b132a5bd5b096cb919830b1d3b93e
set UserAgent=nullvalue
set TGBotToken=nullvalue
set TGAdminId=nullvalue
set GithubToken=你的PAT
set GithubName=你的用户名

.venv\Scripts\python main.py
```

首次运行会在当前目录生成 `cfg.json` 缓存；之后即使日志仓库不可达也能继续跑。

---

## 隐私说明

这个项目**不收集任何个人数据**，但日志里会出现游戏内的统计信息。为了降低隐私暴露，做了以下处理：

| 数据 | 处理方式 |
|---|---|
| authKey / secretKey / userId | 只存在 Secrets 和本地配置，**从不写入仓库** |
| 游戏昵称 | `sha256(salt + name)` 取前 16 位，**不可反推** |
| 等级 / 石头 / 呼符 / 体力 / 友情点 / 登录天数 | 原样写入日志（这是签到结果本身） |
| cfg.json | 只有公开的游戏版本号 |

**盐从哪来**：优先读环境变量 `NAME_SALT`；未配置时由 `secretKey` 派生。
因为 `secretKey` 只在 Secrets 里，外人无法复现同样的哈希；同一账号每天算出来又是一致的，
所以日志能对上，但别人看不出是谁。

> 想要更强的隔离，可以自己设一个随机 `NAME_SALT`。
> 注意：本地和 Actions 必须用同一个盐，否则两边的标识对不上。

**日志仓库建议设为 private**。代码现在通过带 token 的 GitHub API 读写 `cfg.json`，
私有仓库同样可用；只有在你把仓库设为公开时才会退回 raw 地址读取。

---

## 账号信息提取

手机路径：`/sdcard/Android/data/com.aniplex.fategrandorder/files/data/54cc790bf952ea710ed7e8be08049531`

用记事本打开，从字母 `Z` 复制到结尾，替换 `CertificateExtractor.cs` 第 9 行的 `YourCertificate`，
编译运行后打印出的就是三个 Secret 需要的值。

编译方式任选：

- 贴到任意在线 C# 编译器运行
- 本地 `csc /out:CertificateExtractor.exe CertificateExtractor.cs`
- 用 Visual Studio 打开一个 .NET Framework 4.x 控制台项目

---

## 目录结构

```
main.py                  签到主流程
fgourl.py                游戏接口 / Telegram / GitHub 上传
user.py                  登录与签到
rsa.py                   RSA 签名（读取 private_key.pem）
privacy.py               昵称加盐哈希
mytime.py                时间处理
CatAndMouseGame.py       资源包字段解密
pprp/                    纯 Python 的 AES / PBKDF2 实现
private_key.pem          官方客户端签名私钥（所有使用者共用，非个人凭证）
CertificateExtractor.cs  账号信息解密小工具
requirements.txt         Python 依赖
.github/workflows/run.yml  定时任务定义
```

---

## 常见问题

**Q：Actions 里显示 `userIds: ***`，是不是没读到？**
A：不是。GitHub 会把 Secrets 的值自动打码成 `***`，正常运行。

**Q：日志仓库能不能私有？**
A：可以。脚本用带 token 的 API 读写 `cfg.json`，私有仓库同样工作。

**Q：改 `.github/workflows/` 时报 404？**
A：token 缺少 `workflow` 权限。GitHub 对工作流文件有特殊保护，会返回 404 而不是 403。

**Q：同一天跑两次会怎样？**
A：第二次登录不会再发奖励，属于正常现象。

---

## 已验证环境

| 环境 | 版本 / 说明 |
|---|---|
| GitHub Actions | `ubuntu-latest` + Python 3.11 |
| Windows 本地 | Python 3.14.7 + requests 2.34.2 + cryptography 50.0.2（OpenSSL 4.0.3） |
| 日志仓库 | 实测 **private** 可用（走带 token 的 API） |

> 如果你的 `cryptography` 版本很旧（比如 42.x 之前），`private_key.pem` 可能因为
> p/q 顺序问题被新版 OpenSSL 拒绝，报 `ASN.1 parsing error: invalid value`。
> 本仓库里的私钥已按 p > q 规范化，模数未改动，签名结果与原版一致。

---

## 致谢与许可

- 原始项目：[hexstr/FGODailyBonus](https://github.com/hexstr/FGODailyBonus)
- 许可：[MIT](LICENSE)
