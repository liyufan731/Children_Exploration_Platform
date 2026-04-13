from database.dao.db import init_db
from database.dao.knowledge_node_dao import sync_knowledge_nodes_from_neo4j
from graph.graph_repository import get_all_activities

if __name__ == "__main__":
    print("1. 初始化 SQLite 表结构...")
    init_db()

    print("2. 从 Neo4j 同步活动数据到 SQLite...")
    activities = get_all_activities()
    sync_knowledge_nodes_from_neo4j(activities)
    print(f"同步完成，共 {len(activities)} 个活动。")

    print("项目初始化成功！")