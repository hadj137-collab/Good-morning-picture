# -*- coding: utf-8 -*-
import streamlit as st
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps
import io
import os

# ========== 1. 字型載入邏輯 ==========
def load_handwriting_font(font_size):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    font_paths = [
        os.path.join(current_dir, "ChenYuluoyan-Thin-Monospaced.ttf"),
        "ChenYuluoyan-Thin-Monospaced.ttf",
        "JasonHandwriting6p.ttf"
    ]
    for path in font_paths:
        try:
            if os.path.exists(path):
                return ImageFont.truetype(path, font_size)
        except:
            continue
            
    try:
        return ImageFont.load_default()
    except:
        return None

# ========== 2. 核心：評估角落並返回三行文字座標 ==========
def find_best_corner_positions(image, title_font_size, body_font_size):
    width, height = image.size
    scale = min(1.0, 400.0 / max(width, height))
    small = image.resize((max(1, int(width*scale)), max(1, int(height*scale))))
    small_w, small_h = small.size

    edge_img = small.convert("L").filter(ImageFilter.FIND_EDGES)
    edge_data = list(edge_img.getdata())

    cw = int(small_w * 0.40)
    ch = int(small_h * 0.35)
    
    corners_box = {
        '左上角': (0, 0, cw, ch),
        '右上角': (small_w - cw, 0, small_w, ch),
        '左下角': (0, small_h - ch, cw, small_h),
        '右下角': (small_w - cw, small_h - ch, small_w, small_h)
    }

    scores = {}
    for name, (x1, y1, x2, y2) in corners_box.items():
        score = 0
        for y in range(y1, y2):
            row_start = y * small_w
            score += sum(edge_data[row_start + x1 : row_start + x2])
        scores[name] = score

    best_corner = min(scores, key=scores.get)
    
    margin_x = int(width * 0.06)
    margin_y = int(height * 0.06)
    line_gap = int(body_font_size * 0.35) 

    if "上" in best_corner:
        y1 = margin_y + title_font_size // 2
        y2 = y1 + title_font_size // 2 + line_gap + body_font_size // 2
        y3 = y2 + body_font_size // 2 + line_gap + body_font_size // 2
    else:
        y3 = height - margin_y - body_font_size // 2
        y2 = y3 - body_font_size // 2 - line_gap - body_font_size // 2
        y1 = y2 - body_font_size // 2 - line_gap - title_font_size // 2

    if "左" in best_corner:
        align = "left"
        x1, x2, x3 = margin_x, margin_x, margin_x
    else:
        align = "right"
        x1, x2, x3 = width - margin_x, width - margin_x, width - margin_x

    return align, best_corner, x1, y1, x2, y2, x3, y3

def draw_text_with_shadow(draw_obj, text, position, text_font, align="left", fill_color="yellow", shadow_color="black", font_size=40):
    x, y = position
    if text_font is None:
        return
    try:
        bbox = text_font.getbbox(text)
        tw = bbox
    
