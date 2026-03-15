
<div align="center">

![:name](https://count.getloli.com/@astrbot_plugin_minesweeper?name=astrbot_plugin_minesweeper&theme=minecraft&padding=7&offset=0&align=top&scale=1&pixelated=1&darkmode=auto)

# astrbot_plugin_minesweeper

_✨ 扫雷游戏 ✨_  

[![License](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![AstrBot](https://img.shields.io/badge/AstrBot-3.4%2B-orange.svg)](https://github.com/Soulter/AstrBot)
[![GitHub](https://img.shields.io/badge/作者-Zhalslar-blue)](https://github.com/Zhalslar)

</div>

## 💡 介绍

经典的扫雷小游戏，已完美适配 Astrbot！

现在支持 Windows GUI 模式，可以直接在屏幕上用鼠标玩扫雷！

## 📦 安装

在 AstrBot 的插件市场搜索 `astrbot_plugin_minesweeper`，点击安装即可。

## ⚙️ 配置

请在 AstrBot 面板配置，插件管理 -> astrbot_plugin_minesweeper -> 操作 -> 插件配置

## ⌨️ 命令

### AstrBot 聊天命令

| 命令 | 说明 |
|:----:|:-----|
| 扫雷 <初级/中级/高级> <皮肤序号> | 开始扫雷游戏，可选择不同难度（初级、中级、高级），并可指定皮肤序号 |
| 扫雷 <行> <列> <雷数> <皮肤序号> | 开始自定义棋盘（例如：扫雷 10 10 20 1），可选皮肤序号 |
| 结束扫雷 | 强制结束当前进行中的扫雷游戏 |
| 雷盘 | 查看当前扫雷游戏的棋盘状态 |
| A1 B2 C3 / A-C5 / A1-5 | 挖开指定格子，支持批量与连扫区间（字母区间或数字区间，可小写） |
| 标雷 A1 B2 C3 / 标雷 A-C5 / 标雷 A1-5 | 标记地雷，支持批量与连扫区间（字母区间或数字区间，可小写） |
| 清扫 A1 / # A1 / # A1-5 | **清扫**（中键）操作，当格子周围标记的雷数等于格子数字时，自动挖开周围未标记的格子 |

**说明：**
- `标雷` 和 `清扫` 的前缀符号可在配置中自定义
- 默认标雷快捷键：`'` 和 `"`
- 默认清扫快捷键：`#`
- 操作无效果时不会刷屏（不发送棋盘图片）

### Windows GUI 模式

在插件目录下运行 `gui_launcher.py` 即可启动 Windows GUI 版本：

```bash
python gui_launcher.py
```

**操作说明：**
- 左键点击：挖开格子
- 右键点击：标记/取消标记地雷
- 点击笑脸按钮：重新开始游戏

**特性：**
- 支持多种难度选择（初级、中级、高级、自定义）
- 支持所有内置皮肤
- 完整的鼠标交互体验

## 📌 注意事项

- 如果想第一时间得到反馈，请进作者的插件反馈 QQ 群：460973561（不点 star 不给进）

## 👥 贡献指南

- 🌟 Star 这个项目！（点右上角的星星，感谢支持！）
- 🐛 提交 Issue 报告问题
- 💡 提出新功能建议
- 🔧 提交 Pull Request 改进代码
