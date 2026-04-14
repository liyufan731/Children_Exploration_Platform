# database/dao/child_interests_dao.py
from database.dao.db import get_db
from datetime import datetime


def update_child_interest(
        child_id: int,
        interest_tag: str,
        engagement_score: int = 3
):
    """更新或创建儿童兴趣记录"""
    conn = get_db()
    cursor = conn.cursor()

    # 尝试更新
    cursor.execute('''
                   UPDATE child_interests
                   SET exploration_count = exploration_count + 1,
                       avg_engagement    = (avg_engagement * exploration_count + ?) / (exploration_count + 1),
                       last_explored     = ?,
                       preference_level  = CASE
                                               WHEN avg_engagement >= 4.5 THEN '非常喜欢'
                                               WHEN avg_engagement >= 3.5 THEN '比较喜欢'
                                               ELSE '感兴趣'
                           END
                   WHERE child_id = ?
                     AND interest_tag = ?
                   ''', (engagement_score, datetime.now().isoformat(), child_id, interest_tag))

    if cursor.rowcount == 0:
        cursor.execute('''
                       INSERT INTO child_interests
                       (child_id, interest_tag, exploration_count, avg_engagement, last_explored, preference_level)
                       VALUES (?, ?, 1, ?, ?, ?)
                       ''', (child_id, interest_tag, engagement_score, datetime.now().isoformat(),
                             '非常喜欢' if engagement_score >= 4.5 else '比较喜欢' if engagement_score >= 3.5 else '感兴趣'))

    conn.commit()
    conn.close()


def get_child_interests(child_id: int) -> list[dict]:
    """获取儿童的兴趣标签及偏好"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
                   SELECT interest_tag, exploration_count, avg_engagement, preference_level
                   FROM child_interests
                   WHERE child_id = ?
                   ORDER BY exploration_count DESC, avg_engagement DESC
                   ''', (child_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]