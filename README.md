
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

现在支持 AstrBot WebUI 页面，可以跨平台用鼠标操作扫雷，并与群聊共享同一个棋盘。

## 📦 安装

在 AstrBot 的插件市场搜索 `astrbot_plugin_minesweeper`，点击安装即可。

## ⚙️ 配置

请在 AstrBot 面板配置，插件管理 -> astrbot_plugin_minesweeper -> 操作 -> 插件配置

## ⌨️ 命令

### AstrBot 聊天命令

| 命令 | 说明 |
|:----:|:-----|
| 扫雷 <初级/中级/高级> [皮肤序号] | 使用预设难度开始扫雷游戏，可指定皮肤序号 |
| 新建扫雷难度 <名称> <行> <列> <雷数> | 新增并保存自定义难度（例如：新建扫雷难度 专家 20 30 120），之后可使用 `扫雷 专家` 开始游戏 |
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

## 📌 注意事项

- 如果想第一时间得到反馈，请进作者的插件反馈 QQ 群：460973561（不点 star 不给进）

## 👥 贡献指南

- 🌟 Star 这个项目！（点右上角的星星，感谢支持！）
- 🐛 提交 Issue 报告问题
- 💡 提出新功能建议
- 🔧 提交 Pull Request 改进代码
