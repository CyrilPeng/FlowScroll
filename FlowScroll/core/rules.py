from FlowScroll.core.config import cfg
from FlowScroll.platform import OS_NAME


def is_current_app_allowed():
    """
    统一的规则匹配逻辑，判断当前前台应用是否被允许使用平滑滚动
    """
    if cfg.disable_fullscreen and cfg.is_fullscreen:
        return False

    # 拦截 Windows 桌面
    if cfg.disable_desktop and OS_NAME == "Windows":
        if cfg.current_window_class in ("Progman", "WorkerW"):
            return False

    if cfg.filter_mode == 0:
        return True

    app_name = cfg.current_window_name.lower()

    # 黑名单模式
    if cfg.filter_mode == 1:
        for keyword in cfg.filter_list:
            if keyword.lower() in app_name:
                return False
        return True

    # 白名单模式
    elif cfg.filter_mode == 2:
        for keyword in cfg.filter_list:
            if keyword.lower() in app_name:
                return True
        return False

    return True
