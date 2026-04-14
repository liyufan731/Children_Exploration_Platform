# parent_dashboard.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

from database.dao.child_dao import get_child_by_id
from database.dao.exploration_record_dao import (
    get_exploration_stats, get_daily_exploration_stats,
    get_records_by_child, get_activity_type_distribution
)
from database.dao.child_interests_dao import get_child_interests
from database.dao.familiarity_dao import get_all_familiarities
from database.dao.knowledge_node_dao import get_knowledge_node_by_graph_id
from config.settings import COLORS

st.set_page_config(page_title="家长观察面板", page_icon="📊", layout="wide")


def parent_dashboard_page():
    # 权限检查
    if 'logged_in' not in st.session_state or not st.session_state['logged_in']:
        st.switch_page("app.py")
    if 'current_child' not in st.session_state:
        st.warning("请先选择一位小探险家")
        st.session_state['current_page'] = 'child_manager'
        st.rerun()

    child = st.session_state['current_child']
    child_id = child['id']

    # 自定义样式
    st.markdown(f"""
    <style>
        .metric-card {{
            background: white;
            padding: 1.5rem;
            border-radius: 20px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.05);
            text-align: center;
        }}
        .metric-value {{
            font-size: 2.5rem;
            font-weight: bold;
            color: {COLORS['primary']};
        }}
        .metric-label {{
            color: #8B7E6B;
            font-size: 1rem;
        }}
        .section-title {{
            color: {COLORS['text']};
            font-size: 1.6rem;
            margin: 2rem 0 1rem 0;
        }}
    </style>
    """, unsafe_allow_html=True)

    # 头部导航
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.markdown(f"## 📊 {child['name']} 的成长观察")
    with col2:
        if st.button("🗺️ 返回探索"):
            st.session_state['current_page'] = 'exploration'
            st.rerun()
    with col3:
        if st.button("👤 换小朋友"):
            del st.session_state['current_child']
            st.session_state['current_page'] = 'child_manager'
            st.rerun()

    # 获取数据
    stats = get_exploration_stats(child_id)
    daily_stats = get_daily_exploration_stats(child_id, days=30)
    recent_records = get_records_by_child(child_id, limit=20)
    interests = get_child_interests(child_id)
    type_dist = get_activity_type_distribution(child_id)
    familiarities = get_all_familiarities(child_id)

    # ========== 关键指标卡片 ==========
    st.markdown('<p class="section-title">📈 关键指标</p>', unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{stats['total_count']}</div>
            <div class="metric-label">总探索次数</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        total_hours = stats['total_duration'] // 3600
        total_minutes = (stats['total_duration'] % 3600) // 60
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{total_hours}h {total_minutes}m</div>
            <div class="metric-label">累计探索时长</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{stats['avg_engagement']:.1f}</div>
            <div class="metric-label">平均参与度 (1-5)</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        # 计算兴趣多样性（不同标签数量）
        diversity = len(interests)
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{diversity}</div>
            <div class="metric-label">兴趣标签数</div>
        </div>
        """, unsafe_allow_html=True)

    # ========== 趋势图 ==========
    st.markdown('<p class="section-title">📅 近30天探索趋势</p>', unsafe_allow_html=True)

    if daily_stats:
        df_daily = pd.DataFrame(daily_stats)
        fig_trend = go.Figure()
        fig_trend.add_trace(go.Scatter(
            x=df_daily['date'], y=df_daily['count'],
            mode='lines+markers',
            name='探索次数',
            line=dict(color=COLORS['primary'], width=3),
            marker=dict(size=8)
        ))
        fig_trend.add_trace(go.Bar(
            x=df_daily['date'], y=df_daily['avg_engagement'],
            name='平均参与度',
            yaxis='y2',
            marker_color=COLORS['secondary'],
            opacity=0.6
        ))
        fig_trend.update_layout(
            xaxis_title="日期",
            yaxis_title="探索次数",
            yaxis2=dict(
                title="参与度",
                overlaying='y',
                side='right',
                range=[0, 5]
            ),
            hovermode='x unified',
            height=400,
            margin=dict(l=40, r=40, t=40, b=40)
        )
        st.plotly_chart(fig_trend, use_container_width=True)
    else:
        st.info("还没有足够的探索数据，带孩子多探索几次吧！")

    # ========== 兴趣分析 ==========
    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown('<p class="section-title">❤️ 兴趣标签</p>', unsafe_allow_html=True)
        if interests:
            # 准备词云数据
            word_freq = {item['interest_tag']: item['exploration_count'] * item['avg_engagement']
                         for item in interests}

            # 生成词云
            wordcloud = WordCloud(
                width=600, height=400,
                background_color='white',
                colormap='Oranges',
                relative_scaling=0.5,
                font_path=None  # 使用默认字体
            ).generate_from_frequencies(word_freq)

            fig_wc, ax = plt.subplots(figsize=(8, 5))
            ax.imshow(wordcloud, interpolation='bilinear')
            ax.axis('off')
            st.pyplot(fig_wc)

            # 显示偏好等级
            st.markdown("**兴趣偏好详情**")
            for item in interests[:5]:
                st.markdown(f"- {item['interest_tag']}: {item['preference_level']} (探索{item['exploration_count']}次)")
        else:
            st.info("暂无兴趣数据")

    with col2:
        st.markdown('<p class="section-title">🎯 活动类型分布</p>', unsafe_allow_html=True)
        if type_dist:
            df_type = pd.DataFrame({
                '类型': list(type_dist.keys()),
                '次数': list(type_dist.values())
            })
            fig_pie = px.pie(df_type, values='次数', names='类型',
                             color_discrete_sequence=px.colors.qualitative.Pastel)
            fig_pie.update_traces(textposition='inside', textinfo='percent+label')
            fig_pie.update_layout(height=400)
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("暂无活动类型数据")

    # ========== 熟悉度分布 ==========
    st.markdown('<p class="section-title">📚 活动熟悉度</p>', unsafe_allow_html=True)

    if familiarities:
        # 获取活动名称映射
        fam_list = []
        for kid, fam_data in familiarities.items():
            # 通过knowledge_id获取活动信息（需要查询）
            # 简化处理：直接显示部分数据
            fam_list.append({
                '活动ID': kid,
                '熟悉度': fam_data['value'],
                '探索次数': fam_data['count']
            })

        df_fam = pd.DataFrame(fam_list)
        fig_fam = px.bar(df_fam, x='活动ID', y='熟悉度',
                         color='熟悉度', color_continuous_scale='oranges',
                         hover_data=['探索次数'])
        fig_fam.update_layout(height=400)
        st.plotly_chart(fig_fam, use_container_width=True)
    else:
        st.info("还没有熟悉度记录")

    # ========== 最近探索历程 ==========
    st.markdown('<p class="section-title">📋 最近探索历程</p>', unsafe_allow_html=True)

    if recent_records:
        records_data = []
        for rec in recent_records[:10]:
            # 获取活动名称
            node = get_knowledge_node_by_graph_id(rec.get('knowledge_id')) if rec.get('knowledge_id') else None
            activity_name = node['name'] if node else '未知活动'
            records_data.append({
                '时间': rec['created_at'][:16],
                '活动': activity_name,
                '参与度': rec['engagement_score'],
                '时长(秒)': rec['duration_seconds'],
                '状态': rec['completion_status']
            })
        df_records = pd.DataFrame(records_data)
        st.dataframe(df_records, use_container_width=True, hide_index=True)
    else:
        st.info("暂无探索记录")

    # ========== 成长建议 ==========
    st.markdown('<p class="section-title">💡 观察建议</p>', unsafe_allow_html=True)

    with st.container():
        suggestions = []
        if stats['total_count'] < 5:
            suggestions.append("🌱 刚开始探索，多鼓励孩子尝试不同类型的活动，建立兴趣。")
        if interests:
            top_interest = max(interests, key=lambda x: x['exploration_count'])
            suggestions.append(f"❤️ 孩子对「{top_interest['interest_tag']}」特别感兴趣，可以多安排相关主题的活动。")
        if len(type_dist) < 3:
            suggestions.append("🔄 建议增加活动类型的多样性，让孩子接触不同形式的数学概念。")
        if stats['avg_engagement'] < 3.5:
            suggestions.append("🎯 参与度略低，可以尝试更短的活动时长或更有趣的主题。")
        else:
            suggestions.append("✨ 孩子参与度很高，继续保持探索的热情！")

        # 默认建议
        if not suggestions:
            suggestions.append("📖 观察孩子的自主选择，尊重探索节奏，数学能力会在过程中自然成长。")

        for s in suggestions:
            st.markdown(f"- {s}")

    # 底部间距
    st.markdown("<br><br>", unsafe_allow_html=True)


if __name__ == "__main__":
    parent_dashboard_page()