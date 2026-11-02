# -*- coding: utf-8 -*-
"""把游戏内昵称转换成不可反推的匿名标识。

为什么需要这个模块
------------------
原实现直接用 `md5(name)` 当玩家标识，写进公开的日志仓库。MD5 是**无盐哈希**，
短昵称（两三个字）用字典几秒钟就能撞出来，等于把游戏名公开了。

现在的做法：加盐后再哈希。
  * 盐从哪来？环境变量 `NAME_SALT`（可选）；没配置时由 secretKey 派生。
  * 为什么用 secretKey 派生？secretKey 只存在 Secrets 里，外人拿不到，
    所以外人无法复现同样的哈希；同时又保证同一账号每天算出来一致，日志能对上。
  * 输出截断到 16 位十六进制，够用且短。
"""
import hashlib
import os

PREFIX = "fgo-namesalt-v1:"


def _salt(secret_key: str) -> str:
    salt = (os.environ.get("NAME_SALT") or "").strip()
    if salt:
        return salt
    return hashlib.sha256((PREFIX + str(secret_key)).encode("utf-8")).hexdigest()[:16]


def name_id(name: str, secret_key: str) -> str:
    """返回不可反推的玩家标识。"""
    salt = _salt(secret_key)
    return hashlib.sha256((salt + str(name)).encode("utf-8")).hexdigest()[:16]


if __name__ == "__main__":
    # 自测：同一个名字 + 同一个 secretKey 结果稳定，换 secretKey 结果变
    sample = name_id("テスト", "aaaa:bbbb")
    again = name_id("テスト", "aaaa:bbbb")
    other = name_id("テスト", "cccc:dddd")
    print(sample, again, other)
    assert sample == again, "同一账号应稳定"
    assert sample != other, "不同 secretKey 应不同"
    print("privacy self-test OK")
