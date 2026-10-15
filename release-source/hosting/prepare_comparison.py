#!/usr/bin/env python3
"""Adapt an existing Wisteria static build for a separate comparison URL.

This uses only the Python standard library and never edits the source build.
Example:
    python hosting/prepare_comparison.py --source dist \
        --output /workspace/scratch/wisteria-pages/public \
        --site-url https://lucky-man2985.github.io/Wisteria-cafe/

Only public static files are copied. Existing output is replaced only when it
was created by this adapter (its .nojekyll contains the ownership marker), or
when it is empty. The source and output must not overlap, and source symlinks
are rejected. Repeated runs with the same arguments produce identical bytes.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import shutil
import tempfile
from urllib.parse import urlsplit


OUTPUT_MARKER = "wisteria-comparison-v1\n"
PREVIEW_ORIGIN = "https://wisteria-cafe-new.lackyman2985.chatgpt.site"
PUBLIC_EXTENSIONS = {
    ".html", ".css", ".js", ".svg", ".webp", ".jpg", ".jpeg", ".png",
    ".gif", ".avif", ".ico", ".woff", ".woff2", ".ttf", ".otf",
}
# A comparison build cannot load the production counter, even if an old
# consent value exists in the browser or a production build was supplied.
COMPARISON_ANALYTICS = """/* Analytics is disabled in this comparison build. */
(()=>{
 window.WISTERIA_ANALYTICS={enabled:false};
 document.querySelectorAll('[data-analytics-status]').forEach(node=>{
  node.textContent='Статистика отключена в версии для сравнения';
 });
 document.querySelectorAll('[data-analytics-accept],[data-analytics-deny]').forEach(node=>{
  node.disabled=true;node.hidden=true;
 });
})();
"""


class Adapter:
    def __init__(self, site_url: str) -> None:
        parsed = urlsplit(site_url)
        if (parsed.scheme != "https" or not parsed.netloc or parsed.username
                or parsed.password or parsed.query or parsed.fragment):
            raise ValueError("--site-url must be an absolute HTTPS URL without credentials, query or fragment")
        if any(part in {".", ".."} for part in parsed.path.split("/")):
            raise ValueError("--site-url must not contain relative path segments")
        self.base_path = "/" + parsed.path.strip("/") if parsed.path.strip("/") else ""
        self.site_url = f"https://{parsed.netloc}{self.base_path}/"
        self.origin = f"https://{parsed.netloc}"

    def url(self, value: str) -> str:
        """Rewrite local URL roots, preserving external URLs and fragments."""
        if not value.startswith("/") or value.startswith("//"):
            return value
        if self.base_path and (value == self.base_path or value.startswith(self.base_path + "/")
                               or value.startswith(self.base_path + "?")
                               or value.startswith(self.base_path + "#")):
            return value
        return self.base_path + value

    def origins(self, text: str) -> str:
        # Donor URLs are provenance and external links; only the old preview
        # origin belongs to this deployment's canonical/OG/schema/sitemap.
        return text.replace(PREVIEW_ORIGIN, self.site_url.rstrip("/"))

    def css(self, text: str) -> str:
        def replace(match: re.Match[str]) -> str:
            return match[1] + match[2] + self.url(match[3]) + match[2] + match[4]
        return re.sub(r"(url\(\s*)(['\"]?)(/[^\s)'\"]*)\2(\s*\))", replace,
                      self.origins(text), flags=re.I)

    def attributes(self, text: str) -> str:
        # Match whole attribute names. In particular, data-source-path(s) and
        # data-legacy-source-path are donor filter keys, never navigation URLs.
        attributes = r"(?:href|src|action|formaction|poster|background|cite|data-src|data-href|xlink:href)"
        pattern = rf"(?<![\w:-])({attributes}\s*=\s*)(['\"])(.*?)\2"
        text = re.sub(pattern, lambda m: m[1] + m[2] + self.url(m[3]) + m[2],
                      text, flags=re.I | re.S)

        def srcset(match: re.Match[str]) -> str:
            # Preserve descriptors and all spacing; only root-relative URLs
            # at the beginning of an image candidate are changed.
            value = re.sub(r"(^|,)(\s*)(/[^\s,]+)",
                           lambda m: m[1] + m[2] + self.url(m[3]), match[3])
            return match[1] + match[2] + value + match[2]
        text = re.sub(r"(?<![\w:-])(srcset\s*=\s*)(['\"])(.*?)\2", srcset,
                      text, flags=re.I | re.S)
        # The generated build has no refresh redirects, but this is supported
        # for future repository-generated redirects as well.
        return re.sub(r"(?i)(\burl\s*=\s*)(/[^\s\"'<>;]+)",
                      lambda m: m[1] + self.url(m[2]), text)

    def js(self, text: str) -> str:
        text = self.attributes(self.css(text))
        # Dynamic links in template literals were handled as HTML attributes.
        # Handle explicit fetch calls and URL-valued object properties without
        # touching split('/'), regular expressions, or donor source paths.
        text = re.sub(r"(\b(?:fetch|import)\s*\(\s*)(['\"])(/[^'\"\n]*)\2",
                      lambda m: m[1] + m[2] + self.url(m[3]) + m[2], text)
        return re.sub(r"(?<![\w.])((?:url|href|src)\s*:\s*)(['\"])(/[^'\"\n]*)\2",
                      lambda m: m[1] + m[2] + self.url(m[3]) + m[2], text)

    def document(self, text: str) -> str:
        text = self.js(text)
        robots = '<meta name="robots" content="noindex,follow">'
        robot_pattern = r"<meta\b(?=[^>]*\bname\s*=\s*['\"]robots['\"])[^>]*>"
        if re.search(robot_pattern, text, flags=re.I):
            text = re.sub(robot_pattern, robots, text, flags=re.I)
        else:
            text, count = re.subn(r"</head\s*>", robots + "</head>", text,
                                  count=1, flags=re.I)
            if count != 1:
                raise ValueError("HTML document has no closing head for noindex")

        def disable_analytics(match: re.Match[str]) -> str:
            config = json.loads(match[1])
            config["enabled"] = False
            return "window.WISTERIA_ANALYTICS=" + json.dumps(config, ensure_ascii=False) + ";"
        return re.sub(r"window\.WISTERIA_ANALYTICS\s*=\s*(\{[^{}]*\})\s*;",
                      disable_analytics, text)

    def menu(self, text: str) -> str:
        products = json.loads(text)
        if not isinstance(products, list) or not all(isinstance(p, dict) for p in products):
            raise ValueError("menu.json must contain an array of products")
        for product in products:
            if isinstance(product.get("image"), str):
                product["image"] = self.url(product["image"])
        # No other product field is modified, including donor provenance,
        # price, options, availability, nutrition, and source filter fields.
        return json.dumps(products, ensure_ascii=False, separators=(",", ":")) + "\n"


def is_public(path: Path) -> bool:
    if any(part.startswith(".") for part in path.parts):
        return False
    if path.name.upper() == "CNAME":
        return False
    return (path.suffix.lower() in PUBLIC_EXTENSIONS
            or path.as_posix() in {"menu.json", "sitemap.xml", "robots.txt", "assets/fonts/LICENSE.txt"})


def prepare(source: Path, output: Path, site_url: str) -> dict[str, int | str]:
    if source.is_symlink() or output.is_symlink():
        raise ValueError("source and output must not be symlinks")
    source = source.resolve(strict=True)
    output = output.resolve()
    if not source.is_dir() or not (source / "index.html").is_file():
        raise ValueError("source must be an existing static build with index.html")
    if source == output or source in output.parents or output in source.parents:
        raise ValueError("source and output must not overlap")
    if output.exists():
        if not output.is_dir():
            raise ValueError("output exists and is not a directory")
        if any(output.iterdir()) and (not (output / ".nojekyll").is_file()
                                     or (output / ".nojekyll").read_text() != OUTPUT_MARKER):
            raise ValueError("refusing to replace nonempty output not owned by this adapter")
        if any(p.is_symlink() for p in output.rglob("*")):
            raise ValueError("refusing to replace output containing symlinks")
    adapter = Adapter(site_url)
    files = sorted(p for p in source.rglob("*") if p.is_file())
    if any(p.is_symlink() for p in source.rglob("*")):
        raise ValueError("source symlinks are not supported")
    output.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{output.name}-prepare-", dir=output.parent))
    count = html_count = 0
    backup: Path | None = None
    try:
        for original in files:
            relative = original.relative_to(source)
            if not is_public(relative):
                continue
            target = staging / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            if relative.as_posix() == "menu.json":
                text = adapter.menu(original.read_text(encoding="utf-8"))
            elif relative.as_posix() == "analytics.js":
                text = COMPARISON_ANALYTICS
            elif original.suffix == ".html":
                text = adapter.document(original.read_text(encoding="utf-8"))
                html_count += 1
            elif original.suffix == ".css":
                text = adapter.css(original.read_text(encoding="utf-8"))
            elif original.suffix == ".js":
                text = adapter.js(original.read_text(encoding="utf-8"))
            elif relative.as_posix() == "sitemap.xml":
                text = adapter.origins(original.read_text(encoding="utf-8"))
            elif relative.as_posix() == "robots.txt":
                text = ("User-agent: *\nAllow: /\n"
                        "# Comparison version: every HTML page has noindex.\n")
            else:
                shutil.copyfile(original, target)
                count += 1
                continue
            target.write_text(text, encoding="utf-8")
            count += 1
        (staging / ".nojekyll").write_text(OUTPUT_MARKER, encoding="utf-8")
        if output.exists():
            backup = Path(tempfile.mkdtemp(prefix=f".{output.name}-old-", dir=output.parent))
            backup.rmdir()
            output.rename(backup)
        try:
            staging.rename(output)
        except BaseException:
            if backup is not None:
                backup.rename(output)
            raise
        if backup is not None:
            shutil.rmtree(backup)
    finally:
        if staging.exists():
            shutil.rmtree(staging)
    return {"site_url": adapter.site_url, "output": str(output),
            "files": count + 1, "html_pages": html_count}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--site-url", required=True)
    args = parser.parse_args()
    try:
        result = prepare(args.source, args.output, args.site_url)
    except (OSError, ValueError) as error:
        parser.exit(1, f"error: {error}\n")
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
