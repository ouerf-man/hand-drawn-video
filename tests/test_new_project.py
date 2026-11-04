"""Quick checks for the skill (no browser, no models): run on Windows and macOS in CI.

    python tests/test_new_project.py

- p5.brush downloads at the pinned version, its SHA-256 is checked, and the patched copy has no
  Math.random() / requestAnimationFrame( (the HyperFrames lint rejects both);
- a wrong download, a damaged cache and no connection give clear errors;
- every use case folder has a USECASE.md and is listed in SKILL.md, and every template makes a
  complete project that follows the seek contract and uses no unseeded randomness.
Standard library only.
"""
import sys
import tempfile
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL / "scripts"))
import brushlib  # noqa: E402
import new_project  # noqa: E402


def expect_exit(fn, words):
    try:
        fn()
    except SystemExit as e:
        assert all(w in str(e) for w in words), f"error message lacks {words}: {e}"
        return
    raise AssertionError(f"did not fail (expected an error with {words})")


def check_library(tmp: Path):
    js = brushlib.upstream_js()
    assert brushlib.sha256(js.encode("utf-8")) == brushlib.SHA256, "cached p5.brush has the wrong SHA-256"
    assert "Math.random()" in js and "requestAnimationFrame(" in js, "upstream build changed: re-check the patches"
    patched = brushlib.brush_js()
    assert "Math.random()" not in patched and "requestAnimationFrame(" not in patched, "patch did not apply"
    print(f"ok  p5.brush {brushlib.VERSION} downloaded, SHA-256 checked, patched")

    # a download with the wrong content is refused (file:// URL, no network needed)
    bad = tmp / "bad.js"
    bad.write_text("console.log('not p5.brush')", encoding="utf-8")
    expect_exit(lambda: brushlib.upstream_js(tmp / "c1", (bad.as_uri(),)), ["wrong SHA-256"])
    assert not (tmp / "c1" / f"brush-{brushlib.VERSION}.js").exists(), "a bad download was cached"
    # a damaged cache is replaced by a good download
    good = tmp / "good.js"
    good.write_text(js, encoding="utf-8", newline="")
    damaged = tmp / "c2" / f"brush-{brushlib.VERSION}.js"
    damaged.parent.mkdir()
    damaged.write_text("damaged", encoding="utf-8")
    assert brushlib.upstream_js(tmp / "c2", (good.as_uri(),)) == js, "damaged cache not replaced"
    # offline and nothing cached: a clear error
    expect_exit(lambda: brushlib.upstream_js(tmp / "c3", ((tmp / "missing.js").as_uri(),)),
                ["could not download p5.brush", "internet"])
    print("ok  bad download refused, damaged cache replaced, offline error is clear")


def check_usecases(tmp: Path):
    folders = [p for p in (SKILL / "usecases").iterdir() if p.is_dir()]
    for f in folders:
        assert (f / "USECASE.md").is_file(), f"{f.name}: missing USECASE.md"
    templates = new_project.available()
    assert {"blank", "explainer", "story"} <= set(templates), templates
    skill_md = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    for f in folders:
        assert f"`{f.name}`" in skill_md, f"{f.name}: not listed in SKILL.md"

    for name in templates:
        out = new_project.new_project(name, tmp / "projects" / name)
        html = (out / "index.html").read_text(encoding="utf-8")
        for need in ('src="assets/vendor/brush.js"', '"hf-seek"', "brush.render()", '__timelines["main"]', 'data-composition-id="main"'):
            assert need in html, f"{name}: index.html lacks {need}"
        for banned in ("Math.random(", "Date.now(", "requestAnimationFrame(", "setTimeout(", "setInterval("):
            assert banned not in html, f"{name}: index.html uses {banned}"
        for rel in ("assets/vendor/brush.js", "assets/vendor/LICENSE-p5.brush.md", "assets/fonts/caveat-latin-700.woff2",
                    "hyperframes.json", "package.json", "meta.json"):
            assert (out / rel).is_file(), f"{name}: missing {rel}"
        assert (out / "assets/vendor/brush.js").read_text(encoding="utf-8") == brushlib.brush_js(), f"{name}: brush.js not the patched build"
        print(f"ok  {name}")
    expect_exit(lambda: new_project.new_project("does-not-exist", tmp / "x"), ["no use case"])
    print(f"all {len(templates)} templates ok, {len(folders)} use cases documented")


def main():
    with tempfile.TemporaryDirectory() as tmp:
        check_library(Path(tmp))
        check_usecases(Path(tmp))


if __name__ == "__main__":
    main()
