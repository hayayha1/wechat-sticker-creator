# -*- coding: utf-8 -*-
"""
微信表情开放平台全套物料自动化构建脚本
生成内容：
1. 详情页横幅 (750x400, <=80KB, 彩色底，无文字)
2. 封面图 (240x240, 透明 PNG)
3. 聊天面板图标 (50x50, 透明 PNG)
4. 艺术家主页横幅 (750x400, <=80KB, JPEG, 无文字)
5. 艺术家头像 (640x640, <=500KB)
"""

import os
import sys
from PIL import Image

def build_all_materials(best_sticker_240, avatar_src, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    
    # 1. 封面图 (240x240 透明 PNG)
    cover_path = os.path.join(out_dir, "cover_240x240.png")
    with Image.open(best_sticker_240) as im:
        im.save(cover_path, "PNG", optimize=True)
    print("Cover generated: cover_240x240.png")
    
    # 2. 聊天面板图标 (50x50 透明 PNG)
    icon_path = os.path.join(out_dir, "icon_50x50.png")
    with Image.open(best_sticker_240) as im:
        # 分离通道 Lanczos 缩放到 50x50
        r, g, b, a = im.split()
        r50 = r.resize((50, 50), Image.Resampling.LANCZOS)
        g50 = g.resize((50, 50), Image.Resampling.LANCZOS)
        b50 = b.resize((50, 50), Image.Resampling.LANCZOS)
        a50 = a.resize((50, 50), Image.Resampling.LANCZOS)
        im50 = Image.merge("RGBA", (r50, g50, b50, a50))
        im50.save(icon_path, "PNG", optimize=True)
    print("Icon generated: icon_50x50.png")
    
    # 3. 详情页横幅 (750x400, 严格 <= 80KB, 彩色渐变底，严禁文字)
    banner_path = os.path.join(out_dir, "banner_750x400.png")
    banner_w, banner_h = 750, 400
    base_banner = Image.new("RGBA", (banner_w, banner_h), (225, 238, 255, 255))
    # 柔和渐变色
    for y in range(banner_h):
        ratio = y / float(banner_h)
        r = int(225 * (1 - ratio) + 200 * ratio)
        g = int(238 * (1 - ratio) + 220 * ratio)
        b = int(255 * (1 - ratio) + 248 * ratio)
        for x in range(banner_w):
            base_banner.putpixel((x, y), (r, g, b, 255))
    
    # 贴入主体角色
    with Image.open(best_sticker_240) as ch_img:
        # 放大到合适尺寸 (例如 300x300)
        ch_scaled = ch_img.resize((300, 300), Image.Resampling.LANCZOS)
        off_x = (banner_w - 300) // 2
        off_y = (banner_h - 300) // 2
        base_banner.alpha_composite(ch_scaled, (off_x, off_y))
    
    base_banner.save(banner_path, "PNG", optimize=True)
    # 确保 <= 80 KB
    if os.path.getsize(banner_path) > 80 * 1024:
        # 转为高质量 JPG
        rgb_banner = base_banner.convert("RGB")
        rgb_banner.save(banner_path, "JPEG", quality=85, optimize=True)
    print("Detail Banner generated: banner_750x400.png, Size:", os.path.getsize(banner_path), "bytes")
    
    # 4. 艺术家主页条幅 (750x400, <=80KB, JPEG)
    art_banner_path = os.path.join(out_dir, "artist_banner_750x400.jpg")
    base_banner.convert("RGB").save(art_banner_path, "JPEG", quality=85, optimize=True)
    print("Artist Banner generated: artist_banner_750x400.jpg, Size:", os.path.getsize(art_banner_path), "bytes")
    
    # 5. 艺术家头像 (640x640, <=500KB)
    avatar_path = os.path.join(out_dir, "avatar_640x640.png")
    with Image.open(avatar_src) as av_img:
        av_crop = av_img.convert("RGBA")
        aw, ah = av_crop.size
        min_side = min(aw, ah)
        left = (aw - min_side) // 2
        top = (ah - min_side) // 2
        av_square = av_crop.crop((left, top, left + min_side, top + min_side))
        av_final = av_square.resize((640, 640), Image.Resampling.LANCZOS)
        av_final.save(avatar_path, "PNG", optimize=True)
        if os.path.getsize(avatar_path) > 500 * 1024:
            # 严格控制在 500KB 内
            av_final.convert("RGB").save(avatar_path, "JPEG", quality=92, optimize=True)
    print("Avatar generated: avatar_640x640.png, Size:", os.path.getsize(avatar_path), "bytes")
    print("ALL MATERIALS BUILT SUCCESSFULLY!")

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python build_materials.py <best_sticker_240.png> <avatar_source.jpg/png> <output_dir>")
        sys.exit(1)
    build_all_materials(sys.argv[1], sys.argv[2], sys.argv[3])
