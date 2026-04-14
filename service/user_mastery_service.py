# service/user_mastery_service.py
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from database.dao.familiarity_dao import get_all_familiarities, get_familiarity
from database.dao.exploration_record_dao import get_records_by_child
from database.dao.knowledge_node_dao import get_all_knowledge_nodes
from graph.graph_repository import get_related_activities


class UserMasteryService:
    """用户掌握度分析服务（兼容原有概念）"""

    def __init__(self, child_id: int):
        self.child_id = child_id
        self.familiarities = get_all_familiarities(child_id)
        self.recent_records = get_records_by_child(child_id, limit=30)
        self.all_activities = get_all_knowledge_nodes()

    def get_mastery_overview(self) -> Dict[str, Any]:
        """获取掌握度概览"""
        return {
            "total_activities": len(self.all_activities),
            "explored_activities": len(self.familiarities),
            "mastery_distribution": self._get_mastery_distribution(),
            "learning_progress": self._calculate_learning_progress(),
            "weak_areas": self._identify_weak_areas(),
            "recommended_focus": self._recommend_focus_areas()
        }

    def _get_mastery_distribution(self) -> Dict[str, int]:
        """获取掌握度分布"""
        distribution = {
            "new": 0,  # 0次探索
            "beginner": 0,  # <0.3熟悉度
            "learning": 0,  # 0.3-0.6熟悉度
            "familiar": 0,  # 0.6-0.8熟悉度
            "proficient": 0,  # 0.8-0.95熟悉度
            "mastered": 0  # >0.95熟悉度
        }

        # 统计已探索活动
        for kid, data in self.familiarities.items():
            fam_value = data.get('value', 0)
            if fam_value < 0.3:
                distribution["beginner"] += 1
            elif fam_value < 0.6:
                distribution["learning"] += 1
            elif fam_value < 0.8:
                distribution["familiar"] += 1
            elif fam_value < 0.95:
                distribution["proficient"] += 1
            else:
                distribution["mastered"] += 1

        # 统计未探索活动
        explored_ids = set(self.familiarities.keys())
        total_activity_ids = {act['graph_id'] for act in self.all_activities}
        new_count = len(total_activity_ids - explored_ids)
        distribution["new"] = new_count

        return distribution

    def _calculate_learning_progress(self) -> float:
        """计算学习进度（0-1）"""
        if not self.all_activities:
            return 0.0

        # 基于熟悉度计算加权进度
        total_weight = 0
        achieved_weight = 0

        for activity in self.all_activities:
            activity_id = activity['graph_id']
            difficulty = activity.get('difficulty', 1)

            # 难度越高，权重越大
            weight = difficulty

            total_weight += weight

            # 如果已探索，计算掌握贡献
            if activity_id in self.familiarities:
                fam_value = self.familiarities[activity_id].get('value', 0)
                # 熟悉度越高，贡献越大
                achieved_weight += weight * min(fam_value, 1.0)

        return round(achieved_weight / total_weight, 3) if total_weight > 0 else 0.0

    def _identify_weak_areas(self) -> List[Dict]:
        """识别薄弱领域"""
        weak_areas = []

        # 按领域分组
        domain_activities = {}
        for activity in self.all_activities:
            domain = activity.get('domain_id', 'unknown')
            if domain not in domain_activities:
                domain_activities[domain] = []
            domain_activities[domain].append(activity)

        # 分析每个领域的掌握情况
        for domain, activities in domain_activities.items():
            domain_fam_values = []
            for act in activities:
                act_id = act['graph_id']
                if act_id in self.familiarities:
                    domain_fam_values.append(self.familiarities[act_id].get('value', 0))

            if domain_fam_values:
                avg_fam = sum(domain_fam_values) / len(domain_fam_values)
                explored_ratio = len(domain_fam_values) / len(activities)

                # 如果平均熟悉度低或探索比例低，视为薄弱领域
                if avg_fam < 0.4 or explored_ratio < 0.3:
                    weak_areas.append({
                        "domain": domain,
                        "domain_name": self._get_domain_name(domain),
                        "avg_familiarity": round(avg_fam, 2),
                        "explored_ratio": round(explored_ratio, 2),
                        "total_activities": len(activities),
                        "explored_count": len(domain_fam_values)
                    })

        # 按薄弱程度排序
        weak_areas.sort(key=lambda x: x['avg_familiarity'])
        return weak_areas[:3]  # 返回最薄弱的3个领域

    def _recommend_focus_areas(self) -> List[Dict]:
        """推荐需要重点关注的领域"""
        recommendations = []

        # 获取薄弱领域
        weak_areas = self._identify_weak_areas()

        for area in weak_areas:
            domain = area['domain']

            # 找出该领域中熟悉度最低的活动
            domain_activities = [a for a in self.all_activities if a.get('domain_id') == domain]
            low_fam_activities = []

            for act in domain_activities:
                act_id = act['graph_id']
                fam_value = self.familiarities.get(act_id, {}).get('value', 0)

                # 选择熟悉度低或未探索的活动
                if fam_value < 0.3 or act_id not in self.familiarities:
                    low_fam_activities.append({
                        "activity_id": act_id,
                        "name": act['name'],
                        "familiarity": fam_value,
                        "difficulty": act.get('difficulty', 1),
                        "age_range": act.get('age_range', '')
                    })

            # 按难度排序，推荐适中的活动
            if low_fam_activities:
                low_fam_activities.sort(key=lambda x: x['difficulty'])
                recommended_activity = low_fam_activities[len(low_fam_activities) // 2]  # 选择中等难度的

                recommendations.append({
                    "domain": area['domain_name'],
                    "reason": f"掌握度较低（{area['avg_familiarity']}），建议加强练习",
                    "recommended_activity": recommended_activity,
                    "suggested_actions": [
                        f"尝试「{recommended_activity['name']}」活动",
                        "从简单版本开始，逐步增加难度",
                        "结合孩子兴趣选择相关主题"
                    ]
                })

        return recommendations

    def get_activity_mastery_path(self, activity_id: str) -> Dict:
        """获取活动的掌握路径分析"""
        # 获取活动信息
        target_activity = None
        for act in self.all_activities:
            if act['graph_id'] == activity_id:
                target_activity = act
                break

        if not target_activity:
            return {"error": "活动不存在"}

        # 获取前置活动（通过LEADS_TO关系的反向）
        prerequisites = []

        # 获取后续活动
        next_activities = get_related_activities(activity_id, relation_type='LEADS_TO')

        # 获取相似活动（用于兴趣迁移）
        similar_activities = get_related_activities(activity_id, relation_type='SIMILAR_TO')

        # 获取补救活动（降阶）
        remedial_activities = get_related_activities(activity_id, relation_type='REMEDIAL_TO')

        # 分析当前掌握状态
        current_fam = self.familiarities.get(activity_id, {}).get('value', 0)
        practice_count = self.familiarities.get(activity_id, {}).get('count', 0)

        # 评估掌握状态
        if current_fam < 0.3:
            mastery_status = "beginner"
            suggestion = "刚开始接触，建议多次重复探索"
        elif current_fam < 0.6:
            mastery_status = "learning"
            suggestion = "正在学习中，可以尝试不同变体"
        elif current_fam < 0.8:
            mastery_status = "familiar"
            suggestion = "比较熟悉，可以挑战进阶活动"
        elif current_fam < 0.95:
            mastery_status = "proficient"
            suggestion = "掌握良好，可以尝试教学他人"
        else:
            mastery_status = "mastered"
            suggestion = "完全掌握，可以探索相关领域"

        return {
            "activity_id": activity_id,
            "activity_name": target_activity['name'],
            "current_mastery": {
                "value": round(current_fam, 3),
                "status": mastery_status,
                "practice_count": practice_count,
                "last_practice": self._get_last_practice_time(activity_id)
            },
            "prerequisites": prerequisites[:3],  # 最多3个前置
            "next_steps": next_activities[:3],  # 最多3个后续
            "similar_activities": similar_activities[:3],  # 最多3个相似
            "remedial_activities": remedial_activities[:2],  # 最多2个补救
            "suggestions": [
                suggestion,
                f"已练习{practice_count}次，熟悉度{round(current_fam * 100)}%",
                self._get_practice_schedule(practice_count, current_fam)
            ],
            "readiness_for_next": self._assess_readiness_for_next(current_fam, next_activities)
        }

    def _get_domain_name(self, domain_id: str) -> str:
        """获取领域名称"""
        domain_map = {
            "D01": "数与量",
            "D02": "形状与空间",
            "D03": "比较与测量",
            "D04": "规律与逻辑"
        }
        return domain_map.get(domain_id, domain_id)

    def _get_last_practice_time(self, activity_id: str) -> Optional[str]:
        """获取最近练习时间"""
        for record in self.recent_records:
            if record.get('knowledge_id') == activity_id:
                return record.get('created_at', '')[:10]
        return None

    def _get_practice_schedule(self, practice_count: int, familiarity: float) -> str:
        """获取练习计划建议"""
        if practice_count == 0:
            return "建议本周内尝试2-3次"
        elif practice_count < 3:
            if familiarity < 0.4:
                return "建议每天练习一次，持续3天"
            else:
                return "建议隔天练习，巩固记忆"
        elif practice_count < 6:
            if familiarity < 0.6:
                return "建议每周练习2-3次"
            else:
                return "建议每周练习1-2次，保持熟悉度"
        else:
            if familiarity < 0.8:
                return "建议每周练习1次，重点突破难点"
            else:
                return "建议每两周练习1次，防止遗忘"

    def _assess_readiness_for_next(self, current_fam: float, next_activities: List[Dict]) -> Dict:
        """评估是否准备好学习后续活动"""
        if not next_activities:
            return {"ready": True, "reason": "这是当前路径的终点"}

        if current_fam < 0.6:
            return {
                "ready": False,
                "reason": "当前活动掌握度不足",
                "suggestion": f"建议将熟悉度提升到60%以上（当前{round(current_fam * 100)}%）",
                "estimated_practices": max(1, int((0.6 - current_fam) / 0.15))
            }
        elif current_fam < 0.8:
            easiest_next = min(next_activities, key=lambda x: x.get('difficulty', 3))
            return {
                "ready": True,
                "reason": "可以尝试最简单的后续活动",
                "recommended_next": easiest_next,
                "confidence": "中等"
            }
        else:
            return {
                "ready": True,
                "reason": "掌握良好，可以挑战任何后续活动",
                "confidence": "高"
            }

    def generate_learning_report(self) -> Dict[str, Any]:
        """生成学习报告"""
        overview = self.get_mastery_overview()

        report = {
            "report_date": datetime.now().strftime("%Y-%m-%d"),
            "child_id": self.child_id,
            "summary": self._generate_summary(overview),
            "key_metrics": {
                "learning_progress": overview["learning_progress"],
                "activities_explored": overview["explored_activities"],
                "activities_mastered": overview["mastery_distribution"]["mastered"],
                "weak_areas_count": len(overview["weak_areas"])
            },
            "mastery_distribution": overview["mastery_distribution"],
            "weak_areas": overview["weak_areas"],
            "recommendations": overview["recommended_focus"],
            "recent_achievements": self._get_recent_achievements(),
            "next_week_goals": self._suggest_next_week_goals(overview)
        }

        return report

    def _generate_summary(self, overview: Dict) -> str:
        """生成报告摘要"""
        progress = overview["learning_progress"]
        explored = overview["explored_activities"]
        total = overview["total_activities"]
        mastered = overview["mastery_distribution"]["mastered"]

        summary_parts = []

        # 进度总结
        if progress < 0.3:
            summary_parts.append("学习刚刚起步，正在建立基础。")
        elif progress < 0.6:
            summary_parts.append("学习稳步进行中，已掌握部分核心概念。")
        elif progress < 0.8:
            summary_parts.append("学习进展良好，多数概念已熟悉。")
        else:
            summary_parts.append("学习成果显著，接近完成当前阶段。")

        # 探索情况
        exploration_rate = explored / total if total > 0 else 0
        if exploration_rate < 0.3:
            summary_parts.append(f"已探索{explored}个活动，还有丰富内容等待发现。")
        elif exploration_rate < 0.7:
            summary_parts.append(f"已探索{explored}个活动，探索范围较广。")
        else:
            summary_parts.append(f"已探索{explored}个活动，几乎体验了所有内容。")

        # 掌握情况
        if mastered > 0:
            summary_parts.append(f"已完全掌握{mastered}个活动，基础扎实。")

        # 薄弱领域
        weak_areas = overview["weak_areas"]
        if weak_areas:
            area_names = [area['domain_name'] for area in weak_areas[:2]]
            summary_parts.append(f"在「{'、'.join(area_names)}」方面可以进一步加强。")

        return " ".join(summary_parts)

    def _get_recent_achievements(self) -> List[Dict]:
        """获取近期成就"""
        achievements = []

        # 分析最近一周的记录
        one_week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        recent_week_records = [r for r in self.recent_records
                               if r.get('created_at', '').startswith(one_week_ago)]

        if recent_week_records:
            # 成就1：连续探索
            if len(recent_week_records) >= 5:
                achievements.append({
                    "type": "consistency",
                    "title": "坚持探索",
                    "description": f"本周探索{len(recent_week_records)}次，表现持续",
                    "icon": "🔥"
                })

            # 成就2：高参与度
            high_engagement = [r for r in recent_week_records if r.get('engagement_score', 0) >= 4]
            if len(high_engagement) >= 3:
                achievements.append({
                    "type": "engagement",
                    "title": "高度投入",
                    "description": f"{len(high_engagement)}次探索参与度很高",
                    "icon": "⭐"
                })

            # 成就3：新活动尝试
            recent_activity_ids = set(r.get('knowledge_id') for r in recent_week_records)
            new_activities = recent_activity_ids - set(self.familiarities.keys())
            if new_activities:
                achievements.append({
                    "type": "exploration",
                    "title": "勇于尝试",
                    "description": f"尝试了{len(new_activities)}个新活动",
                    "icon": "🚀"
                })

        # 如果没有近期成就，添加鼓励性成就
        if not achievements and self.recent_records:
            achievements.append({
                "type": "encouragement",
                "title": "探索开始",
                "description": "迈出了探索的第一步，继续加油！",
                "icon": "🎉"
            })

        return achievements[:3]  # 最多3个成就

    def _suggest_next_week_goals(self, overview: Dict) -> List[Dict]:
        """建议下周学习目标"""
        goals = []

        # 目标1：探索新活动
        explored_count = overview["explored_activities"]
        if explored_count < len(self.all_activities) * 0.5:
            goals.append({
                "goal": "explore_new",
                "description": "尝试2-3个新活动",
                "reason": "扩大探索范围，发现新兴趣",
                "priority": "high"
            })

        # 目标2：加强薄弱领域
        weak_areas = overview["weak_areas"]
        if weak_areas:
            weakest = min(weak_areas, key=lambda x: x['avg_familiarity'])
            goals.append({
                "goal": "strengthen_weak",
                "description": f"在「{weakest['domain_name']}」领域练习",
                "reason": f"当前掌握度{weakest['avg_familiarity']}，需要加强",
                "priority": "medium"
            })

        # 目标3：巩固已学
        beginner_activities = [kid for kid, data in self.familiarities.items()
                               if data.get('value', 0) < 0.4]
        if beginner_activities:
            goals.append({
                "goal": "consolidate",
                "description": "复习2个刚开始学习的活动",
                "reason": "巩固基础，防止遗忘",
                "priority": "medium"
            })

        # 目标4：保持探索习惯
        if self.recent_records:
            avg_per_week = len([r for r in self.recent_records
                                if r.get('created_at', '').startswith(
                    (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d"))])
            target = max(3, avg_per_week + 1)
            goals.append({
                "goal": "maintain_habit",
                "description": f"完成{target}次探索",
                "reason": "保持学习连续性",
                "priority": "low"
            })

        return goals[:3]  # 最多3个目标