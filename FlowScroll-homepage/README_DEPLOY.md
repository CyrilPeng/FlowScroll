# FlowScroll 官网部署说明

这个目录是一套可直接部署到 Cloudflare Pages 的静态站。

## 当前下载逻辑

- 页面优先请求 GitHub 最新 release：
  `https://api.github.com/repos/{owner}/{repo}/releases/latest`
- GitHub 不可用时，自动回退到 Gitee 最新 release：
  `https://gitee.com/api/v5/repos/{owner}/{repo}/releases/latest`
- 如果 Gitee 最新 release 没直接返回附件列表，页面会继续请求：
  `https://gitee.com/api/v5/repos/{owner}/{repo}/releases/{release_id}/attach_files`
- 页面只展示可直接下载的发布文件类型：
  - `.exe`
  - `.dmg`
  - `.AppImage`
- 顶部和首屏“立即下载”按钮会跟随当前成功获取到的 release 显示版本号，并直接跳到对应来源的发布文件。

## 目录说明

- `index.html`：中文主页
- `en.html`：英文页
- `styles.css`：样式
- `app.js`：下载区逻辑，按页面语言切换文案，并自动获取 GitHub / Gitee 最新 release
- `seo.js`：根据 `config.js` 中的站点 URL 动态补 canonical、hreflang、`og:url` 与结构化数据
- `config.js`：站点配置
- `generate_sitemap.py`：按生产域名生成 `sitemap.xml`
- `robots.txt`：基础爬虫放行规则

## config.js

当前只需要这几个字段：

```js
window.FLOWSCROLL_CONFIG = {
  siteUrl: "https://flowscroll.example.com",
  githubUrl: "https://github.com/CyrilPeng/FlowScroll",
  giteeUrl: "https://gitee.com/CyrilPeng/FlowScroll"
};
```

说明：

- `siteUrl`：用于 canonical、hreflang、`og:url` 和结构化数据
- `githubUrl`：主仓库地址，同时用于拼接 GitHub Releases 页面和 API
- `giteeUrl`：镜像仓库地址，同时用于拼接 Gitee Releases 页面和 API

## 上线检查清单

发布前建议按下面顺序过一遍：

1. `config.js` 中的 `siteUrl`、`githubUrl`、`giteeUrl` 是否指向正式地址
2. GitHub Releases 的最新版本是否已经包含 Windows / macOS / Linux 对应发布文件
3. Gitee Releases 是否已同步同一版本，且附件可访问
4. `python generate_sitemap.py https://你的域名 > sitemap.xml` 是否已经执行
5. `robots.txt` 中是否已经补上正式的 `Sitemap:` 地址
6. `index.html` 与 `en.html` 部署后是否都能正常打开，语言切换是否互通
7. 当 GitHub 不可访问时，下载区是否能自动回退到 Gitee Releases

## 失败回退行为

- GitHub release 读取失败：自动切换到 Gitee release
- Gitee release 也失败：下载区显示 GitHub Releases / Gitee Releases 手动入口
- 如果成功读取到了 release，但没找到可展示的下载文件：按钮会保留版本号，并指向对应 release 页面

## 生成 sitemap

部署到正式域名后，运行：

```bash
python generate_sitemap.py https://flowscroll.example.com > sitemap.xml
```

## robots.txt

生成 `sitemap.xml` 后，把下面这一行替换成真实域名：

```txt
Sitemap: https://flowscroll.example.com/sitemap.xml
```
