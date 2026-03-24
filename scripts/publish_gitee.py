import os
import sys
import json
import urllib.request
import urllib.parse
from pathlib import Path

def upload_file(url, file_path, token):
    boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
    file_path = Path(file_path)
    file_name = file_path.name
    
    with open(file_path, 'rb') as f:
        file_content = f.read()

    body = (
        f'--{boundary}\r\n'
        f'Content-Disposition: form-data; name="access_token"\r\n\r\n'
        f'{token}\r\n'
        f'--{boundary}\r\n'
        f'Content-Disposition: form-data; name="file"; filename="{file_name}"\r\n'
        f'Content-Type: application/octet-stream\r\n\r\n'
    ).encode('utf-8') + file_content + f'\r\n--{boundary}--\r\n'.encode('utf-8')

    req = urllib.request.Request(url, data=body)
    req.add_header('Content-Type', f'multipart/form-data; boundary={boundary}')
    req.add_header('Content-Length', str(len(body)))
    
    try:
        with urllib.request.urlopen(req, timeout=120) as response:
            response.read()
            print(f"✅ Successfully uploaded {file_name}")
            return True
    except urllib.error.HTTPError as e:
        print(f"❌ Failed to upload {file_name}: {e.read().decode('utf-8')}")
        return False

def main():
    owner = "Cyril_P"
    repo = "FlowScroll"
    tag_name = os.environ.get("GITHUB_REF_NAME")
    token = os.environ.get("GITEE_TOKEN")

    if not token:
        print("Error: GITEE_TOKEN is not set.")
        sys.exit(1)
        
    if not tag_name or not tag_name.startswith("v"):
        print(f"Error: Invalid or missing GITHUB_REF_NAME: {tag_name}")
        sys.exit(1)

    print(f"🚀 Creating Gitee release for {tag_name}...")

    # 1. Create release
    url = f"https://gitee.com/api/v5/repos/{owner}/{repo}/releases"
    data = {
        "access_token": token,
        "tag_name": tag_name,
        "name": tag_name,
        "body": """Windows 用户: 下载 FlowScroll_Win.exe，双击即可运行。
macOS 用户: 下载 FlowScroll_Mac.dmg，将其拖入 Applications 文件夹，并在“安全性与隐私”中赋予辅助功能权限。
Linux 用户（Preview）: 下载 FlowScroll_Linux_x86.AppImage，赋予执行权限后双击运行。
注：Ubuntu Wayland 下可能无法工作，目前优先支持 Windows / macOS，Linux 仅在 X11/Xorg 环境下尝试支持""",
        "target_commitish": os.environ.get("GITHUB_SHA", "main")
    }
    
    req = urllib.request.Request(url, data=urllib.parse.urlencode(data).encode("utf-8"))
    req.add_header("Content-Type", "application/x-www-form-urlencoded")

    try:
        with urllib.request.urlopen(req) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            release_id = res_data["id"]
            print(f"✅ Created release ID: {release_id}")
    except urllib.error.HTTPError as e:
        error_msg = e.read().decode('utf-8')
        print(f"❌ Failed to create release: {error_msg}")
        # 如果已经存在或报错，尝试获取ID
        if "already exists" in error_msg.lower() or "missing" in error_msg.lower() or e.code >= 400:
            print("Trying to fetch existing release ID...")
            try:
                get_url = f"https://gitee.com/api/v5/repos/{owner}/{repo}/releases/tags/{tag_name}?access_token={token}"
                with urllib.request.urlopen(urllib.request.Request(get_url)) as get_res:
                    res_data = json.loads(get_res.read().decode("utf-8"))
                    if res_data and isinstance(res_data, dict) and "id" in res_data:
                        release_id = res_data["id"]
                        print(f"✅ Found existing release ID: {release_id}")
                    else:
                        print(f"❌ Failed to get existing release ID, got: {res_data}")
                        sys.exit(1)
            except Exception as ex:
                print(f"❌ Failed to get existing release: {ex}")
                sys.exit(1)
        else:
            sys.exit(1)

    # 2. Upload artifacts
    upload_url = f"https://gitee.com/api/v5/repos/{owner}/{repo}/releases/{release_id}/attach_files"
    artifacts_dir = Path("artifacts")
    
    if not artifacts_dir.exists() or not artifacts_dir.is_dir():
        print(f"Error: Artifacts directory '{artifacts_dir}' not found.")
        sys.exit(1)

    files_uploaded = 0
    for file_path in artifacts_dir.glob("*"):
        if file_path.is_file():
            print(f"Uploading {file_path.name}...")
            if upload_file(upload_url, file_path, token):
                files_uploaded += 1

    print(f"🎉 Done! Uploaded {files_uploaded} files to Gitee.")

if __name__ == "__main__":
    main()