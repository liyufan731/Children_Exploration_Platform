# activity_player.py
import streamlit as st
import time

from database.dao.child_dao import get_child_by_id, update_last_exploration_time
from database.dao.knowledge_node_dao import get_knowledge_node_by_graph_id
from database.dao.exploration_record_dao import create_exploration_record
from database.dao.child_interests_dao import update_child_interest
from service.exploration_familiarity_service import ExplorationFamiliarityService
from engine.activity_engine import ActivityEngine
from config.settings import COLORS

st.set_page_config(page_title="活动探索", page_icon="🎮", layout="wide")


def activity_player_page():
    # 权限检查
    if 'logged_in' not in st.session_state or not st.session_state['logged_in']:
        st.switch_page("app.py")
    if 'current_child' not in st.session_state:
        st.warning("请先选择一位小探险家")
        st.session_state['current_page'] = 'child_manager'
        st.rerun()
    if 'current_activity' not in st.session_state:
        st.warning("请先选择一个活动")
        st.session_state['current_page'] = 'exploration'
        st.rerun()

    child = st.session_state['current_child']
    activity = st.session_state['current_activity']

    # 自定义样式
    st.markdown(f"""
    <style>
        .activity-header {{
            background: linear-gradient(135deg, {COLORS['primary']} 0%, {COLORS['secondary']} 100%);
            padding: 1rem 2rem;
            border-radius: 30px;
            color: white;
            margin-bottom: 2rem;
        }}
        .back-button {{
            margin-bottom: 1rem;
        }}
    </style>
    """, unsafe_allow_html=True)

    # 返回按钮
    if st.button("← 返回探索小径", key="back_to_explore"):
        # 清理引擎状态
        if 'engine' in st.session_state:
            del st.session_state['engine']
        st.session_state['current_page'] = 'exploration'
        st.rerun()

    # 活动标题
    st.markdown(f"""
    <div class="activity-header">
        <h1 style="margin:0;">🎈 {activity['name']}</h1>
        <p style="margin:0; opacity:0.9;">{child['name']}，开始探索吧！</p>
    </div>
    """, unsafe_allow_html=True)

    # 初始化引擎
    if 'engine' not in st.session_state:
        st.session_state['engine'] = ActivityEngine(activity)
        st.session_state['explore_start_time'] = time.time()

    engine = st.session_state['engine']
    result = engine.render_activity()

    # 探索完成处理
    if result and result.get('completed'):
        end_time = time.time()
        duration = int(end_time - st.session_state.get('explore_start_time', end_time))

        interaction = result.get('interaction', {})
        correct = (interaction.get('correct_answer') == interaction.get('answer') or
                   interaction.get('choice') == interaction.get('correct'))
        engagement = 5 if correct else 3

        knowledge_node = get_knowledge_node_by_graph_id(activity['graph_id'])
        if knowledge_node:
            create_exploration_record(
                child_id=child['id'],
                knowledge_id=knowledge_node['id'],
                exploration_type=activity.get('activity_type'),
                engagement_score=engagement,
                duration_seconds=duration,
                completion_status='completed',
                interaction_data=interaction,
                exploration_quality=0.8 if correct else 0.6
            )

            ExplorationFamiliarityService.update_familiarity_after_exploration(
                child_id=child['id'],
                knowledge_id=knowledge_node['id'],
                engagement_score=engagement,
                duration_seconds=duration
            )

            if activity.get('interest_tags'):
                tags = activity['interest_tags'].split(',') if isinstance(activity['interest_tags'], str) else activity['interest_tags']
                for tag in tags:
                    update_child_interest(child['id'], tag.strip(), engagement)

            update_last_exploration_time(child['id'])

            st.success("🎉 探索完成！你的成长档案已更新。")
            if st.button("完成探索，返回小径"):
                for key in ['current_activity', 'engine', 'explore_start_time']:
                    if key in st.session_state:
                        del st.session_state[key]
                st.session_state['current_page'] = 'exploration'
                st.rerun()
        else:
            st.error("活动数据异常，请返回重试")

    # 放弃探索
    if st.button("下次再玩", key="abandon"):
        for key in ['current_activity', 'engine', 'explore_start_time']:
            if key in st.session_state:
                del st.session_state[key]
        st.session_state['current_page'] = 'exploration'
        st.rerun()


if __name__ == "__main__":
    activity_player_page()