import sqlite3
from datetime import datetime
from typing import List, Dict, Any
from pathlib import Path

from .config import DB_PATH


class Database:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row

    def init_db(self):
        cur = self.conn.cursor()
        # 保存每次请求的 token（增加group字段）
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                token TEXT NOT NULL,
                grp TEXT,
                created_at TEXT NOT NULL
            );
            """
        )

        # 消息：文字消息内容也保存在数据库；图片/语音/视频保存文件路径在数据库
        # 增加分组与成员信息，便于查询
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_type TEXT NOT NULL, -- text | image | audio | video
                text_content TEXT,          -- 仅文字消息使用
                file_path TEXT,             -- 非文字消息保存路径
                grp TEXT,                   -- 组：nogi | saku | hina
                member_id TEXT,
                member_name TEXT,
                msg_id TEXT,
                published_at TEXT,          -- 消息发布时间：yyyyMMddHHmmss
                created_at TEXT NOT NULL
            );
            """
        )
        # 兼容旧库：如果缺少列则动态添加
        try:
            info = cur.execute("PRAGMA table_info(messages)").fetchall()
            cols = {row[1] for row in info}
            if "msg_id" not in cols:
                cur.execute("ALTER TABLE messages ADD COLUMN msg_id TEXT")
            if "published_at" not in cols:
                cur.execute("ALTER TABLE messages ADD COLUMN published_at TEXT")
        except Exception:
            pass
        # 为 msg_id 建唯一索引，确保同一消息仅一条记录
        try:
            cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_messages_msg_id ON messages(msg_id)")
        except Exception:
            pass
        self.conn.commit()

    def save_token(self, token: str, grp: str | None = None) -> int:
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO tokens(token, grp, created_at) VALUES (?, ?, ?)",
            (token, grp, datetime.utcnow().isoformat()),
        )
        self.conn.commit()
        return cur.lastrowid

    def save_text_message(
        self,
        text: str,
        file_path: str | None = None,
        grp: str | None = None,
        member_id: str | None = None,
        member_name: str | None = None,
        msg_id: str | None = None,
    ) -> int:
        cur = self.conn.cursor()
        cur.execute(
            """
            INSERT INTO messages(message_type, text_content, file_path, created_at)
            VALUES (?, ?, ?, ?)
            """,
            ("text", text, file_path, datetime.utcnow().isoformat()),
        )
        # 更新新增列（为保持兼容，使用UPDATE填充）
        cur.execute(
            "UPDATE messages SET grp = ?, member_id = ?, member_name = ?, msg_id = ? WHERE id = last_insert_rowid()",
            (grp, member_id, member_name, msg_id),
        )
        self.conn.commit()
        return cur.lastrowid

    def save_media_message(
        self,
        media_type: str,
        file_path: str,
        grp: str | None = None,
        member_id: str | None = None,
        member_name: str | None = None,
        msg_id: str | None = None,
    ) -> int:
        cur = self.conn.cursor()
        cur.execute(
            """
            INSERT INTO messages(message_type, text_content, file_path, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (media_type, None, file_path, datetime.utcnow().isoformat()),
        )
        cur.execute(
            "UPDATE messages SET grp = ?, member_id = ?, member_name = ?, msg_id = ? WHERE id = last_insert_rowid()",
            (grp, member_id, member_name, msg_id),
        )
        self.conn.commit()
        return cur.lastrowid

    def upsert_message(
        self,
        msg_id: str,
        msg_type: str,
        text_content: str | None = None,
        file_path: str | None = None,
        grp: str | None = None,
        member_id: str | None = None,
        member_name: str | None = None,
        published_at: str | None = None,
    ) -> None:
        cur = self.conn.cursor()
        cur.execute(
            """
            INSERT INTO messages (msg_id, message_type, text_content, file_path, grp, member_id, member_name, created_at, published_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(msg_id) DO UPDATE SET
              -- 如果这次有文件，则以这次的类型为准；否则保留原类型
              message_type = CASE WHEN excluded.file_path IS NOT NULL AND excluded.file_path <> '' THEN excluded.message_type ELSE messages.message_type END,
              -- 文本内容：优先使用非空的新值，否则保留原值，避免被空覆盖
              text_content = COALESCE(NULLIF(excluded.text_content, ''), messages.text_content),
              -- 文件路径：如果这次有文件则更新，否则保留原值
              file_path = COALESCE(NULLIF(excluded.file_path, ''), messages.file_path),
              -- 其余字段优先新值，否则保留原值
              grp = COALESCE(NULLIF(excluded.grp, ''), messages.grp),
              member_id = COALESCE(NULLIF(excluded.member_id, ''), messages.member_id),
              member_name = COALESCE(NULLIF(excluded.member_name, ''), messages.member_name),
              published_at = COALESCE(NULLIF(excluded.published_at, ''), messages.published_at)
            """,
            (
                msg_id,
                msg_type,
                text_content,
                file_path,
                grp,
                member_id,
                member_name,
                datetime.utcnow().isoformat(),
                published_at,
            ),
        )
        self.conn.commit()

    def list_messages(self, limit: int = 100, offset: int = 0, msg_id: str | None = None) -> List[Dict[str, Any]]:
        cur = self.conn.cursor()
        if msg_id:
            cur.execute(
                "SELECT * FROM messages WHERE msg_id = ? ORDER BY msg_id ASC LIMIT ? OFFSET ?",
                (msg_id, limit, offset),
            )
        else:
            cur.execute(
                "SELECT * FROM messages ORDER BY msg_id ASC LIMIT ? OFFSET ?",
                (limit, offset),
            )
        rows = cur.fetchall()
        return [dict(r) for r in rows]


_db: Database | None = None


def get_db() -> Database:
    global _db
    if _db is None:
        _db = Database(DB_PATH)
        _db.init_db()
    return _db