import json
import binascii
import base64
import os
import re
import requests
import mytime
import CatAndMouseGame

requests.urllib3.disable_warnings()
session = requests.Session()
session.verify = False

# ===== Game's parameters =====
app_ver_ = ''
data_ver_ = 0
date_ver_ = 0
ver_code_ = ''
asset_bundle_folder_ = ''
data_server_folder_crc_ = 0
server_addr_ = 'https://game.fate-go.jp'
github_token_ = ''
github_name_ = ''
user_agent_ = 'Dalvik/2.1.0 (Linux; U; Android 11; Pixel 5 Build/RD1A.201105.003.A1)'


# ==== User Info ====
CONF_CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cfg.json')


def _read_conf_remote():
    """读远端 cfg.json：先走带 token 的 API（支持私有日志仓库），再退回 raw 地址。"""
    if github_token_:
        try:
            res = requests.get(
                f'https://api.github.com/repos/{github_name_}/FGODailyBonusLog/contents/cfg.json',
                headers={
                    'Authorization': 'token ' + github_token_,
                    'User-Agent': f'{github_name_}_bot',
                    'Accept': 'application/vnd.github+json',
                },
                timeout=20,
            )
            if res.status_code == 200:
                payload = res.json()
                return json.loads(base64.b64decode(payload['content']).decode('utf-8'))
            print(f'[cfg] GitHub API 返回 {res.status_code}，改用 raw 地址')
        except Exception as ex:
            print(f'[cfg] GitHub API 读取失败：{ex}')

    try:
        res = requests.get(
            f'https://raw.githubusercontent.com/{github_name_}/FGODailyBonusLog/main/cfg.json',
            verify=False, timeout=20,
        )
        return json.loads(res.text)
    except Exception as ex:
        print(f'[cfg] raw 地址读取失败：{ex}')
        return None


def ReadConf():
    global app_ver_, data_ver_, date_ver_, asset_bundle_folder_, data_server_folder_crc_
    data = _read_conf_remote()

    if data and 'global' in data:
        try:
            with open(CONF_CACHE, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except OSError:
            pass
        print(f'[cfg] 远端读取成功并缓存: appVer={data["global"]["appVer"]}')
    else:
        print('[cfg] 远端不可用，改用本地缓存')
        with open(CONF_CACHE, encoding='utf-8') as f:
            data = json.load(f)
        print(f'[cfg] 本地缓存: appVer={data["global"]["appVer"]} dataVer={data["global"]["dataVer"]}')

    app_ver_ = data['global']['appVer']
    data_ver_ = data['global']['dataVer']
    date_ver_ = data['global']['dateVer']
    asset_bundle_folder_ = data['global']['assetbundleFolder']
    data_server_folder_crc_ = data['global']['dataServerFolderCrc']


def WriteConf(data):
    UploadFileToRepo('cfg.json', data, 'update config')


def UpdateBundleFolder(assetbundle):
    new_assetbundle = CatAndMouseGame.MouseInfoMsgPack(base64.b64decode(assetbundle))
    print(f'new_assetbundle: {new_assetbundle}')
    global asset_bundle_folder_, data_server_folder_crc_
    asset_bundle_folder_ = new_assetbundle
    data_server_folder_crc_ = binascii.crc32(new_assetbundle.encode('utf8'))
    return 1


def UpdateAppVer(detail):
    matchObj = re.match('.*新ver.：(.*)、現.*', detail)
    if matchObj:
        global app_ver_
        app_ver_ = matchObj.group(1)
        print(f'new version: {app_ver_}')
    else:
        print('No matches')
        raise Exception('update app ver failed')


# ===== End =====

# ===== Telegram arguments =====
TelegramBotToken = ''
TelegramAdminId = ''


def SendMessageToAdmin(message):
    if TelegramBotToken != 'nullvalue':
        nowtime = mytime.GetFormattedNowTime()
        url = f'https://api.telegram.org/bot{TelegramBotToken}/sendMessage'
        payload = {
            'chat_id': TelegramAdminId,
            'parse_mode': 'markdown',
            'text': f'_{nowtime}_\n{message}',
        }
        try:
            result = requests.post(url, data=payload, verify=False, timeout=30).json()
            if not result.get('ok'):
                # 消息里的下划线/反引号可能破坏 markdown 解析，退化成纯文本重发一次
                payload.pop('parse_mode', None)
                result = requests.post(url, data=payload, verify=False, timeout=30).json()
                if not result.get('ok'):
                    print(result)
                    print(message)
        except Exception as ex:
            print(f'Telegram send failed: {ex}')
            print(message)


# ===== End =====


# ===== Github api =====
def UploadFileToRepo(filename, content, commit='updated'):
    url = f'https://api.github.com/repos/{github_name_}/FGODailyBonusLog/contents/' + filename
    header = {
        'Content-Type': 'application/json',
        'User-Agent': f'{github_name_}_bot',
        'Authorization': 'token ' + github_token_,
    }
    # 取已有文件的 sha（必须带鉴权，否则匿名请求会被限流）
    jobject = {}
    try:
        jobject = requests.get(url=url, headers=header, timeout=30).json()
    except Exception:
        jobject = {}
    content = str(base64.b64encode(content.encode('utf-8')), 'utf-8')
    form = {
        'message': commit,
        'committer': {
            'name': f'{github_name_}_bot',
            'email': 'none@none.none'
        },
        'content': content,
    }
    if isinstance(jobject, dict) and 'sha' in jobject:
        form['sha'] = jobject['sha']
    form = json.dumps(form)
    try:
        result = requests.put(url, data=form, headers=header, timeout=30)
    except Exception as ex:
        print(f'[日志] GitHub 同步失败：{ex}（本地日志已保存，不影响签到）')
        return
    if result.status_code in (200, 201):
        print('[日志] 已同步到 GitHub')
    else:
        print(f'[日志] GitHub 同步失败（HTTP {result.status_code}），本地日志已保存，不影响签到')


# ===== End =====

httpheader = {
    'Accept-Encoding': 'gzip, identity',
    'User-Agent': user_agent_,
    'Content-Type': 'application/x-www-form-urlencoded',
    'Connection': 'Keep-Alive, TE',
    'TE': 'identity',
}


def NewSession():
    return requests.Session()


def PostReq(s, url, data):
    res = s.post(url, data=data, headers=httpheader, verify=False).json()
    res_code = res['response'][0]['resCode']
    if res_code != '00':
        detail = res['response'][0]['fail']['detail']
        message = f'[ErrorCode: {res_code}]\n{detail}'
        SendMessageToAdmin(message)
        raise Exception(message)
    return res


def gameData():
    global app_ver_, data_ver_, date_ver_
    data = requests.get(
        f'{server_addr_}/gamedata/top?appVer={app_ver_}&dataVer={data_ver_}&dateVer={date_ver_}', verify=False
    ).json()

    if 'action' in data['response'][0]['fail'] and data['response'][0]['fail']['action'] == 'app_version_up':
        UpdateAppVer(data['response'][0]['fail']['detail'].replace('\r\n', ''))
        gameData()
        return

    if (
        data['response'][0]['success']['dateVer'] != date_ver_
        or data['response'][0]['success']['dataVer'] != data_ver_
    ):
        s = '*Need update*\n'
        s += f'appVer: {app_ver_}\n'
        s += f'dateVer: {date_ver_} Server: {data["response"][0]["success"]["dateVer"]}\n'
        s += f'dataVer: {data_ver_} Server: {data["response"][0]["success"]["dataVer"]}'
        SendMessageToAdmin(s)

        val = UpdateBundleFolder(data['response'][0]['success']['assetbundle'])
        if val == 1:
            data_ver_ = data['response'][0]['success']['dataVer']
            date_ver_ = data['response'][0]['success']['dateVer']
            new_data = {}
            new_data['global'] = {
                'appVer': app_ver_,
                'assetbundleFolder': asset_bundle_folder_,
                'dataServerFolderCrc': data_server_folder_crc_,
                'dataVer': data_ver_,
                'dateVer': date_ver_,
            }
            WriteConf(json.dumps(new_data))
        else:
            SendMessageToAdmin('Update failed')
