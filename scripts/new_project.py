"""Start a hand-drawn video project from a use case.

    python scripts/new_project.py explainer my-video
    python scripts/new_project.py --list

Copies usecases/<name>/index.html plus the shared kit (handwriting font, HyperFrames project
files) into a new folder, with p5.brush (downloaded once, checked and patched by brushlib.py).
Any folder in usecases/ that has an index.html is a use case, so adding one needs no change
here. Works on Windows and macOS.
"""
import argparse
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import brushlib  # noqa: E402

SKILL = Path(__file__).resolve().parent.parent
USECASES = SKILL / "usecases"
KIT = SKILL / "kit"


def available():
    return sorted(p.name for p in USECASES.iterdir() if (p / "index.html").is_file())


def new_project(usecase: str, out: Path) -> Path:
    src = USECASES / usecase / "index.html"
    if not src.is_file():
        raise SystemExit(f"no use case '{usecase}' with an index.html. Available: {', '.join(available())}")
    if out.exists() and any(out.iterdir()):
        raise SystemExit(f"{out} already exists and is not empty: pick a new folder")
    brushlib.upstream_js()   # download (or fail) before making any folder
    (out / "assets" / "fonts").mkdir(parents=True, exist_ok=True)
    (out / "renders").mkdir(exist_ok=True)
    shutil.copyfile(src, out / "index.html")
    brushlib.install(out / "assets" / "vendor")
    for f in (KIT / "fonts").iterdir():
        shutil.copyfile(f, out / "assets" / "fonts" / f.name)
    shutil.copyfile(KIT / "project" / "hyperframes.json", out / "hyperframes.json")
    shutil.copyfile(KIT / "project" / "package.json", out / "package.json")
    slug = out.resolve().name
    (out / "meta.json").write_text(json.dumps({"id": slug, "name": slug}) + "\n", encoding="utf-8")
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description="Start a hand-drawn video project from a use case.")
    ap.add_argument("usecase", nargs="?", help="folder name in usecases/ (see --list)")
    ap.add_argument("out", nargs="?", type=Path, help="new project folder")
    ap.add_argument("--list", action="store_true", help="list the use cases")
    a = ap.parse_args(argv)
    if a.list or not a.usecase or not a.out:
        print("use cases:", ", ".join(available()))
        return 0 if a.list else 1
    p = new_project(a.usecase, a.out)
    print(f"project ready: {p}\n  preview: cd \"{p}\" && npx --yes hyperframes preview"
          f"\n  render:  cd \"{p}\" && npx --yes hyperframes render . -o renders/video.mp4")
    return 0


if __name__ == "__main__":
    sys.exit(main())
