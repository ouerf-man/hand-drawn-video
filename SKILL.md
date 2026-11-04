---
name: hand-drawn-video
description: Make videos that look drawn by hand (pen, pencil, charcoal, marker, crayon, watercolour, ink) with p5.brush inside HyperFrames, in any style. Ships use cases to start from - a hand-drawn explainer, an animated doodle story, and redrawing a real video of a person - and grows by adding use-case folders. Use when someone asks for a "hand-drawn", "drawn", "sketched", "doodle", "sketchnote", "whiteboard", "watercolour" or "rotoscope" video or animation, "draw my video", or "turn me into a drawing". Runs on Windows and macOS.
---

# Hand-drawn video

Everything on screen is painted by [p5.brush](https://github.com/acamposuribe/p5.brush) (real pen, pencil and watercolour textures, drawn on the GPU) inside a [HyperFrames](https://hyperframes.heygen.com) project, and every frame is a pure function of time, so the render is exact. The use cases below are starting points, not limits: any hand-drawn idea works. Paths in this file are relative to this skill's folder.

## 1. Set up (once)
- Node.js 18+ (HyperFrames runs through `npx`).
- Python 3.9+ to start projects (`scripts/new_project.py`).
- Internet the first time: p5.brush is not shipped with the skill. `scripts/brushlib.py` downloads the official build (pinned version, SHA-256 checked) into `kit/.cache/` once, and every project gets a copy.
- The **redraw-video** use case needs more (MediaPipe, ffmpeg): see its `USECASE.md`.
Done when: `npx --yes hyperframes --version` prints a version and `python scripts/brushlib.py` prints `p5.brush ... ok`.

## 2. Pick the use case
| Use case | What it makes | Start with |
|---|---|---|
| `explainer` | A sketchnote that explains steps: pen drawings, arrows, washes, handwritten labels, red-marker payoff | `usecases/explainer/` |
| `story` | A short animated story: a doodle character who acts (squash, anticipation, eyes, brows), a world painted in watercolour | `usecases/story/` |
| `redraw-video` | A real clip of a person redrawn 12 times a second (screen-print or watercolour), with a real-to-drawn wipe | `usecases/redraw-video/` |
| `blank` | Anything else, or a new style: one pen line, one wash, one hatch, handwriting, and the drawing kit | `usecases/blank/` |

Read the chosen `usecases/<name>/USECASE.md` before you write anything. Not in the table: start from `blank` and read `references/p5brush-notes.md`.
Done when: the use case is chosen and the content is agreed (the words, the beats, the length, 9:16 or 16:9).

## 3. Start the project
```
python scripts/new_project.py <use case> <new folder>
```
(`--list` shows the use cases.) `redraw-video` is the exception: it runs its own tool (`USECASE.md`).
Done when: the folder has `index.html`, `assets/vendor/brush.js` (p5.brush, patched for the HyperFrames lint) and `assets/fonts/`.

## 4. Make it yours: rules for good hand-drawn work
These hold for every use case and every new style.
1. **Every frame is a pure function of time.** `renderAt(t)` clears and repaints everything on each `hf-seek`. No `Math.random()`, `Date`, timers or animation frames.
2. **One seed per element** (`sd(id)` before each element). A stroke that is still growing must not change the texture of the strokes after it.
3. **The pen leads, the paint follows.** The outline draws on first; the wash fades in just after; hatching is revealed left to right with `brush.clip`. Paint goes under the lines in paint order.
4. **Draw at hand speed.** A stroke takes 0.2-0.8 s with slow-in and slow-out. Handwriting is about 0.04 s per letter. Nothing appears all at once.
5. **One family of tools per video.** For example pen + watercolour + one red marker. Three or four inks plus the paper colour. Red only on the one thing to look at.
6. **Imperfect, but the same imperfection every frame.** Overshoot corners and wobble lines with fixed sine noise, never new randomness per frame. Exception: a deliberate "boil" (lines shimmer), with a new seed per drawing, held for 2-3 frames (8-12 drawings a second).
7. **Simple shapes read faster than detail.** A character is a circle head, dot eyes and one mouth line; it acts with its body (squash, anticipation, follow-through) and its eyes and brows.
8. **Words are handwritten, short and beside the drawing, never on it.** The kit font is Caveat (Latin). For Arabic, add an OFL Arabic font to `assets/fonts/` and declare it with `@font-face`.
9. **Keep it short and safe.** 5-12 s per clip. On 9:16, keep key drawings and words between about 170 px from the top and 400 px from the bottom (platform buttons and captions).
Done when: the scene says what was agreed and follows the nine rules.

## 5. Check and render
- `npx --yes hyperframes lint`: 0 errors. A "file too large" warning is fine for one-file scenes.
- `npx --yes hyperframes preview` to scrub it, or render and look at frames from the start, middle and end.
- `npx --yes hyperframes render . -o renders/video.mp4`.
- Check the frames against the rules in step 4 and the use case's own checks; fix and render again.
Done when: `renders/video.mp4` exists and its frames pass the checks.

## 6. Add a use case (extend the skill)
Make `usecases/<name>/` with:
- `index.html`: a working HyperFrames composition that loads `assets/vendor/brush.js` and fonts from `assets/fonts/` (copy `blank` to start).
- `USECASE.md`: when to use it, what to change in the template, and its own checks.
`new_project.py` finds it automatically. Add a row to the table in step 2.

## Limits
- p5.brush needs WebGL2: HyperFrames renders in Chrome, which has it.
- Watercolour fills cannot go fully dark (like real watercolour): use a wash for dark areas. More traps in `references/p5brush-notes.md`.
- The redraw use case works best on one person, face front-on or three-quarter.
