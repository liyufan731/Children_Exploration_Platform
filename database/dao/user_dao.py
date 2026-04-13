from database.dao.db import get_db
import hashlib

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def create_user(username: str, password: str, name: str = None, role: str = 'parent') -> int:
    """创建新用户，返回用户ID"""
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO user (username, password_hash, name, role) VALUES (?, ?, ?, ?)",
            (username, hash_password(password), name, role)
        )
        conn.commit()
        return cursor.lastrowid
    except sqlite3.IntegrityError:
        return -1  # 用户名已存在
    finally:
        conn.close()

def verify_user(username: str, password: str) -> dict | None:
    """验证用户登录，返回用户信息字典或None"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, username, name, role FROM user WHERE username = ? AND password_hash = ?",
        (username, hash_password(password))
    )
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_user_by_id(user_id: int) -> dict | None:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, name, role FROM user WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None