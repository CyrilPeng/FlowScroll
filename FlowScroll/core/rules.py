from FlowScroll.core.config import STATE_LOCK, cfg, runtime
from FlowScroll.platform import OS_NAME


def is_current_app_allowed() -> bool:
    """
    缁熶竴鐨勮鍒欏尮閰嶉€昏緫锛屽垽鏂綋鍓嶅墠鍙板簲鐢ㄦ槸鍚﹁鍏佽浣跨敤骞虫粦婊氬姩
    """
    with STATE_LOCK:
        disable_fullscreen = cfg.disable_fullscreen
        is_fullscreen = runtime.is_fullscreen
        disable_desktop = cfg.disable_desktop
        current_window_class = runtime.current_window_class
        filter_mode = cfg.filter_mode
        app_name = runtime.current_window_name.lower()
        filter_blacklist = list(cfg.filter_blacklist)
        filter_whitelist = list(cfg.filter_whitelist)

    if disable_fullscreen and is_fullscreen:
        return False

    # 鎷︽埅 Windows 妗岄潰
    if disable_desktop and OS_NAME == "Windows":
        if current_window_class in ("Progman", "WorkerW"):
            return False

    if filter_mode == 0:
        return True

    # 榛戝悕鍗曟ā寮?
    if filter_mode == 1:
        for keyword in filter_blacklist:
            if keyword.lower() in app_name:
                return False
        return True

    # 鐧藉悕鍗曟ā寮?
    if filter_mode == 2:
        for keyword in filter_whitelist:
            if keyword.lower() in app_name:
                return True
        return False

    return True
