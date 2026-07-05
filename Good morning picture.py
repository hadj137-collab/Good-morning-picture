# -*- coding: utf-8 -*-
import streamlit as st
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps
import io
import os

# ========== 1. 字型載入邏輯 ==========
def load_handwriting_font(font_size):
    # 在雲端伺服器上，建議將字型檔與代碼放在同一個資料夾
    font_paths = [
        "ChenYuluoyan-Thin-Monospaced.ttf", 
        "JasonHandwriting6p.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf" # Linux 伺服器預設防呆
    ]
    for path in font_paths:
        try:
            if os.path.exists(path):
                return ImageFont.truetype(path, font_size)
        except:
            continue
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

    return align, x1, y1, x2, y2, x3, y3

def draw_text_with_shadow(draw_obj, text, position, text_font, align="left", fill_color="yellow", shadow_color="black", font_size=40):
    x, y = position
    try:
        bbox = text_font.getbbox(text)
        tw = bbox[2] - bbox[0]
    except Exception:
        tw = font_size * len(text)
        
    if align == "right":
        render_x = x - tw
    else:
        render_x = x
    render_y = y - font_size // 2
    
    offset = max(1, int(font_size * 0.04))
    for dx, dy in [(-offset,-offset),(offset,-offset),(-offset,offset),(offset,offset)]:
        draw_obj.text((render_x+dx, render_y+dy), text, font=text_font, fill=shadow_color)
    draw_obj.text((render_x, render_y), text, font=text_font, fill=fill_color)

# ========== 3. Streamlit 網頁介面 ==========
st.set_page_config(page_title="🌸 智慧長輩早安圖生成器", layout="centered")
st.title("🌸 智慧避讓長輩早安圖生成器")
st.write("上傳一張照片，AI 會自動尋找空白處並幫你寫上漂亮的手寫長輩祝賀詞！")

# 檔案上傳器
uploaded_file = st.file_uploader("📸 請選擇並上傳您的照片", type=["jpg", "jpeg", "png", "webp"])

if uploaded_file is not None:
    # 讀取並自動旋轉修正
    raw_image = Image.open(uploaded_file).convert("RGB")
    image = ImageOps.exif_transpose(raw_image)
    
    st.image(image, caption="已上傳的照片", use_container_width=True)

    # 祝福語選單
    st.subheader("✍️ 選擇或自訂祝福語")
    option = st.selectbox(
        "請選擇祝福語範本：",
        ["祝您平安喜樂，事事順心！", 
         "迎來幸福一天，健康常相伴！", 
         "願您心情愉快，萬事皆如意！", 
         "新的一天出發，充滿正能量！", 
         "保持微笑樂觀，好運連連來！",
         "🎨 我要自己輸入文字"]
    )

    if option == "🎨 我要自己輸入文字":
        line2_text = st.text_input("請輸入第二行文字：", "祝你生日快樂")
        line3_text = st.text_input("請輸入第三行文字：", "天天開心！")
    else:
        parts = option.split("，")
        line2_text = parts[0]
        line3_text = parts[1] if len(parts) > 1 else ""

    line1_text = "早安"

    # 開始製作按鈕
    if st.button("🚀 開始製作早安圖"):
        with st.spinner("智慧分析畫面並排版中..."):
            img_to_draw = image.copy()
            width, height = img_to_draw.size
            draw = ImageDraw.Draw(img_to_draw)

            title_font_size = int(width * 0.095)
            body_font_size = int(width * 0.062)

            title_font = load_handwriting_font(title_font_size)
            body_font = load_handwriting_font(body_font_size)

            align, l1x, l1y, l2x, l2y, l3x, l3y = find_best_corner_positions(img_to_draw, title_font_size, body_font_size)

            draw_text_with_shadow(draw, line1_text, (l1x, l1y), title_font, align=align, fill_color="#FFD700", font_size=title_font_size)
            draw_text_with_shadow(draw, line2_text, (l2x, l2y), body_font, align=align, fill_color="#FFFFFF", font_size=body_font_size)
            draw_text_with_shadow(draw, line3_text, (l3x, l3y), body_font, align=align, fill_color="#FFFFFF", font_size=body_font_size)

            # 顯示結果
            st.success("🎉 製作完成！")
            st.image(img_to_draw, caption="生成的早安圖", use_container_width=True)

            # 將結果轉為記憶體二進位格式以供下載
            img_byte_arr = io.BytesIO()
            img_to_draw.save(img_byte_arr, format='JPEG', quality=95)
            img_byte_arr = img_byte_arr.getvalue()

            st.download_button(
                label="📥 點我下載成品照片",
                data=img_byte_arr,
                file_name="good_morning.jpg",
                mime="image/jpeg"
            )
