import os
import sys
import re

# Force stdout to use utf-8 to avoid UnicodeEncodeError when printing emojis on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

def sync():
    main_file = "main.py"
    toml_file = "pyproject.toml"

    if not os.path.exists(main_file):
        print(f"Error: {main_file} not found.")
        return

    with open(main_file, "r", encoding="utf-8") as f:
        main_content = f.read()

    # 读取 main.py 第2行 (通常以 # 版本 v1.1.0 格式存在)
    lines = main_content.splitlines()
    if len(lines) < 2:
        print("Error: main.py has less than 2 lines.")
        return
    
    version_line = lines[1]
    match = re.search(r'版本\s*v?([\d\.]+)', version_line)
    if not match:
        print(f"Error: Could not parse version from line 2: {version_line}")
        return
    
    version = match.group(1)
    print(f"✅ 从 main.py 解析到最新版本号: {version}")

    # 1. 更新 main.py 里的 myappid
    new_main_content = re.sub(
        r'(myappid\s*=\s*"cyrilpeng\.FlowScroll\.app\.v)[\d\.]+"',
        rf'\g<1>{version}"',
        main_content
    )
    if new_main_content != main_content:
        with open(main_file, "w", encoding="utf-8") as f:
            f.write(new_main_content)
        print(f"✅ 已同步更新 {main_file} 中的 myappid")
    else:
        print(f"⚡ {main_file} 中的 myappid 已经是最新")

    # 2. 更新 pyproject.toml
    if os.path.exists(toml_file):
        with open(toml_file, "r", encoding="utf-8") as f:
            toml_content = f.read()
        
        new_toml_content = re.sub(
            r'^(version\s*=\s*")[\d\.]+"',
            rf'\g<1>{version}"',
            toml_content,
            flags=re.MULTILINE
        )
        if new_toml_content != toml_content:
            with open(toml_file, "w", encoding="utf-8") as f:
                f.write(new_toml_content)
            print(f"✅ 已同步更新 {toml_file} 中的 version")
        else:
            print(f"⚡ {toml_file} 中的 version 已经是最新")

if __name__ == "__main__":
    sync()
