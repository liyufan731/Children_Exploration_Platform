from graph.neo4j_driver import Neo4jDriver

def get_all_activities() -> list[dict]:
    """获取所有活动节点"""
    driver = Neo4jDriver()
    query = """
        MATCH (a:Activity)
        RETURN a.id AS id, a.name AS name, a.description AS description, 
               a.difficulty AS difficulty, a.age_range AS age_range,
               a.activity_type AS activity_type, a.sensory_type AS sensory_type,
               a.interest_tags AS interest_tags, a.prompt_text AS prompt_text,
               a.materials AS materials, a.image_asset AS image_asset,
               a.domain_id AS domain_id, a.group_id AS group_id,
               a.duration_minutes AS duration_minutes, a.variants AS variants
    """
    return driver.query(query)

def get_activity_by_id(activity_id: str) -> dict | None:
    driver = Neo4jDriver()
    query = """
        MATCH (a:Activity {id: $id})
        RETURN a.id AS id, a.name AS name, a.description AS description, 
               a.difficulty AS difficulty, a.age_range AS age_range,
               a.activity_type AS activity_type, a.sensory_type AS sensory_type,
               a.interest_tags AS interest_tags, a.prompt_text AS prompt_text,
               a.materials AS materials, a.image_asset AS image_asset,
               a.domain_id AS domain_id, a.group_id AS group_id,
               a.duration_minutes AS duration_minutes, a.variants AS variants
    """
    results = driver.query(query, {"id": activity_id})
    return results[0] if results else None

def get_related_activities(activity_id: str, relation_type: str = None) -> list[dict]:
    """获取关联活动，可指定关系类型 LEADS_TO / SIMILAR_TO / REMEDIAL_TO"""
    driver = Neo4jDriver()
    rel_filter = f":{relation_type}" if relation_type else ""
    query = f"""
        MATCH (a:Activity {{id: $id}})-[r{rel_filter}]->(b:Activity)
        RETURN b.id AS id, b.name AS name, b.activity_type AS activity_type,
               b.difficulty AS difficulty, type(r) AS relation_type
    """
    return driver.query(query, {"id": activity_id})