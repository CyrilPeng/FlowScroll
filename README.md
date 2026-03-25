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
  <img src="https://git-pictures.cyrilworkshop.dpdns.org/flowscroll/1.jpg" alt="软件主界面" width="45%" style="margin-right: 2%;">
  <img src="https://git-pictures.cyrilworkshop.dpdns.org/flowscroll/2.jpg" alt="设置界面" width="45%">
</div>

### 使用演示
注：为清楚展示鼠标移动轨迹，VS Code 演示图用蓝色箭头对鼠标位置进行了标记，实际使用中不会显示。
<div align="center">
<img src="https://git-pictures.cyrilworkshop.dpdns.org/flowscroll/demo1.gif" alt="FlowScroll 演示演示" width="80%" style="border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.15);">
<br>
<br>
<img src="https://git-pictures.cyrilworkshop.dpdns.org/flowscroll/demo2.gif" alt="FlowScroll 演示演示" width="80%" style="border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.15);">

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

## 🎯 内置预设

FlowScroll 内置 4 个预设，开箱即用，无需理解参数含义。首次启动默认使用 **长文档/表格**。

| 预设 | 适用场景 | 加速度 | 基础速度 | 死区 | 横向 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **网页阅读** | 刷网页、看新闻、社交媒体 | `1.5` | `3.0` | `25` | 关 |
| **代码办公** | IDE 写代码、Office 办公 | `2.5` | `2.5` | `15` | 关 |
| **长文档/表格** ★ | PDF、超长表格、视频时间轴 | `2.0` | `2.0` | `20` | 开 |
| **轻柔/接近触控板** | 喜欢笔记本触控板手感的用户 | `1.2` | `1.5` | `10` | 关 |

> ★ = 默认预设。你也可以在"高级设置 → 配置预设"中保存自己的自定义预设。

各预设的设计思路：

- **网页阅读**：加速度偏低（`1.5`），速度偏高（`3.0`），死区较大（`25`）。轻移即快速翻页，适合"扫一眼就滑走"的浏览习惯。
- **代码办公**：加速度最高（`2.5`），死区较小（`15`）。小幅移动精准逐行，大幅移动瞬间跳到文件底部。
- **长文档/表格**：各项参数居中，开启横向穿梭。全能型预设，也是默认选择。
- **轻柔/接近触控板**：加速度最低（`1.2`），速度最低（`1.5`），死区最小（`10`）。手感最接近 MacBook 触控板，适合精细操作。

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

## 🔐 权限说明

FlowScroll 是一个系统级输入工具，需要拦截鼠标事件才能工作。以下是各平台的权限需求解释：

### macOS — 为什么需要"辅助功能"权限？

macOS 对全局输入监听有严格限制。FlowScroll 依赖的底层库 [pynput](https://github.com/moses-palmer/pynput) 必须获得辅助功能权限才能：
- 拦截鼠标中键按下/松开事件（否则无法接管滚动）
- 监听键盘快捷键（用于横向穿梭模式切换）
- 通过 AppleScript 读取前台窗口名称（用于黑名单过滤）

> 首次运行时系统会弹出引导窗口，按提示前往 **系统设置 → 隐私与安全性 → 辅助功能** 添加 FlowScroll 即可。

### Windows — 是否需要管理员权限？

**不需要。** FlowScroll 在普通用户权限下即可运行：
- pynput 通过用户级底层鼠标/键盘钩子工作，不涉及系统级驱动
- 开机自启写入 `HKEY_CURRENT_USER` 注册表分支，不需要管理员权限
- 不写入 `Program Files` 等受保护目录，配置文件存储在用户主目录下

### Linux — X11 与 Wayland 的差异

- **X11 / Xorg**：pynput 基于 Xlib 实现，可以正常工作
- **Wayland**：Wayland 的安全模型禁止应用全局监听输入事件，**无法使用**。如果你的发行版默认使用 Wayland（如 Ubuntu 22.04+），需要切换到 X11 会话

<br>

## 🛡️ 隐私说明

也就是 FlowScroll 在你的电脑上做了什么、没做什么：

### 本地处理

所有滚动计算、窗口检测、黑白名单匹配**完全在本地运行**，不依赖任何云服务。

### 不采集

- **不记录键盘输入**：键盘监听器只检测你设定的快捷键组合是否被按下（如 `↑`），不记录、不存储任何按键内容
- **不记录鼠标轨迹**：只在中键按下瞬间读取鼠标位移来计算滚动速度，松开即停止
- **不读取剪贴板**
- **不截屏**
- **不上传任何使用数据或统计信息**

### 唯一的网络请求

程序启动时会向 GitHub API 发送一次版本检查请求：

```
GET https://api.github.com/repos/CyrilPeng/FlowScroll/releases/latest
```

此请求仅接收最新版本号，**不上传任何本地数据**。如果不希望此请求，可在防火墙中阻止或自行编译去除（`services/update_checker.py`）。

### WebDAV 同步

如果你主动配置了 WebDAV：
- **仅同步**滚动参数配置文件（`~/.FlowScroll_config.json`），内容为灵敏度、速度、死区等数值
- **不包含**任何使用记录、窗口历史、键盘记录
- 连接完全由你控制——你填写服务器地址、用户名、密码，FlowScroll 只在你点击"上传/下载"时才发起请求

<br>

## ⚠️ 已知兼容性问题

| 问题 | 说明 |
| :--- | :--- |
| **macOS 全屏检测不精确** | macOS 没有公开 API 获取窗口是否处于全屏状态，"全屏模式下自动禁用"功能在 macOS 上暂时不生效 |
| **Windows UWP / 微软商店应用** | 部分 UWP 应用（如新版 Windows 设置、Microsoft Store 版 Office）运行在沙盒中，鼠标钩子可能无法穿透，导致滚动无效果 |
| **浏览器原生平滑滚动冲突** | Chrome / Edge / Firefox 自带平滑滚动功能。建议在浏览器设置中关闭原生的按下中键滚动或者设置在浏览器中不启用本软件，避免快捷键冲突的问题 |
| **远程桌面 / 虚拟机** | 通过 RDP、TeamViewer、VMware 等远程控制时，鼠标事件的传递方式不同，可能无法正常触发中键拦截 |
| **多个输入钩子工具冲突** | 同时运行 AutoHotkey、X-Mouse Button Control 等修改鼠标行为的工具时，可能互相干扰。如果出现异常，请逐一排查 |
| **高刷新率显示器** | 4ms 的滚动循环间隔对应约 250fps，在极高刷新率（360Hz+）显示器上可能出现细微的滚动不连贯 |

<br>

## ☕ 赞赏

如果这个小工具恰好拯救了你的食指，或者为你带来了一丝桌面上的愉悦——

**不妨，请作者喝一杯咖啡？**

<div align="center">
  <img src="https://git-pictures.cyrilworkshop.dpdns.org/flowscroll/wx.jpg" alt="WeChat Pay" width="250" style="border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
  <p><i>（微信扫一扫）</i></p>
</div>

<br>

## 📝 许可协议

本项目采用 [GNU General Public License v3.0](https://www.gnu.org/licenses/gpl-3.0) 协议开源。
感谢所有支持与热爱开源的开发者。

<div align="center">
  <sub>Made with ❤️ by 某不科学的高数</sub>
</div>