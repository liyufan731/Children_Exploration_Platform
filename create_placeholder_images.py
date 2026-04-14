# create_placeholder_images.py
import os
from PIL import Image, ImageDraw, ImageFont
import json


def create_colorful_placeholder(text, size=(200, 200), color=(100, 150, 200)):
    """创建彩色占位图片"""
    img = Image.new('RGB', size, color)
    draw = ImageDraw.Draw(img)

    # 尝试加载字体
    try:
        font = ImageFont.truetype("arial.ttf", 40)
    except:
        font = ImageFont.load_default()

    # 计算文本位置
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    position = ((size[0] - text_width) // 2, (size[1] - text_height) // 2)

    draw.text(position, text, fill=(255, 255, 255), font=font)
    return img


def generate_all_placeholders():
    """为所有JSON中的活动生成占位图片"""
    with open('data/V2math_activity_graph.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 为每个活动生成图片
    for activity in data['activities']:
        if activity.get('image_asset'):
            # 创建目录
            os.makedirs(os.path.dirname(activity['image_asset']), exist_ok=True)

            # 创建图片
            img = create_colorful_placeholder(activity['name'][:4])
            img.save(activity['image_asset'])
            print(f"已创建: {activity['image_asset']}")


if __name__ == "__main__":
    generate_all_placeholders()