<div align="center">

# <img src="FlowScroll/resources/FlowScroll.svg" width="40" align="center" alt="Logo" /> FlowScroll 

**让你的鼠标拥有丝滑的全局惯性滚动**

[![License](https://img.shields.io/badge/License-GPL%20v3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20MacOS-lightgrey.svg)]()
[![Release](https://img.shields.io/github/v/release/CyrilPeng/FlowScroll?color=success&label=Release)]()

<br>
</div>

---

## ✨ 为什么需要 FlowScroll？

你是否曾羡慕过笔记本触控板或手机屏幕上那“指哪打哪”、带有真实**物理阻尼感**的顺滑滚动体验？

传统的鼠标滚轮往往伴随着生硬的“咔哒”声，在阅读长文档或浏览网页时，视觉跳跃感极强，不仅容易看错行，长时间使用还容易让手指疲劳。

**FlowScroll** 就是为了彻底改变这一现状而诞生的。

只需要**按下鼠标中键，移动鼠标，然后松开**，你就能在电脑上获得如同智能手机般的平滑滚动体验！

- 🚀 **全局通用，一键即滚**：无论你是在刷网页、看 PDF 长文档、还是在编辑器里写代码，只要按下中键，所有的软件都能瞬间拥有平滑滚动能力。

- 📐 **私人定制的丝滑手感**：内置精心调校的物理引擎。你可以自由调整滑动时的“加速度”和“阻尼感”，轻松找回最适合你手指的那份真实手感。

- 🔄 **360° 全向穿梭**：遇到超宽的 Excel 表格或视频剪辑软件的长长时间轴？只要按下你设置的快捷键（如 `⬆️`），鼠标瞬间化身触控板，上下左右任意平移，看表再也不用拖动下面的滚动条了！

- 🛡️ **智能防打扰**：全屏打游戏时会自动暂停，防止误触。你还可以把不想用平滑滚动的软件加入“黑名单”，让它安安静静地待在系统托盘，绝不抢焦点。

- ☁️ **配置云端同步**：好不容易调教出的完美手感，可以通过 WebDAV 随时备份到云端。换了新电脑，一键就能无缝恢复你最熟悉的配置。

- 🎨 **极致清爽的现代界面**：告别繁琐复杂的设置面板，FlowScroll 采用现代扁平化设计，即开即用，对高分辨率屏幕完美适配。

<br>

## 🖼️ 软件展示

### 主界面

<div align="center">
  <img src="picture/1.jpg" alt="软件主界面" width="45%" style="margin-right: 2%;">
  <img src="picture/2.jpg" alt="设置界面" width="45%">
</div>

### 使用演示
注：为清楚展示鼠标移动轨迹，VS Code 演示图用蓝色箭头对鼠标位置进行了标记，实际使用中不会显示。
<div align="center">
<img src="picture/demo.gif" alt="FlowScroll 演示演示" width="80%" style="border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.15);">
<br>
<br>
<img src="picture/demo2.gif" alt="FlowScroll 演示演示" width="80%" style="border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.15);">

</div>


<br>

## 📥 下载与安装

进入 [Release](https://github.com/CyrilPeng/FlowScroll/releases) 页面获取最新版本。

- **Windows 用户**: 下载 `FlowScroll_Win.exe`，双击即可运行。
- **macOS 用户**: 下载 `FlowScroll_Mac.dmg`，将其拖入 `Applications` 文件夹，并在“安全性与隐私”中赋予辅助功能权限。
- **Linux 用户（Preview）**: 下载 `FlowScroll_Linux_x86.AppImage`，赋予执行权限后双击运行。

注：Ubuntu Wayland 下可能无法工作，目前优先支持 Windows / macOS，Linux 仅在 X11/Xorg 环境下尝试支持
<br>

## 🛠️ 构建指南 (For Developers)

使用包管理器 `uv` 进行依赖和环境管理。

```bash
# 1. 克隆仓库
git clone https://github.com/CyrilPeng/FlowScroll.git
cd FlowScroll

# 2. 安装并同步依赖
uv sync

# 3. 运行项目
uv run main.py
```

<br>

## ⚙️ 核心配置说明

| 参数 | 描述 | 建议 |
| :--- | :--- | :--- |
| **加速度曲线** | 决定滑动距离与滚动速度之间的非线性关系。 | `1.0`-`1.5` 适合日常网页，`2.0+` 适合极长代码文件。 |
| **基础速度** | 全局滚动倍率乘数。 | 根据你的鼠标 DPI 调整。 |
| **中心死区** | 按下中键后，鼠标需要移动多少距离才开始触发滚动。 | `0.0` 为即刻触发，建议保留极小值防手抖。 |

<br>

## ☁️ WebDAV 云同步

FlowScroll 支持通过 WebDAV 协议进行配置预设的云端同步，方便在多台设备间共享你的滚动参数设置。

### 配置步骤：

1. 打开 FlowScroll 设置窗口，进入"高级设置"标签页
2. 点击"☁️ WebDAV 云同步配置"按钮
3. 填入你的 WebDAV 服务器信息：
   - **服务器地址**：WebDAV 服务器 URL（例如：`https://dav.jianguoyun.com/dav/`）
   - **用户名**：WebDAV 账号
   - **密码**：WebDAV 密码
4. 点击"测试连接"验证配置是否正确
5. 连接成功后，即可使用"上传配置"和"下载配置"功能进行同步

### 支持的 WebDAV 服务：

- 坚果云
- Nextcloud
- ownCloud
- 群晖 Synology
- 123云盘
- 以及其他支持标准 WebDAV 协议的云存储服务

<br>

## ☕ 赞赏

如果这个小工具恰好拯救了你的食指，或者为你带来了一丝桌面上的愉悦——

**不妨，请作者喝一杯咖啡？**

<div align="center">
  <img src="picture/weixin.jpg" alt="WeChat Pay" width="250" style="border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
  <p><i>（微信扫一扫）</i></p>
</div>

<br>

## 📝 许可协议

本项目采用 [GNU General Public License v3.0](https://www.gnu.org/licenses/gpl-3.0) 协议开源。
感谢所有支持与热爱开源的开发者。

<div align="center">
  <sub>Made with ❤️ by 某不科学的高数</sub>
</div>