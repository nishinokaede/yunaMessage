import json
from pathlib import Path
from typing import Any, Dict, List, Optional


CONFIG_DIR = Path("config")


class GroupConfig:
    def __init__(self, root_path: str, refresh_token: str, members: List[Dict[str, Any]]):
        self.root_path = root_path
        self.refresh_token = refresh_token
        self.members = members


def _load_json(path: Path) -> Optional[Dict[str, Any]]:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def load_group_configs() -> Dict[str, GroupConfig]:
    """加载 nogi/saku/hina 三个配置文件，如果存在则返回对应配置。"""
    configs: Dict[str, GroupConfig] = {}
    mapping = {
        "nogi": CONFIG_DIR / "nogiConfig.json",
        "saku": CONFIG_DIR / "sakuConfig.json",
        "hina": CONFIG_DIR / "hinaConfig.json",
    }

    for grp, path in mapping.items():
        data = _load_json(path)
        if not data:
            continue
        root_path = data.get("rootPath") or data.get("root_path") or "data/messages/"
        token = data.get("token") or data.get("refresh_token") or ""
        members = data.get("member") or data.get("members") or []
        configs[grp] = GroupConfig(root_path, token, members)

    return configs