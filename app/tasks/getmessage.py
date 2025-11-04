import requests
from datetime import datetime
from pathlib import Path
from typing import Optional

from ..db import get_db
from ..config_loader import load_group_configs


HEADERS_MAP = {
    "nogi": {
        "X-Talk-App-ID": "jp.co.sonymusic.communication.nogizaka 2.4",
        "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 6.0; Samsung Galaxy S7 for keyaki messages Build/MRA58K)",
    },
    "saku": {
        "X-Talk-App-ID": "jp.co.sonymusic.communication.nogizaka 2.4",
        "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 6.0; Samsung Galaxy S7 for keyaki messages Build/MRA58K)",
    },
    "hina": {
        "X-Talk-App-ID": "jp.co.sonymusic.communication.nogizaka 2.4",
        "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 6.0; Samsung Galaxy S7 for keyaki messages Build/MRA58K)",
    },
}

BASE_URL = {
    "nogi": "https://api.n46.glastonr.net",
    "saku": "https://api.s46.glastonr.net",
    "hina": "https://api.kh.glastonr.net",
}


def _ensure_dir(path: Path):
    path.mkdir(parents=True, exist_ok=True)


def _latest_file_timestamp(dir_path: Path) -> Optional[str]:
    """返回最近文件名中的发布时间（yyyyMMddHHmmss）；不存在则返回None。"""
    if not dir_path.exists():
        return None
    files = [p for p in dir_path.iterdir() if p.is_file() and p.suffix in {".txt", ".mp4", ".jpg", ".m4a"}]
    if not files:
        return None
    latest = max(files, key=lambda p: p.stat().st_ctime)
    # 期望文件名格式：{id}_{typeIndex}_{publishedAt}{ext}
    try:
        name_no_ext = latest.stem  # 去掉扩展名
        parts = name_no_ext.split("_")
        if len(parts) >= 3:
            timestamp = parts[2][:14]
            return timestamp
    except Exception:
        return None
    return None


def _save_text(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def run_getmessage() -> dict:
    """调用远程API拉取消息，按配置成员与命名规则保存到各自目录，并写入数据库。"""
    print("开始更新所有组的消息")
    db = get_db()
    configs = load_group_configs()
    result = {"processed": 0, "items": []}

    # 需要授权的token从数据库最新一条读取（按组）
    # 如果需要更复杂的token管理，可扩展为缓存或单独表。
    for grp, cfg in configs.items():
        headers_base = {
            "Accept": "application/json",
            "Accept-Language": "ja-JP",
            "Accept-Encoding": "gzip",
            "TE": "gzip, deflate; q=0.5",
            **HEADERS_MAP.get(grp, {}),
        }

        # 遍历成员
        for mem in cfg.members:
            member_id = str(mem.get("id"))
            member_name = str(mem.get("name"))
            member_dir = Path(cfg.root_path) / member_name
            _ensure_dir(member_dir)
            # 如目录为空，创建占位文本（与C#一致）
            if not any(member_dir.iterdir()):
                placeholder = member_dir / f"0_0_{datetime.utcnow().strftime('%Y%m%d')}000000.txt"
                _save_text(placeholder, "DON'T DELETE ME！")

            latest_ts = _latest_file_timestamp(member_dir)
            if latest_ts is None:
                # 默认当天零点
                latest_ts = datetime.utcnow().strftime("%Y%m%d") + "000000"
            # 转换为 created_from=YYYY-MM-DDTHH:mm:ssZ
            created_from = datetime.strptime(latest_ts, "%Y%m%d%H%M%S").strftime("%Y-%m-%dT%H:%M:%SZ")

            url = f"{BASE_URL[grp]}/v2/groups/{member_id}/timeline?count=100&order=asc&created_from={requests.utils.quote(created_from, safe='') }"

            # 取最近token作为授权（如果没有则跳过该组成员）
            # 简化：直接读取最新token
            token_row = db.conn.execute(
                "SELECT token FROM tokens WHERE grp = ? ORDER BY id DESC LIMIT 1",
                (grp,),
            ).fetchone()
            if not token_row:
                continue
            access_token = token_row[0]
            headers = {**headers_base, "Authorization": f"Bearer {access_token}"}

            try:
                r = requests.get(url, headers=headers, timeout=30)
                r.raise_for_status()
                data = r.json()
                messages = data.get("messages") or []
                if not messages:
                    continue

                for ep in messages:
                    if ep.get("state") != "published":
                        continue
                    # published_at 格式调整为 yyyyMMddHHmmss
                    published_at = (
                        str(ep.get("published_at", ""))
                        .replace("-", "")
                        .replace(":", "")
                        .replace("T", "")
                        .replace("Z", "")
                    )
                    msg_id = str(ep.get("id"))
                    msg_type = str(ep.get("type"))
                    text_content = ep.get("text") or ""
                    file_url = ep.get("file")

                    # 命名与C#保持一致
                    if msg_type == "picture":
                        name = f"{msg_id}_1_{published_at}"
                        # 文本
                        _save_text(member_dir / f"{name}.txt", text_content)
                        # 图片下载
                        if file_url:
                            img_path = member_dir / f"{name}.jpg"
                            resp = requests.get(file_url, timeout=60)
                            resp.raise_for_status()
                            img_path.write_bytes(resp.content)
                            file_path_db = str(img_path)
                        else:
                            file_path_db = None
                        # 合并为一条记录（图片消息可能同时拥有文本与文件）
                        db.upsert_message(
                            msg_id=msg_id,
                            msg_type="image",
                            text_content=text_content,
                            file_path=file_path_db,
                            grp=grp,
                            member_id=member_id,
                            member_name=member_name,
                            published_at=published_at,
                        )

                    elif msg_type == "text":
                        name = f"{msg_id}_0_{published_at}.txt"
                        path = member_dir / name
                        _save_text(path, text_content)
                        db.upsert_message(
                            msg_id=msg_id,
                            msg_type="text",
                            text_content=text_content,
                            file_path=None,  # 文本消息不记录文件路径
                            grp=grp,
                            member_id=member_id,
                            member_name=member_name,
                            published_at=published_at,
                        )

                    elif msg_type == "voice":
                        name = f"{msg_id}_3_{published_at}.m4a"
                        if file_url:
                            path = member_dir / name
                            resp = requests.get(file_url, timeout=120)
                            resp.raise_for_status()
                            path.write_bytes(resp.content)
                            file_path_db = str(path)
                        else:
                            file_path_db = None
                        db.upsert_message(
                            msg_id=msg_id,
                            msg_type="audio",
                            text_content=text_content or None,
                            file_path=file_path_db,
                            grp=grp,
                            member_id=member_id,
                            member_name=member_name,
                            published_at=published_at,
                        )

                    elif msg_type == "video":
                        name = f"{msg_id}_2_{published_at}.mp4"
                        if file_url:
                            path = member_dir / name
                            resp = requests.get(file_url, timeout=180)
                            resp.raise_for_status()
                            path.write_bytes(resp.content)
                            file_path_db = str(path)
                        else:
                            file_path_db = None
                        db.upsert_message(
                            msg_id=msg_id,
                            msg_type="video",
                            text_content=text_content or None,
                            file_path=file_path_db,
                            grp=grp,
                            member_id=member_id,
                            member_name=member_name,
                            published_at=published_at,
                        )

                    result["processed"] += 1
                    result["items"].append({
                        "grp": grp,
                        "member": member_name,
                        "id": msg_id,
                        "type": msg_type,
                        "published_at": published_at,
                    })
            except Exception:
                # 柔性跳过个别成员错误
                continue
    print("更新所有组的消息完成")
    return result