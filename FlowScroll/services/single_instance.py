import hashlib
import os

try:
    from PySide6.QtCore import QObject, Signal
    from PySide6.QtNetwork import QLocalServer, QLocalSocket

    QT_IPC_AVAILABLE = True
except ModuleNotFoundError:  # pragma: no cover - 用于无 GUI 测试环境
    QT_IPC_AVAILABLE = False

    class QObject:
        def __init__(self, *_args, **_kwargs):
            pass

    class Signal:
        def __init__(self, *_args, **_kwargs):
            self._callbacks = []

        def connect(self, callback) -> None:
            self._callbacks.append(callback)

        def emit(self, *args, **kwargs) -> None:
            for callback in list(self._callbacks):
                callback(*args, **kwargs)

    class QLocalServer:
        def __init__(self, *_args, **_kwargs):
            self.newConnection = Signal()

        @staticmethod
        def removeServer(_name) -> None:
            return None

        def listen(self, _name) -> bool:
            return False

        def errorString(self) -> str:
            return "QtNetwork unavailable"

        def hasPendingConnections(self) -> bool:
            return False

        def nextPendingConnection(self) -> None:
            return None

    class QLocalSocket:
        def __init__(self, *_args, **_kwargs):
            pass

        def connectToServer(self, _name) -> None:
            return None

        def waitForConnected(self, _timeout) -> bool:
            return False

        def write(self, _payload) -> int:
            return 0

        def flush(self) -> None:
            return None

        def waitForBytesWritten(self, _timeout) -> bool:
            return False

        def disconnectFromServer(self) -> None:
            return None

        def waitForDisconnected(self, _timeout) -> bool:
            return False

from FlowScroll.services.logging_service import logger


class SingleInstanceManager(QObject):
    activation_requested = Signal()

    def __init__(self, app_id: str, parent=None):
        super().__init__(parent)
        self.server_name = self._build_server_name(app_id)
        self.server = None
        self.pending_activation_request = False

    @staticmethod
    def _build_server_name(app_id: str) -> str:
        user_scope = f"{os.path.expanduser('~')}|{app_id}".encode("utf-8")
        digest = hashlib.sha1(user_scope).hexdigest()
        return f"FlowScroll.{digest}"

    def acquire(self) -> bool:
        if not QT_IPC_AVAILABLE:
            logger.info("QtNetwork unavailable; skipping single-instance enforcement")
            return True

        if self.notify_existing_instance():
            return False

        QLocalServer.removeServer(self.server_name)
        self.server = QLocalServer(self)
        self.server.newConnection.connect(self._handle_new_connection)

        if not self.server.listen(self.server_name):
            logger.error(
                "Failed to listen for single-instance server '%s': %s",
                self.server_name,
                self.server.errorString(),
            )
            self.server = None
            # 即使单实例通信初始化失败，也允许程序继续运行，
            # 避免因 IPC 异常导致主功能完全不可用。
            return True

        return True

    def notify_existing_instance(self) -> bool:
        if not QT_IPC_AVAILABLE:
            return False

        socket = QLocalSocket(self)
        socket.connectToServer(self.server_name)
        if not socket.waitForConnected(250):
            return False

        try:
            socket.write(b"show")
            socket.flush()
            socket.waitForBytesWritten(250)
        finally:
            socket.disconnectFromServer()
            socket.waitForDisconnected(250)
        return True

    def _handle_new_connection(self) -> None:
        if not self.server:
            return

        while self.server.hasPendingConnections():
            socket = self.server.nextPendingConnection()
            socket.readyRead.connect(lambda s=socket: self._process_message(s))
            socket.disconnected.connect(socket.deleteLater)
            if socket.bytesAvailable():
                self._process_message(socket)

    def _process_message(self, socket) -> None:
        payload = bytes(socket.readAll()).decode("utf-8", errors="ignore").strip()
        if payload == "show":
            self.pending_activation_request = True
            self.activation_requested.emit()
        socket.disconnectFromServer()
