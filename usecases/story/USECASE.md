# Use case: animated hand-drawn story

A doodle character acts out a tiny story on the page: it picks up a pencil, tries, fails (the drawing is crossed out, crumpled and rolls away), tries again, and the world it draws fills with watercolour and spills out of the frame. One short handwritten line per beat. 9.4 s, 1080x1920.

Use for: a story hook, a mascot moment, a "before / after", a feeling (stuck, trying, winning), a short fable for a reel.

## How the template is built
- **`rig(t)`**: every part of the character is a keyed curve over time, `kf(t, [[time, value, ease], ...])`: position `x`, squash/stretch `sq`, where it looks (`lookX`, `lookY`), `blink`, `mood` (-1 frown to 1 smile), `brow` (-1 worried to 1 determined), `wow`, `eyeScale`, `happyEyes`.
- **`PEN`**: the strokes the character draws, each with its start and end time; the pencil tip rides the head of the active stroke, and `pencilAt(t)` moves it between strokes.
- **`drawPerson(t)`**: draws the character from the rig. The head trails the shoulders and the hair trails the head (follow-through).
- **`drawWorld(t)`**: the watercolour world, revealed by `clip` and fading fills.
- **Text**: one `.line` div per beat, written on with a clip reveal.

## What to change
1. Write the story as 3-4 beats of about 2 s each, one line of text per beat (2-4 words).
2. For each beat, set the rig keys: anticipation before an action (squash down, then stretch), overshoot after, eyes look at what matters, brows and mouth show the feeling.
3. Change what gets drawn (`PEN`, `drawWorld`) and the beat text and times (`.line` divs and `lineIn` / `lineOut`).
4. Change `data-duration` on `#root` and the paper clip if the length changes.

## Its own checks
- Each beat reads in silence: you can tell what the character feels from its body and eyes alone.
- Every action has anticipation before it and settles after it; nothing starts or stops dead.
- Only one thing moves at a time where the eye should be.
- The text never covers the character or what it is drawing.
