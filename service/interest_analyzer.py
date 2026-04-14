# service/interest_analyzer.py
from typing import List, Dict, Any
from datetime import datetime, timedelta
from database.dao.child_interests_dao import get_child_interests
from database.dao.exploration_record_dao import get_records_by_child
from database.dao.knowledge_node_dao import get_knowledge_node_by_graph_id
import json


class InterestAnalyzer:
    """儿童兴趣分析服务"""

    def __init__(self, child_id: int):
        self.child_id = child_id
        self.interests = get_child_interests(child_id)
        self.recent_records = get_records_by_child(child_id, limit=50)

    def analyze_interests(self) -> Dict[str, Any]:
        """综合分析儿童兴趣"""
        return {
            "top_interests": self._get_top_interests(),
            "interest_stability": self._calculate_stability(),
            "new_interests": self._detect_new_interests(),
            "interest_clusters": self._cluster_interests(),
            "interest_evolution": self._analyze_evolution()
        }

    def _get_top_interests(self, limit: int = 5) -> List[Dict]:
        """获取主要兴趣标签"""
        if not self.interests:
            return []

        # 按探索次数和参与度综合排序
        sorted_interests = sorted(
            self.interests,
            key=lambda x: x['exploration_count'] * x['avg_engagement'],
            reverse=True
        )

        top_interests = []
        for item in sorted_interests[:limit]:
            # 获取相关标签（从最近的探索记录中提取）
            related_tags = self._get_related_tags(item['interest_tag'])

            top_interests.append({
                "tag": item['interest_tag'],
                "exploration_count": item['exploration_count'],
                "avg_engagement": round(item['avg_engagement'], 1),
                "preference_level": item['preference_level'],
                "related_tags": related_tags,
                "strength_score": self._calculate_strength_score(item)
            })

        return top_interests

    def _calculate_stability(self) -> float:
        """计算兴趣稳定性指数（0-1）"""
        if not self.interests or len(self.interests) < 2:
            return 0.5  # 默认值

        # 基于兴趣的持续时间和一致性计算稳定性
        stability_scores = []
        for interest in self.interests:
            # 探索次数越多，稳定性越高
            count_score = min(interest['exploration_count'] / 10, 1.0)

            # 参与度越高且稳定，稳定性越高
            engagement_score = interest['avg_engagement'] / 5.0

            # 综合得分
            stability_scores.append(count_score * engagement_score)

        return round(sum(stability_scores) / len(stability_scores), 2)

    def _detect_new_interests(self) -> List[str]:
        """检测新出现的兴趣"""
        if not self.recent_records or len(self.recent_records) < 5:
            return []

        # 分析最近5次探索的新兴趣标签
        recent_tags = set()
        for record in self.recent_records[:5]:
            knowledge_id = record.get('knowledge_id')
            if knowledge_id:
                node = get_knowledge_node_by_graph_id(knowledge_id)
                if node and node.get('interest_tags'):
                    tags = node['interest_tags']
                    if isinstance(tags, str):
                        tags = [t.strip() for t in tags.split(',') if t.strip()]
                    recent_tags.update(tags)

        # 与已有兴趣比较，找出新的
        existing_tags = {item['interest_tag'] for item in self.interests}
        new_tags = list(recent_tags - existing_tags)

        return new_tags[:3]  # 返回最多3个新兴趣

    def _cluster_interests(self) -> List[Dict]:
        """兴趣聚类分析"""
        if not self.interests:
            return []

        # 简单的主题聚类（基于标签相似性）
        clusters = []

        # 数学概念相关
        math_tags = ['数数', '加法', '减法', '比较', '形状', '测量', '规律']
        math_interests = [i for i in self.interests if any(tag in i['interest_tag'] for tag in math_tags)]
        if math_interests:
            clusters.append({
                "theme": "数学概念",
                "interests": [i['interest_tag'] for i in math_interests],
                "strength": sum(i['exploration_count'] for i in math_interests) / len(
                    math_interests) if math_interests else 0
            })

        # 主题相关
        theme_tags = ['动物', '水果', '交通工具', '颜色', '食物']
        theme_interests = [i for i in self.interests if any(tag in i['interest_tag'] for tag in theme_tags)]
        if theme_interests:
            clusters.append({
                "theme": "生活主题",
                "interests": [i['interest_tag'] for i in theme_interests],
                "strength": sum(i['exploration_count'] for i in theme_interests) / len(
                    theme_interests) if theme_interests else 0
            })

        return clusters

    def _analyze_evolution(self) -> Dict[str, Any]:
        """分析兴趣演变趋势"""
        if not self.recent_records or len(self.recent_records) < 10:
            return {"trend": "stable", "details": "数据不足"}

        # 简单趋势分析
        early_records = self.recent_records[-10:-5] if len(self.recent_records) >= 10 else []
        recent_records = self.recent_records[-5:] if len(self.recent_records) >= 5 else []

        early_tags = self._extract_tags_from_records(early_records)
        recent_tags = self._extract_tags_from_records(recent_records)

        # 计算多样性变化
        early_diversity = len(early_tags)
        recent_diversity = len(recent_tags)

        if recent_diversity > early_diversity * 1.5:
            trend = "diversifying"
        elif recent_diversity < early_diversity * 0.7:
            trend = "focusing"
        else:
            trend = "stable"

        return {
            "trend": trend,
            "early_diversity": early_diversity,
            "recent_diversity": recent_diversity,
            "new_tags_in_recent": list(set(recent_tags) - set(early_tags))[:3]
        }

    def _extract_tags_from_records(self, records: List[Dict]) -> List[str]:
        """从探索记录中提取兴趣标签"""
        tags = []
        for record in records:
            knowledge_id = record.get('knowledge_id')
            if knowledge_id:
                node = get_knowledge_node_by_graph_id(knowledge_id)
                if node and node.get('interest_tags'):
                    node_tags = node['interest_tags']
                    if isinstance(node_tags, str):
                        node_tags = [t.strip() for t in node_tags.split(',') if t.strip()]
                    tags.extend(node_tags)
        return list(set(tags))

    def _get_related_tags(self, main_tag: str) -> List[str]:
        """获取与主要标签相关的其他标签"""
        related = set()
        for record in self.recent_records[:10]:
            knowledge_id = record.get('knowledge_id')
            if knowledge_id:
                node = get_knowledge_node_by_graph_id(knowledge_id)
                if node and node.get('interest_tags'):
                    tags = node['interest_tags']
                    if isinstance(tags, str):
                        tags = [t.strip() for t in tags.split(',') if t.strip()]

                    if main_tag in tags:
                        # 添加同一活动中的其他标签
                        related.update([t for t in tags if t != main_tag])

        return list(related)[:3]  # 返回最多3个相关标签

    def _calculate_strength_score(self, interest: Dict) -> float:
        """计算兴趣强度得分（0-1）"""
        # 基于探索次数、参与度和最近性
        count_score = min(interest['exploration_count'] / 20, 1.0)
        engagement_score = interest['avg_engagement'] / 5.0

        # 综合得分
        return round(count_score * engagement_score, 2)

    def get_interest_summary(self) -> str:
        """生成兴趣摘要（用于家长观察面板）"""
        analysis = self.analyze_interests()

        if not analysis["top_interests"]:
            return "孩子刚开始探索，兴趣正在形成中..."

        top_interest = analysis["top_interests"][0]
        summary_parts = []

        # 主要兴趣
        summary_parts.append(f"孩子对「{top_interest['tag']}」表现出浓厚兴趣，"
                             f"已探索{top_interest['exploration_count']}次，"
                             f"平均参与度{top_interest['avg_engagement']}/5。")

        # 兴趣稳定性
        stability = analysis["interest_stability"]
        if stability > 0.7:
            summary_parts.append("兴趣比较稳定，有持续探索的倾向。")
        elif stability > 0.4:
            summary_parts.append("兴趣正在形成中，有一定稳定性。")
        else:
            summary_parts.append("兴趣还在探索阶段，变化较多。")

        # 新兴趣
        new_interests = analysis["new_interests"]
        if new_interests:
            summary_parts.append(f"最近对「{'、'.join(new_interests)}」表现出新兴趣。")

        # 趋势
        trend = analysis["interest_evolution"]["trend"]
        if trend == "diversifying":
            summary_parts.append("兴趣范围正在扩大，探索更加多样化。")
        elif trend == "focusing":
            summary_parts.append("兴趣逐渐聚焦，在某些领域深入探索。")

        return " ".join(summary_parts)