from database.dao.db import get_db
from datetime import datetime


def update_familiarity(
        child_id: int,
        knowledge_id: int,
        familiarity_gain: float,
        practice_increment: int = 1
):
    """更新熟悉度，若记录不存在则创建"""
    conn = get_db()
    cursor = conn.cursor()

    # 尝试更新现有记录
    cursor.execute('''
                   UPDATE familiarity
                   SET familiarity_value = familiarity_value + ?,
                       practice_count    = practice_count + ?,
                       last_update_time  = ?
                   WHERE child_id = ?
                     AND knowledge_id = ?
                   ''', (familiarity_gain, practice_increment, datetime.now().isoformat(), child_id, knowledge_id))

    if cursor.rowcount == 0:
        # 不存在则插入
        cursor.execute('''
                       INSERT INTO familiarity (child_id, knowledge_id, familiarity_value, practice_count,
                                                last_update_time)
                       VALUES (?, ?, ?, ?, ?)
                       ''', (child_id, knowledge_id, familiarity_gain, practice_increment, datetime.now().isoformat()))

    conn.commit()
    conn.close()


def get_familiarity(child_id: int, knowledge_id: int) -> float:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT familiarity_value FROM familiarity WHERE child_id = ? AND knowledge_id = ?",
        (child_id, knowledge_id)
    )
    row = cursor.fetchone()
    conn.close()
    return row['familiarity_value'] if row else 0.0


def get_all_familiarities(child_id: int) -> dict[int, float]:
    """获取儿童所有活动的熟悉度，返回 {knowledge_id: familiarity_value} 字典"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT knowledge_id, familiarity_value FROM familiarity WHERE child_id = ?",
        (child_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    return {row['knowledge_id']: row['familiarity_value'] for row in rows}