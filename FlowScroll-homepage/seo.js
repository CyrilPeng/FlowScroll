(function () {
  const config = window.FLOWSCROLL_CONFIG || {};
  const siteUrl = normalizeSiteUrl(config.siteUrl);
  const githubUrl = String(config.githubUrl || "").replace(/\/+$/, "");
  const giteeUrl = String(config.giteeUrl || "").replace(/\/+$/, "");
  const releasesUrl = githubUrl ? `${githubUrl}/releases` : "";
  const pageLang = document.documentElement.lang.toLowerCase().startsWith("en")
    ? "en-US"
    : "zh-CN";
  const isEnglishPage = pageLang === "en-US";
  const canonicalPath = isEnglishPage ? "en.html" : "";

  if (siteUrl) {
    const canonicalUrl = absoluteUrl(siteUrl, canonicalPath);
    setLinkTag("canonical", canonicalUrl);
    setLinkTag("alternate-zh", absoluteUrl(siteUrl, ""), {
      rel: "alternate",
      hreflang: "zh-CN"
    });
    setLinkTag("alternate-en", absoluteUrl(siteUrl, "en.html"), {
      rel: "alternate",
      hreflang: "en"
    });
    setLinkTag("alternate-default", absoluteUrl(siteUrl, ""), {
      rel: "alternate",
      hreflang: "x-default"
    });
    setMetaTag("og:url", canonicalUrl, "property");
  }

  setStructuredData({
    "@context": "https://schema.org",
    "@type": "SoftwareApplication",
    name: "FlowScroll",
    applicationCategory: "UtilitiesApplication",
    operatingSystem: "Windows, macOS, Linux",
    description:
      document.querySelector('meta[name="description"]')?.getAttribute("content") || "",
    inLanguage: pageLang,
    image: "https://git-pictures.cyrilworkshop.dpdns.org/flowscroll/1.jpg",
    screenshot: [
      "https://git-pictures.cyrilworkshop.dpdns.org/flowscroll/1.jpg",
      "https://git-pictures.cyrilworkshop.dpdns.org/flowscroll/2.jpg",
      "https://git-pictures.cyrilworkshop.dpdns.org/flowscroll/3.jpg"
    ],
    url: siteUrl ? absoluteUrl(siteUrl, canonicalPath) : githubUrl,
    downloadUrl: releasesUrl || githubUrl,
    codeRepository: githubUrl,
    sameAs: [githubUrl, giteeUrl].filter(Boolean)
  });

  function normalizeSiteUrl(value) {
    const text = String(value || "").trim().replace(/\/+$/, "");
    if (!text) return "";
    try {
      return new URL(text).toString().replace(/\/+$/, "");
    } catch (_error) {
      return "";
    }
  }

  function absoluteUrl(base, path) {
    return new URL(path.replace(/^\.\//, ""), `${base}/`).toString();
  }

  function setMetaTag(name, content, attrName) {
    if (!content) return;
    const attribute = attrName || "name";
    let tag = document.head.querySelector(`meta[${attribute}="${name}"]`);
    if (!tag) {
      tag = document.createElement("meta");
      tag.setAttribute(attribute, name);
      document.head.appendChild(tag);
    }
    tag.setAttribute("content", content);
  }

  function setLinkTag(key, href, attrs) {
    if (!href) return;
    let tag = document.head.querySelector(`link[data-seo-key="${key}"]`);
    if (!tag) {
      tag = document.createElement("link");
      tag.setAttribute("data-seo-key", key);
      document.head.appendChild(tag);
    }
    const properties = Object.assign({}, attrs || {}, { href: href });
    Object.entries(properties).forEach(([attr, value]) => {
      tag.setAttribute(attr, value);
    });
  }

  function setStructuredData(payload) {
    let script = document.head.querySelector('script[data-seo-structured="software"]');
    if (!script) {
      script = document.createElement("script");
      script.type = "application/ld+json";
      script.setAttribute("data-seo-structured", "software");
      document.head.appendChild(script);
    }
    script.textContent = JSON.stringify(payload);
  }
})();
