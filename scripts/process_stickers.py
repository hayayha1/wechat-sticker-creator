# -*- coding: utf-8 -*-
"""
微信表情包高质量预处理与无损抗预乘缩图脚本
功能：
1. 采用 u2net / 连通域深度算法精准去底，完美保留浅色毛发（如白尾巴）；
2. 支持两种风格模式：
   - pure_cutout（纯人物透明穿透，推荐）：零白底外框，完美适配微信深色模式与各类聊天壁纸；
   - stroke（模切贴纸白边）：带 2px 饱满白色外描边；
3. 紧致裁剪透明边界，消除留白冗余；
4. 【核心黑科技】分离 R、G、B 与 Alpha 四通道分别执行 Lanczos 高质量重采样，
   杜绝白底预乘（Premultiplied Alpha）导致的黑边、白边与边缘糊化；
5. 输出严格符合微信规范的 240x240 透明 PNG。
"""

import os
import sys
import argparse
import numpy as np
from PIL import Image, ImageFilter
from rembg import new_session, remove

def remove_background_hybrid(raw_img, session=None):
    """
    结合 u2net 与背景连通域算法，确保白色毛发（如白尾巴、白毛衣）饱满保留，背景彻底透明。
    """
    if session is None:
        session = new_session("u2net")
        
    arr = np.array(raw_img.convert("RGB"))
    # 检测外围近白色背景 (R, G, B >= 251)
    white_bg = (arr[:, :, 0] >= 251) & (arr[:, :, 1] >= 251) & (arr[:, :, 2] >= 251)
    
    try:
        import scipy.ndimage as ndimage
        lbl, num = ndimage.label(white_bg)
        border_labels = set(lbl[0, :]).union(set(lbl[-1, :])).union(set(lbl[:, 0])).union(set(lbl[:, -1]))
        if 0 in border_labels:
            border_labels.remove(0)
            
        is_border_bg = np.isin(lbl, list(border_labels))
        fg_mask = (~is_border_bg).astype(np.uint8) * 255
        mask_im = Image.fromarray(fg_mask, mode="L").filter(ImageFilter.GaussianBlur(radius=0.8))
        
        cutout = raw_img.convert("RGBA")
        cutout.putalpha(mask_im)
        return cutout
    except Exception:
        # 回退到标准 u2net 抠图
        return remove(raw_img, session=session)

def process_single_sticker(src_path, out_240_path, out_320_path=None, session=None, pure_cutout=True):
    if session is None:
        session = new_session("u2net")
    
    # 1. 深度抠图
    with Image.open(src_path) as raw_img:
        cutout = remove_background_hybrid(raw_img, session=session)
    
    # 2. 紧致裁剪
    bbox = cutout.getbbox()
    if not bbox:
        raise ValueError(f"Empty bounding box for {src_path}")
    cropped = cutout.crop(bbox)
    cw, ch = cropped.size
    
    if not pure_cutout:
        # 模切贴纸模式：放入 320 画布添加 2px 饱满白色外描边
        scale_320 = 290.0 / max(cw, ch)
        w_320 = int(round(cw * scale_320))
        h_320 = int(round(ch * scale_320))
        resized_320 = cropped.resize((w_320, h_320), Image.Resampling.LANCZOS)
        
        canvas_320 = Image.new("RGBA", (320, 320), (0, 0, 0, 0))
        off_x = (320 - w_320) // 2
        off_y = (320 - h_320) // 2
        canvas_320.alpha_composite(resized_320, (off_x, off_y))
        
        alpha_320 = canvas_320.split()[3]
        dilated_mask = alpha_320.filter(ImageFilter.MaxFilter(5))
        stroke_layer = Image.new("RGBA", (320, 320), (255, 255, 255, 255))
        stroke_layer.putalpha(dilated_mask)
        
        final_320 = Image.new("RGBA", (320, 320), (0, 0, 0, 0))
        final_320.alpha_composite(stroke_layer)
        final_320.alpha_composite(canvas_320)
        
        if out_320_path:
            os.makedirs(os.path.dirname(os.path.abspath(out_320_path)), exist_ok=True)
            final_320.save(out_320_path, "PNG", optimize=True)
            
        r, g, b, a = final_320.split()
        r_240 = r.resize((240, 240), Image.Resampling.LANCZOS)
        g_240 = g.resize((240, 240), Image.Resampling.LANCZOS)
        b_240 = b.resize((240, 240), Image.Resampling.LANCZOS)
        a_240 = a.resize((240, 240), Image.Resampling.LANCZOS)
        
        final_240 = Image.merge("RGBA", (r_240, g_240, b_240, a_240))
    else:
        # 纯人物透明穿透模式（零白底）
        target_size = 230.0
        scale = target_size / max(cw, ch)
        w_new = int(round(cw * scale))
        h_new = int(round(ch * scale))
        
        r, g, b, a = cropped.split()
        r_res = r.resize((w_new, h_new), Image.Resampling.LANCZOS)
        g_res = g.resize((w_new, h_new), Image.Resampling.LANCZOS)
        b_res = b.resize((w_new, h_new), Image.Resampling.LANCZOS)
        a_res = a.resize((w_new, h_new), Image.Resampling.LANCZOS)
        
        # 边缘微锐化，提升 240 下的眼神光与文字清晰度
        r_res = r_res.filter(ImageFilter.UnsharpMask(radius=1.2, percent=120, threshold=2))
        g_res = g_res.filter(ImageFilter.UnsharpMask(radius=1.2, percent=120, threshold=2))
        b_res = b_res.filter(ImageFilter.UnsharpMask(radius=1.2, percent=120, threshold=2))
        
        resized_char = Image.merge("RGBA", (r_res, g_res, b_res, a_res))
        
        final_240 = Image.new("RGBA", (240, 240), (0, 0, 0, 0))
        off_x = (240 - w_new) // 2
        off_y = (240 - h_new) // 2
        final_240.alpha_composite(resized_char, (off_x, off_y))

    os.makedirs(os.path.dirname(os.path.abspath(out_240_path)), exist_ok=True)
    final_240.save(out_240_path, "PNG", optimize=True)
    
    file_size_kb = os.path.getsize(out_240_path) / 1024.0
    print(f"Processed: {os.path.basename(out_240_path)} -> 240x240 ({'Pure Cutout' if pure_cutout else 'With Stroke'}), {file_size_kb:.1f} KB")
    return out_240_path

def batch_process_folder(src_folder, out_folder, out_320_folder=None, pure_cutout=True):
    session = new_session("u2net")
    files = [f for f in os.listdir(src_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))]
    files.sort()
    print(f"Found {len(files)} files to process in {src_folder}...")
    
    success = 0
    for idx, f in enumerate(files, 1):
        src_file = os.path.join(src_folder, f)
        base_name = os.path.splitext(f)[0]
        out_240 = os.path.join(out_folder, f"{base_name}_240.png")
        out_320 = os.path.join(out_320_folder, f"{base_name}_320.png") if out_320_folder else None
        try:
            process_single_sticker(src_file, out_240, out_320, session=session, pure_cutout=pure_cutout)
            success += 1
        except Exception as e:
            print(f"[{idx}/{len(files)}] Error processing {f}: {e}")
    print(f"Batch completed: {success}/{len(files)} successfully generated.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="微信表情包高质量预处理与无损抗预乘缩图工具")
    parser.add_argument("input", help="输入文件或文件夹路径")
    parser.add_argument("output_240", help="输出 240x240 目标文件夹或文件路径")
    parser.add_argument("--output_320", help="可选：输出 320x320 阶段画布路径", default=None)
    parser.add_argument("--pure-cutout", action="store_true", default=True, help="纯人物透明穿透模式（零白底外框，默认开启）")
    parser.add_argument("--stroke", action="store_true", help="模切贴纸白边模式（添加 2px 饱满白色描边）")
    
    args = parser.parse_args()
    is_pure = not args.stroke
    
    if os.path.isdir(args.input):
        batch_process_folder(args.input, args.output_240, args.output_320, pure_cutout=is_pure)
    else:
        process_single_sticker(args.input, args.output_240, args.output_320, pure_cutout=is_pure)
