import requests
from ..db import get_db
from ..config_loader import load_group_configs


HEADERS_MAP = {
    "nogi": {
        "X-Talk-App-ID": "jp.co.sonymusic.communication.nogizaka 2.4",
        "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 6.0; Samsung Galaxy S7 for keyaki messages Build/MRA58K)",
    },
    "saku": {
        "X-Talk-App-ID": "jp.co.sonymusic.communication.sakurazaka 2.4",
        "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 6.0; Samsung Galaxy S7 for keyaki messages Build/MRA58K)",
    },
    "hina": {
        "X-Talk-App-ID": "jp.co.sonymusic.communication.keyakizaka 2.4",
        "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 6.0; Samsung Galaxy S7 for keyaki messages Build/MRA58K)",
    },
}

TOKEN_URL = {
    "nogi": "https://api.n46.glastonr.net/v2/update_token",
    "saku": "https://api.s46.glastonr.net/v2/update_token",
    "hina": "https://api.kh.glastonr.net/v2/update_token",
}


def run_gettoken() -> dict:
    """从远程API更新各组的临时token，并保存到数据库。"""
    db = get_db()
    configs = load_group_configs()
    results = {}

    for grp, cfg in configs.items():
        url = TOKEN_URL.get(grp)
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Accept-Language": "ja-JP",
            "Accept-Encoding": "gzip",
            "TE": "gzip, deflate; q=0.5",
            **HEADERS_MAP.get(grp, {}),
        }
        payload = {"refresh_token": cfg.refresh_token}
        try:
            r = requests.post(url, json=payload, headers=headers, timeout=20)
            r.raise_for_status()
            data = r.json()
            access_token = data.get("access_token")
            if access_token:
                db.save_token(access_token, grp=grp)
                results[grp] = {"ok": True, "access_token": access_token}
            else:
                results[grp] = {"ok": False, "error": "no access_token in response"}
        except Exception as ex:
            results[grp] = {"ok": False, "error": str(ex)}

    return {"groups": results}