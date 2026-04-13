import sqlite3
from config.settings import DATABASE_PATH

def get_db():
    """获取数据库连接，启用外键约束"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row  # 返回字典形式的行
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    """初始化数据库表结构"""
    conn = get_db()
    cursor = conn.cursor()

    # 1. 用户表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            name TEXT,
            role TEXT DEFAULT 'parent',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 2. 儿童表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS child (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            parent_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            age_range TEXT,
            avatar TEXT,
            last_exploration_time TIMESTAMP,
            FOREIGN KEY (parent_id) REFERENCES user(id)
        )
    ''')

    # 3. 知识节点表（活动缓存表，从Neo4j同步过来）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS knowledge_node (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            graph_id TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            category TEXT,
            difficulty INTEGER DEFAULT 1,
            weight REAL DEFAULT 1.0,
            is_core INTEGER DEFAULT 0,
            description TEXT,
            mastery_threshold REAL DEFAULT 0.8,
            age_range TEXT,
            activity_type TEXT,
            sensory_type TEXT,
            interest_tags TEXT,
            prompt_text TEXT,
            materials TEXT,
            image_asset TEXT,
            domain_id TEXT,
            group_id TEXT,
            duration_minutes INTEGER,
            variants TEXT
        )
    ''')

    # 4. 探索记录表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS exploration_record (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            child_id INTEGER NOT NULL,
            knowledge_id INTEGER NOT NULL,
            exploration_type TEXT,
            engagement_score INTEGER,
            duration_seconds INTEGER,
            notes TEXT,
            completion_status TEXT,
            selected_variant INTEGER,
            interaction_data TEXT,
            exploration_quality REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (child_id) REFERENCES child(id),
            FOREIGN KEY (knowledge_id) REFERENCES knowledge_node(id)
        )
    ''')

    # 5. 熟悉度表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS familiarity (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            child_id INTEGER NOT NULL,
            knowledge_id INTEGER NOT NULL,
            familiarity_value REAL DEFAULT 0.0,
            practice_count INTEGER DEFAULT 0,
            last_update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(child_id, knowledge_id),
            FOREIGN KEY (child_id) REFERENCES child(id),
            FOREIGN KEY (knowledge_id) REFERENCES knowledge_node(id)
        )
    ''')

    # 6. 儿童兴趣表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS child_interests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            child_id INTEGER NOT NULL,
            interest_tag TEXT NOT NULL,
            exploration_count INTEGER DEFAULT 0,
            avg_engagement REAL DEFAULT 0.0,
            last_explored TIMESTAMP,
            preference_level TEXT,
            UNIQUE(child_id, interest_tag),
            FOREIGN KEY (child_id) REFERENCES child(id)
        )
    ''')

    # 7. 探索路径表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS exploration_path (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            child_id INTEGER NOT NULL,
            path_sequence TEXT,
            theme_name TEXT,
            start_time TIMESTAMP,
            end_time TIMESTAMP,
            total_duration INTEGER,
            engagement_score REAL,
            FOREIGN KEY (child_id) REFERENCES child(id)
        )
    ''')

    conn.commit()
    conn.close()
    print("SQLite 数据库初始化完成！")

if __name__ == "__main__":
    init_db()