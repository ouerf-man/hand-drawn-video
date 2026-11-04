# Use case: hand-drawn explainer (sketchnote)

A page that explains something step by step while it is being drawn: each step is a small pen drawing with a watercolour wash, linked by charcoal arrows, with a handwritten label beside it. A red marker circles the payoff at the end. 9.3 s, 1080x1920.

Use for: how something works, a process, a before/after, a list of tips, "3 steps to ...".

## What to change in `index.html`
1. **The words** are HTML: the title (`#titleKick`, `#titleBig`), one label block per step (`#lab1` ... `#lab4`, a title and a sub-line), and the closing line (`#ctaKick`, `#ctaBig`). Keep each label to 2-4 words; the sub-line to about 4 words.
2. **The drawings** are in `renderAt(t)`, one block per step (`STEP 1` ... `STEP 4`), placed at `XL`/`XR` and `ROW[i]`. Replace each with a simple picture of that step: a few lines, one wash, at most one hatch or crayon mass. Reuse the helpers: `drawOn`, `wash`, `hatchReveal`, `massReveal`, `arrow`, `headAndShoulders`, `rectPts`, `roundRectPts`, `blobPts`, `wobbleLine`.
3. **The timing**: each step owns about 1.5 s. Its outline starts, the wash follows 0.2 s later, the label is written while it draws, then the arrow to the next step. Move the `seg(t, a, b)` times and the `write(...)` times together.
4. **More or fewer steps**: add or remove a row in `ROW`, a block in `renderAt`, a label div and its `write` calls, and change `data-duration` on `#root` and its clips.

## Its own checks
- Labels sit beside drawings, never on them; nothing touches the edges.
- The eye can follow one path: step 1, arrow, step 2 ...
- The payoff (red marker) is the only red mass on the page at the end.
- Each step can be read in a still frame at the end.
