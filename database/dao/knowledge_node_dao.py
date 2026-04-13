from database.dao.db import get_db
import json

def sync_knowledge_nodes_from_neo4j(activities: list[dict]):
    """
    从 Neo4j 获取的活动数据同步到 SQLite 的 knowledge_node 表
    activities: 从 Neo4j 查询返回的活动节点列表
    """
    conn = get_db()
    cursor = conn.cursor()
    for act in activities:
        cursor.execute('''
            INSERT OR REPLACE INTO knowledge_node 
            (graph_id, name, description, difficulty, age_range, activity_type, sensory_type, 
             interest_tags, prompt_text, materials, image_asset, domain_id, group_id, 
             duration_minutes, variants)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            act['id'],
            act.get('name'),
            act.get('description'),
            act.get('difficulty'),
            act.get('age_range'),
            act.get('activity_type'),
            act.get('sensory_type'),
            act.get('interest_tags'),
            act.get('prompt_text'),
            act.get('materials'),
            act.get('image_asset'),
            act.get('domain_id'),
            act.get('group_id'),
            act.get('duration_minutes'),
            json.dumps(act.get('variants', []))
        ))
    conn.commit()
    conn.close()

def get_all_knowledge_nodes() -> list[dict]:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM knowledge_node")
    rows = cursor.fetchall()
    conn.close()
    nodes = []
    for row in rows:
        node = dict(row)
        # 解析 JSON 字段
        if node.get('variants'):
            node['variants'] = json.loads(node['variants'])
        if node.get('interest_tags'):
            node['interest_tags'] = node['interest_tags'].split(',')
        nodes.append(node)
    return nodes

def get_knowledge_node_by_graph_id(graph_id: str) -> dict | None:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM knowledge_node WHERE graph_id = ?", (graph_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        node = dict(row)
        if node.get('variants'):
            node['variants'] = json.loads(node['variants'])
        if node.get('interest_tags'):
            node['interest_tags'] = node['interest_tags'].split(',')
        return node
    return None