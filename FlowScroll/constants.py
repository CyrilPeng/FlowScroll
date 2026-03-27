"""
FlowScroll 常量配置
集中管理项目中的魔法数字和配置常量
"""

# ==========================================
# 滚动引擎相关常量
# ==========================================

# 引擎轮询间隔（秒）
ENGINE_TICK_INTERVAL = 0.004  # 4ms，与系统滚动事件同步

# 空闲状态轮询间隔（秒）
ENGINE_IDLE_POLL_INTERVAL = 0.05  # 50ms

# 惯性停止阈值
INERTIA_STOP_THRESHOLD = 0.001  # 速度平方低于此值时停止

# 滚动历史窗口（秒）
SCROLL_HISTORY_WINDOW = 0.1  # 100ms

# ==========================================
# 输入监听相关常量
# ==========================================

# 双击检测阈值（秒）
DOUBLE_CLICK_THRESHOLD = 0.15  # 150ms

# ==========================================
# 窗口监控相关常量
# ==========================================

# 窗口监控启动延迟（秒）
WINDOW_MONITOR_START_DELAY = 2.0

# 窗口监控轮询间隔（秒）
WINDOW_MONITOR_POLL_INTERVAL = 0.5

# ==========================================
# 配置相关常量
# ==========================================

# 配置文件版本
CONFIG_VERSION = 3

# 惯性摩擦力默认值（毫秒）
DEFAULT_INERTIA_FRICTION_MS = 500

# 惯性摩擦力范围
INERTIA_FRICTION_MIN_MS = 100
INERTIA_FRICTION_MAX_MS = 3000

# 惯性触发阈值默认值（像素/秒）
DEFAULT_INERTIA_THRESHOLD = 80.0

# 惯性触发阈值范围
INERTIA_THRESHOLD_MIN = 30.0
INERTIA_THRESHOLD_MAX = 300.0

# ==========================================
# 平台相关常量
# ==========================================

# Windows 滚动乘数
WINDOWS_SCROLL_MULTIPLIER = 0.00005

# macOS 滚动乘数
MACOS_SCROLL_MULTIPLIER = 0.0001

# 默认滚动乘数（Linux 等）
DEFAULT_SCROLL_MULTIPLIER = 0.00005

# ==========================================
# UI 相关常量
# ==========================================

# 准星预览显示时间（毫秒）
OVERLAY_PREVIEW_DURATION = 800

# 默认准星大小
DEFAULT_OVERLAY_SIZE = 60.0

# 主窗口最小尺寸
MAIN_WINDOW_MIN_WIDTH = 420
MAIN_WINDOW_MIN_HEIGHT = 680

# 主窗口默认尺寸
MAIN_WINDOW_DEFAULT_WIDTH = 650
MAIN_WINDOW_DEFAULT_HEIGHT = 720

# 对话框尺寸
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

# 滑块默认高度
SLIDER_DEFAULT_HEIGHT = 24

# 数值输入框尺寸
SPINBOX_WIDTH = 70
SPINBOX_HEIGHT = 32

# ==========================================
# 更新检查相关常量
# ==========================================

# 更新检查超时时间（秒）
UPDATE_CHECK_TIMEOUT = 5
