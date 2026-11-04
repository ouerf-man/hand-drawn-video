# Use case: blank (any other idea, or a new style)

The smallest working hand-drawn scene: a pen loop that draws on, a watercolour wash that follows, pencil hatching on the shadow side, a red marker underline and a handwritten title. 4 s, 1080x1920. It carries the drawing kit (`seg`, eases, `sd`, `dense`, `drawOn`, `wash`, `blob`) and the frame structure, so you start from something that renders.

Use for: anything the other use cases do not cover (a hand-drawn chart, a map, a title card, a product sketch, a logo drawn on), and for inventing a new style.

## Inventing a new style
Answer these before you draw:
1. **Tools**: which drawing tools does it imitate? (felt-tip and highlighter, charcoal and chalk, ink and wash, crayon ...) Pick brushes from `references/p5brush-notes.md` or make your own with `brush.add`.
2. **Paper and inks**: the paper colour and 3-4 inks. One accent colour for the one thing to look at.
3. **Line**: clean or wobbly, how thick, do corners overshoot?
4. **Fill**: none, flat wash, watercolour bleed, hatching, crayon mass?
5. **Motion**: does it draw on (stroke by stroke), boil (redrawn 8-12 times a second), or both?
Write the answers as constants and helpers at the top of `index.html`, then build the scene with them. Use the same tools everywhere in the video.

## Its own checks
- A still frame looks like a real drawing on paper, not a vector graphic.
- The style is the same in every part of the frame (no clean vector shape next to a watercolour one).
- Lint passes (`npx --yes hyperframes lint`).
