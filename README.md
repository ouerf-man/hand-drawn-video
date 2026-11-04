# hand-drawn-video

A Claude skill (also works in Codex) that makes videos that look drawn by hand: pen, pencil, charcoal, marker, crayon and watercolour, painted by [p5.brush](https://github.com/acamposuribe/p5.brush) inside [HyperFrames](https://hyperframes.heygen.com). Ask for an idea in plain words; Claude starts from the closest use case and draws it.

**Install:** paste the prompt in [`INSTALL.md`](INSTALL.md) into the Claude desktop app (Code tab) or Codex. Windows and macOS. This whole folder is the skill.

## Use cases
| Use case | What you get | Ask for example |
|---|---|---|
| [`explainer`](usecases/explainer/USECASE.md) | A sketchnote drawn step by step: pen drawings, arrows, watercolour, handwritten labels | "a hand-drawn explainer of how my app works in 4 steps" |
| [`story`](usecases/story/USECASE.md) | A doodle character acting a short story in a watercolour world | "an animated drawn story about someone who keeps trying" |
| [`redraw-video`](usecases/redraw-video/USECASE.md) | A real clip of a person redrawn as a hand-drawn animation, plus a real-to-drawn wipe | "redraw seconds 3 to 6 of this video as a drawing" |
| [`blank`](usecases/blank/USECASE.md) | Any other idea, or a new style of your own | "a hand-drawn map", "a chalkboard style title" |

## How it works
- Every frame is a pure function of time: HyperFrames asks for time `t`, the page repaints the whole drawing for `t` with p5.brush, and the frame is captured. Renders are exact and repeatable.
- Strokes grow along their path at hand speed; washes fade in after the pen; hatching is revealed left to right.
- Each element has its own random seed, so textures never flicker.
- Handwriting is HTML text (Caveat font) revealed with a moving mask.
- p5.brush is not copied into this repo. The first project you start downloads the official build of a pinned version (npm, SHA-256 checked) into `kit/.cache/`, patches two lines for the HyperFrames lint (its random first seed and a "forgot `render()`" warning timer; nothing changes on screen), and copies it into each project with its licence.
- `redraw-video` adds computer vision (MediaPipe person matte and face landmarks, four tone groups) before the painting: see its [README](usecases/redraw-video/README.md).

## Folder
```
SKILL.md                 the steps and the rules Claude follows
INSTALL.md               the one-prompt install
usecases/<name>/         index.html (a working template) + USECASE.md (what to change, checks)
kit/                     Caveat font, HyperFrames project files, p5.brush licence (the library downloads to kit/.cache/)
scripts/new_project.py   start a project from a use case
scripts/brushlib.py      download, check and patch p5.brush (pinned version)
references/              p5.brush cheat sheet and traps
tests/                   quick checks run in CI on Windows and macOS
```

## Add your own use case
Make `usecases/<name>/` with a working `index.html` (copy `blank`) and a `USECASE.md`, and add a row to the table in `SKILL.md`. `scripts/new_project.py` picks it up by itself.

## Credits and licences
- This skill: MIT (`LICENSE`), Raed Ouerfelli.
- The drawing is done by [p5.brush](https://github.com/acamposuribe/p5.brush) by Alejandro Campos Uribe, MIT (`kit/LICENSE-p5.brush.md`, copied into every project). Thank you, Alejandro.
- Rendering: [HyperFrames](https://hyperframes.heygen.com). Caveat font: SIL OFL 1.1 (`kit/fonts/OFL-Caveat.txt`). MediaPipe models (downloaded by `redraw-video`): Apache-2.0.
