#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""病人侧持久化存储 (闭环工程债清理)

为何不复用 delivery_database.py:
- 它属于"医嘱/扫码审计"领域, 表结构稳定不该改
- 病人 IM + override 是新的运营数据, 单独一个 SQLite 文件方便后期备份/清理

文件路径: /mnt/sdcard/medicine_robot_data/patient_state.db (默认, 可参数化)
线程安全: sqlite3.connect(check_same_thread=False) + 自带 _lock 串行化写
重启恢复: load_all_messages() / load_all_overrides() 把表内容灌回内存 deque/dict

不破坏现有 API:
- _append_message / _set_status_override 之外的代码完全不感知存储层存在
- 数据库故障时降级到 in-memory only (打 warn log)
"""

import os
import sqlite3
import threading
import time
from typing import Any, Dict, List, Optional


class PatientStateStore:
    """病人 IM + 取药状态 override 的持久化层。"""

    def __init__(
        self,
        db_path: str = "/mnt/sdcard/medicine_robot_data/patient_state.db",
        message_keep_days: int = 30,
        logger=None,
    ):
        self.db_path = db_path
        self.message_keep_days = max(1, int(message_keep_days))
        self._logger = logger
        self._lock = threading.Lock()
        self._ok = False
        try:
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            self.conn = sqlite3.connect(db_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row
            self._create_tables()
            self._purge_old_messages()
            self._ok = True
            self._log("info", f"patient_state_store ready @ {db_path}")
        except Exception as exc:
            self._log("warn", f"patient_state_store init failed: {exc} (fallback to memory-only)")
            self.conn = None

    # ---------- 工具 ----------

    def _log(self, level: str, msg: str):
        if self._logger is None:
            return
        try:
            getattr(self._logger, level, self._logger.info)(msg)
        except Exception:
            pass

    @property
    def ok(self) -> bool:
        return self._ok and self.conn is not None

    def _create_tables(self):
        cur = self.conn.cursor()
        # 病人 IM
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS patient_messages (
                id TEXT PRIMARY KEY,
                bed TEXT NOT NULL,
                sender TEXT NOT NULL,
                nurse_name TEXT DEFAULT '',
                content TEXT NOT NULL,
                delivery_id TEXT DEFAULT '',
                created_at REAL NOT NULL,
                read_by_patient INTEGER DEFAULT 0,
                read_by_nurse INTEGER DEFAULT 0
            )
            """
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_patient_messages_bed ON patient_messages(bed, created_at)"
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_patient_messages_created ON patient_messages(created_at)"
        )
        # 取药状态 override (病人确认/拒绝)
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS patient_status_overrides (
                bed TEXT PRIMARY KEY,
                status TEXT NOT NULL,
                reason TEXT DEFAULT '',
                delivery_id TEXT DEFAULT '',
                updated_at REAL NOT NULL
            )
            """
        )
        # 历史日志 (前 50 条)
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS patient_history_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                delivery_id TEXT,
                bed TEXT,
                date TEXT,
                drugs_summary TEXT,
                status TEXT,
                created_at REAL NOT NULL
            )
            """
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_history_created ON patient_history_log(created_at)"
        )
        self.conn.commit()

    def _purge_old_messages(self):
        """启动时清理 N 天前的旧 IM, 避免 db 无限膨胀。"""
        if self.conn is None:
            return
        cutoff = time.time() - self.message_keep_days * 86400
        try:
            cur = self.conn.cursor()
            cur.execute("DELETE FROM patient_messages WHERE created_at < ?", (cutoff,))
            cur.execute("DELETE FROM patient_history_log WHERE created_at < ?", (cutoff,))
            self.conn.commit()
        except Exception as exc:
            self._log("warn", f"purge_old_messages failed: {exc}")

    # ---------- 消息读写 ----------

    def insert_message(self, msg: Dict[str, Any]) -> bool:
        if not self.ok:
            return False
        with self._lock:
            try:
                cur = self.conn.cursor()
                cur.execute(
                    """
                    INSERT OR REPLACE INTO patient_messages
                    (id, bed, sender, nurse_name, content, delivery_id,
                     created_at, read_by_patient, read_by_nurse)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        msg.get("id"),
                        msg.get("bed", ""),
                        msg.get("sender", "patient"),
                        msg.get("nurse_name", ""),
                        msg.get("content", ""),
                        msg.get("delivery_id", ""),
                        float(msg.get("created_at") or time.time()),
                        1 if msg.get("read_by_patient") else 0,
                        1 if msg.get("read_by_nurse") else 0,
                    ),
                )
                self.conn.commit()
                return True
            except Exception as exc:
                self._log("warn", f"insert_message failed: {exc}")
                return False

    def mark_message_read(self, message_id: str, by_nurse: bool = True, read: bool = True) -> bool:
        if not self.ok:
            return False
        col = "read_by_nurse" if by_nurse else "read_by_patient"
        with self._lock:
            try:
                self.conn.execute(
                    f"UPDATE patient_messages SET {col} = ? WHERE id = ?",
                    (1 if read else 0, message_id),
                )
                self.conn.commit()
                return True
            except Exception as exc:
                self._log("warn", f"mark_message_read failed: {exc}")
                return False

    def mark_thread_read(self, bed: str, by_nurse: bool = True) -> bool:
        if not self.ok:
            return False
        col = "read_by_nurse" if by_nurse else "read_by_patient"
        with self._lock:
            try:
                if bed:
                    self.conn.execute(
                        f"UPDATE patient_messages SET {col} = 1 WHERE bed = ?",
                        (bed,),
                    )
                else:
                    self.conn.execute(f"UPDATE patient_messages SET {col} = 1")
                self.conn.commit()
                return True
            except Exception as exc:
                self._log("warn", f"mark_thread_read failed: {exc}")
                return False

    def load_all_messages(self, limit: int = 500) -> List[Dict[str, Any]]:
        """启动时回灌 deque 用; 按时间升序返回最近 limit 条。"""
        if not self.ok:
            return []
        try:
            cur = self.conn.cursor()
            cur.execute(
                """
                SELECT id, bed, sender, nurse_name, content, delivery_id,
                       created_at, read_by_patient, read_by_nurse
                FROM patient_messages
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (int(limit),),
            )
            rows = cur.fetchall()
        except Exception as exc:
            self._log("warn", f"load_all_messages failed: {exc}")
            return []
        out = []
        for r in reversed(rows):  # 改回升序, 让 deque 顺序与运行时一致
            out.append(
                {
                    "id": r["id"],
                    "bed": r["bed"],
                    "sender": r["sender"],
                    "nurse_name": r["nurse_name"] or "",
                    "content": r["content"],
                    "delivery_id": r["delivery_id"] or "",
                    "created_at": float(r["created_at"]),
                    "read_by_patient": bool(r["read_by_patient"]),
                    "read_by_nurse": bool(r["read_by_nurse"]),
                }
            )
        return out

    # ---------- override 读写 ----------

    def upsert_override(
        self,
        bed: str,
        status: str,
        reason: str = "",
        delivery_id: str = "",
    ) -> bool:
        if not self.ok or not bed:
            return False
        with self._lock:
            try:
                self.conn.execute(
                    """
                    INSERT OR REPLACE INTO patient_status_overrides
                    (bed, status, reason, delivery_id, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (bed, status, reason or "", delivery_id or "", time.time()),
                )
                self.conn.commit()
                return True
            except Exception as exc:
                self._log("warn", f"upsert_override failed: {exc}")
                return False

    def delete_override(self, bed: str) -> bool:
        if not self.ok or not bed:
            return False
        with self._lock:
            try:
                self.conn.execute(
                    "DELETE FROM patient_status_overrides WHERE bed = ?", (bed,)
                )
                self.conn.commit()
                return True
            except Exception as exc:
                self._log("warn", f"delete_override failed: {exc}")
                return False

    def load_all_overrides(self) -> Dict[str, Dict[str, Any]]:
        if not self.ok:
            return {}
        try:
            cur = self.conn.cursor()
            cur.execute(
                "SELECT bed, status, reason, delivery_id, updated_at FROM patient_status_overrides"
            )
            rows = cur.fetchall()
        except Exception as exc:
            self._log("warn", f"load_all_overrides failed: {exc}")
            return {}
        out = {}
        for r in rows:
            out[r["bed"]] = {
                "status": r["status"],
                "eta": None,
                "reason": r["reason"] or "",
                "delivery_id": r["delivery_id"] or "",
                "updated_at": float(r["updated_at"]),
            }
        return out

    # ---------- 历史日志 ----------

    def insert_history(self, entry: Dict[str, Any]) -> bool:
        if not self.ok:
            return False
        with self._lock:
            try:
                self.conn.execute(
                    """
                    INSERT INTO patient_history_log
                    (delivery_id, bed, date, drugs_summary, status, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        entry.get("delivery_id", ""),
                        entry.get("bed", ""),
                        entry.get("date", ""),
                        entry.get("drugs_summary", ""),
                        entry.get("status", ""),
                        time.time(),
                    ),
                )
                # 只留最近 50 条 (与 patient_http 现有上限一致)
                self.conn.execute(
                    """
                    DELETE FROM patient_history_log
                    WHERE id NOT IN (
                        SELECT id FROM patient_history_log
                        ORDER BY created_at DESC LIMIT 50
                    )
                    """
                )
                self.conn.commit()
                return True
            except Exception as exc:
                self._log("warn", f"insert_history failed: {exc}")
                return False

    def load_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        if not self.ok:
            return []
        try:
            cur = self.conn.cursor()
            cur.execute(
                """
                SELECT delivery_id, bed, date, drugs_summary, status
                FROM patient_history_log
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (int(limit),),
            )
            rows = cur.fetchall()
        except Exception as exc:
            self._log("warn", f"load_history failed: {exc}")
            return []
        return [
            {
                "delivery_id": r["delivery_id"] or "",
                "bed": r["bed"] or "",
                "date": r["date"] or "",
                "drugs_summary": r["drugs_summary"] or "",
                "status": r["status"] or "",
            }
            for r in rows
        ]

    def close(self):
        if self.conn is not None:
            try:
                self.conn.close()
            except Exception:
                pass
            self.conn = None
            self._ok = False


# 单元测试
if __name__ == "__main__":
    import tempfile

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
    tmp.close()
    db = PatientStateStore(db_path=tmp.name)
    assert db.ok, "store should be ok"

    # 消息
    msg = {
        "id": "msg-1",
        "bed": "A-01",
        "sender": "patient",
        "content": "肚子疼",
        "delivery_id": "DLV-1",
        "created_at": time.time(),
        "read_by_patient": True,
        "read_by_nurse": False,
    }
    assert db.insert_message(msg)
    rows = db.load_all_messages()
    assert len(rows) == 1
    assert rows[0]["content"] == "肚子疼"

    # override
    assert db.upsert_override("A-01", "confirmed", "", "DLV-1")
    ovr = db.load_all_overrides()
    assert ovr["A-01"]["status"] == "confirmed"

    # history
    assert db.insert_history(
        {"delivery_id": "DLV-1", "bed": "A-01", "date": "06/13 14:30",
         "drugs_summary": "病人确认收到", "status": "confirmed"}
    )
    h = db.load_history()
    assert len(h) == 1
    assert h[0]["bed"] == "A-01"

    db.close()
    os.unlink(tmp.name)
    print("PatientStateStore OK")
