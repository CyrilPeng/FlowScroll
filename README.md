<div align="center">



# <img src="FlowScroll/resources/FlowScroll.svg" width="40" align="center" alt="Logo" /> FlowScroll

`中文` | [English](README.en.md)

**让你的鼠标拥有丝滑的全局无级滚动**

——把浏览器里的中键自动滚动，带到整个系统。

[![License](https://img.shields.io/badge/License-GPL%20v3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)]()
[![Release](https://img.shields.io/github/v/release/CyrilPeng/FlowScroll?color=success&label=Release)](https://github.com/CyrilPeng/FlowScroll/releases) ![Channel](https://img.shields.io/badge/Channel-dev-f59e0b) 

[项目官网](https://flowscroll.pages.dev/) | [发行版](https://github.com/CyrilPeng/FlowScroll/releases)

</div>

---

## 📖 简介

你是否也喜欢浏览器里那种**单击鼠标中键后，以当前位置为中心自由滚动页面**的体验？

FlowScroll 就是把这种熟悉、直觉的交互方式扩展到整个桌面系统——网页、PDF、代码编辑器、表格、时间轴，都能获得更连贯、更轻松的滚动体验。相比传统滚轮一格一格地拨动，FlowScroll 更适合：

- 阅读长网页、长文档、PDF
- 浏览大段代码、日志、配置文件
- 查看超宽表格、时间轴、画布
- 减少频繁拨动滚轮和拖拽滚动条的操作负担

---

## 🖼️ 软件展示

### 主界面

<div align="center">
  <img src="https://git-pictures.cyrilworkshop.dpdns.org/flowscroll/1.jpg" alt="软件主界面" width="30%" style="margin-right: 2%;">
  <img src="https://git-pictures.cyrilworkshop.dpdns.org/flowscroll/2.jpg" alt="设置界面" width="30%" style="margin-right: 2%;">
  <img src="https://git-pictures.cyrilworkshop.dpdns.org/flowscroll/3.jpg" alt="工作模式" width="30%">
</div>

### 使用演示

> 注：为更清楚地展示鼠标移动轨迹，演示图中额外标出了鼠标位置；实际使用时不会出现这些蓝色标记。

<div align="center">
<img src="https://git-pictures.cyrilworkshop.dpdns.org/flowscroll/demo1.gif" alt="FlowScroll 演示 1" width="80%" style="border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.15);">
<br>
<br>
<img src="https://git-pictures.cyrilworkshop.dpdns.org/flowscroll/demo2.gif" alt="FlowScroll 演示 2" width="80%" style="border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.15);">
</div>

---

## 📥 下载与安装

进入 [Release](https://github.com/CyrilPeng/FlowScroll/releases) 页面获取最新版本。

正式 Release 版本使用 `Nuitka` 进行打包。相比 `PyInstaller` 等常见打包方案，在本项目上通常能带来更好的启动与运行效率，也更适合发布正式产物。

| 平台 | 文件 | 安装方式 |
| :--- | :--- | :--- |
| **Windows** | `FlowScroll_Win_v*.exe` | 双击即可运行 |
| **macOS** | `FlowScroll_Mac_v*.dmg` | 拖入 Applications，并在"隐私与安全性"中授予辅助功能权限 |
| **Linux（Preview）** | `FlowScroll_Linux_x86_v*.AppImage` | 赋予执行权限后运行 |

> **平台支持状态**
> - **Windows**：完整支持，推荐平台
> - **macOS**：主要支持，需授予辅助功能权限；全屏检测精度有限
> - **Linux**：实验性预览，仅在 X11/Xorg 下可用；Wayland 由于安全限制无法进行全局输入监听

---

## 🚀 快速上手

FlowScroll 提供两种启用模式。两种模式都支持单独设置**启用键**，留空时默认使用**鼠标中键**。

### 点击启用键启用/关闭（默认）

1. **单击启用键**
2. 屏幕上会出现**准星**，表示已进入滚动模式
3. **移动鼠标**——鼠标往哪个方向偏移，就往哪个方向滚动；离中心越远，滚动越快
4. **再次单击**同一个启用键，退出滚动模式

### 长按启用键时启用

1. **按住启用键不放**
2. 屏幕上出现**准星**，进入滚动模式
3. **保持按住并移动鼠标**即可滚动
4. **松开启用键**，自动退出滚动模式

> 默认模式与浏览器中键自动滚动一致；长按模式更像"按住启用键当触控板用"，松手即停。
>
> 切换方式：高级设置 → 配置工作模式 → 启用模式 / 启用键

### 延迟启动

如果你希望继续保留“中键单击”的原生行为，可以在“工作模式”中开启**延迟启动**。

- 短按中键时，不会立即触发 FlowScroll
- 只有按住达到设定时间后，才会进入滚动模式
- 这样可以减少“中键单击”和 FlowScroll 启动动作之间的冲突

典型场景包括：

- 浏览器中键单击触发原生功能
- 中键关闭标签页
- 其他应用将中键单击绑定为窗口或视图操作

建议将延迟时间设置为 `150~250ms`，通常比较容易兼顾响应速度与避免冲突。

---

## ⭐ 功能介绍

- 🚀 **全局可用，开箱即用**
  在很多常见的可滚动区域中直接使用中键滚动交互，无需反复拖滚动条。

- 🎯 **状态清晰，容易理解**
  进入模式后显示准星，并根据鼠标偏移方向变化指针形态，一眼知道当前状态。

- 📐 **滚动手感可调**
  调整加速度曲线、基础速度和中心死区，找到最适合自己的节奏。

- 🔄 **支持 360° 全向移动**
  不只是上下滚动，也适合处理横向内容——Excel、设计画布、视频时间轴等。

- 🛡️ **尽量不打扰其他使用习惯**
  支持全屏自动停用、应用排除名单、系统托盘常驻，减少误触和冲突。

- ☁️ **配置可同步**
  通过 WebDAV 同步预设和参数，换设备后也能快速恢复熟悉的手感。

- 🪽 **可选惯性滚动**
  松开中键后页面继续滑行并逐渐停下，模拟触控板手感。搭配"长按启用键时启用"使用效果最佳。

- 🔁 **支持方向反转**
  可分别反转纵向 / 横向滚动方向，适配习惯"向上拨轮 = 页面向下"的用户。

---

## ⚙️ 配置说明

### 内置预设

FlowScroll 内置 4 个预设，开箱即用。首次启动默认使用 **长文档 / 表格**。

| 预设 | 适用场景 | 加速度 | 基础速度 | 死区 | 横向 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **网页阅读** | 刷网页、看新闻、社交媒体 | `1.5` | `3.0` | `25` | 关 |
| **代码办公** | IDE 写代码、Office 办公 | `2.5` | `2.5` | `15` | 关 |
| **长文档 / 表格** ★ | PDF、超长表格、视频时间轴 | `2.0` | `2.0` | `20` | 开 |
| **轻柔 / 接近触控板** | 喜欢更平缓手感的用户 | `1.2` | `1.5` | `10` | 关 |

> ★ 默认预设。也可在 "参数调校 → 配置预设" 中保存自定义预设。默认情况下，Windows 写入 `%AppData%\FlowScroll\FlowScroll_config.json`，macOS 写入 `~/Library/Application Support/FlowScroll/FlowScroll_config.json`，Linux 写入 `~/.config/FlowScroll/FlowScroll_config.json`。也支持通过环境变量 `FLOWSCROLL_CONFIG_FILE` 或 `FLOWSCROLL_CONFIG_DIR` 自定义存储位置。

### 核心参数

如果你想自己微调，最重要的通常是这三个：

| 参数 | 描述 | 建议 |
| :--- | :--- | :--- |
| **加速度曲线** | 鼠标偏移距离与滚动速度之间的变化关系 | `1.0`-`1.5` 平缓，`2.0+` 适合快速拉开速度差 |
| **基础速度** | 整体滚动快慢 | 太快太慢时优先调它 |
| **中心死区** | 鼠标离中心多远后才开始滚动 | 增大可减少手抖误触 |

简单理解：

- **太快** → 降低基础速度
- **太慢** → 提高基础速度
- **容易误触** → 增大中心死区
- **想"轻推慢走、远推快冲"** → 提高加速度曲线

### 反转模式

部分用户习惯反转操作方向（例如 macOS 触控板用户：双指上推 = 页面向下）。FlowScroll 支持独立反转纵向和横向滚动。

1. 高级设置 → 点击"配置滚轮方向反转"
2. 勾选需要的选项：
   - **反转纵向滚动 (Y轴)**：向上偏移鼠标时页面向下滚动
   - **反转横向滚动 (X轴)**：向左偏移鼠标时页面向右滚动
3. 点击"确定"生效，设置随预设自动保存

### 惯性滚动

开启后，松开中键时页面继续滑行一段距离并逐渐停下，模拟触控板手感。

1. 高级设置 → 勾选"启用惯性滚动"
2. 点击右侧 ⚙ 齿轮按钮调节：
   - **阻尼 / 摩擦力**：控制滑行持续时间（"紧凑"↔"松弛"）
   - **触发阈值**：鼠标速度超过此值才触发惯性，避免轻微拖动也产生滑行

> 建议搭配「长按启用键时启用」模式使用（在“配置工作模式”中切换）。

### WebDAV 云同步

通过 WebDAV 在多台设备之间共享滚动参数配置。

1. 高级设置 → 点击"WebDAV 云同步配置"
2. 填入服务器地址、用户名、密码
3. 点击"保存配置"，然后使用"上传配置" / "下载配置"进行同步

支持的 WebDAV 服务：坚果云、Nextcloud、ownCloud、群晖 Synology、123 云盘等。

---

## 🔐 权限说明

FlowScroll 是系统级输入工具，需要监听全局鼠标事件才能工作。

### macOS — 为什么需要"辅助功能"权限？

macOS 对全局输入监听有严格限制。FlowScroll 依赖 [pynput](https://github.com/moses-palmer/pynput) 需要辅助功能权限才能监听鼠标事件、快捷键和读取前台窗口名称。

> 首次运行时系统会弹出引导窗口，按提示前往 **系统设置 → 隐私与安全性 → 辅助功能** 添加即可。

### Windows — 是否需要管理员权限？

**通常不需要。** FlowScroll 在普通用户权限下即可运行（用户级鼠标/键盘钩子、注册表自启写入 `HKEY_CURRENT_USER`）。

### Linux — X11 与 Wayland 的差异

- **X11 / Xorg**：通常可以正常工作
- **Wayland**：由于系统安全限制，通常无法进行全局输入监听

---

## 🛡️ 隐私说明

所有滚动计算、窗口检测、黑白名单匹配都在本地完成，不依赖云服务。

- **不记录键盘输入内容**：键盘监听仅用于判断快捷键是否被触发
- **不保存鼠标轨迹历史**：只读取当前鼠标位置与中心点的相对偏移
- **不读取剪贴板、不截屏、不上传任何使用数据**

唯一的默认网络请求是启动时的版本检查（`GET https://api.github.com/repos/CyrilPeng/FlowScroll/releases/latest`），不会上传本地数据。

WebDAV 密码通过系统安全存储（macOS Keychain / Windows Credential Manager / Linux Secret Service）管理，配置文件中不保存可逆密码。

---

## ⚠️ 已知兼容性问题

| 问题 | 说明 |
| :--- | :--- |
| **macOS 全屏检测不够精确** | 没有公开 API 可靠判断全屏状态，"全屏模式下自动禁用"可能不完全准确 |
| **Windows UWP / 微软商店应用** | 部分沙盒应用中鼠标钩子可能无法正常生效 |
| **浏览器原生中键自动滚动冲突** | Chrome / Edge / Firefox 自带中键自动滚动，可关闭浏览器原生功能或将浏览器加入排除名单 |
| **远程桌面 / 虚拟机** | RDP、TeamViewer、VMware 等环境中鼠标事件传递方式不同，可能导致触发异常 |
| **多个输入钩子工具冲突** | 与 AutoHotkey、X-Mouse Button Control 等同时运行时可能互相干扰 |

---

## ❓ FAQ

### 1. 会和浏览器自带的中键自动滚动冲突吗？

默认情况下会由 FlowScroll 接管中键滚动行为，也就是**会替代浏览器原生中键滚动**。  
如果你不希望在浏览器中启用 FlowScroll，只需要把浏览器进程名关键词加入**黑名单**（例如 `chrome`、`msedge`、`firefox`），即可直接禁止在浏览器中使用。

### 2. 黑名单和白名单有什么区别？

- **黑名单模式**：除名单内应用外，其他应用都可用
- **白名单模式**：只有名单内应用可用
- **全局模式**：所有应用都可用（仍受“全屏禁用”等选项影响）

### 3. 关键词如何匹配应用？

关键词按“前台进程名包含”进行匹配，不区分大小写。  
建议使用稳定且简短的进程名片段，例如 `chrome`、`code`、`potplayer`。
如果当前环境无法识别进程名，则仅对当前前台应用回退为窗口标题匹配。

### 4. 为什么有时看起来不生效？

可按下面顺序排查：

1. 是否在当前模式下被过滤（黑名单/白名单）
2. 是否开启了“全屏时禁用”
3. 是否被安全软件、游戏反作弊或远程桌面环境拦截全局输入

### 5. WebDAV 同步会上传账号密码吗？

不会。WebDAV 同步只上传参数配置，不上传密码。  
密码优先保存在系统凭据管理（Keyring）中。

---

## 🛠️ 构建指南

使用包管理器 `uv` 进行依赖和环境管理。

如果你直接从 `main` 运行源码，使用的可能是开发中版本，而不是最新稳定发布版。

稳定 Release 产物会另行使用 `Nuitka` 打包；直接运行源码更适合开发、调试和测试场景。

```bash
git clone https://github.com/CyrilPeng/FlowScroll.git
cd FlowScroll
uv sync
uv run main.py
```

---

## ☕ 赞赏

如果这个小工具恰好为你省下了很多操作滚轮和滚动条的动作——

**欢迎请作者喝一杯咖啡。**

<div align="center">
  <img src="https://git-pictures.cyrilworkshop.dpdns.org/flowscroll/wx.jpg" alt="WeChat Pay" width="250" style="border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
  <p><i>（微信扫一扫）</i></p>
</div>

---

## 📈 星标历史

<div align="center">
  <a href="https://star-history.com/#CyrilPeng/FlowScroll&Timeline">
    <picture>
      <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=CyrilPeng/FlowScroll&theme=dark">
      <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=CyrilPeng/FlowScroll">
      <img alt="Star History Chart" src="https://api.star-history.com/svg?repos=CyrilPeng/FlowScroll" width="100%">
    </picture>
  </a>
</div>

---

## 🤝 协助者

感谢所有提交 PR、反馈问题、参与讨论并帮助打磨 FlowScroll 的朋友。

下面的贡献者展示会随仓库贡献情况自动更新：

<div align="center">
  <a href="https://github.com/CyrilPeng/FlowScroll/graphs/contributors">
    <img src="https://contrib.rocks/image?repo=CyrilPeng/FlowScroll" alt="FlowScroll contributors" />
  </a>
</div>

如果你也愿意一起完善它，欢迎继续提交 issue 或 PR。

<div align="center">
  <sub>Made with ❤️ by 某不科学的高数</sub>
</div>

---

## 🔗 社区友情链接

- [Linux.do](https://linux.do/)：通用技术社区，聚焦开源、效率工具、开发与 AI 等话题讨论。

---

## 🧩 关于代码

FlowScroll 更偏向一种“先解决真实问题，再持续打磨实现”的开发方式。

在这个项目里，作者承担的角色更接近产品设计与功能统筹；部分实现来自快速迭代、实验性验证以及 AI 辅助生成。因此在工程结构、抽象层次和细节处理上，未必处处都是最理想的写法。

如果你在阅读或使用过程中发现了实现上的不足、可改进之处，欢迎直接提出具体的 issue 或 PR。

- 欢迎带有上下文、复现步骤和改进建议的反馈
- 欢迎针对交互设计、兼容性问题和代码实现的建设性讨论
- 如果只是停留在姿态上的否定，而没有具体信息，对项目本身帮助不大

FlowScroll 首先是一个为真实使用场景服务的小工具。
它也许并不完美，但会继续演进。

---

## 📝 许可协议

本项目采用 [GNU General Public License v3.0](https://www.gnu.org/licenses/gpl-3.0) 协议开源。
