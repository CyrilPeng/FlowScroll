from __future__ import annotations

import argparse
import re
import sys
import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def normalize_version(value: str) -> str:
    version = value.strip()
    return version[1:] if version.lower().startswith("v") else version


def read_versions(root: Path = ROOT) -> dict[str, str]:
    pyproject = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    project_version = str(pyproject["project"]["version"])

    init_text = (root / "FlowScroll" / "__init__.py").read_text(encoding="utf-8")
    match = re.search(r'^__version__\s*=\s*["\']([^"\']+)["\']', init_text, re.MULTILINE)
    if match is None:
        raise ValueError("FlowScroll/__init__.py does not define __version__")

    lock = tomllib.loads((root / "uv.lock").read_text(encoding="utf-8"))
    lock_versions = [
        str(package["version"])
        for package in lock.get("package", [])
        if str(package.get("name", "")).lower() == "flowscroll"
    ]
    if len(lock_versions) != 1:
        raise ValueError("uv.lock must contain exactly one FlowScroll package")

    return {
        "pyproject.toml": project_version,
        "FlowScroll/__init__.py": match.group(1),
        "uv.lock": lock_versions[0],
    }


def check_versions(expected: str | None = None, root: Path = ROOT) -> dict[str, str]:
    versions = read_versions(root)
    normalized_expected = normalize_version(expected) if expected else next(iter(versions.values()))
    mismatches = {source: version for source, version in versions.items() if version != normalized_expected}
    if mismatches:
        details = ", ".join(f"{source}={version}" for source, version in versions.items())
        raise ValueError(f"Version mismatch: expected {normalized_expected}; {details}")
    return versions


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Check FlowScroll version consistency.")
    parser.add_argument("--expected", help="Expected version or release tag, for example v1.9.1")
    args = parser.parse_args(argv)

    try:
        versions = check_versions(args.expected)
    except (KeyError, OSError, ValueError, tomllib.TOMLDecodeError) as error:
        print(str(error), file=sys.stderr)
        return 1

    version = next(iter(versions.values()))
    print(f"FlowScroll version is consistent: {version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
