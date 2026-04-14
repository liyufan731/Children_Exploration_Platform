# database/dao/exploration_record_dao.py
import json
from database.dao.db import get_db
from datetime import datetime

def create_exploration_record(
    child_id: int,
    knowledge_id: int,
    exploration_type: str = None,
    engagement_score: int = None,
    duration_seconds: int = None,
    notes: str = None,
    completion_status: str = 'completed',
    selected_variant: int = None,
    interaction_data: dict = None,
    exploration_quality: float = None
) -> int:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO exploration_record 
        (child_id, knowledge_id, exploration_type, engagement_score, duration_seconds,
         notes, completion_status, selected_variant, interaction_data, exploration_quality)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        child_id, knowledge_id, exploration_type, engagement_score, duration_seconds,
        notes, completion_status, selected_variant,
        json.dumps(interaction_data) if interaction_data else None,
        exploration_quality
    ))
    conn.commit()
    record_id = cursor.lastrowid
    conn.close()
    return record_id

def get_records_by_child(child_id: int, limit: int = 50) -> list[dict]:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM exploration_record WHERE child_id = ? ORDER BY created_at DESC LIMIT ?",
        (child_id, limit)
    )
    rows = cursor.fetchall()
    conn.close()
    records = []
    for row in rows:
        rec = dict(row)
        if rec.get('interaction_data'):
            rec['interaction_data'] = json.loads(rec['interaction_data'])
        records.append(rec)
    return records

def get_exploration_stats(child_id: int) -> dict:
    """获取儿童探索统计"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT 
            COUNT(*) as total_count,
            SUM(duration_seconds) as total_duration,
            AVG(engagement_score) as avg_engagement,
            AVG(exploration_quality) as avg_quality
        FROM exploration_record 
        WHERE child_id = ?
    ''', (child_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            'total_count': row['total_count'] or 0,
            'total_duration': row['total_duration'] or 0,
            'avg_engagement': round(row['avg_engagement'] or 0, 2),
            'avg_quality': round(row['avg_quality'] or 0, 2)
        }
    return {'total_count': 0, 'total_duration': 0, 'avg_engagement': 0, 'avg_quality': 0}

# database/dao/exploration_record_dao.py 追加

def get_daily_exploration_stats(child_id: int, days: int = 30) -> list[dict]:
    """获取每日探索统计（用于趋势图）"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT 
            DATE(created_at) as date,
            COUNT(*) as count,
            AVG(engagement_score) as avg_engagement,
            SUM(duration_seconds) as total_duration
        FROM exploration_record 
        WHERE child_id = ? 
        AND created_at >= DATE('now', ?)
        GROUP BY DATE(created_at)
        ORDER BY date
    ''', (child_id, f'-{days} days'))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_activity_type_distribution(child_id: int) -> dict:
    """获取活动类型分布"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT exploration_type, COUNT(*) as count
        FROM exploration_record
        WHERE child_id = ?
        GROUP BY exploration_type
    ''', (child_id,))
    rows = cursor.fetchall()
    conn.close()
    return {row['exploration_type']: row['count'] for row in rows if row['exploration_type']}