# auth.py
import streamlit as st
from database.dao.user_dao import create_user, verify_user
from config.settings import COLORS


def login_page():
    """家长登录/注册页面"""

    # 自定义CSS样式
    st.markdown(f"""
    <style>
        .stApp {{
            background: linear-gradient(135deg, {COLORS['background']} 0%, #FFF5E6 100%);
        }}
        .main-header {{
            text-align: center;
            padding: 2rem 0 1rem 0;
        }}
        .main-header h1 {{
            color: {COLORS['text']};
            font-size: 2.8rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
        }}
        .main-header p {{
            color: #8B7E6B;
            font-size: 1.2rem;
        }}
        .stTabs [data-baseweb="tab-list"] {{
            gap: 2rem;
            justify-content: center;
        }}
        .stTabs [data-baseweb="tab"] {{
            font-size: 1.2rem;
            padding: 0.5rem 2rem;
            border-radius: 30px;
            color: {COLORS['text']};
        }}
        .stTabs [aria-selected="true"] {{
            background-color: {COLORS['primary']} !important;
            color: white !important;
        }}
        .login-card {{
            background: white;
            padding: 2.5rem;
            border-radius: 30px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.05);
            max-width: 450px;
            margin: 0 auto;
        }}
        .stButton button {{
            background-color: {COLORS['primary']} !important;
            color: white !important;
            border: none !important;
            border-radius: 30px !important;
            padding: 0.6rem 2rem !important;
            font-size: 1.1rem !important;
            font-weight: 600 !important;
            width: 100% !important;
            transition: all 0.3s !important;
        }}
        .stButton button:hover {{
            background-color: #E09E3A !important;
            box-shadow: 0 5px 15px rgba(255, 179, 71, 0.3) !important;
        }}
        .footer {{
            text-align: center;
            margin-top: 3rem;
            color: #B0A392;
            font-size: 0.9rem;
        }}
    </style>
    """, unsafe_allow_html=True)

    # 头部信息
    st.markdown("""
    <div class="main-header">
        <h1>🧸 数学探索乐园</h1>
        <p>陪伴孩子发现数学的乐趣</p>
    </div>
    """, unsafe_allow_html=True)

    # 创建选项卡
    tab1, tab2 = st.tabs(["🔐 登录", "📝 注册"])

    # ---------- 登录选项卡 ----------
    with tab1:
        with st.container():
            st.markdown('<div class="login-card">', unsafe_allow_html=True)
            st.subheader("欢迎回来")

            with st.form("login_form"):
                username = st.text_input("用户名", placeholder="请输入用户名")
                password = st.text_input("密码", type="password", placeholder="请输入密码")

                submitted = st.form_submit_button("登录")

                if submitted:
                    if not username or not password:
                        st.error("请填写完整信息")
                    else:
                        user = verify_user(username, password)
                        if user:
                            st.session_state['user'] = user
                            st.session_state['logged_in'] = True
                            st.session_state['current_page'] = 'child_manager'
                            st.success("登录成功！正在跳转...")
                            st.rerun()
                        else:
                            st.error("用户名或密码错误")

            st.markdown('</div>', unsafe_allow_html=True)

    # ---------- 注册选项卡 ----------
    with tab2:
        with st.container():
            st.markdown('<div class="login-card">', unsafe_allow_html=True)
            st.subheader("创建家长账户")

            with st.form("register_form"):
                col1, col2 = st.columns(2)
                with col1:
                    username = st.text_input("用户名 *", placeholder="字母或数字", key="reg_username")
                with col2:
                    name = st.text_input("称呼", placeholder="例如：乐乐妈妈", key="reg_name")

                password = st.text_input("密码 *", type="password", placeholder="至少6位", key="reg_password")
                password_confirm = st.text_input("确认密码 *", type="password", key="reg_confirm")

                submitted = st.form_submit_button("注册")

                if submitted:
                    if not username or not password or not password_confirm:
                        st.error("请填写必填项")
                    elif password != password_confirm:
                        st.error("两次密码输入不一致")
                    elif len(password) < 6:
                        st.error("密码长度至少6位")
                    else:
                        user_id = create_user(username, password, name)
                        if user_id > 0:
                            st.success("🎉 注册成功！请切换到登录选项卡登录。")
                        else:
                            st.error("用户名已存在，请更换")

            st.markdown('</div>', unsafe_allow_html=True)

    # 页脚
    st.markdown("""
    <div class="footer">
        <p>🐻 蒙台梭利教育理念 · 尊重儿童自主探索</p>
    </div>
    """, unsafe_allow_html=True)


def logout():
    """登出函数：清空所有会话状态并返回登录页"""
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.session_state['logged_in'] = False
    st.session_state['current_page'] = 'auth'
    st.rerun()


# 独立运行时测试（可选）
if __name__ == "__main__":
    st.set_page_config(page_title="数学探索乐园", page_icon="🧸", layout="centered")
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False
    if not st.session_state['logged_in']:
        login_page()
    else:
        st.success(f"已登录用户：{st.session_state['user']['name'] or st.session_state['user']['username']}")
        if st.button("登出"):
            logout()