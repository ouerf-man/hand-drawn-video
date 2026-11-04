# Install: one prompt

Open the **Code** tab of the Claude desktop app (or Codex), paste the prompt below, and answer its questions. It downloads the skill, checks what your computer needs, and makes a test video. Works on Windows and macOS.

```text
Install the "hand-drawn-video" skill for me, step by step. Ask me before installing any program.

1. Download https://github.com/ouerf-man/hand-drawn-video/archive/refs/heads/main.zip and unzip it into a temporary folder. It holds one folder, "hand-drawn-video-main": that whole folder is the skill.
2. Copy "hand-drawn-video-main" into my skills folder and name it "hand-drawn-video", replacing any older copy:
   - Claude: ~/.claude/skills/hand-drawn-video (Windows: %USERPROFILE%\.claude\skills\hand-drawn-video)
   - Codex: ~/.codex/skills/hand-drawn-video
3. Check Node.js 18 or newer (node --version). If it is missing, install the LTS version from nodejs.org.
4. Find a Python 3.10, 3.11 or 3.12 (the redraw tool needs one of these; newer Pythons are too new for it). On Mac try python3.12, python3.11, python3.10, then python3 (the "python" command usually does not exist on Mac). On Windows try py -3.12, py -3.11, py -3.10, then python. If none is 3.10-3.12, ask me, then install Python 3.12 from python.org.
5. Make a private Python for the skill with that Python, outside the skill folder so updates never delete it: <that python> -m venv ~/.cache/hand-drawn-video/venv (Windows: %USERPROFILE%\.cache\hand-drawn-video\venv). From now on "the skill Python" means ~/.cache/hand-drawn-video/venv/bin/python (Windows: %USERPROFILE%\.cache\hand-drawn-video\venv\Scripts\python.exe). Use it for every python command below, never pip on the system Python.
6. Run the skill Python with <skill folder>/scripts/brushlib.py: it downloads the p5.brush drawing library once (about 110 KB) and checks it.
7. So I can redraw my own videos: run the skill Python with -m pip install -r <skill folder>/requirements.txt, then with <skill folder>/usecases/redraw-video/drawify.py --doctor (it downloads two small face models, about 4 MB). The first run can take a few minutes, and TensorFlow/absl warnings in the output are normal. Check ffmpeg too; if it is missing, tell me it is only needed for the real-to-drawn wipe.
8. Test it: in my Documents folder (on Windows it may be inside OneDrive), run the skill Python with <skill folder>/scripts/new_project.py blank hand-drawn-test (if hand-drawn-test already exists, use hand-drawn-test-2), then inside that folder run npx --yes hyperframes render . -o renders/video.mp4, and show me the video.
9. Tell me in two lines what is installed, and that I can now ask for a hand-drawn explainer, an animated story, or to redraw one of my videos.
```

## By hand
1. Download the zip above, unzip it, and copy the `hand-drawn-video-main` folder into your skills folder as `hand-drawn-video` (`~/.claude/skills/hand-drawn-video`, Windows `%USERPROFILE%\.claude\skills\hand-drawn-video`, or `~/.codex/skills/hand-drawn-video`).
2. Install Node.js 18+ and Python 3.10-3.12.
3. Make the skill Python: `python3.12 -m venv ~/.cache/hand-drawn-video/venv` (Windows: `py -3.12 -m venv %USERPROFILE%\.cache\hand-drawn-video\venv`).
4. Inside the skill folder, with the skill Python (`~/.cache/hand-drawn-video/venv/bin/python`, Windows `...\venv\Scripts\python.exe`): `scripts/brushlib.py` (downloads p5.brush once).
5. Only to redraw videos, with the skill Python: `-m pip install -r requirements.txt`, then `usecases/redraw-video/drawify.py --doctor`.
Or with git: `git clone https://github.com/ouerf-man/hand-drawn-video ~/.claude/skills/hand-drawn-video`.
