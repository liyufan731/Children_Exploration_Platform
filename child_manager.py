# child_manager.py
import streamlit as st
from database.dao.child_dao import (
    create_child, get_children_by_parent, update_last_exploration_time
)
from config.settings import COLORS, AGE_RANGES, AVATAR_OPTIONS
import auth


def child_manager_page():
    """儿童管理页面 - 添加/选择儿童"""

    # 自定义样式
    st.markdown(f"""
    <style>
        .child-card {{
            background: white;
            border-radius: 20px;
            padding: 1.5rem;
            margin-bottom: 1rem;
            box-shadow: 0 4px 15px rgba(0,0,0,0.05);
            transition: all 0.2s;
            border: 2px solid transparent;
        }}
        .child-card:hover {{
            box-shadow: 0 8px 25px rgba(0,0,0,0.1);
            border-color: {COLORS['primary']};
            cursor: pointer;
        }}
        .avatar-circle {{
            width: 70px;
            height: 70px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 2.8rem;
            margin: 0 auto;
        }}
        .add-child-btn {{
            background: linear-gradient(135deg, {COLORS['secondary']} 0%, #5B9DB0 100%);
            color: white;
            border: none;
            border-radius: 50px;
            padding: 0.8rem 1.5rem;
            font-size: 1.1rem;
            font-weight: 600;
            width: 100%;
            transition: all 0.3s;
        }}
        .add-child-btn:hover {{
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(126, 200, 227, 0.3);
        }}
        .section-title {{
            color: {COLORS['text']};
            font-size: 1.8rem;
            font-weight: 600;
            margin-bottom: 1.5rem;
        }}
        .empty-state {{
            text-align: center;
            padding: 3rem;
            background: white;
            border-radius: 30px;
            color: #B0A392;
        }}
    </style>
    """, unsafe_allow_html=True)

    # 获取当前登录用户
    user = st.session_state.get('user')
    if not user:
        st.error("请先登录")
        auth.logout()
        st.rerun()
        return

    parent_id = user['id']

    # 页面头部
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"""
        <div style="padding: 1rem 0;">
            <h2 style="color: {COLORS['text']}; margin-bottom: 0.2rem;">👋 你好，{user.get('name') or user['username']}</h2>
            <p style="color: #8B7E6B; font-size: 1.1rem;">选择一位小探险家开始今天的旅程吧</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        if st.button("🚪 登出", use_container_width=True):
            auth.logout()
            # logout() 函数会清理 session，并重新运行，无需额外设置

    # 获取当前家长的儿童列表
    children = get_children_by_parent(parent_id)

    # 显示已有儿童（卡片形式）
    st.markdown('<p class="section-title">🌟 我的小探险家</p>', unsafe_allow_html=True)

    if children:
        # 每行显示最多3个卡片
        cols = st.columns(3)
        for idx, child in enumerate(children):
            with cols[idx % 3]:
                # 构建卡片内容
                avatar_data = None
                if child.get('avatar'):
                    try:
                        import json
                        avatar_data = json.loads(child['avatar'])
                    except:
                        avatar_data = AVATAR_OPTIONS[0]  # 默认头像
                else:
                    avatar_data = AVATAR_OPTIONS[0]

                # 卡片HTML
                card_html = f"""
                <div class="child-card" onclick="select_child_{child['id']}()">
                    <div class="avatar-circle" style="background: {avatar_data['bg']};">
                        {avatar_data['emoji']}
                    </div>
                    <h3 style="text-align: center; margin: 1rem 0 0.3rem; color: {COLORS['text']};">{child['name']}</h3>
                    <p style="text-align: center; color: #8B7E6B; margin-bottom: 0.5rem;">
                        {child.get('age_range', '未设置年龄')}
                    </p>
                    <p style="text-align: center; font-size: 0.8rem; color: #B0A392;">
                        上次探索: {child.get('last_exploration_time', '暂无')[:10] if child.get('last_exploration_time') else '暂无'}
                    </p>
                </div>
                """
                st.markdown(card_html, unsafe_allow_html=True)

                # 通过按钮实现点击选择（由于HTML onclick需要JS，改用按钮）
                if st.button(f"选择 {child['name']}", key=f"select_{child['id']}", use_container_width=True):
                    st.session_state['current_child'] = child
                    update_last_exploration_time(child['id'])
                    st.session_state['current_page'] = 'exploration'
                    st.rerun()
                st.markdown("<br>", unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="empty-state">
            <p style="font-size: 3rem;">🧸</p>
            <p style="font-size: 1.2rem;">还没有添加小探险家</p>
            <p>点击下方按钮，为孩子创建专属探索档案</p>
        </div>
        """, unsafe_allow_html=True)

    # 添加新儿童区域
    st.markdown('<p class="section-title" style="margin-top: 3rem;">✨ 添加新成员</p>', unsafe_allow_html=True)

    with st.expander("➕ 点击添加新儿童", expanded=not children):
        with st.form("add_child_form"):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("孩子名字/昵称", placeholder="例如：乐乐")
                age_range = st.selectbox("年龄范围", AGE_RANGES)

            with col2:
                st.markdown("<p style='margin-bottom: 0.5rem;'>选择头像</p>", unsafe_allow_html=True)
                avatar_options = [av['emoji'] for av in AVATAR_OPTIONS]
                selected_avatar_idx = st.radio(
                    "选择头像",
                    options=range(len(AVATAR_OPTIONS)),
                    format_func=lambda i: AVATAR_OPTIONS[i]['emoji'],
                    label_visibility="collapsed",
                    horizontal=True
                )

            submitted = st.form_submit_button("✨ 创建档案", type="primary")

            if submitted:
                if not name:
                    st.error("请输入孩子名字")
                else:
                    import json
                    avatar_json = json.dumps(AVATAR_OPTIONS[selected_avatar_idx])
                    child_id = create_child(parent_id, name, age_range, avatar_json)
                    if child_id:
                        st.success(f"🎉 {name}的探索档案已创建！")
                        st.rerun()
                    else:
                        st.error("创建失败，请重试")


if __name__ == "__main__":
    # 页面配置
    st.set_page_config(
        page_title="数学探索乐园 - 儿童管理",
        page_icon="🧸",
        layout="centered"
    )

    if 'logged_in' not in st.session_state or not st.session_state['logged_in']:
        st.warning("请先登录")
        st.switch_page("app.py")
    else:
        child_manager_page()