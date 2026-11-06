# WeChat Sticker Creator (微信表情包全流程自动化设计与上架技能)

基于 AI 图像生成与计算机视觉图像后处理技术的微信表情包工业级全流程自动化制作技能。

支持从**单张角色原画立绘**出发，全自动完成 16 张或 24 张符合**微信表情开放平台**官方标准的表情包制作、规范物料打包及合规文案速配。

## 🌟 核心特性

- 🎯 **双构图模式支持**：
  - **半身大头特写（Bust-up / Waist-up，推荐）**：面部放大 3 倍，在微信 240×240 官方限制尺寸下保持极致清晰与眼神微表情表达；
  - **全身立绘（Full-body）**：完整展示全身穿搭、鞋袜与大幅度肢体动作梗图。
- 🔮 **双透明度风格支持**：
  - **纯人物透明穿透（Pure Cutout，推荐）**：零白底外框，发丝与道具缝隙透明穿透，完美融合深色模式（Dark Mode）与任意聊天壁纸；
  - **模切贴纸风（Die-cut Stroke）**：提供 2px 饱满白色外描边。
- ⚡ **Pure Alpha 独立四通道 Lanczos 降采样**：彻底解耦 R、G、B 与 Alpha 通道分别重采样，杜绝 Premultiplied Alpha 导致的白底预乘白边与锯齿。
- 📦 **全套上架物料一键打包**：自动生成表情封面（240×240）、面板图标（50×50）、无字彩色横幅（750×400，严格 $\le 80\text{ KB}$）与艺术家头像。
- 📝 **零差错合规文案表**：自动输出符合平台字数与标点红线（$\le 4$ 字无标点含义词等）的审核速查清单。

## 📂 目录结构

```text
wechat-sticker-creator/
├── SKILL.md                          # 技能主指令与完整 SOP 指南
├── README.md                         # 仓库介绍
├── references/
│   └── wechat_platform_spec.md       # 微信表情开放平台官方工业级参数规范
└── scripts/
    ├── process_stickers.py           # 智能抠图、降采样与描边预处理脚本
    └── build_materials.py            # 微信开放平台全套展示物料自动构建脚本
```

## 🚀 快速开始

```bash
# 纯人物透明穿透模式处理表情包 (推荐)
python scripts/process_stickers.py <输入原图文件夹> <输出240文件夹> --pure-cutout

# 自动构建全套微信展示物料
python scripts/build_materials.py <最佳表情_240.png> <头像原图.png> <输出物料目录>
```
