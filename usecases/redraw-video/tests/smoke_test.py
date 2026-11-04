"""Smoke test: runs the whole extraction on a synthetic clip, on any OS (used by CI on Windows and macOS).

    python usecases/redraw-video/tests/smoke_test.py   (from the skill folder)

A coloured 'person' (head + body ellipses with a dark 'hair' cap) moves over a gradient wall.
The matte is given, faces are skipped (no real face in a synthetic clip), so no model download is needed.
Checks: both styles write a project; 12 drawings per second; tone shapes exist; the HTML has the duration.
"""
import json
import sys
import tempfile
from pathlib import Path

import cv2
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import drawify  # noqa: E402


def make_clip(folder: Path, seconds=1.0, fps=30, size=(360, 640)):
    w, h = size
    vid, mat = folder / "clip.mp4", folder / "matte.mp4"
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    v = cv2.VideoWriter(str(vid), fourcc, fps, (w, h))
    m = cv2.VideoWriter(str(mat), fourcc, fps, (w, h))
    for i in range(int(seconds * fps)):
        x = int(w * 0.5 + 25 * np.sin(i / 6))
        frame = np.dstack([np.tile(np.linspace(170, 220, w, dtype=np.uint8), (h, 1))] * 3)
        matte = np.zeros((h, w, 3), np.uint8)
        for img, body, head, hair in ((frame, (120, 110, 190), (140, 165, 215), (40, 35, 35)),
                                      (matte, (255,) * 3, (255,) * 3, (255,) * 3)):
            cv2.ellipse(img, (x, int(h * 0.85)), (int(w * 0.38), int(h * 0.25)), 0, 0, 360, body, -1)
            cv2.ellipse(img, (x, int(h * 0.42)), (int(w * 0.17), int(h * 0.13)), 0, 0, 360, head, -1)
            cv2.ellipse(img, (x, int(h * 0.36)), (int(w * 0.17), int(h * 0.08)), 0, 180, 360, hair, -1)
        v.write(frame)
        m.write(matte)
    v.release()
    m.release()
    return vid, mat


def main():
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        vid, mat = make_clip(tmp)
        for style in ("print", "watercolour"):
            out = tmp / f"proj-{style}"
            drawify.main([str(vid), "--matte", str(mat), "--no-face", "--duration", "1", "--style", style, "--out", str(out)])
            data_js = (out / "assets" / "data.js").read_text(encoding="utf-8")
            data = json.loads(data_js[len("window.DRAWIFY="):].rstrip().rstrip(";"))
            assert len(data["frames"]) == 12, f"{style}: expected 12 drawings, got {len(data['frames'])}"
            assert all(f["tones"] for f in data["frames"]), f"{style}: a drawing has no tone shapes"
            assert any(t["r"] == 0 for t in data["frames"][0]["tones"]), f"{style}: no dark shapes (hair cap)"
            html = (out / "index.html").read_text(encoding="utf-8")
            assert 'data-duration="1"' in html, f"{style}: duration not filled"
            assert not any(k in html for k in ("__DUR__", "__W2__", "__H2__")), f"{style}: template placeholder left"
            brush = (out / "assets" / "vendor" / "brush.js").read_text(encoding="utf-8")
            assert "Math.random()" not in brush and "requestAnimationFrame(" not in brush, "brush.js not patched"
            print(f"ok  {style}: {len(data['frames'])} drawings, {sum(len(f['tones']) for f in data['frames'])} tone shapes")
    print("smoke test passed")


if __name__ == "__main__":
    main()
