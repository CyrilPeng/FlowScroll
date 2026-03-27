"""
凭据安全存储服务。
优先使用系统钥匙串 (macOS Keychain / Windows Credential Manager /
Linux Secret Service)。不可用时保守降级：不落盘密码，仅在会话内存中保留。
"""

from FlowScroll.services.logging_service import logger

_SERVICE_NAME = "FlowScroll"
_KEY_WEBDAV = "webdav_password"
_PROBE_KEY = "_probe"


class CredentialService:
    """WebDAV 密码安全存储，优先系统 keyring。"""

    def __init__(self):
        self._keyring_available = False
        self._keyring = None
        self._memory_password = ""
        self._init_keyring()

    def _init_keyring(self):
        try:
            import keyring

            backend = keyring.get_keyring()
            if backend is None:
                logger.info("keyring 无后端，降级为内存存储")
                return

            # keyring 约定：可用后端 priority > 0，null/fail 后端 priority <= 0
            priority = getattr(backend, "priority", 0)
            if priority <= 0:
                logger.info(
                    f"keyring 后端 {backend.__class__.__name__} priority={priority}，"
                    "降级为内存存储"
                )
                return

            # 实际探测：写入 + 读取 + 删除，确认后端真正可用
            try:
                keyring.set_password(_SERVICE_NAME, _PROBE_KEY, "ok")
                result = keyring.get_password(_SERVICE_NAME, _PROBE_KEY)
                keyring.delete_password(_SERVICE_NAME, _PROBE_KEY)
                if result != "ok":
                    raise RuntimeError("读写探测结果不一致")
            except Exception as probe_err:
                logger.info(
                    f"keyring 后端 {backend.__class__.__name__} 探测失败: "
                    f"{probe_err}，降级为内存存储"
                )
                return

            self._keyring = keyring
            self._keyring_available = True
            logger.info(f"keyring 后端可用: {backend.__class__.__name__}")
        except ImportError:
            logger.info("keyring 库未安装，降级为内存存储")
        except Exception as e:
            logger.warning(f"keyring 初始化失败: {e}，降级为内存存储")

    @property
    def is_keyring_available(self) -> bool:
        return self._keyring_available

    def save_password(self, password: str) -> bool:
        """保存密码到系统钥匙串。成功返回 True。"""
        if not password:
            self._memory_password = ""
            return True

        if self._keyring_available and self._keyring:
            try:
                self._keyring.set_password(_SERVICE_NAME, _KEY_WEBDAV, password)
                self._memory_password = ""
                return True
            except Exception as e:
                logger.error(f"Keyring 保存密码失败: {e}")

        # 降级: 仅内存
        self._memory_password = password
        return False

    def load_password(self) -> str:
        """读取密码。优先 keyring，否则从内存读取。"""
        if self._keyring_available and self._keyring:
            try:
                pw = self._keyring.get_password(_SERVICE_NAME, _KEY_WEBDAV)
                if pw is not None:
                    return pw
            except Exception as e:
                logger.error(f"Keyring 读取密码失败: {e}")

        return self._memory_password

    def delete_password(self) -> bool:
        """删除存储的密码。"""
        self._memory_password = ""
        if self._keyring_available and self._keyring:
            try:
                self._keyring.delete_password(_SERVICE_NAME, _KEY_WEBDAV)
                return True
            except Exception as e:
                # 密码不存在时也可能抛异常，记 debug 即可
                logger.debug(f"Keyring 删除密码: {e}")
        return False


# 全局单例
credential_service = CredentialService()
