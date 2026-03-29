"""集中定义项目级常量，避免在各处散落魔法数字。

本模块按子系统整理时序、界面尺寸和平台参数，便于统一调整。
"""

# 滚动引擎时序。
# 激活状态下的轮询间隔决定了引擎采样鼠标位移、
# 以及发送模拟滚轮事件的频率。
# 4 毫秒可以兼顾流畅度与处理器占用。
ENGINE_TICK_INTERVAL = 0.004

# 当程序未激活且惯性也未运行时，
# 引擎使用更长的休眠间隔以降低处理器占用。
# 此时不需要实时跟踪，因此可以远大于激活轮询间隔。
ENGINE_IDLE_POLL_INTERVAL = 0.05

# 当速度平方低于该阈值时，惯性滚动停止。
# 引擎内部以两个浮点分量保存速度，
# 直接比较平方值可避免每帧额外开平方。
INERTIA_STOP_THRESHOLD = 0.001

# 估算惯性初速度时，只保留最近一小段滚动和鼠标移动历史。
SCROLL_HISTORY_WINDOW = 0.1

# 输入监听时序。
# 在单击启用模式下，用于抑制快速重复中键点击
# 或某些系统连续发出近邻事件导致的重复触发。
DOUBLE_CLICK_THRESHOLD = 0.15

# 前台窗口监控。
# 启动时略微延迟，给界面和钩子初始化留出稳定时间，
# 再开始持续查询当前活动窗口和进程。
WINDOW_MONITOR_START_DELAY = 2.0

# 查询前台窗口元信息的轮询间隔，例如进程名和全屏状态。
# 这里不需要帧级精度。
WINDOW_MONITOR_POLL_INTERVAL = 0.5

# 连续失败达到该次数后，缓存的窗口元信息视为过期，
# 会被清空以避免基于旧状态继续做过滤判断。
WINDOW_INFO_FAILURE_STALE_THRESHOLD = 3

# 配置结构版本。
# 当磁盘配置结构发生需要显式迁移的变更时，应提升此版本号。
CONFIG_VERSION = 3

# 惯性默认值与编辑范围。
# 摩擦力以半衰期毫秒数表示，便于界面向用户解释，
# 避免直接暴露难以理解的衰减系数。
DEFAULT_INERTIA_FRICTION_MS = 500
INERTIA_FRICTION_MIN_MS = 100
INERTIA_FRICTION_MAX_MS = 3000

# 释放后进入惯性所需的鼠标速度阈值，单位为像素每秒。
DEFAULT_INERTIA_THRESHOLD = 80.0
INERTIA_THRESHOLD_MIN = 30.0
INERTIA_THRESHOLD_MAX = 300.0

# 平台滚动倍率。
# 滚动策略先计算方向向量和基于距离的标量，
# 再乘以平台特定倍率，用来补偿不同系统
# 对模拟滚轮单位的解释差异。
WINDOWS_SCROLL_MULTIPLIER = 0.00005
MACOS_SCROLL_MULTIPLIER = 0.0001
DEFAULT_SCROLL_MULTIPLIER = 0.00005

# 界面时序与尺寸。
# 预览持续时间以毫秒表示，因为它直接用于界面定时器。
OVERLAY_PREVIEW_DURATION = 800

# 屏幕悬浮指示器的默认直径。
DEFAULT_OVERLAY_SIZE = 60.0

# 主窗口尺寸约束。
# 默认尺寸用于首次启动，最小尺寸用于保证较小屏幕下
# 仍能容纳较密集的设置布局。
MAIN_WINDOW_MIN_WIDTH = 420
MAIN_WINDOW_MIN_HEIGHT = 680
MAIN_WINDOW_DEFAULT_WIDTH = 650
MAIN_WINDOW_DEFAULT_HEIGHT = 720

# 各对话框默认尺寸经过调整，可在常见显示缩放下尽量避免内部滚动。
WORK_MODE_DIALOG_WIDTH = 520
WORK_MODE_DIALOG_HEIGHT = 620
INERTIA_DIALOG_WIDTH = 460
INERTIA_DIALOG_HEIGHT = 420
REVERSE_DIALOG_WIDTH = 400
REVERSE_DIALOG_HEIGHT = 240
WEBDAV_DIALOG_DEFAULT_WIDTH = 500
WEBDAV_DIALOG_DEFAULT_HEIGHT = 320
WEBDAV_DIALOG_MIN_WIDTH = 500
WEBDAV_DIALOG_MIN_HEIGHT = 320

# 自定义控件构建函数共用的尺寸参数。
SLIDER_DEFAULT_HEIGHT = 24
SPINBOX_WIDTH = 70
SPINBOX_HEIGHT = 32

# 更新检查。
# 超时时间单位为秒，并且故意设置得较短，
# 因为版本检查只是尽力而为的后台任务，
# 不是关键启动依赖。
UPDATE_CHECK_TIMEOUT = 5
