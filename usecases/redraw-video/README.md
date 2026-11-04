# Redraw a video (part of the hand-drawn-video skill)

Turn a video of a person into a hand-drawn animation painted with [p5.brush](https://github.com/acamposuribe/p5.brush): redrawn 12 times a second, like real hand-drawn animation, in one of two styles.

| Style | What it looks like |
|---|---|
| `print` (default, recommended) | Screen-print poster: four flat inks (black, maroon, tan, cream). Keeps the person's real light and dark shapes, so it stays recognisable on its own. |
| `watercolour` (softer, experimental) | Paper, watercolour washes, pencil hatching and pen lines, with the face drawn from landmarks. Prettier as a drawing, but less recognisable when seen alone. |

It also makes an optional **wipe** from the real footage into the drawing.

Runs on **Windows and macOS** (Python 3.9-3.12, tested in CI on both). It is one use case of the [hand-drawn-video](../../SKILL.md) Claude skill; the step-by-step is in [`USECASE.md`](USECASE.md).

## Install
```
<skill Python> -m pip install -r requirements.txt
<skill Python> usecases/redraw-video/drawify.py --doctor
```
(Commands run from the skill folder.) `--doctor` downloads p5.brush (if not cached yet) and the two MediaPipe models once (face landmarks ~3.7 MB, person segmenter ~0.25 MB, Apache-2.0, into `~/.cache/drawify`) and checks the setup. Rendering needs **Node.js 18+** (HyperFrames runs through `npx`); the wipe needs **ffmpeg**.

## Use
```
<skill Python> usecases/redraw-video/drawify.py talk.mp4 --start 2 --duration 3 --style print --out my-drawing --render --wipe
```
| Option | Meaning |
|---|---|
| `--start`, `--duration` | Seconds. Short clips (2-5 s) render fast. |
| `--style` | `print` or `watercolour`. |
| `--fps` | Drawings per second (default 12, "on twos"). |
| `--matte` | Optional person matte video (white = person). Without it, MediaPipe finds the person. |
| `--no-face` | Skip face landmarks (non-face subjects). |
| `--render` | Render `renders/drawn-<style>.mp4` with HyperFrames. |
| `--wipe` | Also render `renders/wipe-<style>.mp4` (real → drawn). |

Without `--render` you get a HyperFrames project (`index.html`, `assets/data.js`, `assets/vendor/brush.js`); open it with `npx hyperframes preview` or render it with `npx hyperframes render . -o drawn.mp4`.

## How it works
1. **Drawings.** The clip is sampled 12 times a second. Each drawing is held for 2-3 video frames and gets a new random seed, so lines shimmer slightly between drawings, the classic hand-drawn "boil".
2. **The person.** A matte separates the person from the background. In `watercolour` the background is drawn **once**, so only the person moves; `print` leaves plain paper behind the person.
3. **Face landmarks.** MediaPipe Face Landmarker gives 478 points per drawing: brows, eyelids, irises, nose and lips.
4. **Light.** One-sided light pushes the lit side's brow, beard and nose out of the dark tones. A plane is fitted to the lightness of the skin and its slope is removed, **on skin only**: hair and beard are dark in themselves, not shadowed.
5. **Four tone groups.** Pixels are grouped by lightness *and* colour strength (Lab chroma). Hair and beard are dark and grey; skin in shadow is dark but saturated, so this separates them where brightness alone cannot. The groups and the colours are fixed from the first drawing, so nothing flickers.
6. **Features from landmarks** (watercolour):
   - brows in the person's own shape;
   - the white of the eye, the iris, and a lid band covering the top of the iris (the expression lives here);
   - the nose shadow side, the shadow under the tip, and the nostrils;
   - lips cut out of the beard and painted in their own colour, with a dark interior when the mouth is open;
   - a beard (only when the region is really dark) in its measured colour, with a dark core and a soft edge.
7. **Painting.** p5.brush paints each drawing in [HyperFrames](https://hyperframes.heygen.com): `print` uses flat washes, painted largest shape first so small islands stay on top; `watercolour` uses washes, `fill`, `hatch` and pen strokes. Every frame is a pure function of time, so frames render in any order.

## What we learned building it
It was tuned in seven rounds against an independent reviewer that compared real and drawn frames and scored likeness. The main lessons:
- **People recognise a face by its dark pattern** (hair, beard, brows, irises, nostrils, mouth line), not by its outlines. Edge detection draws every edge the same and changes who the person is.
- **A watercolour fill cannot go dark.** At 230 opacity it reaches mid-grey, like real watercolour. Dark values need a flat wash underneath.
- **Take each feature's darkness from the footage,** not from maximum ink. A beard painted at full black looks pasted on.
- **Cut child features out of parent masses.** Paint the lips after the beard, or the beard swallows them.
- **Stamped generic marks read as clip art or blemishes.** Every feature comes from this person's own landmark shapes.
- **Every fix can undo an earlier win.** Check the whole list every time (see `USECASE.md`, step 4).
- **Judge likeness blind.** The watercolour style passed a side-by-side review at 8/10, but the person himself did not recognise it when watching it alone. A real frame next to the drawing fills in the likeness for the viewer. Test on the drawing alone, ideally with someone who knows the person.

## Notes
- `assets/vendor/brush.js` in a generated project is the official p5.brush build ([MIT](https://github.com/acamposuribe/p5.brush), by Alejandro Campos Uribe), downloaded once and checked by `scripts/brushlib.py`, with two lines neutralised for HyperFrames' determinism lint: the library's random initial seed (`Math.random()`; the drawing re-seeds every frame anyway) and a "you forgot `render()`" warning timer.
- Best on front or three-quarter faces, one person. Hands are drawn as shapes.
- Smoke test (synthetic clip, no models needed): `<skill Python> usecases/redraw-video/tests/smoke_test.py`.
