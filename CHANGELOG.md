# CHANGELOG

## v1.3.1

New Features:
- 添加 `MessageSender` 工具类，将棋盘图片保存到缓存中，并在包括 QQ 官方机器人和 OneBot 在内的受支持平台上发送这些图片。
- 支持在平台允许的情况下，按会话和发送者维度，通过回溯上一条消息来替换最近一次发送的棋盘图片。

Enhancements:
- 重构 `CommandHandler` 和主初始化流程，使其在棋盘渲染与投递上依赖 `MessageSender` 而非 `ImageService`。
- 在 `CommandHandler` 中通过基于事件来源的统一游戏键，规范游戏查找逻辑。
- 在新的核心 sender 到位后，移除旧的顶层 sender 模块。

## v1.3.0

New Features:

- 为扫雷添加 AstrBot WebUI 仪表盘页面，提供交互式棋盘控制和实时游戏状态。
- 暴露用于管理扫雷游戏的 HTTP API 和服务器推送事件，以在 WebUI 与聊天会话之间同步棋盘。
- 支持通过机器人命令和配置更新来创建并持久化自定义难度等级。

Enhancements:

- 重构命令处理流程，使用集中式的 `GameService` 共享游戏实例，实现统一的位置解析和一致的封禁逻辑。
- 简化配置，将基于快捷键的标记/扫雷模式替换为单一前缀字段和正则辅助工具。
- 扩展游戏核心以跟踪显示名称、已用时间，并为 UI 和 API 使用方提供 JSON 快照。
- 调整图片处理方式，对 CQHTTP 使用 base64 发送并移除未使用的 GUI 特定逻辑。
- 更新 README，描述对 WebUI 的支持以及新的难度创建命令。