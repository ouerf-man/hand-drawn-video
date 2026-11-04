"""p5.brush for hand-drawn projects: download once, check, patch, copy into a project.

The skill does not ship p5.brush. It downloads the official standalone build of a pinned version
(p5.brush by Alejandro Campos Uribe, MIT, https://github.com/acamposuribe/p5.brush) from npm,
checks its SHA-256, and keeps it in kit/.cache/. Each new project gets a copy patched for the
HyperFrames lint, which rejects Math.random() and requestAnimationFrame in any script. p5.brush
only uses them for its first random seed (the drawings re-seed every frame) and a "you forgot
render()" warning timer, so the patch changes nothing on screen.

    python scripts/brushlib.py        # download now (or check the cached copy)

Standard library only. Works on Windows and macOS.
"""
from __future__ import annotations

import hashlib
import os
import shutil
import sys
import urllib.request
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
VERSION = "3.0.0"
URLS = (
    f"https://cdn.jsdelivr.net/npm/p5.brush@{VERSION}/dist/brush.js",
    f"https://unpkg.com/p5.brush@{VERSION}/dist/brush.js",
)
SHA256 = "d8afe814fa4557dcdc41b3fa7a9cec5dfe1c9819700d745232f6c0a4e7add186"
PATCHES = (("Math.random()", "0.5"), ("requestAnimationFrame(", "((f)=>0)("))
CACHE = SKILL / "kit" / ".cache"
LICENSE = SKILL / "kit" / "LICENSE-p5.brush.md"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def patch(js: str) -> str:
    for old, new in PATCHES:
        js = js.replace(old, new)
    return js


def _download(urls) -> bytes:
    errors = []
    for url in urls:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "hand-drawn-video"})
            with urllib.request.urlopen(req, timeout=60) as r:
                data = r.read()
        except Exception as e:  # offline, DNS, HTTP error: try the next mirror
            errors.append(f"{url}: {e}")
            continue
        if sha256(data) != SHA256:
            errors.append(f"{url}: wrong SHA-256 {sha256(data)} (expected {SHA256})")
            continue
        return data
    raise SystemExit(
        f"could not download p5.brush {VERSION}:\n  " + "\n  ".join(errors or ["no download address"])
        + f"\nConnect to the internet and run again, or download {URLS[0]} by hand"
        f" and save it as {CACHE / f'brush-{VERSION}.js'}"
    )


def upstream_js(cache: Path = CACHE, urls=URLS) -> str:
    """The official p5.brush build (unpatched), from the cache or downloaded once and checked."""
    path = cache / f"brush-{VERSION}.js"
    if path.is_file():
        data = path.read_bytes()
        if sha256(data) == SHA256:
            return data.decode("utf-8")
        print(f"[p5.brush] cached {path.name} is damaged: downloading again", file=sys.stderr)
    print(f"[p5.brush] downloading p5.brush {VERSION} (one time, ~110 KB)", file=sys.stderr)
    data = _download(urls)
    cache.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".part")
    tmp.write_bytes(data)
    os.replace(tmp, path)
    return data.decode("utf-8")


def brush_js(cache: Path = CACHE, urls=URLS) -> str:
    """p5.brush patched for HyperFrames."""
    return patch(upstream_js(cache, urls))


def install(vendor_dir: Path, cache: Path = CACHE, urls=URLS) -> Path:
    """Write brush.js (patched) and its MIT licence into a project's vendor folder."""
    vendor_dir.mkdir(parents=True, exist_ok=True)
    target = vendor_dir / "brush.js"
    target.write_text(brush_js(cache, urls), encoding="utf-8", newline="")
    shutil.copyfile(LICENSE, vendor_dir / "LICENSE-p5.brush.md")
    return target


if __name__ == "__main__":
    js = brush_js()
    print(f"p5.brush {VERSION}: ok ({len(js)} characters, cached in {CACHE})")
