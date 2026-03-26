<div align="center">

# <img src="FlowScroll/resources/FlowScroll.svg" width="40" align="center" alt="Logo" /> FlowScroll

**让你的鼠标拥有丝滑的全局无级滚动**

——把浏览器里的中键自动滚动，带到整个系统。

[![License](https://img.shields.io/badge/License-GPL%20v3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20MacOS-lightgrey.svg)]()
[![Release](https://img.shields.io/github/v/release/CyrilPeng/FlowScroll?color=success&label=Release)]()

</div>

---

## ✨ 为什么需要 FlowScroll？

你是否也喜欢浏览器里那种**单击鼠标中键后，以当前位置为中心自由滚动页面**的体验？

FlowScroll 的目标，就是把这种熟悉、直觉的交互方式扩展到更多桌面软件中，让网页、PDF、代码编辑器、表格、时间轴等场景，也能获得更连贯、更轻松的滚动体验。

相比传统鼠标滚轮一格一格地拨动，FlowScroll 更适合：

- 阅读长网页、长文档、PDF
- 浏览大段代码、日志、配置文件
- 查看超宽表格、时间轴、画布
- 减少频繁拨动滚轮和拖拽滚动条的操作负担

---

## 🚀 怎么用？

FlowScroll 提供两种启用模式。两种模式都支持单独设置**启用键**，留空时默认使用**鼠标中键**。

### 点击启用键启用/关闭（默认）

1. **单击启用键**
2. 屏幕上会在当前位置出现一个**准星**，表示已进入滚动模式
3. **移动鼠标**
   - 鼠标往哪个方向偏移，就往哪个方向滚动
   - 离中心越远，滚动越快
4. **再次单击同一个启用键**，退出滚动模式

### 长按启用键时启用

1. **按住启用键不放**
2. 屏幕上出现**准星**，进入滚动模式
3. **保持按住并移动鼠标**即可滚动
4. **松开启用键**，自动退出滚动模式

也就是说，默认模式与浏览器里的中键自动滚动一致；长按模式则更像“按住启用键当触控板用”，松手即停。

> 切换方式：高级设置 → 配置工作模式与应用过滤 → 启用模式 / 启用键

---

## 🌟 你会得到什么体验？

- 🚀 **全局可用，开箱即用**  
  在很多常见的可滚动区域中，你都可以直接使用这套中键滚动交互，无需反复拖滚动条。

- 🎯 **状态清晰，容易理解**  
  进入模式后会显示准星，并根据鼠标偏移方向变化指针形态，让你一眼知道当前是否处于滚动模式、正在往哪个方向移动。

- 📐 **滚动手感可调**  
  你可以根据自己的习惯调整加速度曲线、基础速度和中心死区，找到最适合自己的节奏。

- 🔄 **支持 360° 全向移动**  
  不只是上下滚动，也适合处理横向内容，例如 Excel、设计画布、视频时间轴等场景。

- 🛡️ **尽量不打扰其他使用习惯**  
  支持全屏自动停用、应用排除名单、系统托盘常驻等能力，减少误触和冲突。

- ☁️ **配置可同步**  
  通过 WebDAV 同步预设和参数，换设备后也能快速恢复熟悉的手感。

- 🎨 **现代、清爽的界面**  
  尽量减少设置门槛，开箱可用，同时保留足够的可调空间。

- 🔁 **支持方向反转**  
  在高级设置中可分别反转纵向 / 横向滚动方向，适配习惯"向上拨轮 = 页面向下"的用户。

- 🪽 **可选惯性滚动**  
  松开中键后页面继续滑行并逐渐停下，模拟触控板的惯性手感。搭配"长按启用键时启用"模式使用效果最佳。

---

## 🖼️ 软件展示

### 主界面

<div align="center">
  <img src="https://git-pictures.cyrilworkshop.dpdns.org/flowscroll/1.jpg" alt="软件主界面" width="45%" style="margin-right: 2%;">
  <img src="https://git-pictures.cyrilworkshop.dpdns.org/flowscroll/2.jpg" alt="设置界面" width="45%">
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

- **Windows 用户**：下载 `FlowScroll_Win.exe`，双击即可运行。
- **macOS 用户**：下载 `FlowScroll_Mac.dmg`，将其拖入 `Applications` 文件夹，并在“隐私与安全性”中授予辅助功能权限。
- **Linux 用户（Preview）**：下载 `FlowScroll_Linux_x86.AppImage`，赋予执行权限后运行。

> 注：当前优先支持 **Windows / macOS**。  
> Linux 仍处于预览阶段，通常在 **X11 / Xorg** 环境下更容易正常工作；Wayland 下通常无法使用。

---

## 🎯 内置预设

FlowScroll 内置 4 个预设，开箱即用，无需先理解复杂参数。首次启动默认使用 **长文档 / 表格**。

| 预设 | 适用场景 | 加速度 | 基础速度 | 死区 | 横向 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **网页阅读** | 刷网页、看新闻、社交媒体 | `1.5` | `3.0` | `25` | 关 |
| **代码办公** | IDE 写代码、Office 办公 | `2.5` | `2.5` | `15` | 关 |
| **长文档 / 表格** ★ | PDF、超长表格、视频时间轴 | `2.0` | `2.0` | `20` | 开 |
| **轻柔 / 接近触控板** | 喜欢更平缓手感的用户 | `1.2` | `1.5` | `10` | 关 |

> ★ 默认预设。你也可以在 “参数调校 → 配置预设” 中保存自己的自定义预设。

各预设的大致风格：

- **网页阅读**：滚动更轻快，适合快速浏览页面
- **代码办公**：更适合兼顾精细移动和快速跳转
- **长文档 / 表格**：整体更均衡，适合作为默认方案
- **轻柔 / 接近触控板**：节奏更平缓，适合细腻浏览

> 配置保存后写入 `~/.FlowScroll_config.json`，也支持通过 WebDAV 云同步。

---

## ⚙️ 核心配置说明

如果你想自己微调，最重要的通常是下面三个参数：

| 参数 | 描述 | 建议 |
| :--- | :--- | :--- |
| **加速度曲线** | 决定鼠标偏移距离与滚动速度之间的变化关系 | `1.0`-`1.5` 更平缓，`2.0+` 更适合快速拉开速度差 |
| **基础速度** | 决定整体滚动快慢 | 觉得太快或太慢时，优先调整它 |
| **中心死区** | 决定鼠标离中心多远后才开始滚动 | 适当增大可以减少轻微手抖带来的误触 |

简单理解：

- 觉得**太快**：先降低基础速度
- 觉得**太慢**：先提高基础速度
- 觉得**容易误触**：增大中心死区
- 想要更明显的“轻推慢走、远推快冲”：提高加速度曲线

---

## 🔁 反转模式

部分用户习惯反转操作方向（例如 macOS 触控板用户：双指上推 = 页面向下）。FlowScroll 支持独立反转纵向和横向滚动。

### 配置方式

1. 打开 FlowScroll 设置窗口，进入"高级设置"标签页
2. 点击"配置滚轮方向反转"
3. 勾选需要的选项：
   - **反转纵向滚动 (Y轴)**：向上偏移鼠标时页面向下滚动
   - **反转横向滚动 (X轴)**：向左偏移鼠标时页面向右滚动
4. 点击"确定"即可生效，设置会随预设自动保存

---

## 🪽 惯性滚动

开启后，松开中键时页面会继续滑行一段距离并逐渐停下，模拟触控板或触摸屏的惯性手感。

### 开启方式

1. 打开 FlowScroll 设置窗口，进入"高级设置"标签页
2. 勾选"启用惯性滚动"
3. 点击右侧 ⚙ 齿轮按钮，可进一步调节：
   - **阻尼 / 摩擦力**：控制惯性滑行的持续时间。数值越大，滑得越远越久（"紧凑"↔"松弛"）
   - **触发阈值**：鼠标移动速度超过此值时才触发惯性，避免轻微拖动也产生滑行

> 建议搭配「长按启用键时启用」模式使用（在"配置工作模式与应用过滤"中切换），松手即停配合惯性滑行，可以更好地模拟触控板的滑动手感。

---

## ☁️ WebDAV 云同步

FlowScroll 支持通过 WebDAV 同步配置预设，方便在多台设备之间共享你的滚动参数设置。

### 配置步骤

1. 打开 FlowScroll 设置窗口，进入“高级设置”标签页
2. 点击“WebDAV 云同步配置”
3. 填入你的 WebDAV 服务器信息：
   - **服务器地址**：WebDAV 服务器 URL（例如：`https://dav.jianguoyun.com/dav/`）
   - **用户名**：WebDAV 账号
   - **密码**：WebDAV 密码
4. 点击“测试连接”验证配置
5. 连接成功后，即可使用“上传配置”和“下载配置”进行同步

### 支持的 WebDAV 服务

- 坚果云
- Nextcloud
- ownCloud
- 群晖 Synology
- 123云盘
- 以及其他支持标准 WebDAV 协议的云存储服务

---

## 🔐 权限说明

FlowScroll 是一个系统级输入工具，需要监听全局鼠标事件才能工作。以下是各平台的权限说明：

### macOS — 为什么需要“辅助功能”权限？

macOS 对全局输入监听有严格限制。FlowScroll 依赖的底层库 [pynput](https://github.com/moses-palmer/pynput) 需要辅助功能权限，才能：

- 监听鼠标中键事件
- 监听你设置的快捷键
- 读取前台窗口名称，用于应用规则判断

> 首次运行时系统通常会弹出引导窗口，按提示前往 **系统设置 → 隐私与安全性 → 辅助功能** 添加 FlowScroll 即可。

### Windows — 是否需要管理员权限？

**通常不需要。** FlowScroll 在普通用户权限下即可运行：

- 使用用户级鼠标/键盘钩子
- 开机自启写入 `HKEY_CURRENT_USER`
- 配置文件保存在用户目录下

### Linux — X11 与 Wayland 的差异

- **X11 / Xorg**：通常可以正常工作
- **Wayland**：由于系统安全限制，通常无法进行全局输入监听，因此无法正常使用

---

## 🛡️ 隐私说明

也就是 FlowScroll 在你的电脑上做了什么、没做什么：

### 本地处理

所有滚动计算、窗口检测、黑白名单匹配都在本地完成，不依赖云服务。

### 不采集

- **不记录键盘输入内容**：键盘监听仅用于判断你设置的快捷键是否被触发
- **不保存鼠标轨迹历史**：程序只读取当前鼠标位置与滚动中心点的相对偏移，用于计算滚动方向与速度
- **不读取剪贴板**
- **不截屏**
- **不上传任何使用数据或统计信息**

### 唯一的默认网络请求

程序启动时会向 GitHub API 发送一次版本检查请求：

```text
GET https://api.github.com/repos/CyrilPeng/FlowScroll/releases/latest
```

此请求仅用于获取最新版本信息，**不会上传任何本地数据**。如果你不希望发送该请求，可以在防火墙中阻止，或自行编译去除（`services/update_checker.py`）。

### WebDAV 同步

如果你主动配置了 WebDAV：

- **仅同步**滚动参数配置文件（`~/.FlowScroll_config.json`）
- **不包含**使用记录、窗口历史、键盘记录
- 只有在你点击“上传 / 下载”时，程序才会发起对应请求

---

## ⚠️ 已知兼容性问题

| 问题 | 说明 |
| :--- | :--- |
| **macOS 全屏检测不够精确** | macOS 没有公开 API 可可靠判断窗口是否处于全屏状态，因此“全屏模式下自动禁用”在 macOS 上可能不完全准确 |
| **Windows UWP / 微软商店应用** | 部分运行在沙盒中的应用，鼠标钩子可能无法正常生效 |
| **浏览器原生中键自动滚动冲突** | Chrome / Edge / Firefox 自带中键自动滚动。如果你想避免冲突，可以关闭浏览器原生中键自动滚动，或将浏览器加入排除名单 |
| **远程桌面 / 虚拟机** | 在 RDP、TeamViewer、VMware 等环境中，鼠标事件传递方式不同，可能导致触发异常 |
| **多个输入钩子工具冲突** | 与 AutoHotkey、X-Mouse Button Control 等工具同时运行时，可能互相干扰 |
| **高刷新率显示器** | 在极高刷新率（如 360Hz+）场景下，可能出现轻微不连贯 |

---

## 🛠️ 构建指南（For Developers）

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

## 📝 许可协议

本项目采用 [GNU General Public License v3.0](https://www.gnu.org/licenses/gpl-3.0) 协议开源。  
感谢所有支持与热爱开源的开发者。

<div align="center">
  <sub>Made with ❤️ by 某不科学的高数</sub>
</div>
