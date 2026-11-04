# p5.brush in HyperFrames: what you need and the traps

A project's `assets/vendor/brush.js` is the official p5.brush 3 standalone build (no p5.js needed), downloaded and checked by `scripts/brushlib.py`, with two lines neutralised for HyperFrames' determinism lint: the library's random first seed (`Math.random()`) and a "you forgot `render()`" warning timer. Every frame re-seeds, so nothing changes.

## Set up (once per page)
```js
brush.createCanvas(540, 960, { parent: document.getElementById("paper"), pixelDensity: 2 }); // 1080x1920 px
brush.scaleBrushes(2.6);          // brush sizes made for a 540-unit canvas
brush.angleMode(brush.RADIANS);
```
The canvas origin is the centre: `brush.push(); brush.translate(-W / 2, -H / 2);` puts (0, 0) top-left.

## The frame
```js
function renderAt(t) {
  brush.seed(SEED); brush.noiseSeed(SEED);
  brush.clear(PAPER);
  brush.push(); brush.translate(-W / 2, -H / 2);
  try { /* draw everything for time t */ } finally { brush.pop(); }
  brush.render();                 // mandatory: nothing shows without it
}
window.addEventListener("hf-seek", (e) => renderAt(e.detail.time));
renderAt(0);
```
Also register a paused GSAP timeline as `window.__timelines["main"]` (it can be empty or drive the HTML text).

## The tools
| Want | Call |
|---|---|
| A line with a brush | `brush.set(name, color, weight)` then `brush.line`, `brush.spline(points, curvature)`, `brush.arc`, `brush.rect`, `brush.circle` |
| Built-in brushes | `pen`, `rotring`, `2B`, `HB`, `2H`, `cpencil`, `charcoal`, `marker`, `marker2`, `spray` |
| Your own brush | `brush.add(name, { type: "marker" or "custom", weight, scatter, opacity, spacing, pressure, ... })`, added after `scaleBrushes` so its size is in canvas units |
| Watercolour | `brush.fill(color, alpha)`, `brush.fillBleed(0.1-0.3)`, `brush.fillTexture(texture, border)`, then a shape |
| Flat solid colour | `brush.wash(color, alpha)` then a shape, `brush.noWash()` |
| Pencil hatching | `brush.hatchStyle(name, color, weight)`, `brush.hatch(distance, angle, { rand, continuous })`, then a shape, `brush.noHatch()` |
| Crayon / pastel mass | `brush.mass(name, color, { strength, precision })`, then a shape, `brush.noMass()` |
| Free shape | `brush.beginShape(curvature)`, `brush.vertex(x, y)`, `brush.endShape(true)` |
| Reveal part | `brush.clip([x1, y1, x2, y2])` ... `brush.noClip()` (lines and hatches only) |

Colours mix like real pigment (Kubelka-Munk): blue over yellow gives green, not grey.

## Traps (each one cost a render)
- **Forgot `brush.render()`**: blank frame.
- **An error between `push` and `pop`** stacks the transform on every later frame: wrap the drawing in `try { } finally { brush.pop(); }`.
- **One seed per frame is not enough.** A growing stroke consumes random numbers and changes every later stroke's texture: call `sd(id)` (own seed) before each element.
- **`brush.arc` with a full 2π sweep draws nothing.** Stop at about 1.96π.
- **`fill`, `wash`, `mass` ignore `brush.clip`.** Reveal them with alpha or by growing the shape, or clip a hatch instead.
- **`noHatch()` forgets `hatchStyle`.** Set the style again before the next hatch.
- **The first hatch on a page can throw "No brush or color set".** Draw one throwaway frame first (`renderAt(0)` at load does this).
- **A watercolour fill at alpha 230 only reaches mid-grey.** For dark areas use `wash` (255 gives near black).
- **Very short strokes throw "Brush pressure must be finite".** Skip strokes under two points (`drawOn` does).
- **Math.random / requestAnimationFrame anywhere in a script fail the lint.** Use the patched `assets/vendor/brush.js` that `new_project.py` copies in, and seeded maths only.
