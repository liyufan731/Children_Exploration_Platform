# engine/activity_engine.py
import streamlit as st
import json
import random
import time
from typing import Dict, Any, Optional


class ActivityEngine:
    """蒙氏教育活动引擎 - 支持多种交互类型"""

    def __init__(self, activity: dict):
        self.activity = activity
        # 解析变体
        variants = activity.get('variants', [])
        if isinstance(variants, str):
            try:
                self.variants = json.loads(variants)
            except json.JSONDecodeError:
                self.variants = []
        else:
            self.variants = variants

        self.current_variant = None
        self.interaction_data = {}
        self.start_time = time.time()

        # 随机选一个变体（如果存在）
        if self.variants:
            self.current_variant = random.choice(self.variants)
        else:
            # 如果没有变体，构造一个默认占位变体
            self.current_variant = {
                'params': {},
                'hint': '自由探索这个活动吧！'
            }

    def render_activity(self) -> Optional[Dict[str, Any]]:
        """渲染活动，返回探索结果或None（表示未完成）"""
        activity_type = self.activity.get('activity_type', 'counting')

        # 显示引导卡片
        with st.container():
            prompt = self.activity.get('prompt_text', '一起来探索吧！')
            materials = self.activity.get('materials', '眼睛和小手')
            st.markdown(f"""
            <div style="background: #FFF9E6; padding: 1.2rem; border-radius: 20px; margin-bottom: 1.5rem;
                        border-left: 6px solid #FFB347;">
                <h3 style="margin:0 0 0.5rem 0; color: #5D4E37;">🎈 {prompt}</h3>
                <p style="margin:0; color: #8B7E6B;">📦 材料: {materials}</p>
            </div>
            """, unsafe_allow_html=True)

        # 根据类型分发渲染
        render_method = getattr(self, f'_render_{activity_type}', None)
        if render_method:
            return render_method()
        else:
            # 默认渲染
            return self._render_default()

    def _record_interaction(self, key: str, value: Any):
        """记录交互数据"""
        self.interaction_data[key] = value

    # ---------- 具体活动类型渲染 ----------

    def _render_counting(self):
        """数数活动"""
        params = self.current_variant.get('params', {})
        obj = params.get('object', '物品')
        max_count = params.get('max', 5)
        correct = self.current_variant.get('correct_answer', max_count)

        st.markdown(f"### 数一数有多少个{obj}？")

        # 用emoji模拟图片
        emoji_map = {'duck': '🦆', 'apple': '🍎', 'car': '🚗', 'star': '⭐', 'ball': '⚽',
                     'cat': '🐱', 'dog': '🐶', 'bear': '🐻'}
        emoji = emoji_map.get(obj, '🔴')
        st.markdown(f"<div style='font-size: 60px; text-align: center;'>{emoji * max_count}</div>",
                    unsafe_allow_html=True)

        st.caption("用手指点一点，一个一个数")

        answer = st.number_input(f"一共有几个{obj}？", min_value=0, max_value=10, step=1, key="count_answer")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("我数好了", key="count_submit", type="primary"):
                self._record_interaction('answer', answer)
                self._record_interaction('correct_answer', correct)

                if answer == correct:
                    st.balloons()
                    st.success(f"🎉 太棒了！你数得真仔细，确实是{correct}个！")
                    return {'completed': True, 'interaction': self.interaction_data}
                else:
                    hint = self.current_variant.get('hint', '再数一次试试看？')
                    st.info(f"💡 {hint}")
                    return None

        with col2:
            if st.button("我需要帮助", key="count_help"):
                hint = self.current_variant.get('hint', f"我们可以一起数：{', '.join(str(i+1) for i in range(max_count))}")
                st.info(f"👆 {hint}")
        return None

    def _render_matching(self):
        """配对/形状匹配活动"""
        params = self.current_variant.get('params', {})
        target = params.get('target', '物品')
        options = params.get('options', [])
        correct_idx = self.current_variant.get('correct_answer', 0)

        st.markdown(f"### 找出和「{target}」一样的")

        st.markdown(f"<div style='font-size: 50px; text-align: center;'>🔍 {target}</div>",
                    unsafe_allow_html=True)

        if not options:
            st.warning("选项加载失败")
            return self._render_default()

        st.markdown("**选一选**")
        cols = st.columns(len(options))
        choice = None
        for i, opt in enumerate(options):
            with cols[i]:
                # 显示选项标签
                st.markdown(f"<div style='text-align: center; font-size: 30px;'>{opt.get('label', '?')}</div>",
                            unsafe_allow_html=True)
                if st.button(f"选这个", key=f"match_{i}"):
                    choice = i

        if choice is not None:
            self._record_interaction('choice', choice)
            self._record_interaction('correct_answer', correct_idx)

            if choice == correct_idx:
                st.balloons()
                st.success("🎉 配对成功！你的眼睛真亮！")
                return {'completed': True, 'interaction': self.interaction_data}
            else:
                hint = self.current_variant.get('hint', '再仔细观察一下？')
                st.info(f"💡 {hint}")

        return None

    def _render_comparing(self):
        """比较活动（多少、大小、长短）"""
        params = self.current_variant.get('params', {})
        left_count = params.get('left_count', 2)
        right_count = params.get('right_count', 3)
        correct = self.current_variant.get('correct_answer', 'right')

        st.markdown("### 哪边更多？")

        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"### {'🐶' * left_count}")
            st.caption("左边")
            if st.button("左边更多", key="compare_left"):
                self._record_interaction('choice', 'left')
                self._record_interaction('correct', correct)
                if 'left' == correct:
                    st.balloons()
                    st.success("🎉 比较得非常准确！")
                    return {'completed': True, 'interaction': self.interaction_data}
                else:
                    st.info("💡 再数一数两边分别有多少？")
                    return None

        with col2:
            st.markdown(f"### {'🐱' * right_count}")
            st.caption("右边")
            if st.button("右边更多", key="compare_right"):
                self._record_interaction('choice', 'right')
                self._record_interaction('correct', correct)
                if 'right' == correct:
                    st.balloons()
                    st.success("🎉 比较得非常准确！")
                    return {'completed': True, 'interaction': self.interaction_data}
                else:
                    st.info("💡 再数一数两边分别有多少？")
                    return None

        if st.button("一样多", key="compare_equal"):
            self._record_interaction('choice', 'equal')
            self._record_interaction('correct', correct)
            if 'equal' == correct:
                st.balloons()
                st.success("🎉 比较得非常准确！")
                return {'completed': True, 'interaction': self.interaction_data}
            else:
                st.info("💡 再数一数两边分别有多少？")
                return None

        return None

    def _render_shape_recognition(self):
        """形状识别"""
        params = self.current_variant.get('params', {})
        target = params.get('target', '形状')
        options = params.get('options', [])
        correct_idx = self.current_variant.get('correct_answer', 0)

        st.markdown(f"### 哪个是{target}？")

        if not options:
            st.warning("选项加载失败")
            return self._render_default()

        cols = st.columns(len(options))
        choice = None
        for i, opt in enumerate(options):
            with cols[i]:
                st.markdown(f"### {opt.get('label', '?')}")
                if st.button(f"这个", key=f"shape_{i}"):
                    choice = i

        if choice is not None:
            self._record_interaction('choice', choice)
            self._record_interaction('correct_answer', correct_idx)
            if choice == correct_idx:
                st.balloons()
                st.success(f"🎉 正确！这就是{target}！")
                return {'completed': True, 'interaction': self.interaction_data}
            else:
                hint = self.current_variant.get('hint', '再观察一下形状特征？')
                st.info(f"💡 {hint}")
        return None

    def _render_pattern(self):
        """规律识别"""
        params = self.current_variant.get('params', {})
        sequence = params.get('sequence', [])
        options = params.get('options', [])
        correct_idx = self.current_variant.get('correct_answer', 0)

        st.markdown("### 下一个是什么？")
        st.markdown(f"## {' '.join(sequence)} ❓")

        if not options:
            st.warning("选项加载失败")
            return self._render_default()

        cols = st.columns(len(options))
        choice = None
        for i, opt in enumerate(options):
            with cols[i]:
                st.markdown(f"### {opt}")
                if st.button(f"选这个", key=f"pattern_{i}"):
                    choice = i

        if choice is not None:
            self._record_interaction('choice', choice)
            self._record_interaction('correct_answer', correct_idx)
            if choice == correct_idx:
                st.balloons()
                st.success("🎉 你发现了规律！真聪明！")
                return {'completed': True, 'interaction': self.interaction_data}
            else:
                st.info("💡 看看前面的图案是怎么重复的？")
        return None

    def _render_addition(self):
        """简单加法（简易实现）"""
        params = self.current_variant.get('params', {})
        a = params.get('a', 2)
        b = params.get('b', 3)
        correct = self.current_variant.get('correct_answer', a + b)

        st.markdown(f"### 一共有多少？")
        st.markdown(f"## {'🐶' * a} + {'🐱' * b}")

        answer = st.number_input("总数是多少？", min_value=0, max_value=20, step=1, key="add_answer")

        if st.button("我算好了", key="add_submit"):
            self._record_interaction('answer', answer)
            self._record_interaction('correct_answer', correct)
            if answer == correct:
                st.balloons()
                st.success(f"🎉 正确！{a} + {b} = {correct}！")
                return {'completed': True, 'interaction': self.interaction_data}
            else:
                hint = self.current_variant.get('hint', '可以把两边合起来数一数')
                st.info(f"💡 {hint}")
        return None

    def _render_subtraction(self):
        """简单减法（简易实现）"""
        params = self.current_variant.get('params', {})
        total = params.get('total', 5)
        remove = params.get('remove', 2)
        correct = self.current_variant.get('correct_answer', total - remove)

        st.markdown(f"### 还剩多少？")
        st.markdown(f"## {'🍎' * total}  拿走 {remove} 个")

        answer = st.number_input("还剩几个？", min_value=0, max_value=20, step=1, key="sub_answer")

        if st.button("我算好了", key="sub_submit"):
            self._record_interaction('answer', answer)
            self._record_interaction('correct_answer', correct)
            if answer == correct:
                st.balloons()
                st.success(f"🎉 正确！{total} - {remove} = {correct}！")
                return {'completed': True, 'interaction': self.interaction_data}
            else:
                hint = self.current_variant.get('hint', '可以数一数剩下的')
                st.info(f"💡 {hint}")
        return None

    def _render_measurement(self):
        """测量比较（长度/重量）"""
        params = self.current_variant.get('params', {})
        left_val = params.get('left_length', params.get('left_weight', 5))
        right_val = params.get('right_length', params.get('right_weight', 8))
        correct = self.current_variant.get('correct_answer', 'right')
        measure_type = '更长' if 'left_length' in params else '更重'

        st.markdown(f"### 哪边{measure_type}？")

        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"### {'📏' if measure_type=='更长' else '⚖️'} 左边")
            st.markdown(f"**{left_val}**")
            if st.button("左边", key="measure_left"):
                self._record_interaction('choice', 'left')
                self._record_interaction('correct', correct)
                if 'left' == correct:
                    st.balloons()
                    st.success("🎉 比较正确！")
                    return {'completed': True, 'interaction': self.interaction_data}
                else:
                    st.info("💡 再仔细观察一下")
                    return None

        with col2:
            st.markdown(f"### 右边")
            st.markdown(f"**{right_val}**")
            if st.button("右边", key="measure_right"):
                self._record_interaction('choice', 'right')
                self._record_interaction('correct', correct)
                if 'right' == correct:
                    st.balloons()
                    st.success("🎉 比较正确！")
                    return {'completed': True, 'interaction': self.interaction_data}
                else:
                    st.info("💡 再仔细观察一下")
                    return None

        return None

    def _render_default(self):
        """默认简易交互"""
        st.info("这个活动鼓励自由探索，家长可以陪同孩子一起完成。")
        if st.button("完成探索", key="default_done"):
            self._record_interaction('type', 'free_exploration')
            return {'completed': True, 'interaction': self.interaction_data}
        return None