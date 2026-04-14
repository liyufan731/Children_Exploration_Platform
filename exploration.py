# exploration.py
import streamlit as st
import time
import plotly.graph_objects as go
import networkx as nx

from database.dao.child_dao import get_child_by_id, update_last_exploration_time
from database.dao.knowledge_node_dao import get_knowledge_node_by_graph_id, get_all_knowledge_nodes
from database.dao.exploration_record_dao import get_exploration_stats
from service.exploration_recommender import ExplorationRecommender
from graph.graph_repository import get_related_activities, get_activity_by_id
from config.settings import COLORS

st.set_page_config(page_title="探索小径", page_icon="🗺️", layout="wide")


def exploration_page():
    # 权限检查
    if 'logged_in' not in st.session_state or not st.session_state['logged_in']:
        st.switch_page("app.py")
    if 'current_child' not in st.session_state:
        st.warning("请先选择一位小探险家")
        st.session_state['current_page'] = 'child_manager'
        st.rerun()

    child = st.session_state['current_child']
    if 'id' not in child:
        st.error("儿童信息异常")
        st.session_state['current_page'] = 'child_manager'
        st.rerun()

    fresh_child = get_child_by_id(child['id'])
    if fresh_child:
        child = fresh_child
        st.session_state['current_child'] = fresh_child

    if not child.get('age_range'):
        child['age_range'] = '3-4'

    # 样式
    st.markdown(f"""
    <style>
        .explore-header {{
            background: linear-gradient(135deg, {COLORS['primary']} 0%, {COLORS['secondary']} 100%);
            padding: 1.5rem 2rem;
            border-radius: 30px;
            color: white;
            margin-bottom: 2rem;
        }}
        .activity-card {{
            background: white;
            padding: 1.2rem;
            border-radius: 20px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.05);
            margin-bottom: 1rem;
            border-left: 5px solid {COLORS['primary']};
        }}
        .stButton button {{
            border-radius: 30px !important;
        }}
    </style>
    """, unsafe_allow_html=True)

    # 头部导航
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.markdown(f"""
        <div class="explore-header">
            <h1 style="margin:0;">🗺️ 探索小径</h1>
            <p style="margin:0; opacity:0.9;">{child['name']}，今天想去哪里探险？</p>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        if st.button("👤 换小朋友"):
            st.session_state['current_page'] = 'child_manager'
            st.rerun()
    with col3:
        if st.button("📊 家长观察"):
            st.session_state['current_page'] = 'parent_dashboard'
            st.rerun()

    # 侧边栏统计
    with st.sidebar:
        st.markdown(f"### 🧸 {child['name']}的旅程")
        stats = get_exploration_stats(child['id'])
        st.metric("探索次数", stats['total_count'])
        st.metric("探索总时长", f"{stats['total_duration'] // 60}分钟")

        st.divider()
        st.markdown("### 🎯 今日推荐模式")
        mode = st.selectbox(
            "选择推荐风格",
            ["balanced", "interest_first", "variety_first", "challenge", "comfort"],
            format_func=lambda x: {
                "balanced": "⚖️ 平衡推荐",
                "interest_first": "❤️ 兴趣优先",
                "variety_first": "🌈 多样探索",
                "challenge": "🚀 适度挑战",
                "comfort": "🛋️ 舒适重温"
            }.get(x, x)
        )

    # 推荐活动
    recommender = ExplorationRecommender(child['id'], child['age_range'])
    recommendations = recommender.get_recommendations(mode=mode)

    if not recommendations:
        st.info("😊 还没有足够的数据进行智能推荐，先来看看这些有趣的活动吧！")
        all_acts = recommender.all_activities
        filtered_acts = [a for a in all_acts if a.get('age_range') == child['age_range']] or all_acts
        recommendations = [{'activity': act, 'score': 0.5, 'invitation': f"来试试「{act['name']}」吧！"} for act in filtered_acts[:9]]

    st.markdown("### 🌟 为你推荐的活动")
    cols = st.columns(3)
    for i, rec in enumerate(recommendations):
        act = rec['activity']
        with cols[i % 3]:
            with st.container():
                st.markdown(f"""
                <div class="activity-card">
                    <h4>{act['name']}</h4>
                    <p style="color: #666;">{act.get('description', '')[:50]}...</p>
                    <p>🏷️ {act.get('interest_tags', '数学')}  |  ⏱️ {act.get('duration_minutes', 3)}分钟</p>
                    <p style="color: {COLORS['primary']};">✨ {rec['invitation']}</p>
                </div>
                """, unsafe_allow_html=True)
                if st.button(f"开始探索", key=f"explore_{act['id']}"):
                    st.session_state['current_activity'] = act
                    st.session_state['current_page'] = 'activity_player'
                    st.rerun()

    # ---------- 学习路线可视化 ----------
    st.markdown("---")
    st.markdown("## 🧭 学习路线图")
    st.caption("基于你已探索的活动，推荐后续学习路径")

    # 获取已探索的活动（熟悉度>0.3）
    familiarities = recommender.familiarities
    explored_ids = [kid for kid, data in familiarities.items() if data.get('value', 0) > 0.3]

    if explored_ids:
        # 取最近探索的一个活动作为起点
        last_activity_id = explored_ids[-1] if explored_ids else None
        if last_activity_id:
            # 获取该活动的后续推荐路径（LEADS_TO 关系）
            related = get_related_activities(last_activity_id, relation_type='LEADS_TO')
            if related:
                # 构建图
                G = nx.DiGraph()
                start_node = get_activity_by_id(last_activity_id)
                G.add_node(last_activity_id, name=start_node['name'][:8] if start_node else last_activity_id)
                for rel in related:
                    to_id = rel['id']
                    to_name = rel['name'][:8]
                    G.add_node(to_id, name=to_name)
                    G.add_edge(last_activity_id, to_id)

                # 绘制
                pos = nx.spring_layout(G, seed=42)
                edge_x, edge_y = [], []
                for edge in G.edges():
                    x0, y0 = pos[edge[0]]
                    x1, y1 = pos[edge[1]]
                    edge_x.extend([x0, x1, None])
                    edge_y.extend([y0, y1, None])

                node_x, node_y, node_text = [], [], []
                for node in G.nodes():
                    x, y = pos[node]
                    node_x.append(x)
                    node_y.append(y)
                    node_text.append(G.nodes[node].get('name', node))

                fig = go.Figure()
                fig.add_trace(go.Scatter(x=edge_x, y=edge_y, mode='lines', line=dict(width=2, color='#7EC8E3'), hoverinfo='none'))
                fig.add_trace(go.Scatter(x=node_x, y=node_y, mode='markers+text', text=node_text,
                                         textposition="top center", marker=dict(size=30, color=COLORS['primary']),
                                         hoverinfo='text'))
                fig.update_layout(showlegend=False, height=300, margin=dict(l=20, r=20, t=20, b=20),
                                  xaxis=dict(showgrid=False, zeroline=False, visible=False),
                                  yaxis=dict(showgrid=False, zeroline=False, visible=False))
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("多探索几个活动，就会显示学习路线啦！")
        else:
            st.info("先去探索第一个活动吧～")
    else:
        st.info("还没有探索记录，完成一个活动后就能看到学习路线。")


if __name__ == "__main__":
    exploration_page()