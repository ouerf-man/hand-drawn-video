#!/usr/bin/env python3
"""drawify: turn a video of a person into a hand-drawn animation, painted with p5.brush.

    python drawify.py talk.mp4 --start 2 --duration 3 --style print --out my-drawing
    python drawify.py talk.mp4 --style watercolour --out my-drawing --render
    python drawify.py --doctor            # check the install (models, versions)

Pipeline (each step is explained in README.md):
  1. frames  : the clip is sampled at --fps drawings per second (default 12, "on twos")
  2. person  : a matte (--matte video) or MediaPipe's selfie segmenter separates the person
  3. face    : MediaPipe Face Landmarker gives 478 points (brows, lids, irises, nose, lips)
  4. light   : one-sided light is flattened on the face (plane fit), so lit-side features stay dark
  5. tones   : four tone groups on [lightness, 2 x chroma], fixed from the first drawing
  6. marks   : brows, lids, irises, nose and lips placed from the landmarks
  7. project : a HyperFrames project (index.html + data) that p5.brush paints frame by frame
Runs on Windows and macOS: Python 3.9-3.12, no shell commands, paths via pathlib.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

import cv2
import numpy as np

HERE = Path(__file__).resolve().parent
SKILL = HERE.parent.parent
KIT = SKILL / "kit"   # shared HyperFrames project files
sys.path.insert(0, str(SKILL / "scripts"))
import brushlib  # noqa: E402  (downloads, checks and patches p5.brush)
CACHE = Path.home() / ".cache" / "drawify"
MODELS = {
    "face": ("face_landmarker.task",
             "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task"),
    "person": ("selfie_segmenter.tflite",
               "https://storage.googleapis.com/mediapipe-models/image_segmenter/selfie_segmenter/float16/latest/selfie_segmenter.tflite"),
}

# MediaPipe face mesh indices
BROWS = [([70, 63, 105, 66, 107], [55, 65, 52, 53, 46]), ([300, 293, 334, 296, 336], [285, 295, 282, 283, 276])]
EYES = [  # (upper lid outer->inner, lower lid inner->outer, iris centre, iris ring)
    ([33, 246, 161, 160, 159, 158, 157, 173, 133], [133, 155, 154, 153, 145, 144, 163, 7, 33], 468, [469, 470, 471, 472]),
    ([263, 466, 388, 387, 386, 385, 384, 398, 362], [362, 382, 381, 380, 374, 373, 390, 249, 263], 473, [474, 475, 476, 477]),
]
BEARD_TOP = [132, 205, 98, 2, 327, 425, 361]           # jaw - low cheek - under the nose - low cheek - jaw
JAW = [361, 288, 397, 365, 379, 378, 400, 377, 152, 148, 176, 149, 150, 136, 172, 58, 132]
LIPS_OUTER = [61, 185, 40, 39, 37, 0, 267, 269, 270, 409, 291, 375, 321, 405, 314, 17, 84, 181, 91, 146]
LIPS_INNER = [78, 191, 80, 81, 82, 13, 312, 311, 310, 415, 308, 324, 318, 402, 317, 14, 87, 178, 88, 95]
LIP_LINE = [78, 191, 80, 81, 82, 13, 312, 311, 310, 415, 308]
LOWER_LIP = [61, 146, 91, 181, 84, 17, 314, 405, 321, 375, 291, 308, 324, 318, 402, 317, 14, 87, 178, 88, 95, 78]
NOSE_BRIDGE = [168, 6, 197, 195, 5]
FACE_OVAL = [10, 338, 297, 332, 284, 251, 389, 356, 454, 323, 361, 288, 397, 365, 379, 378, 400, 377, 152, 148,
             176, 149, 150, 136, 172, 58, 132, 93, 234, 127, 162, 21, 54, 103, 67, 109]


def log(msg):
    print(f"[drawify] {msg}", flush=True)


def model_path(key):
    name, url = MODELS[key]
    p = CACHE / name
    if not p.exists():
        CACHE.mkdir(parents=True, exist_ok=True)
        log(f"downloading {name} (one time) from {url}")
        urllib.request.urlretrieve(url, p)
    return p


# ---------------------------------------------------------------- small helpers
def half(pts):
    return [round(float(v) / 2, 1) for p in pts for v in p]


def hexc(bgr):
    b, g, r = [int(x) for x in bgr]
    return f"#{r:02x}{g:02x}{b:02x}"


def clean(mask, k_open, k_close):
    if k_open:
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((k_open, k_open), np.uint8))
    if k_close:
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((k_close, k_close), np.uint8))
    return mask


def polys(mask, min_area, eps=2.0, max_n=99):
    cs, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    out = []
    for c in sorted(cs, key=cv2.contourArea, reverse=True)[:max_n]:
        if cv2.contourArea(c) < min_area:
            continue
        p = cv2.approxPolyDP(c, eps, True)[:, 0, :]
        if len(p) >= 3:
            out.append(half(p))
    return out


def edge_lines(gray, mask, lo, hi, min_len, eps, size):
    """Long edges only; each point carries a pressure = how dark the image is there."""
    FW, FH = size
    e = cv2.Canny(gray, lo, hi)
    e[mask == 0] = 0
    cs, _ = cv2.findContours(e, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
    dark = cv2.GaussianBlur(gray, (9, 9), 0)
    out = []
    for c in cs:
        per = cv2.arcLength(c, False)
        if per < min_len:
            continue
        pts = c[:, 0, :].astype(np.float32)
        if cv2.contourArea(c) < per * 1.5:      # a 1-px edge's contour runs out and back: keep one way
            pts = pts[: max(2, len(pts) // 2 + 1)]
        p = cv2.approxPolyDP(pts.reshape(-1, 1, 2), eps, False)[:, 0, :]
        if len(p) < 2:
            continue
        flat = []
        for x, y in p:
            v = dark[min(FH - 1, int(y)), min(FW - 1, int(x))] / 255.0
            flat += [round(float(x) / 2, 1), round(float(y) / 2, 1), round(0.45 + 1.1 * (1 - v), 2)]
        out.append(flat)
    return out


# ---------------------------------------------------------------- reading
def read_frames(video, times, size):
    cap = cv2.VideoCapture(str(video))
    if not cap.isOpened():
        raise SystemExit(f"cannot open {video}")
    out = []
    for t in times:
        cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
        ok, f = cap.read()
        if not ok:
            raise SystemExit(f"cannot read {video} at {t:.2f}s (clip too short?)")
        out.append(cv2.resize(f, size, interpolation=cv2.INTER_AREA))
    return out


def person_masks(frames, matte, times, size):
    if matte:
        raw = read_frames(matte, times, size)
        return [((cv2.GaussianBlur(cv2.cvtColor(m, cv2.COLOR_BGR2GRAY), (7, 7), 0)) > 127).astype(np.uint8) * 255 for m in raw]
    import mediapipe as mp
    from mediapipe.tasks import python as mpt
    from mediapipe.tasks.python import vision
    seg = vision.ImageSegmenter.create_from_options(vision.ImageSegmenterOptions(
        base_options=mpt.BaseOptions(model_asset_path=str(model_path("person"))), output_confidence_masks=True))
    out = []
    for f in frames:
        r = seg.segment(mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(f, cv2.COLOR_BGR2RGB)))
        conf = r.confidence_masks[-1].numpy_view()
        conf = cv2.resize(conf.astype(np.float32), size)
        out.append((cv2.GaussianBlur(conf, (9, 9), 0) > 0.5).astype(np.uint8) * 255)
    return out


def face_points(frames, fps):
    import mediapipe as mp
    from mediapipe.tasks import python as mpt
    from mediapipe.tasks.python import vision
    lm = vision.FaceLandmarker.create_from_options(vision.FaceLandmarkerOptions(
        base_options=mpt.BaseOptions(model_asset_path=str(model_path("face"))),
        running_mode=vision.RunningMode.VIDEO, num_faces=1))
    out = []
    for i, f in enumerate(frames):
        r = lm.detect_for_video(mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(f, cv2.COLOR_BGR2RGB)),
                                int(i * 1000 / fps))
        if r.face_landmarks:
            h, w = f.shape[:2]
            out.append(np.array([[p.x * w, p.y * h] for p in r.face_landmarks[0]], np.float32))
        else:
            out.append(None)
    return out


# ---------------------------------------------------------------- light, tones, marks
def head_weight(P, shape):
    """Soft weight map over the head (face oval grown to include hair), 0 elsewhere."""
    wmap = np.zeros(shape, np.float32)
    if P is None:
        return wmap
    oval = P[FACE_OVAL]
    c = oval.mean(0)
    grown = (oval - c) * np.array([1.35, 1.5]) + c - np.array([0, 0.12 * (oval[:, 1].max() - oval[:, 1].min())])
    cv2.fillPoly(wmap, [grown.astype(np.int32)], 1.0)
    return cv2.GaussianBlur(wmap, (0, 0), 25)


def flatten_light(L, P, inner, chroma):
    """One-sided light pushes lit-side brows/beard out of the dark group. Fit a plane to the
    lightness of the face's skin and remove its slope (dark hair stays dark: only the slope goes)."""
    if P is None:
        return L
    # only skin gets corrected: hair and beard are dark in themselves (low colour), not shadowed.
    # Correcting them too bleached the beard in testing.
    skin_w = np.clip((cv2.GaussianBlur(chroma, (0, 0), 3) - 10) / 12, 0, 1)
    face = np.zeros(L.shape, np.uint8)
    cv2.fillPoly(face, [P[FACE_OVAL].astype(np.int32)], 1)
    sel = (face > 0) & (inner > 0)
    vals = L[sel]
    if vals.size < 500:
        return L
    skin = sel & (L > np.percentile(vals, 45))           # lit-ish skin only
    ys, xs = np.nonzero(skin)
    if len(xs) < 200:
        return L
    A = np.c_[xs, ys, np.ones_like(xs)].astype(np.float32)
    coef, *_ = np.linalg.lstsq(A, L[ys, xs].astype(np.float32), rcond=None)
    yy, xx = np.mgrid[0:L.shape[0], 0:L.shape[1]].astype(np.float32)
    plane = coef[0] * xx + coef[1] * yy
    plane -= plane[sel].mean()
    return L - plane * head_weight(P, L.shape) * skin_w


def features(img, P, inner):
    s = cv2.medianBlur(cv2.bilateralFilter(img, 9, 45, 9), 5)
    lab = cv2.cvtColor(s, cv2.COLOR_BGR2LAB).astype(np.float32)
    chroma = np.hypot(lab[..., 1] - 128, lab[..., 2] - 128)
    L = flatten_light(lab[..., 0], P, inner, chroma)
    return s, np.dstack([L, 2.0 * chroma])


def beard_shape(P, feat, inner, img_bgr):
    """Beard as one continuous mass: landmark region, kept only where it is really dark and low in colour."""
    if P is None:
        return None
    region = np.zeros(inner.shape, np.uint8)
    cv2.fillPoly(region, [P[BEARD_TOP + JAW[1:]].astype(np.int32)], 255)
    cv2.fillPoly(region, [P[LIPS_OUTER].astype(np.int32)], 0)
    region &= inner
    if region.sum() == 0:
        return None
    L, C = feat[..., 0], feat[..., 1] / 2
    skin_L = np.percentile(L[(region > 0)], 85)
    hairy = ((L < skin_L - 28) | (C < 14)) & (region > 0)
    if hairy.sum() < 0.35 * (region > 0).sum():          # clean-shaven: no beard
        return None
    m = (cv2.GaussianBlur(hairy.astype(np.uint8) * 255, (31, 31), 0) > 110).astype(np.uint8) * 255
    m &= region
    cs, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cs = [c for c in sorted(cs, key=cv2.contourArea, reverse=True)[:3] if cv2.contourArea(c) > 400]
    out = [half(cv2.approxPolyDP(c, 2.0, True)[:, 0, :]) for c in cs]
    # darker core well inside the edge: the edge stays soft and textured, not a pasted-on block
    core = cv2.erode(m, np.ones((25, 25), np.uint8))
    cc, _ = cv2.findContours(core, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cores = [half(cv2.approxPolyDP(c, 2.0, True)[:, 0, :]) for c in cc if cv2.contourArea(c) > 300]
    # value target = the beard's own average colour in the footage, not maximum ink
    colour = hexc(cv2.mean(img_bgr, mask=(hairy & (m > 0)).astype(np.uint8))[:3])
    lit_left = float(L[:, : int(P[2][0])][region[:, : int(P[2][0])] > 0].mean()) > float(L[:, int(P[2][0]):][region[:, int(P[2][0]):] > 0].mean())
    return {"p": out, "core": cores, "c": colour, "lit_left": lit_left} if out else None


def marks_from(P, gray, img_bgr):
    if P is None:
        return {}
    def pp(ids):
        return half(P[ids])
    eyes = []
    for up, low, c, ring in EYES:
        r = float(np.mean(np.linalg.norm(P[ring] - P[c], axis=1)))
        eyes.append({"upper": pp(up), "lower": pp(low), "iris": [round(float(P[c][0]) / 2, 1), round(float(P[c][1]) / 2, 1), round(r / 2, 1)]})
    # nose: shadow side = the darker cheek-side of the nose
    lside, rside = P[129].astype(int), P[358].astype(int)
    def patch(p):
        x, y = int(p[0]), int(p[1])
        return float(gray[max(0, y - 6):y + 6, max(0, x - 6):x + 6].mean())
    shadow_left = patch(lside) < patch(rside)
    side = NOSE_BRIDGE + ([98, 64, 129] if shadow_left else [327, 294, 358])
    nostrils = [half([0.55 * P[98] + 0.45 * P[2]]), half([0.55 * P[327] + 0.45 * P[2]])]
    nose_w = float(np.linalg.norm(P[98] - P[327]))
    fh = float(P[152][1] - P[10][1])
    face_up = P[FACE_OVAL].copy()
    top = face_up[:, 1] < P[1][1]                       # grow the upper half to meet the hairline
    face_up[top, 1] -= 0.08 * fh * (P[1][1] - face_up[top, 1]) / max(1.0, P[1][1] - P[10][1])
    lipmask = np.zeros(gray.shape, np.uint8)
    cv2.fillPoly(lipmask, [P[LIPS_OUTER].astype(np.int32)], 255)
    cv2.fillPoly(lipmask, [P[LIPS_INNER].astype(np.int32)], 0)
    lip_c = hexc(cv2.mean(img_bgr, mask=lipmask)[:3]) if lipmask.any() else "#b5706c"
    mc = P[LIPS_OUTER].mean(0)

    def tight(ids):   # the mesh's lip ring reaches past the visible lips into the beard: pull it in
        return (P[ids] - mc) * np.array([0.84, 0.95]) + mc
    return {
        "brows": [half(np.vstack([P[u], P[l]])) for u, l in BROWS],
        "eyes": eyes,
        "nose": {"shadow": half(P[side]), "under": pp([98, 97, 2, 326, 327]), "nostrils": nostrils,
                 "nostril_r": round(nose_w * 0.07 / 2, 1)},
        "lips": {"line": half(tight(LIP_LINE)), "lower": half(tight(LOWER_LIP)), "inner": half(tight(LIPS_INNER)), "c": lip_c,
                 "outer": half(tight(LIPS_OUTER)),
                 "upper": half(tight([61, 185, 40, 39, 37, 0, 267, 269, 270, 409, 291, 308, 415, 310, 311, 312, 13, 82, 81, 80, 191, 78])),
                 "open": bool(np.linalg.norm(P[13] - P[14]) > 0.08 * np.linalg.norm(P[61] - P[291]))},
        # eye socket = underside of the brow (inner -> outer) joined to the upper lid (outer -> inner)
        "sockets": [half(np.vstack([P[BROWS[k][1]], P[EYES[k][0]]])) for k in (0, 1)],
        "face": half(face_up),
        "under_tip": half(np.vstack([P[[98, 2, 327]], P[[327, 2, 98]] + [0, 0.06 * fh]])),
    }


# ---------------------------------------------------------------- main extraction
def extract(args):
    cap = cv2.VideoCapture(str(args.video))
    vw, vh = cap.get(cv2.CAP_PROP_FRAME_WIDTH), cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    if not vw:
        raise SystemExit(f"cannot open {args.video}")
    scale = 1920 / max(vw, vh)
    FW, FH = int(round(vw * scale / 2)) * 2, int(round(vh * scale / 2)) * 2
    size = (FW, FH)
    n = max(1, int(round(args.duration * args.fps)))
    times = [args.start + i / args.fps for i in range(n)]
    log(f"{n} drawings at {args.fps}/s from {args.start}s, working size {FW}x{FH}")
    frames = read_frames(args.video, times, size)
    masks = person_masks(frames, args.matte, times, size)
    pts = [None] * n if args.no_face else face_points(frames, args.fps)
    log(f"face found in {sum(p is not None for p in pts)}/{n} drawings")
    detail = args.style == "print"

    # background, once, away from everywhere the person goes
    union = np.zeros((FH, FW), np.uint8)
    for m in masks:
        union |= m
    bgmask = cv2.bitwise_not(cv2.dilate(union, np.ones((31, 31), np.uint8)))
    bg = cv2.bilateralFilter(frames[0], 9, 60, 9)
    bg_gray = cv2.cvtColor(bg, cv2.COLOR_BGR2GRAY)
    bg_lines = [[v for i, v in enumerate(l) if i % 3 != 2]
                for l in edge_lines(cv2.GaussianBlur(bg_gray, (5, 5), 0), bgmask, 30, 90, 60, 2.0, size)]
    bg_fills = []
    pix = bg[bgmask > 0].reshape(-1, 3).astype(np.float32)
    if len(pix) > 100:
        cv2.setRNGSeed(3)
        _, lb, cen = cv2.kmeans(pix, 6, None, (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0), 2, cv2.KMEANS_PP_CENTERS)
        lab_img = np.full((FH, FW), -1, np.int32)
        lab_img[bgmask > 0] = lb[:, 0]
        for i in range(6):
            for p in polys(clean((lab_img == i).astype(np.uint8) * 255, 9, 9), 2500, eps=4.0, max_n=6):
                bg_fills.append({"c": hexc(cen[i]), "pts": p})

    # four tone groups, fixed from the first drawing (the head when a face is found)
    inner0 = cv2.erode(masks[0], np.ones((7, 7), np.uint8))
    _, f0 = features(frames[0], pts[0], inner0)
    region0 = inner0 > 0
    hw = head_weight(pts[0], inner0.shape)
    if hw.max() > 0:
        region0 &= hw > 0.5
    sample = f0[region0].reshape(-1, 2).astype(np.float32)
    if len(sample) < 100:
        raise SystemExit("no person found in the first drawing (try --matte or another --start)")
    cv2.setRNGSeed(5)
    _, _, CEN = cv2.kmeans(sample, 4, None, (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.5), 3, cv2.KMEANS_PP_CENTERS)
    order = list(np.argsort(CEN[:, 0]))
    palette, out = {}, []
    for i, (img, m) in enumerate(zip(frames, masks)):
        P = pts[i]
        inner = cv2.erode(m, np.ones((7, 7), np.uint8))
        s, feat = features(img, P, inner)
        lab_i = (((feat[:, :, None, :] - CEN[None, None, :, :]) ** 2).sum(-1)).argmin(-1)
        chin = float(P[152][1] + 0.08 * (P[152][1] - P[10][1])) if P is not None else (FH * 0.45)
        tones = []
        for rank, ci in enumerate(order):
            reg = ((lab_i == ci) & (inner > 0)).astype(np.uint8) * 255
            reg = clean(reg, 3, 3) if detail else clean(reg, 3, 7 if rank == 0 else 9)
            if rank in (1, 2) and not detail:          # fewer, larger, softer washes
                reg = (cv2.GaussianBlur(reg, (41, 41), 0) > 140).astype(np.uint8) * 255
            cs, _ = cv2.findContours(reg, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            for c in sorted(cs, key=cv2.contourArea, reverse=True)[:(160 if detail else 40)]:
                if cv2.contourArea(c) < ((25 if rank == 0 else 60) if detail else (60 if rank == 0 else 300)):
                    continue
                p = cv2.approxPolyDP(c, 0.8 if detail else (1.5 if rank == 0 else 2.5), True)[:, 0, :]
                if len(p) < 3:
                    continue
                M = cv2.moments(c)
                head = bool(M["m01"] / max(1e-6, M["m00"]) < chin)
                key = f"{rank}{'h' if head else 'b'}"
                if key not in palette:                 # colours fixed from the first drawing: no flicker
                    one = np.zeros_like(reg)
                    cv2.drawContours(one, [c], -1, 255, -1)
                    palette[key] = hexc(cv2.mean(s, mask=one & reg)[:3])
                t = {"r": rank, "h": head, "p": half(p)}
                if rank == 0 and not detail:           # dark core for the wash; full shape keeps a soft edge
                    one = np.zeros_like(reg)
                    cv2.drawContours(one, [c], -1, 255, -1)
                    core = cv2.erode(one & reg, np.ones((9, 9), np.uint8))
                    cs2, _ = cv2.findContours(core, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                    t["core"] = [half(cv2.approxPolyDP(k, 1.5, True)[:, 0, :]) for k in cs2 if cv2.contourArea(k) > 40]
                tones.append(t)
        gray = cv2.cvtColor(s, cv2.COLOR_BGR2GRAY)
        sil = polys(m, 4000, eps=2.0, max_n=1)
        sil_p = []
        if sil:
            dk = cv2.GaussianBlur(gray, (25, 25), 0)
            for k in range(0, len(sil[0]), 2):
                x, y = int(sil[0][k] * 2), int(sil[0][k + 1] * 2)
                sil_p += [sil[0][k], sil[0][k + 1], round(0.35 + 1.3 * (1 - dk[min(FH - 1, y), min(FW - 1, x)] / 255.0), 2)]
        no_hair = cv2.erode(inner, np.ones((9, 9), np.uint8))
        no_hair[cv2.dilate(((lab_i == order[0]) & (inner > 0)).astype(np.uint8), np.ones((15, 15), np.uint8)) > 0] = 0
        lines = [] if detail else edge_lines(cv2.GaussianBlur(gray, (3, 3), 0), no_hair, 30, 85, 90, 1.6, size)
        mk = {} if detail else marks_from(P, gray, s)
        if mk:
            b = beard_shape(P, feat, inner, s)
            if b:
                mk["beard"] = b
        out.append({"sil": sil_p, "tones": tones, "lines": lines, "chin": round(chin / 2, 1), "marks": mk})
    return {"w": FW // 2, "h": FH // 2, "fps": args.fps, "start": args.start, "duration": n / args.fps,
            "style": args.style, "palette": palette, "bg": {"lines": bg_lines, "fills": bg_fills}, "frames": out}


# ---------------------------------------------------------------- project
def write_project(data, out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "assets").mkdir(exist_ok=True)
    brushlib.install(out_dir / "assets" / "vendor")   # p5.brush, patched for the HyperFrames lint
    (out_dir / "assets" / "data.js").write_text("window.DRAWIFY=" + json.dumps(data, separators=(",", ":")) + ";\n", encoding="utf-8")
    tpl = (HERE / "templates" / f"{data['style']}.html").read_text(encoding="utf-8")
    dur = f"{data['duration']:.3f}".rstrip("0").rstrip(".")
    W2, H2 = data["w"] * 2, data["h"] * 2
    html = tpl.replace("__DUR__", dur).replace("__W2__", str(W2)).replace("__H2__", str(H2))
    (out_dir / "index.html").write_text(html, encoding="utf-8")
    for name in ("hyperframes.json", "package.json", "meta.json"):
        (out_dir / name).write_text((KIT / "project" / name).read_text(encoding="utf-8"), encoding="utf-8")
    log(f"project written: {out_dir}")


def render(out_dir: Path, name: str):
    npx = shutil.which("npx") or shutil.which("npx.cmd")
    if not npx:
        raise SystemExit("Node.js is needed to render (npx not found). Install Node 18+ and run again.")
    target = out_dir / "renders" / f"{name}.mp4"
    log(f"rendering with HyperFrames -> {target}")
    subprocess.run([npx, "--yes", "hyperframes", "render", ".", "-o", str(target)], cwd=out_dir, check=True)
    return target


def doctor():
    import platform
    log(f"python {platform.python_version()} on {platform.system()} {platform.machine()}")
    log(f"opencv {cv2.__version__}, numpy {np.__version__}")
    import mediapipe as mp
    from mediapipe.tasks import python as mpt
    from mediapipe.tasks.python import vision
    log(f"mediapipe {mp.__version__}")
    vision.FaceLandmarker.create_from_options(vision.FaceLandmarkerOptions(base_options=mpt.BaseOptions(model_asset_path=str(model_path("face")))))
    vision.ImageSegmenter.create_from_options(vision.ImageSegmenterOptions(base_options=mpt.BaseOptions(model_asset_path=str(model_path("person"))), output_confidence_masks=True))
    log("models load: ok")
    brushlib.brush_js()
    log(f"p5.brush {brushlib.VERSION}: ok (cached in {brushlib.CACHE})")
    log(f"node/npx (for --render): {shutil.which('npx') or shutil.which('npx.cmd') or 'not found'}")
    log(f"ffmpeg (for --wipe): {shutil.which('ffmpeg') or 'not found'}")


def wipe(video, start, dur, drawn: Path, target: Path):
    ff = shutil.which("ffmpeg")
    if not ff:
        log("ffmpeg not found: skipping the real-to-drawn wipe")
        return None
    fc = ("[0:v]fps=30,settb=1/30,setpts=PTS-STARTPTS,format=yuv420p[a];"
          "[1:v]fps=30,settb=1/30,setpts=PTS-STARTPTS,format=yuv420p,scale=w=iw:h=ih[b0];"
          "[a][b0]scale2ref[a2][b2];"
          f"[b2]trim=start={dur * 0.27:.3f},setpts=PTS-STARTPTS[b];"
          f"[a2][b]xfade=transition=wipeleft:duration={dur * 0.4:.3f}:offset={dur * 0.27:.3f}[v]")
    subprocess.run([ff, "-v", "error", "-y", "-ss", str(start), "-t", str(dur), "-i", str(video), "-i", str(drawn),
                    "-filter_complex", fc, "-map", "[v]", "-an", "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p",
                    "-movflags", "+faststart", str(target)], check=True)
    return target


def main(argv=None):
    ap = argparse.ArgumentParser(description="Turn a video of a person into a hand-drawn animation (p5.brush).")
    ap.add_argument("video", nargs="?", type=Path)
    ap.add_argument("--start", type=float, default=0.0, help="start time in seconds")
    ap.add_argument("--duration", type=float, default=3.0, help="length in seconds")
    ap.add_argument("--fps", type=float, default=12.0, help="drawings per second (12 = classic 'on twos')")
    ap.add_argument("--style", choices=["print", "watercolour"], default="print")
    ap.add_argument("--matte", type=Path, help="optional person matte video (white = person); default: MediaPipe")
    ap.add_argument("--no-face", action="store_true", help="skip face landmarks (non-face subjects, tests)")
    ap.add_argument("--out", type=Path, default=Path("drawify-out"), help="project folder to write")
    ap.add_argument("--render", action="store_true", help="render the MP4 with HyperFrames (needs Node.js)")
    ap.add_argument("--wipe", action="store_true", help="also make a real-to-drawn wipe (needs --render and ffmpeg)")
    ap.add_argument("--doctor", action="store_true", help="check the install and download the models")
    a = ap.parse_args(argv)
    if a.doctor:
        return doctor()
    if not a.video:
        ap.error("give a video (or --doctor)")
    brushlib.upstream_js()   # get p5.brush first, so an offline run fails before the long extraction
    data = extract(a)
    write_project(data, a.out)
    if a.render:
        drawn = render(a.out, f"drawn-{a.style}")
        if a.wipe:
            w = wipe(a.video, a.start, data["duration"], drawn, a.out / "renders" / f"wipe-{a.style}.mp4")
            if w:
                log(f"wipe: {w}")
    else:
        log("next: cd into the project and run  npx hyperframes render . -o drawn.mp4  (or pass --render)")


if __name__ == "__main__":
    sys.exit(main())
