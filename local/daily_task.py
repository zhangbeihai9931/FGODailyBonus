# -*- coding: utf-8 -*-
"""每日自动任务入口：先推心跳触发云端签到，失败则本地兜底。

由 Windows 计划任务调用，全程无人值守。
输出写到 logs/自动化记录.txt，出问题看这个文件。
"""
import datetime
import os
import runpy
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)          # 仓库根目录
sys.path.insert(0, ROOT)              # 让 main.py 里的 import 找得到
LOG_DIR = os.path.join(ROOT, "logs")
TRACE = os.path.join(LOG_DIR, "自动化记录.txt")

sys.path.insert(0, HERE)
import _env      # noqa: E402
import trigger   # noqa: E402


def trace(text):
    os.makedirs(LOG_DIR, exist_ok=True)
    with open(TRACE, "a", encoding="utf-8-sig") as f:
        f.write(f"{datetime.datetime.now():%Y-%m-%d %H:%M:%S}  {text}\n")


def run_local():
    """在本地直接执行 main.py。"""
    for k, v in _env.game_env().items():
        os.environ[k] = v
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    os.chdir(ROOT)
    runpy.run_path(os.path.join(ROOT, "main.py"), run_name="__main__")


def main():
    print(f"[{datetime.datetime.now():%H:%M:%S}] 每日自动任务开始")

    if trigger.push():
        trace("已推送心跳 -> 触发 GitHub Actions")
        print("[OK] 已触发云端签到")
        return 0

    trace(f"心跳推送失败（{trigger.LAST_ERROR}）-> 本地兜底")
    print("[WARN] 推送失败，改在本地签到")
    try:
        run_local()
        trace("本地兜底完成")
        return 0
    except Exception as ex:  # noqa: BLE001
        trace(f"本地兜底失败: {type(ex).__name__}: {ex}")
        print("[ERR] 本地签到失败:", ex)
        return 1


if __name__ == "__main__":
    sys.exit(main())
