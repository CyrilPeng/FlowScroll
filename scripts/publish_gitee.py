import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


def log(msg):
    print(msg, flush=True)


def api_request_json(url, data=None, timeout=60):
    req = urllib.request.Request(url, data=data)
    if data is not None:
        req.add_header("Content-Type", "application/x-www-form-urlencoded")
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def create_or_get_release(owner, repo, tag_name, token):
    log(f"🚀 Creating Gitee release for {tag_name}...")

    url = f"https://gitee.com/api/v5/repos/{owner}/{repo}/releases"
    body = """Windows 用户：下载对应的 .exe 文件，双击即可运行。
macOS 用户：下载对应的 .dmg 文件，将其拖入 Applications 文件夹，并在“安全性与隐私”中赋予辅助功能权限。
Linux 用户（Preview）：下载对应的 .AppImage 文件，赋予执行权限后双击运行。
注：Ubuntu Wayland 下可能无法工作，目前优先支持 Windows / macOS，Linux 仅在 X11/Xorg 环境下尝试支持。"""

    data = {
        "access_token": token,
        "tag_name": tag_name,
        "name": tag_name,
        "body": body,
        "target_commitish": os.environ.get("GITHUB_SHA", "main"),
    }

    try:
        log("🌐 Request: create release")
        res_data = api_request_json(
            url,
            data=urllib.parse.urlencode(data).encode("utf-8"),
            timeout=60,
        )
        release_id = res_data["id"]
        log(f"✅ Created release ID: {release_id}")
        return release_id
    except urllib.error.HTTPError as e:
        error_msg = e.read().decode("utf-8", errors="ignore")
        log(f"⚠️ Create release failed: {error_msg}")
        log("Trying to fetch existing release by tag...")

        get_url = (
            f"https://gitee.com/api/v5/repos/{owner}/{repo}/releases/tags/"
            f"{urllib.parse.quote(tag_name)}?access_token={urllib.parse.quote(token)}"
        )
        try:
            log("🌐 Request: get existing release by tag")
            res_data = api_request_json(get_url, timeout=60)
            if isinstance(res_data, dict) and "id" in res_data:
                release_id = res_data["id"]
                log(f"✅ Found existing release ID: {release_id}")
                return release_id
            log(f"❌ Failed to get existing release ID, got: {res_data}")
            sys.exit(1)
        except Exception as ex:
            log(f"❌ Failed to get existing release: {ex}")
            sys.exit(1)
    except Exception as e:
        log(f"❌ Unexpected error while creating release: {e}")
        sys.exit(1)


def list_existing_attachments(owner, repo, release_id, token):
    url = (
        f"https://gitee.com/api/v5/repos/{owner}/{repo}/releases/{release_id}"
        f"?access_token={urllib.parse.quote(token)}"
    )
    try:
        log("🌐 Request: list existing attachments")
        res_data = api_request_json(url, timeout=60)

        assets = []
        if isinstance(res_data, dict):
            for key in ("assets", "attachments", "files"):
                value = res_data.get(key)
                if isinstance(value, list):
                    assets = value
                    break

        names = set()
        for item in assets:
            if not isinstance(item, dict):
                continue
            for key in ("name", "filename", "file_name"):
                v = item.get(key)
                if v:
                    names.add(str(v))
                    break

        if names:
            log("📎 Existing attachments on Gitee:")
            for n in sorted(names):
                log(f" - {n}")
        else:
            log("📎 No existing attachments found on Gitee release.")

        return names

    except Exception as e:
        log(f"⚠️ Failed to query existing attachments: {e}")
        log("Will continue without skip-check.")
        return set()


def upload_file(url, file_path, token, max_retries=4):
    file_path = Path(file_path)
    file_name = file_path.name

    for attempt in range(1, max_retries + 1):
        log(f"Uploading {file_name}... (attempt {attempt}/{max_retries})")

        cmd = [
            "curl",
            "--fail",
            "--location",
            "--http1.1",
            "--retry", "3",
            "--retry-all-errors",
            "--connect-timeout", "30",
            "--max-time", "1800",
            "--progress-bar",
            "-F", f"access_token={token}",
            "-F", f"file=@{file_path}",
            url,
        ]

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )

        output_lines = []
        assert process.stdout is not None
        for line in process.stdout:
            line = line.rstrip()
            if line:
                print(line, flush=True)
                output_lines.append(line)

        return_code = process.wait()

        if return_code == 0:
            log(f"✅ Successfully uploaded {file_name}")
            return True

        combined = "\n".join(output_lines).lower()

        duplicate_signals = [
            "already exists",
            "duplicate",
            "duplicated",
            "has been taken",
            "file exists",
        ]
        if any(s in combined for s in duplicate_signals):
            log(f"⏭️ Attachment already exists on Gitee, skip: {file_name}")
            return True

        log(f"❌ Failed to upload {file_name}")

        if attempt < max_retries:
            sleep_seconds = attempt * 10
            log(f"Retrying in {sleep_seconds}s...")
            time.sleep(sleep_seconds)

    return False

def main():
    owner = "Cyril_P"
    repo = "FlowScroll"
    tag_name = os.environ.get("GITHUB_REF_NAME")
    token = os.environ.get("GITEE_TOKEN")

    log("▶ publish_gitee.py started")

    if not token:
        log("Error: GITEE_TOKEN is not set.")
        sys.exit(1)

    if not tag_name or not tag_name.startswith("v"):
        log(f"Error: Invalid or missing GITHUB_REF_NAME: {tag_name}")
        sys.exit(1)

    release_id = create_or_get_release(owner, repo, tag_name, token)

    upload_url = f"https://gitee.com/api/v5/repos/{owner}/{repo}/releases/{release_id}/attach_files"
    artifacts_dir = Path("artifacts")

    log(f"📂 Checking artifacts dir: {artifacts_dir.resolve()}")

    if not artifacts_dir.exists() or not artifacts_dir.is_dir():
        log(f"Error: Artifacts directory '{artifacts_dir}' not found.")
        sys.exit(1)

    artifact_files = sorted([p for p in artifacts_dir.glob("*") if p.is_file()])
    if not artifact_files:
        log(f"Error: No artifact files found in '{artifacts_dir}'.")
        sys.exit(1)

    log("📦 Files to process:")
    for p in artifact_files:
        size_mb = p.stat().st_size / 1024 / 1024
        log(f" - {p.name} ({size_mb:.2f} MB)")

    existing_names = list_existing_attachments(owner, repo, release_id, token)

    files_uploaded = 0
    files_skipped = 0
    failed_files = []

    for file_path in artifact_files:
        if file_path.name in existing_names:
            log(f"⏭️ Skip existing attachment: {file_path.name}")
            files_skipped += 1
            continue

        if upload_file(upload_url, file_path, token):
            files_uploaded += 1
        else:
            failed_files.append(file_path.name)

    log(
        f"🎉 Done! Uploaded {files_uploaded}/{len(artifact_files)} files, "
        f"skipped {files_skipped} existing files."
    )

    if failed_files:
        log("❌ These files failed to upload:")
        for name in failed_files:
            log(f" - {name}")
        sys.exit(1)


if __name__ == "__main__":
    main()