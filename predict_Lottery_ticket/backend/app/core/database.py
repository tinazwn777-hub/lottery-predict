"""
数据库管理模块
使用SQLite存储历史开奖数据
"""
import sqlite3
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# 数据库路径
DB_PATH = Path(__file__).parent.parent.parent / "data" / "lottery.db"


class Database:
    """SQLite数据库管理"""

    def __init__(self, db_path: str = None):
        self.db_path = db_path or DB_PATH
        self._ensure_dir()
        self._init_db()

    def _ensure_dir(self):
        """确保数据库目录存在"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def _get_connection(self) -> sqlite3.Connection:
        """获取数据库连接"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """初始化数据库表"""
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS lottery_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    lottery_type TEXT NOT NULL,
                    issue TEXT NOT NULL,
                    red_balls TEXT NOT NULL,
                    blue_ball TEXT NOT NULL,
                    open_date TEXT,
                    created_at TEXT NOT NULL,
                    UNIQUE(lottery_type, issue)
                )
            """)

            # 创建索引
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_lottery_type_issue
                ON lottery_records(lottery_type, issue)
            """)

            # 创建用户预测表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS user_predictions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    lottery_type TEXT NOT NULL,
                    target_issue TEXT NOT NULL,
                    red_balls TEXT NOT NULL,
                    blue_balls TEXT NOT NULL,
                    method TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)

            # 如果 target_issue 列不存在，添加它（兼容旧数据库）
            try:
                conn.execute("""
                    ALTER TABLE user_predictions ADD COLUMN target_issue TEXT DEFAULT ''
                """)
            except:
                pass  # 列已存在

            conn.commit()
        logger.info(f"数据库初始化完成: {self.db_path}")

    def insert_records(self, records: List[Dict[str, Any]]) -> int:
        """
        批量插入开奖记录

        Args:
            records: 开奖记录列表

        Returns:
            插入数量
        """
        if not records:
            return 0

        count = 0
        with self._get_connection() as conn:
            for record in records:
                try:
                    conn.execute("""
                        INSERT OR REPLACE INTO lottery_records
                        (lottery_type, issue, red_balls, blue_ball, open_date, created_at)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        record["lottery_type"],
                        record["issue"],
                        record["red_balls"],
                        record["blue_ball"],
                        record.get("open_date", ""),
                        record.get("created_at", datetime.now().isoformat())
                    ))
                    count += 1
                except Exception as e:
                    logger.warning(f"插入记录失败: {e}")

            conn.commit()

        logger.info(f"成功插入 {count} 条记录")
        return count

    def get_history(
        self,
        lottery_type: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict]:
        """
        获取历史开奖记录

        Args:
            lottery_type: 彩种类型
            limit: 返回数量
            offset: 偏移量

        Returns:
            开奖记录列表
        """
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM lottery_records
                WHERE lottery_type = ?
                ORDER BY issue DESC
                LIMIT ? OFFSET ?
            """, (lottery_type, limit, offset))

            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def get_latest_issue(self, lottery_type: str) -> Optional[Dict]:
        """获取最新一期开奖记录"""
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM lottery_records
                WHERE lottery_type = ?
                ORDER BY issue DESC
                LIMIT 1
            """, (lottery_type,))

            row = cursor.fetchone()
            return dict(row) if row else None

    def get_issue(self, lottery_type: str, issue: str) -> Optional[Dict]:
        """获取指定期号的开奖记录"""
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM lottery_records
                WHERE lottery_type = ? AND issue = ?
            """, (lottery_type, issue))

            row = cursor.fetchone()
            return dict(row) if row else None

    def get_count(self, lottery_type: str) -> int:
        """获取指定彩种的记录总数"""
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT COUNT(*) FROM lottery_records
                WHERE lottery_type = ?
            """, (lottery_type,))
            return cursor.fetchone()[0]

    def clear(self, lottery_type: str) -> int:
        """清空指定彩种的所有记录"""
        with self._get_connection() as conn:
            cursor = conn.execute("""
                DELETE FROM lottery_records
                WHERE lottery_type = ?
            """, (lottery_type,))
            conn.commit()
            return cursor.rowcount

    # ========== 用户预测相关方法 ==========

    def save_prediction(self, prediction: Dict[str, Any]) -> int:
        """
        保存用户预测号码

        Args:
            prediction: 预测记录，包含 lottery_type, red_balls, blue_balls, method

        Returns:
            新记录ID
        """
        with self._get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO user_predictions
                (lottery_type, red_balls, blue_balls, method, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (
                prediction["lottery_type"],
                prediction["red_balls"],
                prediction["blue_balls"],
                prediction["method"],
                prediction.get("created_at", datetime.now().isoformat())
            ))
            conn.commit()
            return cursor.lastrowid

    def save_predictions(self, predictions: List[Dict[str, Any]]) -> int:
        """
        批量保存用户预测号码

        Args:
            predictions: 预测记录列表

        Returns:
            保存数量
        """
        if not predictions:
            return 0

        count = 0
        with self._get_connection() as conn:
            for prediction in predictions:
                try:
                    # 确保每个预测都有 lottery_type 和 target_issue
                    lottery_type = prediction.get("lottery_type")
                    target_issue = prediction.get("target_issue")
                    if not lottery_type:
                        logger.warning(f"保存预测失败: 缺少 lottery_type 字段")
                        continue
                    if not target_issue:
                        logger.warning(f"保存预测失败: 缺少 target_issue 字段")
                        continue

                    conn.execute("""
                        INSERT INTO user_predictions
                        (lottery_type, target_issue, red_balls, blue_balls, method, created_at)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        lottery_type,
                        target_issue,
                        prediction["red_balls"],
                        prediction["blue_balls"],
                        prediction["method"],
                        prediction.get("created_at", datetime.now().isoformat())
                    ))
                    count += 1
                except Exception as e:
                    logger.warning(f"保存预测失败: {e}")

            conn.commit()

        logger.info(f"成功保存 {count} 条预测")
        return count

    def get_predictions(self, lottery_type: str) -> List[Dict]:
        """
        获取用户预测记录

        Args:
            lottery_type: 彩种类型

        Returns:
            预测记录列表
        """
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM user_predictions
                WHERE lottery_type = ?
                ORDER BY created_at DESC, id DESC
            """, (lottery_type,))

            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def get_prediction_count(self, lottery_type: str) -> int:
        """获取指定彩种的预测记录总数"""
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT COUNT(*) FROM user_predictions
                WHERE lottery_type = ?
            """, (lottery_type,))
            return cursor.fetchone()[0]

    def clear_predictions(self, lottery_type: str) -> int:
        """清空指定彩种的所有预测记录"""
        with self._get_connection() as conn:
            cursor = conn.execute("""
                DELETE FROM user_predictions
                WHERE lottery_type = ?
            """, (lottery_type,))
            conn.commit()
            return cursor.rowcount


# 全局数据库实例
db = Database()


def get_db() -> Database:
    """获取数据库实例"""
    return db
