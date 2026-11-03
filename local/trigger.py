# -*- coding: utf-8 -*-
"""推送一次心跳提交，用来触发 GitHub Actions 的 push 事件。

GitHub 的 cron 常年延迟数小时甚至丢失，而 push 是实时的（实测 1 秒内触发）。
所以本机只要每天推一次心跳，签到就会稳定在云端执行。

用法：
    python trigger.py
    python trigger.py --check
"""
import base64
import datetime
import sys

import requests

import _env

LAST_ERROR = ""


def push(verbose=True):
    global LAST_ERROR
    LAST_ERROR = ""

    token = _env.get("GITHUB_TOKEN")
    owner = _env.get("GITHUB_OWNER")
    repo = _env.get("GITHUB_REPO", "FGODailyBonus")
    if not token or not owner:
        LAST_ERROR = "缺少 GITHUB_TOKEN 或 GITHUB_OWNER（见 env.example）"
        if verbose:
            print("[ERR] " + LAST_ERROR)
        return False

    s = requests.Session()
    s.headers.update({
        "Authorization": "token " + token,
        "Accept": "application/vnd.github+json",
        "User-Agent": "fgo-heartbeat",
    })
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/heartbeat.txt"
    now = datetime.datetime.now().astimezone()
    text = (
        "FGODailyBonus heartbeat\n"
        f"time: {now:%Y-%m-%d %H:%M:%S %z}\n"
        "purpose: 用一次提交触发 GitHub Actions\n"
    )

    try:
        r = s.get(url, timeout=30)
        payload = {
            "message": f"heartbeat {now:%Y-%m-%d %H:%M}",
            "content": base64.b64encode(text.encode("utf-8")).decode(),
        }
        if r.status_code == 200:
            payload["sha"] = r.json()["sha"]

        p = s.put(url, json=payload, timeout=30)
        if p.status_code in (200, 201):
            if verbose:
                sha = p.json().get("commit", {}).get("sha", "")[:8]
                print(f"[OK] 心跳已推送 {now:%H:%M:%S}  commit {sha}")
            return True
        LAST_ERROR = f"HTTP {p.status_code}: {p.text[:150]}"
        if verbose:
            print("[ERR] " + LAST_ERROR)
        return False
    except Exception as ex:  # noqa: BLE001
        LAST_ERROR = f"{type(ex).__name__}: {ex}"
        if verbose:
            print("[ERR] " + LAST_ERROR)
        return False


if __name__ == "__main__":
    if "--check" in sys.argv:
        print("配置来源:", _env.ENV_FILE, "存在" if _env.CONF else "缺失")
        print("owner:", _env.get("GITHUB_OWNER"), "| repo:", _env.get("GITHUB_REPO"))
        print("token:", "已配置" if _env.get("GITHUB_TOKEN") else "未配置")
        sys.exit(0)
    sys.exit(0 if push() else 1)
