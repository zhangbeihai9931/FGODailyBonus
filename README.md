# FGODailyBonus

Fate/Grand Order 每日自动签到，跑在 GitHub Actions 上。
fork 自 [hexstr/FGODailyBonus](https://github.com/hexstr/FGODailyBonus)，在原版基础上修复了签名私钥无法加载的问题（见下方"变更记录"）。

> **风险提示**：本项目通过官方 API 自动完成登录。FGO 已启用 Play Integrity / App Check，非官方客户端行为可能被标记，
> 导致之后在手机 App 上登录出现 `99-` 开头的错误。**使用后果自负。**

## 运行方式

`.github/workflows/run.yml` 已配置：

- 每天 `UTC 19:30`（东京 04:30 / 北京 03:30）自动运行
- 随时可在 Actions 页面手动 `Run workflow`

### 需要的 Secrets

| Secret | 说明 |
|---|---|
| `GAME_USERIDS` | 账号 id，多个用英文逗号分隔 |
| `GAME_AUTHKEYS` | 认证 key，和 userId 一一对应 |
| `GAME_SECRETKEYS` | 密钥，和 userId 一一对应 |
| `GAME_VERCODE` | 固定值，见下 |
| `GAME_USERAGENT` | 伪装 UA，不需要就填 `nullvalue` |
| `TELEGRAM_BOT_TOKEN` | 可选，不通知填 `nullvalue` |
| `TELEGRAM_ADMIN_ID` | 可选，不通知填 `nullvalue` |
| `VERY_IMPORTANT_NAME` | 你的 GitHub 用户名 |
| `VERY_IMPORTANT_TOKEN` | 有 `repo` 权限的 PAT，用来写日志仓库 |

`GAME_VERCODE` 固定填：

```
48a1e86bdbb80b4795204d447cfc073ce21b132a5bd5b096cb919830b1d3b93e
```

## 日志仓库

签到结果写到同账号下的 `FGODailyBonusLog` 仓库：

- `cfg.json` —— 游戏数据版本（appVer / dataVer / dateVer / assetbundleFolder）。
  脚本发现版本过期会自动向服务器查询新值并回写，**不需要手动维护**。
- `YYYY-MM-DD-HH-mm.txt` —— 每次签到的结果日志

## 本地运行

```bash
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt        # Windows
# source .venv/bin/activate && pip install -r requirements.txt   # Linux / macOS

# git-bash / Linux 写法
export userIds=...; export authKeys=...; export secretKeys=...
export verCode=48a1e86bdbb80b4795204d447cfc073ce21b132a5bd5b096cb919830b1d3b93e
export UserAgent=nullvalue; export TGBotToken=nullvalue; export TGAdminId=nullvalue
export GithubToken=...; export GithubName=...

python main.py
```

## 账号信息提取

手机路径 `/sdcard/Android/data/com.aniplex.fategrandorder/files/data/54cc790bf952ea710ed7e8be08049531`，
用记事本打开，从字母 `Z` 复制到结尾，替换 `CertificateExtractor.cs` 第 9 行的 `YourCertificate`，
编译运行后打印出的就是 `GAME_AUTHKEYS` / `GAME_SECRETKEYS` / `GAME_USERIDS` 需要的值。

编译方式：把 `CertificateExtractor.cs` 贴到任意在线 C# 编译器运行，或本地用
`csc /out:CertificateExtractor.exe CertificateExtractor.cs`，或建一个 .NET Framework 4.x 控制台项目。

## 变更记录

**2026-11-02 — 修复 Actions 全部失败的问题**

原 `private_key.pem` 是 PKCS#1 私钥，但 `p < q`。新版 OpenSSL（GitHub Runner / cryptography 42+ 之后）
解析时会直接报 `ASN.1 parsing error: invalid value`，导致每次运行都在 `import rsa` 处崩溃。

修复：交换 `p`/`q` 并重算 `dP`/`dQ`/`qInv` 重新编码。**模数 n、指数 e、私钥 d 均未改变，
签名结果与原文件完全一致**（PKCS#1 v1.5 签名是确定性的，已用公钥验签通过）。

同时：

- `run.yml`：`actions/checkout@v2` → `@v4`，补 `setup-python@v5` + `pip install -r requirements.txt`，
  删掉没用的 `python-version: [3.8]` 矩阵和 `pull_request` 触发，增加 `workflow_dispatch` 与 `concurrency`
- `requirements.txt`：补上漏掉的 `requests`
- 删除 `imgs/`（17 张截图，约 1.8 MB）、`pprp/crypto_2.py`、`pprp/pbkdf2_2.py`（仅 Python 2 使用的死代码）

## 目录

```
main.py                  签到主流程
fgourl.py                游戏接口 / Telegram 通知 / GitHub 上传
user.py                  登录与签到
rsa.py                   RSA 签名（读取 private_key.pem）
mytime.py                时间处理
CatAndMouseGame.py       资源包字段解密
pprp/                    纯 Python 的 AES / PBKDF2 实现
private_key.pem          登录请求签名用的 RSA 私钥
CertificateExtractor.cs  账号信息解密小工具
```

## 许可

MIT，见 [LICENSE](LICENSE)。
