# Install: one prompt

Open the **Code** tab of the Claude desktop app (or Codex), paste the prompt below, and answer its questions. It downloads the skill, checks what your computer needs, and makes a test video. Works on Windows and macOS.

```text
Install the "hand-drawn-video" skill for me, step by step. Ask me before installing any program.

1. Download https://github.com/ouerf-man/hand-drawn-video/archive/refs/heads/main.zip and unzip it into a temporary folder. It holds one folder, "hand-drawn-video-main": that whole folder is the skill.
2. Copy "hand-drawn-video-main" into my skills folder and name it "hand-drawn-video", replacing any older copy:
   - Claude: ~/.claude/skills/hand-drawn-video (Windows: %USERPROFILE%\.claude\skills\hand-drawn-video)
   - Codex: ~/.codex/skills/hand-drawn-video
3. Check Node.js 18 or newer (node --version). If it is missing, install the LTS version from nodejs.org.
4. Check Python 3.9 to 3.12 (python --version, or python3 --version on Mac). If it is missing, install Python 3.12 from python.org.
5. Run python <skill folder>/scripts/brushlib.py: it downloads the p5.brush drawing library once (about 110 KB) and checks it.
6. So I can redraw my own videos: run python -m pip install -r <skill folder>/requirements.txt, then python <skill folder>/usecases/redraw-video/drawify.py --doctor (it downloads two small face models, about 4 MB). Check ffmpeg too; if it is missing, tell me it is only needed for the real-to-drawn wipe.
7. Test it: run python <skill folder>/scripts/new_project.py blank hand-drawn-test in my Documents folder, then inside hand-drawn-test run npx --yes hyperframes render . -o renders/video.mp4, and show me the video.
8. Tell me in two lines what is installed, and that I can now ask for a hand-drawn explainer, an animated story, or to redraw one of my videos.
```

## By hand
1. Download the zip above, unzip it, and copy the `hand-drawn-video-main` folder into your skills folder as `hand-drawn-video` (`~/.claude/skills/hand-drawn-video`, Windows `%USERPROFILE%\.claude\skills\hand-drawn-video`, or `~/.codex/skills/hand-drawn-video`).
2. Install Node.js 18+ and Python 3.9-3.12.
3. Inside the skill folder: `python scripts/brushlib.py` (downloads p5.brush once; needs internet the first time).
4. Only to redraw videos, inside the skill folder: `python -m pip install -r requirements.txt` and `python usecases/redraw-video/drawify.py --doctor`.
Or with git: `git clone https://github.com/ouerf-man/hand-drawn-video ~/.claude/skills/hand-drawn-video`.
