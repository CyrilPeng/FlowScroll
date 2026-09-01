import importlib.util
from pathlib import Path

import pytest


SCRIPT_PATH = Path(__file__).resolve().parents[1] / ".github" / "scripts" / "check_version_consistency.py"
SPEC = importlib.util.spec_from_file_location("check_version_consistency", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
version_check = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(version_check)


def _write_version_files(root: Path, *, pyproject: str, package: str, lock: str) -> None:
    (root / "FlowScroll").mkdir()
    (root / "pyproject.toml").write_text(
        f'[project]\nname = "FlowScroll"\nversion = "{pyproject}"\n',
        encoding="utf-8",
    )
    (root / "FlowScroll" / "__init__.py").write_text(
        f'__version__ = "{package}"\n',
        encoding="utf-8",
    )
    (root / "uv.lock").write_text(
        f'version = 1\n\n[[package]]\nname = "flowscroll"\nversion = "{lock}"\n',
        encoding="utf-8",
    )


def test_versions_match_release_tag(tmp_path):
    _write_version_files(tmp_path, pyproject="1.9.1", package="1.9.1", lock="1.9.1")

    assert version_check.check_versions("v1.9.1", tmp_path) == {
        "pyproject.toml": "1.9.1",
        "FlowScroll/__init__.py": "1.9.1",
        "uv.lock": "1.9.1",
    }


def test_version_mismatch_fails(tmp_path):
    _write_version_files(tmp_path, pyproject="1.9.1", package="1.9.1", lock="1.9.0")

    with pytest.raises(ValueError, match="Version mismatch"):
        version_check.check_versions(root=tmp_path)
