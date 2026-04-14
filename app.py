# auth.py
import streamlit as st

import activity_player
import auth
import child_manager
import exploration
import parent_dashboard
from database.dao.user_dao import create_user, verify_user
from config.settings import PAGE_TITLE, PAGE_ICON, LAYOUT, COLORS

# 页面配置（必须在最前面）
st.set_page_config(
    page_title=f"{PAGE_TITLE} - 登录",
    page_icon=PAGE_ICON,
    layout=LAYOUT
)

def main():
    # 初始化会话状态
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False
    if 'current_page' not in st.session_state:
        st.session_state['current_page'] = 'auth'

    # 路由逻辑
    if not st.session_state['logged_in']:
        auth.login_page()
    else:
        if st.session_state['current_page'] == 'child_manager':
            child_manager.child_manager_page()
        elif st.session_state['current_page'] == 'exploration':
            exploration.exploration_page()
        elif st.session_state['current_page'] == 'parent_dashboard':
            parent_dashboard.parent_dashboard_page()
        elif st.session_state['current_page'] == 'activity_player':
            activity_player.activity_player_page()
        else:
            # 默认显示儿童管理页
            child_manager.child_manager_page()



if __name__ == "__main__":
    main()