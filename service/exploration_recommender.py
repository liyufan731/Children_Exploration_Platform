# service/exploration_recommender.py
from database.dao.knowledge_node_dao import get_all_knowledge_nodes
from database.dao.familiarity_dao import get_all_familiarities
from database.dao.exploration_record_dao import get_records_by_child
from database.dao.child_interests_dao import get_child_interests
import random


class ExplorationRecommender:
    """探索推荐服务"""

    def __init__(self, child_id: int, age_range: str = None):
        self.child_id = child_id
        self.age_range = age_range
        self.all_activities = get_all_knowledge_nodes()
        self.familiarities = get_all_familiarities(child_id)
        self.recent_records = get_records_by_child(child_id, limit=20)
        self.interests = self._load_interests()

    def _load_interests(self) -> dict:
        """加载儿童兴趣标签及权重"""
        interests = get_child_interests(self.child_id)
        interest_map = {}
        for item in interests:
            # 权重 = 探索次数 × 平均参与度 / 5（归一化）
            weight = item['exploration_count'] * (item['avg_engagement'] / 5.0)
            interest_map[item['interest_tag']] = weight
        return interest_map

    def get_recommendations(self, mode: str = "balanced", limit: int = 6) -> list[dict]:
        """
        获取推荐活动列表
        mode: balanced, interest_first, variety_first, challenge, comfort
        """
        # 过滤适龄活动（如果年龄范围无效或过滤后为空，则使用全部）
        if self.age_range:
            filtered = [a for a in self.all_activities if a.get('age_range') == self.age_range]
            if not filtered:
                filtered = self.all_activities
        else:
            filtered = self.all_activities

        if not filtered:
            return []

        # 计算每个活动的推荐分数
        scored = []
        recent_ids = [r['knowledge_id'] for r in self.recent_records[:5]] if self.recent_records else []

        for act in filtered:
            score = self._calculate_score(act, mode, recent_ids)
            # 保证最低分数，避免全部为零
            score = max(score, 0.15)
            scored.append((act, score))

        # 按分数降序排序
        scored.sort(key=lambda x: x[1], reverse=True)

        # 返回前 limit 个
        recommendations = []
        for act, score in scored[:limit]:
            recommendations.append({
                'activity': act,
                'score': round(score, 2),
                'invitation': self._generate_invitation(act),
                'reason': self._generate_reason(act)
            })
        return recommendations

    def _calculate_score(self, activity: dict, mode: str, recent_ids: list) -> float:
        """计算推荐分数"""
        scores = {}

        # 1. 兴趣匹配度
        tags = activity.get('interest_tags', '')
        if isinstance(tags, str):
            tags = [t.strip() for t in tags.split(',') if t.strip()]
        interest_score = 0.3  # 基础分
        for tag in tags:
            if tag in self.interests:
                interest_score += self.interests[tag] * 0.2
        scores['interest'] = min(interest_score, 1.0)

        # 2. 探索新鲜度
        knowledge_id = activity['id']
        if knowledge_id in recent_ids:
            scores['freshness'] = 0.2
        else:
            scores['freshness'] = 0.8

        # 3. 认知适宜性（基于年龄匹配）
        if activity.get('age_range') == self.age_range:
            scores['cognitive'] = 0.9
        else:
            scores['cognitive'] = 0.5

        # 4. 熟悉度
        fam_data = self.familiarities.get(knowledge_id, {})
        fam = fam_data.get('value', 0.0)
        if fam < 0.3:
            scores['familiarity'] = 0.8  # 新活动
        elif fam < 0.7:
            scores['familiarity'] = 1.0  # 适中
        else:
            scores['familiarity'] = 0.5  # 过于熟悉

        # 根据模式调整权重
        weights = {
            'balanced': {'interest': 0.4, 'freshness': 0.25, 'cognitive': 0.2, 'familiarity': 0.15},
            'interest_first': {'interest': 0.6, 'freshness': 0.2, 'cognitive': 0.1, 'familiarity': 0.1},
            'variety_first': {'interest': 0.2, 'freshness': 0.5, 'cognitive': 0.2, 'familiarity': 0.1},
            'challenge': {'interest': 0.3, 'freshness': 0.2, 'cognitive': 0.4, 'familiarity': 0.1},
            'comfort': {'interest': 0.3, 'freshness': 0.1, 'cognitive': 0.1, 'familiarity': 0.5},
        }
        weight = weights.get(mode, weights['balanced'])

        total = sum(scores[k] * weight[k] for k in weight)
        return total

    def _generate_invitation(self, activity: dict) -> str:
        """生成儿童友好的邀请语"""
        name = activity['name']
        templates = [
            f"想不想试试「{name}」？",
            f"「{name}」看起来很有趣哦！",
            f"来玩「{name}」吧！",
        ]
        return random.choice(templates)

    def _generate_reason(self, activity: dict) -> str:
        """生成家长可见的推荐理由"""
        age = activity.get('age_range', '未知年龄')
        return f"基于年龄{age}和兴趣推荐"