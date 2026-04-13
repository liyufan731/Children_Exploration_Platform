from database.dao.db import get_db
import json

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