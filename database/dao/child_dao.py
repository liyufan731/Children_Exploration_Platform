from database.dao.db import get_db
from datetime import datetime

def create_child(parent_id: int, name: str, age_range: str = None, avatar: str = None) -> int:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO child (parent_id, name, age_range, avatar) VALUES (?, ?, ?, ?)",
        (parent_id, name, age_range, avatar)
    )
    conn.commit()
    child_id = cursor.lastrowid
    conn.close()
    return child_id

def get_children_by_parent(parent_id: int) -> list[dict]:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM child WHERE parent_id = ?", (parent_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_child_by_id(child_id: int) -> dict | None:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM child WHERE id = ?", (child_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def update_last_exploration_time(child_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE child SET last_exploration_time = ? WHERE id = ?",
        (datetime.now().isoformat(), child_id)
    )
    conn.commit()
    conn.close()