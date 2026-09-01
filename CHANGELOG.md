# Changelog

## v1.9.1

### Fixed
- 修复 Windows 延迟启动模式下原生中键按下与松开事件不配对的问题；短按现在重放完整中键点击，长按激活 FlowScroll 时不再向目标应用遗留按下状态
- 修复 macOS launchd 自启动把可执行路径和 `--silent` 拼成单个参数导致启动失败的问题，并检测过期的 plist 参数
- 修复配置写入失败后仍提示成功、配置存储指针可能切换到不可写路径的问题；新路径写入失败时保持原路径生效
- 修复 WebDAV 下载配置未经校验、异常字段可能造成部分配置生效的问题；远程配置现在完整校验后一次性应用

### Improved
- 修复 Qt 无头降级分支和平台单例的类型声明，使项目 MyPy 检查恢复通过
- 增加版本一致性和代码质量 CI 门禁，发布标签必须与源码及锁文件版本一致

### Tests
- 补充 Windows 中键事件配对、macOS 自启动、配置路径回滚、损坏 WebDAV 配置及版本一致性回归覆盖

## v1.9.0

### Added
- 新增 CLI 参数支持：`--silent` / `-s` 静默启动（窗口不显示，仅托盘运行）、`--version` / `-v` 显示版本号、`--help` / `-h` 显示帮助信息
- 开机自启动自动携带 `--silent` 参数，实现真正的后台静默启动

### Changed
- `--version` 和 `--help` 在 Windows 上以消息框形式显示（兼容无控制台的 GUI 应用）

### Tests
- 新增 CLI 参数解析测试（`tests/test_cli.py`）
- 更新自启动管理器测试以匹配新的 `--silent` 参数行为

## v1.8.1

### Fixed
- 修复 Windows 延迟启动模式下，浏览器中键点击网页链接被 FlowScroll 提前拦截，导致 Chrome / Edge 无法在后台打开新标签页的问题

### Tests
- 补充 Windows 中键延迟启动事件放行与激活态关闭抑制的回归测试

## v1.8.0

### Fixed
- 修复配置路径平台判断被缓存后污染跨平台测试的问题，确保模拟 Windows 时使用正确路径分隔符
- 修复 WebDAV 上传配置时调用缺失同步序列化接口导致的异常
- 修复删除自定义预设时访问错误控制器属性导致的异常
- 修复准星覆盖层淡出后未真正隐藏的问题
- 修复语言切换后内置预设显示名可能沿用旧语言的问题

### Improved
- 拆分 UI 组件、设置窗口 Mixin 与对话框模块，降低单文件复杂度
- 新增速度曲线可视化与托盘预设/横向滚动快捷操作
- 优化滚动引擎低速精度、惯性估算、窗口监控停止流程与日志轮转
- 调整打包配置，确保拆分后的 FlowScroll 子包被正确包含

### Tests
- 补充配置、规则、快捷键、预设、对话框、组件与输入监听回归测试

## v1.7.13

### Fixed
- 因 Gitee 仓库地址变化，所以修改 Gitee 回退地址

## v1.7.12

### Improved
- 卡片悬浮时边框高亮并微调背景色，增强交互反馈
- 标签栏改为胶囊式圆角选中样式，替代下划线指示
- 滑块手柄增加放大悬浮态和收缩按下态，操作手感更明确
- 下拉框统一定制下拉列表主题样式，选中项蓝色高亮
- 补全按钮、输入框、复选框、滑块、下拉框的禁用态样式
- 准星覆盖层改为蓝色半透明光晕中心 + 渐变方向箭头，视觉更现代
- 高级设置页按功能拆分为三个分区：滚动行为、系统集成、数据与同步，结构更清晰
- 标题字重统一为 700，标签和选项卡为 600，数值输入框字号缩小至 13px
- 高频操作按钮（反转、工作模式、应用过滤）保留蓝色边框，低频操作按钮（WebDAV、配置存储）改为灰色次要样式
- 预设保存按钮添加文件夹图标

## v1.7.11

### Fixed
- 修复 Windows 下白名单正则匹配时左键/右键点击可能失效的问题：滚动激活态下普通左右键点击现在会先退出滚动模式，但不会拦截当前点击事件
- 补充左键/右键取消滚动激活态的回归测试，覆盖白名单精确正则更容易触发的输入状态残留问题

## v1.7.10

### Fixed
- 修复 v1.7.8 起 Windows exe 体积从 23MB 飙升至 80MB 的问题：移除 `zstandard` 运行依赖后 Nuitka onefile 压缩静默失效，现将 `zstandard` 作为 CI 构建依赖恢复压缩

### Improved
- 三平台构建排除 20 个未使用的 PySide6 模块（QtWebEngine、Qt3D、QtMultimedia、QtQuick 等），减小产物体积

## v1.7.9

### Fixed
- 修复长按模式下惯性滚动与激活冲突的问题：惯性运行期间按下激活键时，中断惯性后未继续执行激活逻辑，导致按住期间不滚动

## v1.7.8

### Fixed
- 修复 `ScrollEngine` 中 `inertia_active`/`inertia_vx`/`inertia_vy` 的数据竞争：新增 `_inertia_lock` 专用锁，保护引擎线程与输入线程之间的惯性状态读写
- 修复 `GlobalConfig.from_dict()` 批量写入无锁保护导致其他线程读到半更新配置的问题：整体操作包裹在 `STATE_LOCK` 内。同步修复 `from_webdav_dict()`
- 修复 `_to_dict_common()` 中 `filter_blacklist`/`filter_whitelist` 直接暴露可变列表引用的问题，改为返回防御性副本
- 修复 `KeyboardManager.current_keys` 集合在 pynput 回调线程中的 add/discard 与快照拷贝不原子的问题：新增 `_keys_lock` 保护
- 修复 `_compute_friction()` 中 tick 间隔硬编码为 `4.0` 的问题，改为从 `ENGINE_TICK_INTERVAL` 常量动态计算
- 修复 `win32_event_filter` 中 `suppress_event()` 后 `return False` 可能导致 pynput 监听线程意外终止的问题，改为 `return None`
- 修复 `WM_MBUTTONDBLCLK (0x0209)` 被误当作按下事件触发二次激活切换的问题，双击事件现在仅被抑制而不触发逻辑
- 修复 `set_persisted_config_file()` 非原子写入导致崩溃时配置指针文件损坏的问题，改为 write-to-temp + `os.replace` 原子替换
- 修复 `from_dict()` 中 `filter_mode == 0`（禁用过滤）时旧版 `filter_list` 同时填充黑名单和白名单的问题，现在仅填充黑名单

### Improved
- `ApplicationController.start_threads()` 新增重复调用守卫，在重复调用时先停止旧线程再启动新线程
- macOS 前台窗口检测优先使用 `AppKit NSWorkspace` 原生 API（零子进程开销），不可用时回退到 `osascript` 并带 `timeout=2`
- Linux 前台窗口检测从 4 次独立 `xprop` 子进程调用合并为 1 次批量查询，减少进程创建开销
- 单实例 IPC 消息读取添加 1024 字节上限，防止恶意本机进程发送大量数据
- 崩溃提示框从硬编码中文改为通过 `tr()` 国际化，非中文用户可看到英文消息
- 内置预设名称完成 i18n 全流程集成：combo box 和对话框均显示本地化名称，内部键名不变以保持配置兼容
- `sync_ui_from_config()` 和 `update_hotkey_label()` 中的 `cfg` 属性读取统一纳入 `STATE_LOCK` 保护，与项目加锁纪律一致
- `ScrollEngine` 新增 `_stop_event` 和 `request_stop()` 方法，支持优雅停止与 `join()`，不再依赖守护线程强制终止
- `MainWindow` 移除全部 15+ 代理属性，`tabs_builder` / `dialogs` 改为直接访问 `main_window.ctrl.*`，减少维护噪音
- 配置文件写入（`preset_manager.save_to_file` 和 `set_persisted_config_file`）统一改为 `tempfile.mkstemp` + `os.replace` 原子写入，非 Windows 下设置 `0o600` 权限

### Removed
- 移除未使用的 `zstandard` 依赖

## v1.7.7

### Changed
- `MainWindow` 重构为 `ApplicationController`，`ui/app_controller.py` 成为主界面 UI 架构的单一可信来源，所有配置读写、状态管理、跨组件通信均通过它完成
- `BUILTIN_PRESETS` 重命名为 `_PRESET_DEFAULTS`，避免与运行时变量混淆，语义更清晰
- `GlobalConfig.to_dict` / `to_dict_for_sync` 合并为 `_to_dict_common` 辅助方法，消除重复序列化逻辑
- `ScrollEngine.run()` 改为在进入 `STATE_LOCK` 前调用 `_snapshot_config()` 快照配置
- `test_smoke.py` 中 500+ 行测试代码拆分为 `test_config.py`、`test_services.py`、`test_keyboard_webdav.py`
- `single_instance.py` 中的校验算法从 SHA-1 升级到 SHA-256
- `i18n.py` 移除对 `cfg` / `STATE_LOCK` 的直接依赖，通过信号/槽机制实现翻译器与配置层解耦
- `main.py` 在 Windows 异常处理中添加 `traceback.print_exc()` 辅助诊断，再初始化 `QApplication`

### Fixed
- 修复 `FlowScroll.input.listeners` 与 `FlowScroll.core.hotkeys` 的顶层导入硬依赖问题；当测试或无头环境仅提供部分 `pynput` / `PySide6` mock 时，现在可正常导入模块，并将失败延后到实际启用输入监听或处理 Qt 按键事件时再显式报错
- 修复 `ScrollEngine` 中 `_scroll_history` / `_mouse_pos_history` 的并发问题：`interrupt_inertia` 中遍历并计算历史极值的操作存在竞态/读取脏数据的风险，统一改为 `collections.deque` + 独立 `_history_lock` 保护；废弃原地截断策略，实现 `_prune_history` 并改用 `popleft()` 保证 O(1) 复杂度
- 修复 UI 层直接修改 `cfg` 导致的数据竞争问题：`tabs_builder`、`settings_window`、`dialogs`、`webdav_dialog` 中多处 `cfg.xxx = ...` 调整为 `set_config_attr()`，并配合 `STATE_LOCK` 加锁写入
- 修复 `GlobalInputListener` 中重复创建监听器的问题，移除冗余的 `mouse.Controller()` 实例化，改为线程间复用
- 修复 WebDAV 同步地址包含 `http://` 协议前缀时的路径拼接错误，确保同步路径正确解析
- 修复 `overlay.py` 中 `show_preview` 使用 `geometry()` 而非 `availableGeometry()` 导致超出屏幕边缘的问题 + 修复 DPI 缩放下的显示异常
- 修复 `autostart.py` 中 docstring 的错误引用与格式问题
- 修复 `main.py` 异常提示框 Windows `MessageBoxW` 调用中 `\n` 被错误转义为换行的问题
- 修复 `ApplicationController.start_threads()` 中 `ScrollEngine` 启动失败后的错误消息仍然指向已废弃的 `MainWindow._start_threads()`，改为正确指向 `ApplicationController`
- 修复 `ScrollEngine.run()` 中 active 状态的 busy-wait 空转问题，改为事件驱动等待，显著降低 CPU 占用
- 修复 `GlobalInputListener` 中键盘快捷键组合键的重复触发问题：当组合键中包含修饰键时，重复按下修饰键会导致快捷键被多次触发

### Improved
- GitHub Actions 的测试依赖安装改为 `uv sync --frozen --extra dev`，并将 CI / Release workflow 中的 `uv sync` 统一切换到 `--frozen`，避免 `uv pip install pytest` 这类绕过 `uv.lock` 的依赖漂移
- 完善核心模块与 UI 组件的 docstring 文档：`app_controller.py`、`settings_window.py`、`engine.py`、`config.py`、`listeners.py`、`webdav_dialog.py`、`i18n.py`、`single_instance.py`、`overlay.py`、`main.py`
- 补充核心逻辑与集成测试的注释说明：`test_engine.py`、`test_config.py`、`test_services.py`、`test_keyboard_webdav.py`
- 新增 `set_config_attr(name, value)` 辅助方法，统一处理 UI 层对 `cfg` 的写入操作，避免多处重复加锁逻辑
- `listeners.py` 中 `import platform` 移至文件顶部，优化导入层级

### Added
- 在 `tests/test_app_controller.py` 中补充 `hotkeys` 模块在缺少 `Qt` 时仍可导入的回归测试，锁定最小 mock 场景下的导入稳定性
- 新增 `tests/test_engine.py` 中的 23 个测试用例，覆盖 `PowerCurveStrategy` 的各个分支与 `ScrollEngine` 的集成
- `PowerCurveStrategy` 的策略切换、边界值处理、极小/极大值输入均有测试覆盖
- `ScrollEngine` 的配置快照、历史窗口、惯性中断、竞态条件保护均经过验证
- 新增 `test_config.py` 中 `test_to_dict_for_sync_equals_to_dict` 与 `test_all_presets_share_common_defaults` 回归测试
- 新增 `webdav.insecure_http_warning` 开关的 UI 绑定与功能测试
- 新增 `tests/test_app_controller.py`，验证 `ScrollEngine` 启动失败时 `start_threads()` 的异常处理
- 在 `tests/test_engine.py` 中补充 active 状态切换的测试用例，确保事件驱动避免 CPU 空转
- 在 `tests/test_input_listener_timing.py` 中补充输入监听时序测试，验证防抖与延迟触发逻辑

### Removed
- 移除 `services/crypto.py` 及基于 XOR 的旧版配置加密逻辑，统一使用系统密钥环管理敏感信息

### Changed
- `flowscroll-homepage` 站点升级：更新品牌标识、添加特性说明与安装引导、优化多设备响应式布局/排版
- 首页增加下载按钮，直接链接到最新版本，同时保留 GitHub / Gitee 入口
- README 与 README.en 中的项目官网链接更新为 `https://flowscroll.pages.dev/`
- 更新项目发布流程：优先同步到 GitHub Releases，再镜像到 Gitee Releases，确保两个平台的版本一致性
- 在 README 中添加演示 GIF 的加载优化，提升国内用户的浏览体验
- 修复项目官网在 macOS Safari 浏览器下的显示异常，添加兼容性处理
- 清理废弃的 GitHub / Releases / Gitee 同步脚本，移除不再使用的 manifest / JSON 配置文件

## v1.7.6

### Added
- 新增“配置存储位置”管理能力：支持在高级设置中通过独立弹窗查看当前配置文件位置，并提供“修改路径”“恢复默认”“打开所在目录”“复制当前路径”等操作
- 新增配置路径指针文件机制：当用户自定义配置文件位置时，会在默认应用数据目录保存一个轻量指针文件，用于下次启动时定位真实配置文件
- 新增配置路径相关回归测试，覆盖默认 Windows 路径、自定义路径覆盖、旧 `~/.FlowScroll_config.json` 迁移、新路径指针持久化以及高级设置页面 smoke

### Changed
- 默认配置文件位置从用户主目录下的 `~/.FlowScroll_config.json` 调整为平台标准应用数据目录
- README 与 README.en 中的配置文件位置说明同步更新，补充默认路径规则以及 `FLOWSCROLL_CONFIG_FILE` / `FLOWSCROLL_CONFIG_DIR` 两个环境变量覆盖方式
- “修改配置路径”入口调整为与其他高级设置一致的大按钮样式，并改为在专用弹窗中统一处理路径查看与切换

### Fixed
- 配置加载流程现在会优先读取新路径，同时兼容旧的主目录隐藏配置文件，并在后续保存时自动迁移到新路径或用户指定路径
- 预设管理与 WebDAV 下载后的本地落盘统一改为使用新的配置路径解析逻辑，避免仍然写回旧硬编码位置
- 环境变量覆盖配置路径时，界面会正确提示当前路径由环境变量控制，避免 GUI 自定义路径与环境变量配置互相冲突
- 修复 Windows 环境下自启动配置失效的问题：自启动写入改为标准命令格式，自动处理带空格路径的引号；同时优化状态判断逻辑，减少路径格式差异导致的误判

## v1.7.5

### Fixed
- 修复自动语言识别优先读取 Windows UI 语言与 Qt 系统语言的逻辑，避免在 Windows 环境下错误回退到 `locale` 或环境变量
- 修复 `test_get_system_language_falls_back_to_env` 在 Windows CI 上未隔离系统语言探测器导致的误失败，确保该测试只验证环境变量回退链

## v1.7.4

### Added
- 新增"隐藏导航准星"选项，可在高级设置中开启，完全隐藏滚动模式下的准星指示器

### Fixed
- 修复导航指示器大小过小时准星渲染异常（中心圆向右下角偏移）的问题
- 导航指示器大小最小值调整为 20，避免因尺寸过小导致的渲染问题

## v1.7.3

### Added
- 应用过滤新增正则表达式匹配模式：黑白名单默认仍为模糊匹配，用户可在过滤设置中勾选"启用正则表达式匹配"切换为正则模式；无效正则表达式自动跳过，不影响其他规则正常匹配
- 新增正则过滤功能测试模块，覆盖模糊/正则匹配、黑白名单、无效正则容错、配置序列化、缓存与保存校验等场景

### Fixed
- 修复高级设置页构建时缺少 Qt 相关导入导致的启动即崩溃问题，并为对应的 UI 构建路径补充回归测试
- 修复 Linux / macOS 在使用 `uv run` 等源码运行时自启动命令丢失 Python 解释器的问题，确保非打包环境下也能正常写入自启动项
- 修复 WebDAV 连接信息被混入预设配置的问题，调整为单独持久化 `webdav` 字段，避免切换预设时悄悄改写同步目标，并兼容旧配置迁移
- 修复国际化语言检测中对 `locale.getdefaultlocale()` 的弃用调用，改为 `getlocale` 与环境变量回退链，消除 Python 3.15 兼容性警告
- 修复 Windows 下未启用开机自启时将缺失注册表项误记为 debug 错误的问题，改为安静返回 `False`
- 修复部分 WebDAV 服务在根目录地址下直接上传 `FlowScroll_config.json` 返回 404 的兼容性问题；上传失败时会自动回退到 `FlowScroll/FlowScroll_config.json`，并在下载时同时兼容旧路径与新路径
- 补充 WebDAV 路径规范化与根目录回退上传/下载的回归测试，避免后续修改再次引入同类问题
- 修复 Linux CI 在缺少 `libEGL.so.1` 的 headless 环境下导入 `webdav_dialog` 和 `tabs_builder` 即失败的问题；将可测试的非 UI 逻辑与 Qt Widgets 依赖解耦，确保 WebDAV 错误格式化与配置持久化相关测试可正常运行
- 修复应用过滤正则表达式保存校验的报错行号偏移问题，改为基于原始输入行号提示
- 将正则规则校验抽离到核心模块并补充无 GUI 依赖的单元测试，避免无头环境下相关逻辑仅通过 UI 测试覆盖

### Improved
- 日志策略调整为“开发源码运行时控制台输出 DEBUG，二进制发行时仍保持 ERROR 级别”，兼顾排查效率与发行体积
- 补充自启动、WebDAV 配置隔离、Windows 日志降噪和语言回退等多条回归测试，提升后续修改的稳定性

## v1.7.2

### Fixed
- 修复主界面参数调整后未立即持久化的问题，现在包括“导航指示器大小”在内的主要参数和开关在修改后会立刻保存，重启后不再丢失

## v1.7.1

### Fixed
- WebDAV 连接失败时新增 URL 校验与更清晰的错误提示，包括连接被拒绝、超时、域名解析失败和 HTTP 异常
- WebDAV 相关错误日志改为结构化记录，包含 `mode`、`url`、`username`（脱敏）、`status/error` 和 `duration_ms`，便于排查
- 日志策略收紧为“仅在出错时记录”，避免正常运行产生多余 `app.log`

## v1.7.0

### Fixed
- 恢复 `main` 分支的开发版版本纪律：版本号回到开发版本，并保留 `Unreleased` 区段以满足 CI 校验
- 修复 Linux AppImage 打包产物缺少 `AppRun` 入口脚本的问题，并补齐 `.desktop` 与图标安装路径
- 修复英文界面下快捷键输入框占位符仍显示中文的问题，统一改为走多语言词条

### Improved
- README 底部新增“关于代码 / About The Code”说明，以更诚恳且克制的方式交代项目的迭代背景、AI 辅助生成特征与期望的反馈方式
- 输入监听启动失败提示按平台环境细化，补充 Windows、macOS、Linux Wayland/X11 的排查说明
- 高级设置页新增输入监听状态提示条；当键盘和鼠标监听均不可用时，相关输入入口会临时置灰
- “工作模式”相关文案改为更统一、易理解的术语，使用“单击启用”“按住启用”“延迟启动”等表述
- README 补充“延迟启动”说明，明确其主要用于避免“中键单击”原生行为与 FlowScroll 启动动作发生冲突
- WebDAV 上传/下载改为后台线程执行并增加超时，避免网络异常时界面阻塞
- 本地配置文件新增当前用户配置持久化，使当前实际生效的参数与预设信息可一起保存

### Added
- 新增单实例保护，避免重复启动后多个进程同时注册全局输入钩子、滚动线程和托盘导致互相冲突
- 重复启动时改为唤醒已有实例并弹出明确提示，避免第二个进程静默退出
- 重复启动提示框改为继承应用默认 logo，修复标题栏图标显示为空白占位的问题

## v1.6.3

> 稳定版发布：本版本对应当前本地发布提交，`main` 分支后续可继续前进。

### Changed
- `main` 分支版本切换为开发中标识，稳定版本以 Release / Git tag 为准

### Changed
- 更新检查改为显式语义化版本比较，正式版会正确覆盖同版本号的 dev/rc 预发布版本
- 应用过滤改为“优先进程名，失败时回退到窗口标题”，并在 UI 中显示相应提示

### Fixed
- 线程启动流程分离 `WindowMonitor`、`ScrollEngine`、`GlobalInputListener` 的失败路径，避免滚动引擎启动失败后被误报为键鼠权限问题

## v1.6.2

### Fixed
- 补齐托盘菜单与 WebDAV 对话框的中英文界面文案，确保语言切换覆盖完整
- 清理主窗口中残留的失效高级设置切换代码，避免后续误接线触发运行时错误

## v1.6.1

### Changed
- 黑白名单匹配机制改为优先进程名匹配，并在无法获取进程名时回退到窗口标题匹配

### Improved
- 同步更新中英文 README 与应用过滤相关界面文案，明确关键词按进程名匹配

## v1.6.0

### Added
- 新增中英文界面资源，并支持在主界面切换 UI 语言

### Fixed
- 修复 `CapsLock` / `NumLock` / `ScrollLock` 等键位在输入监听中的标准化匹配问题

## v1.5.3

### Fixed
- 修复防误触延迟触发时使用按下坐标的问题，改为触发当下读取实时鼠标坐标，避免激活瞬间位移跳变
- 修复点击模式防抖与惯性历史窗口对系统时钟跳变敏感的问题，统一改用 `time.monotonic()`
- 修复多线程下 `cfg/runtime` 并发读写导致的偶发状态抖动问题，引入线程锁并在输入监听、滚动引擎、窗口监控与规则判断中使用快照/加锁访问

### Added
- 新增两条输入时序回归测试：延迟激活实时坐标测试、monotonic 防抖测试

### Improved
- CI/CD 流程拆分：新增面向 push/PR 的常规 CI（依赖安装 + pytest），Release workflow 聚焦 tag 打包与发布

---

## v1.5.1

### Improved
- 工作模式弹窗视觉重构：统一为卡片化层级、用户化文案与更清晰的信息节奏
- 应用过滤模式弹窗视觉重构：模式区与关键词区分层，标题与操作更易理解
- 应用过滤关键词区域布局优化：标题居中、导入/清空按钮横向铺满并与文本框对齐
- 统一惯性滚动设置弹窗风格，与工作模式/过滤模式保持一致

### Fixed
- 修复防误触文案重复与可读性问题
- 修复应用过滤按钮高度与布局异常导致的文本框位移问题

---

## v1.5.0

### Added
- 新增“防误触模式”与“触发等待时间”，支持鼠标/键盘启用键统一延迟触发，减少误触
- 新增应用过滤独立图标 `ic_filter.svg`，提升入口语义一致性

### Improved
- 将“应用过滤模式”从“工作模式”中拆分为独立弹窗
- 高级设置页新增独立入口按钮：“配置应用过滤模式”
- 优化工作模式相关文案，改为更贴近用户理解的描述

### Fixed
- 修复点击模式下开启防误触后“关闭也被延迟”的问题，改为按快捷键立即关闭
- 修复 `CapsLock` / `NumLock` / `ScrollLock` 等键名归一化兼容性问题
- 修复 Linux CI 中 `PySide6.QtGui` 导入导致测试失败的问题（延迟导入 `QKeySequence`）

---

## v1.4.4

### Fixed
- 修复工作模式中 `Ctrl+字母` 键盘快捷键在部分环境下无法触发的问题（控制字符归一化）
- 修复键盘按键 `char` 缺失时的回退识别问题，补充 `vk` 到字母/数字的映射

### Added
- 新增快捷键归一化单元测试，覆盖 `Ctrl+字母` 控制字符与 `vk` 回退路径
- 新增纯 mock 测试方案，在无 `pynput` 环境也可验证上述逻辑

---

## v1.4.3

### Improved
- Windows 自启动写入改为标准命令格式，自动处理带空格路径的引号
- Windows 自启动状态判断改为路径归一化 + 可执行文件提取比较，减少格式差异导致的误判

### Fixed
- 修复开发环境下 Windows 自启动项仅写入脚本路径导致无法直接启动的问题
- 优化 Windows 平台注册表读写流程，使用上下文管理避免句柄泄漏

---

## v1.4.2

### Added
- 应用过滤支持黑白名单分离存储：新增 `filter_blacklist` 与 `filter_whitelist`
- 应用过滤弹窗改为双输入框（左黑名单、右白名单）
- 黑白名单均新增“导入 / 清空”小按钮，支持从文本文件导入关键词
- 新增 FAQ 文档章节，补充常见问题与排查说明

### Improved
- 发布工作流改为优先使用 Git Tag 注入版本，避免产物版本号与 tag 不一致
- 更新检测改为语义化版本比较，忽略预发布版本（alpha/beta/rc/dev）
- 多个设置弹窗改为“最小尺寸 + 可拉伸 + 自适应初始高度”，提升高 DPI 兼容性
- WebDAV 弹窗按钮样式优化，修复中文文字被裁切问题

### Fixed
- 修复“清空关键词”误触风险：新增确认弹窗
- 修复预设加载后部分 UI 状态不同步问题（包含全屏禁用项）
- 补充并通过 smoke tests，覆盖白名单与版本比较等关键逻辑

---

## v1.4.0

### Added
- 新增惯性滚动功能：松开中键后页面继续滑行并逐渐停下，模拟触控板手感
- 惯性滚动设置弹窗：支持调节阻尼/摩擦力（半衰期 100~3000ms）和触发阈值（30~300 px/s）
- 高级设置新增"启用惯性滚动"开关及齿轮设置入口
- 支持"急刹车"机制：惯性滑动中点击鼠标或按键盘立即停止

### Improved
- ScrollEngine 重构为三态状态机（inactive / active / inertia），惯性逻辑复用现有滚动循环
- 鼠标速度历史记录采用滑动窗口最大模值算法，更准确捕获用户释放意图
- 摩擦系数通过半衰期自动换算，用户无需理解底层参数

---

## v1.3.5

### Added
- 工作模式新增"启用模式"设置，支持"点击中键启用/关闭"和"长按中键时启用"两种模式
- 工作模式弹窗为"全局模式"和"黑名单模式"增加功能说明
- 工作模式为两种启用模式分别新增“启用键”设置，支持键盘键、媒体键和鼠标侧键，留空时默认使用鼠标中键

### Improved
- 高级设置页移除重复的分组标题，将反转模式、工作模式和云同步入口合并进同一张设置卡片，同时保留原有大按钮样式
- README 更新启用模式、启用键、WebDAV 入口和预设入口说明，文档与当前界面保持一致

### Fixed
- 修复 NEW 标识点击后打开本地资源管理器而非浏览器的问题
- 修复版本检测功能稳定性，新增检测失败时的日志输出
- 修复“配置预设”下拉框弹出时先向下闪烁再上弹的问题
- 修复预设覆盖保存与删除时缺少确认提示的问题
- 修复横向穿梭模式快捷键对鼠标侧键、音量键和媒体播放键等映射按键的兼容性问题，并统一热键规范化逻辑
- 修复点击启用模式下，默认鼠标中键开启功能后被任意鼠标左键或右键错误关闭的问题

---

## v1.3.3

### Fixed
- CI：移除已废弃的 sync_version.py 调用

---

## v1.3.2

### Added
- 新增反转模式：支持独立反转纵向 / 横向滚动方向

### Removed
- 移除 sync_version.py 及相关版本同步逻辑

---

## v1.3.1

### Improved
- 预设下拉框改为向上弹出，避免遮挡下方内容
- 禁止滚轮意外调整滑块和数值框的值
- NEW 标识变为可点击按钮，可直接跳转最新版本页面
- 版本更新检测新增 Gitee 回退，提升国内网络可访问性

### Fixed
- 修复"导航指示器大小"调节项实时预览不生效的问题

---

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
