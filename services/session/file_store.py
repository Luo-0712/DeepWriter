"""
文件存储实现

使用 JSON 文件持久化 Session 数据。
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from services.session.base import Session, SessionStore


class FileSessionStore(SessionStore):
    """
    基于文件的 Session 存储实现

    使用 JSON 格式保存 Session 数据到本地文件系统。
    """

    def __init__(self, storage_dir: Optional[str] = None):
        """
        初始化文件存储

        Args:
            storage_dir: 存储目录，默认为 ./data/sessions
        """
        self.storage_dir = Path(storage_dir) if storage_dir else Path(__file__).parent.parent.parent / "data" / "sessions"
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def _get_file_path(self, session_id: str) -> Path:
        """获取 Session 文件路径"""
        return self.storage_dir / f"{session_id}.json"

    def save(self, session: Session) -> None:
        """保存 Session 到文件"""
        file_path = self._get_file_path(session.session_id)
        session.updated_at = datetime.now()
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(session.to_dict(), f, ensure_ascii=False, indent=2, default=str)

    def load(self, session_id: str) -> Optional[Session]:
        """从文件加载 Session"""
        file_path = self._get_file_path(session_id)
        if not file_path.exists():
            return None
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return Session.from_dict(data)

    def delete(self, session_id: str) -> None:
        """删除 Session 文件"""
        file_path = self._get_file_path(session_id)
        if file_path.exists():
            file_path.unlink()

    def list_sessions(self) -> list[str]:
        """列出所有 Session ID"""
        session_ids = []
        for file_path in self.storage_dir.glob("*.json"):
            session_ids.append(file_path.stem)
        return session_ids

    def clear(self) -> None:
        """清空所有 Session"""
        for file_path in self.storage_dir.glob("*.json"):
            file_path.unlink()

    def get_session_count(self) -> int:
        """获取 Session 数量"""
        return len(list(self.storage_dir.glob("*.json")))
