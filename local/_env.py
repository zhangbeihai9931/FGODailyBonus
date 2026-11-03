# -*- coding: utf-8 -*-
"""读取配置：优先环境变量，其次同目录的 env.txt。

env.txt 里放个人凭证，已被 .gitignore 排除，不会提交。
兼容两种写法：
    KEY=VALUE
    KEY  VALUE      （和 Actions Secrets 的习惯一致）
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ENV_FILE = os.path.join(HERE, "env.txt")


def _parse(path):
    conf = {}
    with open(path, encoding="utf-8-sig") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                k, v = line.split("=", 1)
            else:
                parts = line.split(None, 1)
                if len(parts) != 2:
                    continue
                k, v = parts
            conf[k.strip()] = v.strip()
    return conf


def load():
    conf = {}
    if os.path.exists(ENV_FILE):
        conf.update(_parse(ENV_FILE))
    for k, v in os.environ.items():
        if v:
            conf.setdefault(k, v)
    return conf


CONF = load()


def get(key, default=""):
    return CONF.get(key, default)


def game_env():
    """返回 main.py 需要的环境变量字典。"""
    return {
        "userIds": get("GAME_USERIDS"),
        "authKeys": get("GAME_AUTHKEYS"),
        "secretKeys": get("GAME_SECRETKEYS"),
        "verCode": get("GAME_VERCODE"),
        "UserAgent": get("GAME_USERAGENT", "nullvalue"),
        "TGBotToken": get("TELEGRAM_BOT_TOKEN", "nullvalue"),
        "TGAdminId": get("TELEGRAM_ADMIN_ID", "nullvalue"),
        "GithubToken": get("GITHUB_TOKEN"),
        "GithubName": get("GITHUB_OWNER"),
    }
