# Session Handoff — manga-image-translator local deployment

Status as of 2026-08-15. This is a fork (`overgodev/manga-image-translator`) of
`zyddnys/manga-image-translator`, set up as a local web translator backed by
LM Studio running on the machine's RTX 3060 (12GB VRAM) / 32GB RAM (VM, RAM can
be increased if needed).

## How to run it

Double-click **`start-web-server.bat`** in the repo root. It starts the web
server bound to `0.0.0.0:8000` (LAN-accessible) with GPU enabled, and prints
the LAN URL. Closing the console window stops the server.

Before translating, make sure **LM Studio's server is running** (Server tab)
with at least one Sugoi model loaded — it auto-loads on first request if not,
but that adds a delay.

Manual start (equivalent to the .bat, useful if you need output redirected to
a file instead of a console window):
```powershell
cd server
..\venv\Scripts\python.exe main.py --start-instance --host 0.0.0.0 --use-gpu
```
Run it as a `Start-Process` (not a background task in an assistant session) —
see "Lesson learned" below for why.

## LLM setup (LM Studio)

Two Sugoi models are downloaded and available, selectable per-request via the
web UI's "LLM Model" dropdown (only shown when Translator = custom_openai):

- **`sugoi-14b-ultra`** (Q4_K_M, ~9GB) — fast, fully GPU-resident.
- **`sugoitoolkit/sugoi-32b-ultra`** (Q4_K_M, ~20GB) — more accurate, doesn't
  fit fully in 12GB VRAM so it partially offloads to system RAM (slower).

LM Studio auto-loads whichever isn't already resident when requested by name
(no restart needed), but the first request after switching pays a load delay.
Both can be loaded simultaneously if VRAM/RAM allows, but that causes
contention — expect degraded speed on whichever handles a request.

`.env` in the repo root points the `custom_openai` translator at LM Studio's
OpenAI-compatible endpoint (`http://localhost:1234/v1`).

## What's been fixed / added this session (see git log for full details)

Commits `a1d60bf` → `7c73f1f` on `main`. Highlights:

- **Windows/LAN server bugs**: worker registered at unreachable `0.0.0.0`
  instead of `127.0.0.1`; nonce auth header never sent to the worker;
  worker's pickled response parsed as JSON. All fixed in `server/*.py`.
- **Detection accuracy tuning**: default detector switched from `ctd` to
  `default` (DBNet) — `ctd` silently ignores `detection_size`/`box_threshold`
  entirely (hardcoded to a fixed 1024px model input + `box_thresh=0.6`); fixed
  the `box_threshold` part but **do not** try to make `ctd` respect
  `detection_size` — confirmed empirically that pushing it past its trained
  1024px resolution measurably degrades OCR quality (tested 1024/1536/2560).
  `ctd` is now used only as an automatic fallback when the primary detector
  finds zero regions on a page.
- **`no_text_lang_skip: true`** default — short exclamations (`哈？`, `啊!`)
  were getting misclassified by `langid` as "already target language" and
  silently dropped before translation.
- **`renderer: manga2eng`** default — old default renderer fit text to the
  source textline bbox instead of the actual bubble, causing English
  (usually more verbose than CJK) to overflow bubble outlines.
- **Cross-page translation context**: `--context-size 3` (server/args.py,
  default on) feeds the last 3 pages' translated lines back to the LLM as
  reference for consistency. This mechanism already existed in the codebase
  but was CLI-only and only wired to the `chatgpt`/`chatgpt_2stage`
  translators — added `custom_openai` support
  (`manga_translator/translators/custom_openai.py`).
- **Translation response desync bug** (`server/to_json.py`) — found *twice*:
  the JSON response built each region's translated text from a separately
  tracked `ctx.translations[lang][i]` list that can be empty or desynced from
  `text_regions` depending on which code path translated it (e.g. the
  context-injection path bypasses it entirely). Fixed by always trusting
  `text_region.translation` (set unconditionally by every path) instead.
- **PP-OCRv6 OCR mode** (`manga_translator/ocr/model_ppocr.py`) — a second,
  generally stronger OCR option (multi-script, single model for EN/CN/JP/KR)
  via the `rapidocr` package, selectable as "Multi-script (PP-OCRv6)" under
  Source Language. Uses the recognizer directly, not rapidocr's own detection
  step (which performs poorly on already-cropped single-line images).
- **Web UI**: dark mode, "Download All" (zips results under their original
  uploaded filenames), Source Language presets (auto-picks OCR
  model/rotation), "Enhance small text" (opt-in per-page `upscale_ratio: 2`
  — genuinely catches small/stylized text a normal pass misses, but roughly
  doubles detection+inpainting time), LLM Model selector, settings schema
  bumped a few times so old saved browser settings don't silently override
  new defaults.

## Known limitations (accepted, not actively being chased)

- A single very short exclamation bubble (`啊!`) on one specific busy panel
  was never caught by any detector/threshold/upscale combination tried —
  likely a genuine detector ceiling for text overlapping complex line art,
  not a config problem.
- `ctd` cannot be pushed past its native 1024px training resolution — see
  above. Don't re-attempt this; it was tested at 1024/1536/2560 with clear
  before/after evidence of degradation.

## Lesson learned: how to run the server reliably

Earlier in this session the server was run as a background Bash task inside
the assistant's own tool session. After many restarts across a long
conversation, the session's background-task management reaped an older
instance and took the live server down — Windows crash logs / GPU driver
logs showed nothing, and the task status literally read "killed". Since
then, the server has been run via `Start-Process` (PowerShell) or the new
`.bat` file — a genuine standalone OS process, not tied to any assistant
session. Keep doing that; don't go back to launching it as a tracked
background task for anything long-lived.
