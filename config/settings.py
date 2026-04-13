import os

# 项目根目录
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# SQLite 数据库路径
DATABASE_PATH = os.path.join(BASE_DIR, "data", "math_explorer.db")

# Neo4j 配置
NEO4J_URI = "neo4j://localhost:7687"
NEO4J_USERNAME = "neo4j"
NEO4J_PASSWORD = "20030731"

# 确保数据目录存在
os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)

# config/settings.py（追加内容）

# 页面配置
PAGE_TITLE = "数学探索乐园"
PAGE_ICON = "🧸"
LAYOUT = "centered"

# 主题颜色（柔和蒙氏风格）
COLORS = {
    "primary": "#FFB347",      # 暖橙色
    "secondary": "#7EC8E3",    # 淡蓝色
    "background": "#FFF9F0",   # 奶油色背景
    "card": "#FFFFFF",         # 白色卡片
    "text": "#5D4E37",         # 暖棕色文字
    "success": "#A8D5BA",      # 淡绿色
    "warning": "#FFD4A9",      # 淡橙色
}

# config/settings.py（追加内容）

# 儿童年龄范围选项
AGE_RANGES = ["2-3岁", "3-4岁", "4-5岁", "5-6岁"]

# 儿童头像选项（emoji + 背景色）
AVATAR_OPTIONS = [
    {"emoji": "🐶", "bg": "#FFE0B2"},
    {"emoji": "🐱", "bg": "#FFCDD2"},
    {"emoji": "🐻", "bg": "#D7CCC8"},
    {"emoji": "🦊", "bg": "#FFCC80"},
    {"emoji": "🐼", "bg": "#B3E5FC"},
    {"emoji": "🐸", "bg": "#C8E6C9"},
    {"emoji": "🐨", "bg": "#B2DFDB"},
    {"emoji": "🦁", "bg": "#FFECB3"},
]