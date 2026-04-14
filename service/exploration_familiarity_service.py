# service/exploration_familiarity_service.py
from database.dao.familiarity_dao import update_familiarity, get_familiarity
import math


class ExplorationFamiliarityService:
    """熟悉度计算服务"""

    @staticmethod
    def calculate_gain(
            base_gain: float = 0.1,
            engagement_score: int = 3,
            duration_seconds: int = 60,
            practice_count: int = 0
    ) -> float:
        """
        计算本次探索的熟悉度增益
        公式: 总增益 = (基础增益 + 重复奖励 + 参与度奖励 + 时长奖励) × 递减因子
        """
        # 重复奖励：重复练习有额外增益
        repeat_bonus = 0.02 * min(practice_count, 5)

        # 参与度奖励：高参与度获得更多
        engagement_bonus = (engagement_score - 3) * 0.03

        # 时长奖励：适宜时长获得奖励（3-5分钟最佳）
        if 180 <= duration_seconds <= 300:
            time_bonus = 0.05
        elif duration_seconds > 300:
            time_bonus = 0.03
        else:
            time_bonus = 0.01

        # 递减因子：熟悉度越高增益越小（由外部传入当前熟悉度计算）
        # 此处只计算原始增益，递减在更新时应用
        raw_gain = base_gain + repeat_bonus + engagement_bonus + time_bonus
        return max(0.01, raw_gain)  # 至少0.01

    @staticmethod
    def apply_decay(current_familiarity: float, gain: float) -> float:
        """应用递减效应"""
        # 熟悉度越高，实际增益越小
        decay = 1.0 - (current_familiarity * 0.5)  # 熟悉度0.8时，增益减40%
        return gain * max(0.3, decay)

    @classmethod
    def update_familiarity_after_exploration(
            cls,
            child_id: int,
            knowledge_id: int,
            engagement_score: int,
            duration_seconds: int,
            practice_count: int = 0
    ):
        """探索后更新熟悉度"""
        current_fam = get_familiarity(child_id, knowledge_id)

        # 计算原始增益
        raw_gain = cls.calculate_gain(
            engagement_score=engagement_score,
            duration_seconds=duration_seconds,
            practice_count=practice_count
        )

        # 应用递减
        actual_gain = cls.apply_decay(current_fam, raw_gain)

        # 更新数据库
        update_familiarity(child_id, knowledge_id, actual_gain, 1)

        return current_fam + actual_gain