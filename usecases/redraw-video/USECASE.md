# Use case: redraw a video (rotoscope)

Turn a real clip of a person into a hand-drawn animation, redrawn 12 times a second, in a screen-print style (`print`, default) or watercolour + ink (`watercolour`), plus an optional wipe from the real footage into the drawing. Use when someone says "draw my video", "turn me into a drawing / cartoon", "rotoscope this".

`drawify.py` (next to this file) does the whole job; commands below run from the skill folder. You run it, look at the frames, and adjust.

## 1. Set up (once)
- Python 3.9-3.12: `python -m pip install -r requirements.txt` (skill folder; MediaPipe brings OpenCV and NumPy).
- Node.js 18+ for rendering (HyperFrames runs through `npx`). ffmpeg only for the optional wipe.
- `python usecases/redraw-video/drawify.py --doctor`: downloads p5.brush (if not cached yet) and the two MediaPipe models once (face landmarks ~3.7 MB, person segmenter ~0.25 MB, to `~/.cache/drawify`) and checks everything.
Done when: the doctor prints `models load: ok` and finds `npx`.

## 2. Pick the moment and the style
- Ask for the clip and which seconds (short is best: 2-5 s).
- **Default to `print`.** It only needs the four tone groups, so it gives the same quality on any person and any light. `watercolour` adds face-specific painting tuned on one face: prettier as a drawing, but less recognisable seen alone and less predictable on new faces. Offer it as a variation, not the default.
- If a person matte already exists (white = person), pass it with `--matte`; it is more exact than the automatic one.
Done when: you have the video path, start, duration and style.

### Rules for good results (check the footage before running)
Good input matters more than settings. Tell the person what to change when a rule fails.
1. **One person, face front-on or three-quarter,** taking at least a quarter of the frame height. Profiles and tiny faces lose the features.
2. **Soft, even light on the face.** Strong light from one side is corrected, but darkness still decides the shapes. No backlight, no very dark rooms.
3. **Sharp, not blurry.** Fast head or hand moves turn into blobs; pick a calmer moment.
4. **Nothing over the face:** no hand in front of the mouth, no sunglasses, no microphone across the lips.
5. **A plain, calm background** gives clean shapes behind the person (it is drawn once).
6. **Pick an expressive moment:** speaking, a small head move, eyes to camera. A still face looks like a photo filter.
7. **Keep `--fps 12`** (the hand-drawn feel). 8 is more hand-made and jumpier; 24 is smooth but loses the drawn feel.
8. **2-5 seconds per clip.** Longer works but renders slower; cut it into a few moments instead.

## 3. Run
```
python usecases/redraw-video/drawify.py VIDEO --start S --duration D --style print --out OUT_FOLDER --render --wipe
```
Without `--render` it only writes the HyperFrames project; render later with `npx hyperframes render . -o drawn.mp4` inside it.
Done when: `OUT_FOLDER/renders/drawn-<style>.mp4` exists (and `wipe-<style>.mp4` with `--wipe`).

## 4. Check it like a portrait artist
Extract 3 frames of the result next to the same moments of the source and look at them side by side, face close-up included. Go down this list; each item must pass:
1. Dark masses (hair, beard, brows) are dark and continuous, not grey or patchy.
2. Brows have the person's own shape and angle.
3. The upper lid covers the top of the iris (no round, staring eyes).
4. The nose has a shadow side; nostrils are where they are on the face.
5. The mouth is a line, not a blob; a dark interior when it is open.
6. No marks that read as blemishes or bruises; no white paper gaps between hair and skin.
7. Colours do not jump between drawings (play it once).
Then judge likeness **blind**: look at the drawing alone, playing, without the source next to it (side by side, the real frame fills in the likeness and hides problems). Best: ask the person, or someone who knows them.
If something fails, change the matching part of `drawify.py` or the template (see this folder's README, "How it works") and run again. One change per run, and re-check the whole list each time: a fix can undo an earlier win.

## 5. Deliver
Send the drawn clip and the wipe, say which style and seconds, and what is still weak (for example hands, profile views).

## Limits
- Front or three-quarter faces work best; profiles lose the features.
- Hands are drawn as shapes, not as detailed fingers.
- One person at a time.
- Strong one-sided light is corrected on the skin; very dark footage still loses detail.
