# check_data.py
from database.dao.knowledge_node_dao import get_all_knowledge_nodes

nodes = get_all_knowledge_nodes()
print(f"knowledge_node 表中共有 {len(nodes)} 条活动记录")
if nodes:
    print("前3条活动：")
    for n in nodes[:3]:
        print(f"  - {n['name']} (年龄: {n.get('age_range')})")
else:
    print("⚠️ 表为空！请先运行 graph/knowledge_initializer.py 初始化 Neo4j，再运行 init_project.py 同步到 SQLite")