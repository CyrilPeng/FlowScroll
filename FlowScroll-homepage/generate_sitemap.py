from __future__ import annotations

import argparse
import sys
from datetime import date
from xml.sax.saxutils import escape

PAGES = [
    ("/", "weekly", 1.0),
    ("/en.html", "weekly", 0.8),
]


def normalize_site_url(value: str) -> str:
    site_url = value.strip().rstrip("/")
    if not site_url.startswith(("http://", "https://")):
        raise ValueError("site_url must start with http:// or https://")
    return site_url


def build_sitemap(site_url: str, lastmod: str) -> str:
    lines = ['<?xml version="1.0" encoding="UTF-8"?>']
    lines.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
    for path, changefreq, priority in PAGES:
        loc = escape(f"{site_url}{path}")
        lines.extend(
            [
                "  <url>",
                f"    <loc>{loc}</loc>",
                f"    <lastmod>{lastmod}</lastmod>",
                f"    <changefreq>{changefreq}</changefreq>",
                f"    <priority>{priority:.1f}</priority>",
                "  </url>",
            ]
        )
    lines.append("</urlset>")
    return "\n".join(lines) + "\n"


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate sitemap.xml for the FlowScroll homepage.")
    parser.add_argument("site_url", help="Production site URL, for example https://flowscroll.example.com")
    parser.add_argument(
        "--lastmod",
        default=date.today().isoformat(),
        help="ISO date to use as the lastmod value (default: today)",
    )
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    try:
        site_url = normalize_site_url(args.site_url)
    except ValueError as error:
        print(str(error), file=sys.stderr)
        return 1

    sys.stdout.write(build_sitemap(site_url, args.lastmod))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
