(function () {
  const messages = {
    zh: {
      latestVersionFallback: "最新版",
      downloadItem: "下载项",
      platformPackage: "平台包",
      viewPlatformNote: "查看平台说明",
      genericNote: "请确认平台兼容性后再下载。",
      downloadPrefix: "下载",
      downloadCta: (platform) => `下载 ${platform} 版本`,
      sourceGithub: "GitHub Releases",
      sourceGitee: "Gitee Releases",
      loadingGithub: "正在读取 GitHub Releases…",
      loadingGitee: "GitHub Releases 暂时不可用，正在切换到 Gitee Releases…",
      releaseEmpty: "已获取最新发行版，但没有找到可直接展示的下载包。你仍可使用下方备用入口。",
      releaseFailed: "暂时无法连接 GitHub Releases 或 Gitee Releases，请稍后重试，或直接访问仓库页面。",
      statusLoaded: (version, source) => `${source} 最新版本 v${version} 已同步到下载区。`,
      statusLoadedWithDate: (version, source, date) => `${source} 最新版本 v${version} 已同步到下载区，发布时间：${date}。`,
      fallback: {
        githubTitle: "GitHub 官方发布页",
        githubBody: "如果自动检测失败，仍可从 GitHub Releases 手动获取最新版本。",
        githubCta: "前往 GitHub Releases",
        giteeTitle: "Gitee 镜像仓库",
        giteeBody: "当 GitHub 访问受限时，可从 Gitee Releases 获取同步版本。",
        giteeCta: "前往 Gitee Releases"
      },
      platformDetails: {
        windows: {
          label: "Windows",
          badge: "推荐平台",
          className: "good",
          requirement: "通常无需管理员权限",
          note: "推荐大多数用户直接下载。",
          recommended: true
        },
        macos: {
          label: "macOS",
          badge: "需授权",
          className: "warn",
          requirement: "首次运行需授予辅助功能权限",
          note: "首次运行可能需要授予辅助功能权限。"
        },
        linux: {
          label: "Linux",
          badge: "实验性预览",
          className: "neutral",
          requirement: "建议在 X11/Xorg 环境使用",
          note: "Wayland 通常无法进行传统的全局输入监听。"
        },
        default: {
          badge: "平台包",
          className: "neutral",
          requirement: "查看平台说明",
          note: "请确认平台兼容性后再下载。"
        }
      }
    },
    en: {
      latestVersionFallback: "Latest",
      downloadItem: "Download",
      platformPackage: "Package",
      viewPlatformNote: "Check platform notes",
      genericNote: "Check platform compatibility before downloading.",
      downloadPrefix: "Download",
      downloadCta: (platform) => `Download for ${platform}`,
      sourceGithub: "GitHub Releases",
      sourceGitee: "Gitee Releases",
      loadingGithub: "Loading the latest GitHub release…",
      loadingGitee: "GitHub Releases is unavailable. Falling back to Gitee Releases…",
      releaseEmpty: "The latest release was loaded, but no downloadable packages were found. You can still use the fallback links below.",
      releaseFailed: "GitHub Releases and Gitee Releases are both temporarily unavailable. Please try again later or open the repository pages directly.",
      statusLoaded: (version, source) => `Latest build v${version} from ${source} is available in the download section.`,
      statusLoadedWithDate: (version, source, date) => `Latest build v${version} from ${source} is available in the download section. Published: ${date}.`,
      fallback: {
        githubTitle: "GitHub Releases",
        githubBody: "If automatic detection fails, GitHub Releases remains available as the primary manual download path.",
        githubCta: "Open GitHub Releases",
        giteeTitle: "Gitee mirror",
        giteeBody: "When GitHub is unavailable, Gitee Releases stays available as the fallback source.",
        giteeCta: "Open Gitee Releases"
      },
      platformDetails: {
        windows: {
          label: "Windows",
          badge: "Recommended",
          className: "good",
          requirement: "Usually no admin rights required",
          note: "Best default choice for most users.",
          recommended: true
        },
        macos: {
          label: "macOS",
          badge: "Permission",
          className: "warn",
          requirement: "Accessibility permission required on first run",
          note: "You will usually need to grant Accessibility permission."
        },
        linux: {
          label: "Linux",
          badge: "Preview",
          className: "neutral",
          requirement: "Best used on X11/Xorg",
          note: "Wayland usually cannot support this class of global input hook."
        },
        default: {
          badge: "Package",
          className: "neutral",
          requirement: "Check platform notes",
          note: "Check platform compatibility before downloading."
        }
      }
    }
  };

  const defaultConfig = {
    githubUrl: "https://github.com/CyrilPeng/FlowScroll",
    giteeUrl: "https://gitee.com/CyrilPeng/FlowScroll"
  };

  const config = Object.assign({}, defaultConfig, window.FLOWSCROLL_CONFIG || {});
  const locale = document.documentElement.lang.toLowerCase().startsWith("en") ? "en" : "zh";
  const releasesUrl = toReleasesUrl(config.githubUrl);
  const giteeReleasesUrl = toReleasesUrl(config.giteeUrl);
  const text = messages[locale];
  const githubRepo = parseRepoInfo(config.githubUrl);
  const giteeRepo = parseRepoInfo(config.giteeUrl);

  const el = {
    status: document.getElementById("download-status"),
    grid: document.getElementById("download-grid"),
    headerDownloadButton: document.getElementById("header-download-button"),
    heroDownloadButton: document.getElementById("hero-download-button"),
    repoLink: document.getElementById("repo-link"),
    giteeLink: document.getElementById("gitee-link")
  };
  const primaryDownloadButtons = [
    el.headerDownloadButton,
    el.heroDownloadButton
  ].filter(Boolean);

  const repoLinks = [el.repoLink].filter(Boolean);
  const giteeLinks = [el.giteeLink].filter(Boolean);

  repoLinks.forEach((node) => (node.href = config.githubUrl));
  giteeLinks.forEach((node) => (node.href = config.giteeUrl));
  setPrimaryDownloadButtons();

  function toReleasesUrl(value) {
    const url = String(value || "").replace(/\/+$/, "");
    if (!url) return "";
    return /\/releases$/i.test(url) ? url : `${url}/releases`;
  }

  function parseRepoInfo(value) {
    const match = String(value || "")
      .trim()
      .match(/^https?:\/\/[^/]+\/([^/]+)\/([^/#?]+?)(?:\/(?:releases|tags).*)?$/i);
    if (!match) return null;
    return {
      owner: match[1],
      repo: match[2].replace(/\.git$/i, "")
    };
  }

  function escapeHtml(value) {
    return String(value)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#39;");
  }

  function formatDate(dateString) {
    if (!dateString) return "--";
    const date = new Date(dateString);
    if (Number.isNaN(date.getTime())) return dateString;
    return new Intl.DateTimeFormat(locale === "en" ? "en-US" : "zh-CN", {
      year: "numeric",
      month: "2-digit",
      day: "2-digit"
    }).format(date);
  }

  function normalizePlatform(value) {
    return String(value || "").trim().toLowerCase();
  }

  function sortFiles(files) {
    const rank = { windows: 0, macos: 1, linux: 2 };
    return files.slice().sort((a, b) => {
      const aRank = rank[normalizePlatform(a.platform)] ?? 99;
      const bRank = rank[normalizePlatform(b.platform)] ?? 99;
      return aRank - bRank;
    });
  }

  function normalizeUrl(value) {
    if (!value) return "";
    return /^https?:\/\//i.test(value) ? value : "";
  }

  function inferFileType(filename) {
    const name = String(filename || "").toLowerCase();
    if (name.endsWith(".exe")) return "EXE";
    if (name.endsWith(".dmg")) return "DMG";
    if (name.endsWith(".appimage")) return "AppImage";
    if (name.endsWith(".zip")) return "ZIP";
    return locale === "en" ? "File" : "文件";
  }

  function getPlatformDetail(platformKey) {
    return text.platformDetails[platformKey] || text.platformDetails.default;
  }

  function getDisplayNote(item, detail) {
    if (locale === "zh") {
      return item.note || detail.note || text.genericNote;
    }
    return detail.note || item.note || text.genericNote;
  }

  function setPrimaryDownloadButtons(version, url) {
    const safeVersion = formatVersionLabel(version);
    const href = url || "#downloads";

    primaryDownloadButtons.forEach((node) => {
      if (!node.dataset.label) {
        node.dataset.label = node.textContent.trim();
      }
      const baseLabel = node.dataset.label;
      node.textContent = safeVersion ? `${baseLabel} ${safeVersion}` : baseLabel;
      setButtonLink(node, href);
    });
  }

  function setButtonLink(node, href) {
    node.href = href;
    if (/^https?:\/\//i.test(href)) {
      node.target = "_blank";
      node.rel = "noreferrer";
    } else {
      node.removeAttribute("target");
      node.removeAttribute("rel");
    }
  }

  function normalizeVersion(value) {
    return String(value || "").trim().replace(/^v/i, "");
  }

  function formatVersionLabel(value) {
    const token = String(value || "").trim();
    if (!token) return "";
    if (/^v/i.test(token)) return token;
    return /^\d/.test(token) ? `v${token}` : token;
  }

  function inferPlatformAsset(name) {
    const filename = String(name || "").trim();
    const lower = filename.toLowerCase();

    if (lower.endsWith(".exe") || /(?:^|[-_. ])win(?:dows)?(?:[-_. ]|$)/.test(lower)) {
      return { platform: "windows", label: "Windows" };
    }

    if (lower.endsWith(".dmg") || /(?:^|[-_. ])(?:mac|macos|darwin)(?:[-_. ]|$)/.test(lower)) {
      return { platform: "macos", label: "macOS" };
    }

    if (lower.endsWith(".appimage") || /(?:^|[-_. ])linux(?:[-_. ]|$)/.test(lower)) {
      return { platform: "linux", label: "Linux" };
    }

    return { platform: "", label: filename || text.downloadItem };
  }

  function isInstallerAsset(name) {
    const lower = String(name || "").toLowerCase();
    return lower.endsWith(".exe") || lower.endsWith(".dmg") || lower.endsWith(".appimage");
  }

  function normalizeAsset(item, releaseVersion, releaseTag, source, repoInfo) {
    const filename = String(item.name || item.filename || "").trim();
    if (!isInstallerAsset(filename)) return null;

    const inferred = inferPlatformAsset(filename);
    const url =
      normalizeUrl(
        item.browser_download_url || item.browserDownloadUrl || item.download_url || item.downloadUrl
      ) ||
      (source === "gitee" && repoInfo
        ? `https://gitee.com/${repoInfo.owner}/${repoInfo.repo}/releases/download/${encodeURIComponent(
            releaseTag || releaseVersion
          )}/${encodeURIComponent(filename)}`
        : "");

    if (!url) return null;

    return {
      platform: inferred.platform,
      label: inferred.label,
      filename: filename,
      url: url,
      version: releaseVersion
    };
  }

  function normalizeReleasePayload(source, release, files, repoInfo) {
    const rawTag = String(release.tag_name || release.name || "").trim();
    const version = normalizeVersion(rawTag || text.latestVersionFallback);
    const normalizedFiles = files
      .map((item) => normalizeAsset(item, version, rawTag, source, repoInfo))
      .filter(Boolean);

    return {
      source: source,
      version: version || text.latestVersionFallback,
      updatedAt: release.published_at || release.created_at || release.updated_at || "",
      releaseUrl: release.html_url || (source === "github" ? releasesUrl : giteeReleasesUrl),
      files: sortFiles(normalizedFiles)
    };
  }

  async function fetchJson(url, options) {
    const response = await fetch(url, Object.assign({ cache: "no-store" }, options || {}));
    if (!response.ok) {
      throw new Error(`Request failed: ${response.status}`);
    }
    return response.json();
  }

  async function fetchGitHubRelease() {
    if (!githubRepo) throw new Error("GitHub repository URL is not configured");
    const release = await fetchJson(
      `https://api.github.com/repos/${githubRepo.owner}/${githubRepo.repo}/releases/latest`,
      {
        headers: {
          Accept: "application/vnd.github+json"
        }
      }
    );
    return normalizeReleasePayload("github", release, Array.isArray(release.assets) ? release.assets : [], githubRepo);
  }

  async function fetchGiteeRelease() {
    if (!giteeRepo) throw new Error("Gitee repository URL is not configured");
    const release = await fetchJson(
      `https://gitee.com/api/v5/repos/${giteeRepo.owner}/${giteeRepo.repo}/releases/latest`
    );

    let files =
      release.attach_files || release.attachFiles || release.assets || release.attachFilesList || [];

    if ((!Array.isArray(files) || !files.length) && release.id) {
      files = await fetchJson(
        `https://gitee.com/api/v5/repos/${giteeRepo.owner}/${giteeRepo.repo}/releases/${release.id}/attach_files`
      );
    }

    return normalizeReleasePayload("gitee", release, Array.isArray(files) ? files : [], giteeRepo);
  }

  function renderDownloads(releaseData) {
    const version = releaseData.version || text.latestVersionFallback;
    const updatedAt = releaseData.updatedAt || "";
    const files = Array.isArray(releaseData.files) ? releaseData.files : [];
    const primaryFile = files.find((item) => item.platform === "windows") || files[0];
    const sourceLabel = releaseData.source === "gitee" ? text.sourceGitee : text.sourceGithub;
    const primaryUrl = primaryFile?.url || releaseData.releaseUrl || releasesUrl;

    if (!files.length) {
      renderFallback(text.releaseEmpty, {
        preferredUrl: primaryUrl,
        preferredVersion: version
      });
      return;
    }

    setPrimaryDownloadButtons(version, primaryUrl);

    el.grid.innerHTML = files
      .map((item) => {
        const platformKey = normalizePlatform(item.platform);
        const detail = getPlatformDetail(platformKey);
        const rawTitle = item.label || detail.label || item.platform || text.downloadItem;
        const title = escapeHtml(rawTitle);
        const note = escapeHtml(getDisplayNote(item, detail));
        const url = escapeHtml(normalizeUrl(item.url || item.filename || ""));
        const versionText = escapeHtml(item.version || version);
        const badge = escapeHtml(detail.badge || text.platformPackage);
        const requirement = escapeHtml(detail.requirement || text.viewPlatformNote);
        const badgeClass = detail.className || "neutral";
        const fileType = inferFileType(item.filename || item.url || "");
        const downloadLabel = escapeHtml(text.downloadCta ? text.downloadCta(rawTitle) : `${text.downloadPrefix} ${rawTitle}`);

        return `
          <article class="download-card ${detail.recommended ? "recommended" : ""}">
            <div class="download-header">
              <div>
                <span class="platform-pill ${badgeClass}">${badge}</span>
                <h3>${title}</h3>
              </div>
              <span class="download-version">v${versionText}</span>
            </div>
            <p>${note}</p>
            <div class="download-hints">
              <span>${requirement}</span>
              <span>${fileType}</span>
            </div>
            <a class="download-button" href="${url}" target="_blank" rel="noreferrer">${downloadLabel}</a>
          </article>
        `;
      })
      .join("");

    el.status.className = "status-banner success";
    el.status.textContent = updatedAt
      ? text.statusLoadedWithDate(version, sourceLabel, formatDate(updatedAt))
      : text.statusLoaded(version, sourceLabel);
  }

  function renderFallback(message, options) {
    const preferredUrl = options?.preferredUrl || releasesUrl;
    const preferredVersion = options?.preferredVersion || "";

    el.grid.innerHTML = `
      <article class="download-card">
        <h3>${text.fallback.githubTitle}</h3>
        <p>${text.fallback.githubBody}</p>
        <a class="repo-fallback" href="${escapeHtml(releasesUrl)}" target="_blank" rel="noreferrer">${text.fallback.githubCta}</a>
      </article>
      <article class="download-card">
        <h3>${text.fallback.giteeTitle}</h3>
        <p>${text.fallback.giteeBody}</p>
        <a class="repo-fallback" href="${escapeHtml(giteeReleasesUrl || config.giteeUrl)}" target="_blank" rel="noreferrer">${text.fallback.giteeCta}</a>
      </article>
    `;

    el.status.className = "status-banner warning";
    el.status.textContent = message;
    setPrimaryDownloadButtons(preferredVersion, preferredUrl);
  }

  async function init() {
    try {
      el.status.textContent = text.loadingGithub;
      const release = await fetchGitHubRelease();
      renderDownloads(release);
    } catch (error) {
      console.error(error);
      try {
        el.status.textContent = text.loadingGitee;
        const fallbackRelease = await fetchGiteeRelease();
        renderDownloads(fallbackRelease);
      } catch (fallbackError) {
        renderFallback(text.releaseFailed);
        console.error(fallbackError);
      }
    }
  }

  init();
})();
