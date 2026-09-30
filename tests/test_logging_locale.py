import io
import logging
import sys


def test_console_diagnostics_survive_ascii_locale(tmp_path, monkeypatch):
    from FlowScroll.services import logging_service

    output = io.BytesIO()
    stderr = io.TextIOWrapper(output, encoding="ascii", errors="backslashreplace")
    stdout = io.TextIOWrapper(io.BytesIO(), encoding="ascii", errors="strict")
    isolated_logger = logging.Logger("FlowScroll-locale-test")
    log_file = tmp_path / "app.log"
    monkeypatch.setattr(sys, "stdout", stdout)
    monkeypatch.setattr(sys, "stderr", stderr)
    monkeypatch.setitem(logging.Logger.manager.loggerDict, "FlowScroll", isolated_logger)
    monkeypatch.setattr(logging_service, "LOG_FILE", str(log_file))
    try:
        logger = logging_service.setup_logging()
        logger.error("中文诊断")
        stderr.flush()
        console = output.getvalue().decode("ascii")
        assert "\\u4e2d\\u6587" in console
        assert "Logging error" not in console
        assert "中文诊断" in log_file.read_text(encoding="utf-8")
    finally:
        for handler in isolated_logger.handlers:
            handler.close()
