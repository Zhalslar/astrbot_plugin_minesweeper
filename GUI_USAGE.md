# 扫雷游戏 Windows GUI 使用说明
# Minesweeper Windows GUI Usage Guide

## 快速开始 / Quick Start

### 方法 1: 使用批处理文件 (Windows)
直接双击 `start_gui.bat` 文件即可启动游戏。

### 方法 2: 使用 Python 脚本
在命令行中运行：
```bash
python gui_launcher.py
```

## 游戏操作 / Game Controls

- **左键点击** / **Left Click**: 挖开格子 / Open tile
- **右键点击** / **Right Click**: 标记/取消标记地雷 / Mark/unmark mine
- **点击笑脸** / **Click Face Button**: 重新开始游戏 / Restart game

## 难度选择 / Difficulty Levels

启动游戏后，可以选择以下难度：

1. **初级 / Beginner**: 9x9 格子，10 个地雷
2. **中级 / Intermediate**: 16x16 格子，40 个地雷
3. **高级 / Expert**: 16x30 格子，99 个地雷
4. **自定义 / Custom**: 自定义行数、列数和地雷数

## 游戏规则 / Game Rules

1. 点击一个格子会挖开它
2. 如果格子是地雷，游戏失败
3. 如果格子不是地雷，会显示周围 8 个格子中地雷的数量
4. 使用数字提示来推断哪些格子是地雷
5. 右键点击可以标记你认为是地雷的格子
6. 挖开所有非地雷格子即可获胜

## 系统要求 / System Requirements

- **操作系统 / OS**: Windows 7 或更高版本 / Windows 7 or later
- **Python**: Python 3.10 或更高版本 / Python 3.10 or later
- **依赖库 / Dependencies**:
  - tkinter (Python 自带 / Built-in with Python)
  - Pillow (PIL) - 用于图像处理 / For image processing

## 安装依赖 / Installing Dependencies

如果提示缺少 Pillow，可以使用以下命令安装：
```bash
pip install Pillow
```

## 更换皮肤 / Changing Skins

当前 GUI 默认使用 "default" 皮肤。如需使用其他皮肤，可以编辑 `gui_launcher.py` 文件中的 `skin_name` 参数。

可用皮肤列表 / Available skins:
- clone
- colorsonly
- hibbeler
- icicle
- mario
- maviz
- mine
- narkomania
- ocean
- pacman
- predator
- scratch
- symbol
- unknown
- vista
- win98
- winbw
- winxp (默认 / default)

## 故障排除 / Troubleshooting

### 问题: 提示找不到 tkinter
**解决方案**: 确保安装了完整的 Python，tkinter 通常是标准库的一部分。

### 问题: 提示找不到 PIL/Pillow
**解决方案**: 运行 `pip install Pillow` 安装 Pillow 库。

### 问题: 游戏窗口无法显示
**解决方案**: 
1. 检查是否在 Windows 系统上运行
2. 确保 Python 版本为 3.10 或更高
3. 尝试更新显卡驱动程序

## 技术支持 / Technical Support

如有问题，请访问项目仓库提交 Issue:
https://github.com/Zhalslar/astrbot_plugin_minesweeper
