# Changelog

## v1.3.0

### Improved
- 内置 4 个预设（网页阅读 / 代码办公 / 长文档表格 / 轻柔触控板），降低上手门槛
- 配置预设移至"参数调校"标签页，操作更直观
- WebDAV 云同步移入独立模态框
- 工作模式与应用过滤设置分离到独立模态框
- 版本更新提示改为 NEW 标识，更直观
- 统一版本号管理，崩溃日志包含版本信息
- README 新增权限说明、隐私说明、已知兼容性问题、内置预设参数表

### Fixed
- 修复 GlobalConfig 缺失 `disable_desktop` 属性导致 `rules.py` 运行时崩溃
- 消除 `MainWindow` 中重复的应用过滤逻辑
- 修复崩溃日志中 `Error` 行多余转义符

### Removed
- 移除悬浮窗（导航指示器）及相关代码
- 清理死代码：`overlay.py`、`state.py`、`diagnostics.py`、`github_icon_yellow.svg`
- 移除所有 tooltip 悬浮窗

### Known Issues
- macOS 全屏检测不精确，"全屏模式下自动禁用"功能暂不生效
- Wayland 环境下无法使用（需切换至 X11 会话）
- 部分 Windows UWP 应用鼠标钩子可能无法穿透

---

## v1.0.3

- 初始releases版本
