# graph/knowledge_initializer.py
import json
from neo4j import GraphDatabase
from config.settings import NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD, BASE_DIR
import os


class KnowledgeGraphInitializer:
    def __init__(self):
        self.driver = GraphDatabase.driver(
            NEO4J_URI,
            auth=(NEO4J_USERNAME, NEO4J_PASSWORD)
        )

    def close(self):
        self.driver.close()

    def clear_all(self):
        """清空数据库（慎用，仅用于重新初始化）"""
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
        print("已清空 Neo4j 所有数据")

    def init_from_json(self, json_path: str):
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        activities = data.get('activities', [])
        relations = data.get('relations', [])

        with self.driver.session() as session:
            # 1. 创建 Activity 节点
            for act in activities:
                # 将列表字段转为逗号分隔字符串（Neo4j 存储友好）
                interest_tags = act.get('interest_tags', [])
                if isinstance(interest_tags, list):
                    interest_tags = ','.join(interest_tags)
                materials = act.get('materials', [])
                if isinstance(materials, list):
                    materials = ','.join(materials)
                variants = act.get('variants', [])
                variants_str = json.dumps(variants) if variants else '[]'

                session.run("""
                    CREATE (a:Activity {
                        id: $id,
                        name: $name,
                        description: $description,
                        difficulty: $difficulty,
                        age_range: $age_range,
                        activity_type: $activity_type,
                        sensory_type: $sensory_type,
                        interest_tags: $interest_tags,
                        prompt_text: $prompt_text,
                        materials: $materials,
                        image_asset: $image_asset,
                        domain_id: $domain_id,
                        group_id: $group_id,
                        duration_minutes: $duration_minutes,
                        variants: $variants
                    })
                """, {
                    'id': act['id'],
                    'name': act['name'],
                    'description': act.get('description', ''),
                    'difficulty': act.get('difficulty', 1),
                    'age_range': act.get('age_range', ''),
                    'activity_type': act.get('activity_type', ''),
                    'sensory_type': act.get('sensory_type', ''),
                    'interest_tags': interest_tags,
                    'prompt_text': act.get('prompt_text', ''),
                    'materials': materials,
                    'image_asset': act.get('image_asset', ''),
                    'domain_id': act.get('domain_id', ''),
                    'group_id': act.get('group_id', ''),
                    'duration_minutes': act.get('duration_minutes', 3),
                    'variants': variants_str
                })

            print(f"已创建 {len(activities)} 个 Activity 节点")

            # 2. 创建关系
            for rel in relations:
                rel_type = rel['type']  # LEADS_TO, SIMILAR_TO, REMEDIAL_TO
                from_id = rel['from']
                to_id = rel['to']
                # 动态 Cypher 关系创建
                session.run(f"""
                    MATCH (a:Activity {{id: $from_id}})
                    MATCH (b:Activity {{id: $to_id}})
                    MERGE (a)-[:{rel_type}]->(b)
                """, {'from_id': from_id, 'to_id': to_id})

            print(f"已创建 {len(relations)} 条关系")

        print("Neo4j 知识图谱初始化完成！")


if __name__ == "__main__":
    # 设置 JSON 文件路径（请根据实际位置调整）
    json_file = os.path.join(BASE_DIR, 'data', 'V2math_activity_graph.json')

    init = KnowledgeGraphInitializer()

    # 可选：如果之前有错误数据，先清空
    # init.clear_all()

    init.init_from_json(json_file)
    init.close()