# Session Handoff — panelglot local deployment

Status as of 2026-08-16. `panelglot` (`overgodev/panelglot`) is the renamed
continuation of the `overgodev/manga-image-translator` fork of
`zyddnys/manga-image-translator` — this is now the repo to work in. Set up as
a local web translator backed by LM Studio running on the machine's RTX 3060
(12GB VRAM) / 32GB RAM (VM, RAM can be increased if needed).

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

## Batch/whole-story translation (already in panelglot's initial commit)

Uploading more than one file now routes through a new whole-story batch mode
instead of translating pages one at a time:

- Front end (`front/app/App.tsx`): `processTranslation()` now checks
  `files.length > 1` and calls `processBatchTranslation()`, which OCRs every
  queued page up front, sends them all to `/api/translate/batch/json-images`
  in one request, and renders results back per-page. Files are tracked by a
  generated `id` (`types.ts` `UploadedFile`) instead of filename, so same-name
  uploads no longer collide.
- Backend: new `/translate/batch/json-images` endpoint (`server/main.py`)
  returns base64 PNG data URLs in input order via `get_batch_ctx`
  (`server/request_extraction.py` → `BatchQueueElement`). The old
  `/simple_execute/translate_batch` and `/execute/translate_batch` internal
  stub endpoints (dead code, always returned empty results) were removed;
  `server/instance.py` / `server/sent_data_internal.py` gained
  `fetch_data_raw` / `fetch_data_stream_raw` for the worker RPC shape this
  needs (arbitrary kwargs dict, not the fixed single-image `{image, config}`
  shape `fetch_data` assumes).
- **Not yet tested end-to-end** — this was in-progress work when it got
  committed into panelglot's initial snapshot. Verify batch mode actually
  works (multi-file upload → correct per-page results, correct target
  language, no id/filename mismatches) before relying on it.

## Fixed: batch translation "forgetting" everything past ~3 pages

Reported symptom (after the batch feature above): translating a multi-page
story still only carried context from roughly the last 3 pages, defeating
the point of batching everything together.

Root cause wasn't `--context-size 3` (that setting only matters between
separate `translate()` calls, e.g. per-page mode) — in batch mode all pages'
OCR'd text really does get combined into one `_translate()` call. The actual
bug was inside `CustomOpenAiTranslator._translate()`
(`manga_translator/translators/custom_openai.py`): when the combined text is
too long for one prompt, `_assemble_prompts()` silently splits it into
several sequential LLM requests (chunked by `_MAX_TOKENS`, a small
~4096-character budget). Each request after the first started with **zero**
memory of the previous one — so once a story's dialogue passed roughly 3
pages' worth of text, translation continuity reset to blank at every chunk
boundary. That's what looked like a hardcoded 3-page limit.

Fix: `_translate()` now carries the immediately-preceding chunk's
query→translation pairs forward as reference context for the next chunk,
chained on top of whatever cross-page context (`context_size`) was already
set, via a temporary override of `self.prev_context` restored in a
`try`/`finally` once the whole call finishes (so it can't leak into
unrelated calls).

**Caveat**: only the *immediately preceding* chunk is carried forward
(bounded on purpose, to avoid runaway prompt growth against a local LLM's
limited context window) — not the full story's history. Consistency should
no longer reset every ~3 pages, but very long-range callbacks (a name
introduced in chunk 1, referenced again in chunk 10) still won't be
perfectly preserved. **Not yet empirically verified** — needs a real
multi-page batch run against LM Studio to confirm terminology actually stays
consistent past the old 3-page boundary.

## What's been fixed this session (2026-08-16): Thai target language

Reported symptom: selecting Thai (`THA`) as target language with the
`custom_openai` (LM Studio) translator produced English output with a layout
that "didn't make sense." Three separate bugs, found by reading the actual
`result/log_*.txt` output rather than guessing:

- **No few-shot example for Thai**
  (`manga_translator/translators/config_gpt.py`) — `_CHAT_SAMPLE` /
  `_JSON_SAMPLE` only had entries for Chinese (Simplified), English, and
  Korean. `_closest_sample_match()` uses `langcodes.closest_supported_match`
  with `max_distance=5` to fuzzy-match `to_lang` against those keys; verified
  directly that Thai's distance to all three exceeds that cutoff, so it
  matched **nothing** — the LLM got zero example of correctly-formatted Thai
  output. Added a Thai entry to both sample dicts.
- **Root cause of the English fallback**
  (`manga_translator/manga_translator.py`, `_dispatch_with_context`) — the
  cross-page-context path (see `custom_openai` context wiring below) calls
  `translator._translate(ctx.from_lang, config.translator.target_lang, texts)`
  **directly**, bypassing `CommonTranslator.translate()` which normally
  resolves the raw config code (`"THA"`) to the human-readable name
  (`"Thai"`) via `parse_language_codes()`. The log showed the system prompt
  literally saying *"Translate the following text into **THA**"* — the LLM
  doesn't recognize the raw code and silently defaults to English. Fixed by
  resolving `config.translator.target_lang` through `VALID_LANGUAGES` before
  calling `_translate()`, matching what the normal path already does.
- **Layout/orientation bug** (`manga_translator/utils/textblock.py`,
  `LANGUAGE_ORIENTATION_PRESETS`) — Thai (`'THA'`) was missing from this
  dict entirely. Every other alphabetic language (English, French, etc.) is
  forced to horizontal (`'h'`); without an entry, `TextBlock.direction`
  fell through to aspect-ratio auto-detection, which picks vertical layout
  for tall/narrow bubbles (tuned for CJK). Thai script doesn't work stacked
  vertically — that was the "layout doesn't make sense" complaint. Added
  `'THA': 'h'`.

**Not yet fixed, same class of bug**: `IND`, `SRP`, `CNR`, `HRV` are also
missing from `LANGUAGE_ORIENTATION_PRESETS` and would hit the same
vertical-layout issue if selected as target language. Flagged, not fixed —
only Thai was reported/tested.

All three fixes require a server restart to take effect (see "Lesson
learned" below for how to do that safely) — not yet re-verified against a
live translation after restart as of this writing.

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

## Repo reorg + translator backend cleanup (2026-08-29)

**Folder reorganization** — the repo root, `server/`, and the
`manga_translator/` package were tidied. Full rationale/verification is in
the session's plan; summary of what moved:

- Root docs → `docs/` (`CHANGELOG*.md`, `HANDOFF.md` — this file,
  `UPSTREAM_README*.md`, `system-overview.html`). `README.md` stays at
  root (GitHub convention; `devscripts/make_readme.py` writes to it by
  relative path).
- Root launcher scripts → `scripts/` (`run.bat`, `run.sh`,
  `run_as_colab.ipynb`, `run-as-kaggle.ipynb`, `start-web-server.bat`,
  `docker_prepare.py`). **`start-web-server.bat` now lives at
  `scripts/start-web-server.bat`** — update any shortcuts/muscle memory.
- `requirements-dev.txt` / `-rocm.txt` / `-xpu.txt` → `requirements/`.
  `requirements.txt` stays at root (Dockerfile/CI expect it there).
- `server/` split from a flat file list into `server/core/` (queue,
  executor registry, streaming protocol, internal RPC wire format),
  `server/api/` (request→context→response translation layer), and
  `server/web/` (`index.html`, `manual.html`). `server/main.py` and
  `server/args.py` stay at `server/` root.
- `manga_translator/manga_translator.py` (the orchestrator) renamed to
  `manga_translator/pipeline.py` — it shared its name with the package
  itself, which was confusing. `manga_translator/utils/generic2.py`
  renamed to `manga_translator/utils/text_utils.py` for the same reason.
- **Deliberately left alone**: `manga_translator/`'s domain subpackages
  (detection/, ocr/, inpainting/, translators/, rendering/, etc.) were
  already sensibly organized — restructuring them further would touch
  dozens of relative-import sites for no real benefit. `config.py` /
  `args.py` / `save.py` stay at the package root for the same reason.
  `dict/`, `fonts/`, `examples/`, `server/` (as a top-level dir) all stay
  at repo root — Docker, the Makefile's dev bind-mounts, and
  `BASE_PATH = dirname(dirname(__file__))` in
  `manga_translator/utils/generic.py` all assume that layout.
- Every moved file's call sites were updated (imports, Dockerfile,
  Makefile mount paths, CI `paths:` triggers, doc links) and verified via
  a static AST-based import audit across the whole repo (no venv was
  available in the sandbox this was done in, so `pytest`/`python -c
  "import manga_translator"` could not be run live — do that as a
  first check next session).

**Translator backend cleanup** — panelglot is LM Studio-only now (see
"LLM setup" above), so all translator backends except `custom_openai` were
deleted from `manga_translator/translators/`: `baidu`, `caiyun`, `chatgpt`
(+`chatgpt_2stage`), `common_gpt` (only used by the two deleted GPT
backends), `deepl`, `deepseek`, `gemini` (+`gemini_2stage`), `google`
(+`google_gtoken`), `groq`, `m2m100` (+`m2m100_hf`), `mbart50`, `nllb`,
`papago`, `qwen2`, `sakura`, `selective` (the "auto-pick best offline
translator" wrapper — meaningless once every offline backend it wrapped
was removed), `sugoi` (the old dedicated NMT model wrapper — **not** the
same thing as "Sugoi" the LLM model name loaded via LM Studio and selected
through `customOpenaiModel` in the web UI, which is untouched), `youdao`,
and the now-orphaned `tokenizers/` folder. Kept: `custom_openai.py`,
`none.py`, `original.py` (no-op utility translators the pipeline needs
regardless of backend), plus their shared infra (`common.py`,
`config_gpt.py`, `keys.py` — trimmed to only the `CUSTOM_OPENAI_*` env
vars `custom_openai.py` actually uses).

Follow-on edits this required: `manga_translator/config.py`'s `Translator`
enum trimmed to `none`/`original`/`custom_openai`, its default changed
from `Translator.sugoi` → `Translator.custom_openai`, and the `'gpt'*'`/`'openai'`
alias in `_missing_` now resolves to `custom_openai` instead of the
deleted `chatgpt`. `manga_translator/pipeline.py`'s two translation-dispatch
functions had their `chatgpt`/`chatgpt_2stage`-specific branches removed,
keeping only the `custom_openai` context-injection path (streaming/
per-page mode) and the generic `dispatch_translation` fallback (batch
mode — still not `custom_openai`-context-aware in batch, per the existing
note above; unchanged by this cleanup). `server/web/index.html`'s
`validTranslators` list trimmed to match. `test/test_translation.py`
rewritten around the surviving three translators. `examples/Example.env`,
`examples/translator_chain_example.json`, `examples/gpt_config-example.yaml`
updated to stop referencing deleted backends.

**Not done / explicitly out of scope this session**: rewriting the API
server (`server/`) from Python to TypeScript — mentioned as a future
direction, not started. Trimming OCR backends (`manga_translator/ocr/`) —
no evidence yet of which ones "work" vs. don't; needs empirical testing
before cutting anything there.

**`demo/` removed** — the `demo/doc/` Docker Compose variants
(local-dev/web-cpu/web-gpu) were deleted per user request. The
`Makefile`'s `run-web-server` target used a `/demo/doc/../../...` path
trick to bind-mount `result/`, `server/main.py`, and
`server/core/instance.py` — rewritten to plain relative paths
(`./result`, `./server/main.py`, `./server/core/instance.py`) now that
the `demo/doc` anchor is gone. `docs/UPSTREAM_README*.md` still reference
`demo/doc/*.yml` — left as-is since those files are preserved,
unmodified copies of the *upstream* project's own docs (per the note at
the top of `README.md`), not this fork's active documentation.

## Plan: rewrite `server/` (API orchestration layer) from Python to TypeScript

Not started — this is the plan for a future session, written 2026-08-29.
Scope note first: **only `server/` moves.** The `manga_translator/`
package (detection/OCR/inpainting/translation/rendering, all torch/cv2/
numpy-backed) stays Python — there is no realistic TS port of that, and
no reason to attempt one. `server/` itself is comparatively thin: HTTP
API surface, a request queue, an executor registry that proxies requests
to one or more worker processes, and static file serving of `result/`.
That's a good fit for Node — the question is entirely about the wire
protocol between orchestrator and worker, which is the one piece that
doesn't translate directly.

### Why this isn't a drop-in rewrite: the pickle boundary

Today's flow is `front → server/main.py (FastAPI) → queue/instance
registry → worker (manga_translator/mode/share.py, a separate `python -m
manga_translator shared` process)`. The server↔worker leg
(`server/core/sent_data_internal.py` + `manga_translator/mode/share.py`)
is **not** a translation-specific API — it's a generic reflective RPC
bridge: the server pickles `{**kwargs}` (a PIL `Image`, a pydantic
`Config`), POSTs it to `/execute/{method_name}` or
`/simple_execute/{method_name}`, and the worker does
`getattr(self.manga, method_name)(**attr)` and pickles back whatever
Python object that method returns — for `translate`, a full `Context`
with numpy arrays, PIL images, and `TextBlock` objects. `server/main.py`
then calls `transform_to_image`/`to_json`/`to_bytes`
(`server/api/to_json.py`) **on that raw `Context`** to produce the
client-facing response. A Node process cannot unpickle any of this —
there is no equivalent of Python's object graph pickling available, and
reimplementing enough of `numpy`'s pickle format plus `TextBlock`'s
class shape in TS is not worth attempting.

So the wire protocol has to change first, independent of language:

1. **Move response serialization into the worker.** `to_json.py`'s
   `to_translation()` / `Translation.to_bytes()` and the
   `ctx.result.save(..., format="PNG")` PNG-encode step currently run in
   `server/main.py` after unpickling. They need to move into
   `manga_translator/mode/share.py` (or a new sibling module) so the
   worker itself produces the *final* wire payload — PNG bytes, the
   existing custom binary `Translation`/`TranslationResponse` format
   (already just base64/struct-packed primitives, nothing Python-specific), or a plain JSON body — and
   the orchestrator never needs to touch a `Context`, numpy array, or PIL
   image again. This means the worker's `/execute/{method_name}` /
   `/simple_execute/{method_name}` endpoints stop being fully generic;
   they need to know which output shape the caller wants (an
   `output_format` field in the request, e.g. `image|json|bytes`) and
   apply the corresponding transform before responding.
2. **Replace pickle with JSON (+ base64 for binary blobs) on the
   remaining orchestrator↔worker traffic**: the request side (image
   bytes + `Config`) and the streaming progress-report envelope
   (`server/core/streaming.py` / `sent_data_internal.py`'s 1-byte
   status + 4-byte length framing can stay as-is — that framing is
   already language-agnostic; only the payload inside status `0`
   changes from a pickled `Context` to the pre-serialized bytes from
   step 1). `Config` is already a pydantic model — it round-trips
   through `.model_dump_json()`/`.parse_raw()` today for the multipart
   form endpoints, so JSON is not a new capability, just making it the
   only capability.
3. **Register/nonce handshake** (`/register`, `X-Nonce` header) is
   already plain HTTP + JSON — no change needed there.

This is worth doing as its own preliminary change, landed and verified
against the *existing* Python `server/`, before writing a single line of
TS — it's the part with the most room for silent bugs (e.g. re-deriving
`text_region.translation` vs. the `ctx.translations` dict correctly, per
the desync bug fixed earlier this session) and is much easier to debug
Python-to-Python than across a language boundary.

### TS server scope (once the wire protocol is JSON-clean)

Port these modules 1:1, matching the existing module boundaries:

- `server/core/myqueue.py` → an in-memory queue (array + event emitter
  in place of `asyncio.Event`) — `QueueElement`/`BatchQueueElement`,
  `wait_in_queue`. Client-disconnect detection needs Node's request
  `close`/`aborted` event in place of `req.is_disconnected()`.
- `server/core/instance.py` → `ExecutorInstance`/`Executors`, using
  `fetch`/`undici` instead of `aiohttp` for the worker calls.
- `server/core/sent_data_internal.py` → simplifies a lot post-pickle:
  just JSON POST + the existing binary stream framing (a small
  `Buffer`-based reader replacing `handle_buffer`/`extract_header`).
- `server/api/request_extraction.py` → `to_pil_image` has no TS
  equivalent need (no local image decoding required — the worker still
  does OCR/decoding in Python) but the *shape* (accept multipart, raw
  bytes, base64 data URL, or a remote URL fetch) has to be preserved for
  the front end's existing requests; forward the bytes through
  untouched rather than decoding them.
- `server/main.py` → route definitions (Express or Fastify; pick
  Fastify — it has first-class TS support and schema validation, which
  maps naturally onto porting the pydantic `Config`/`TranslateRequest`/
  `BatchTranslateRequest` models to `zod` schemas generated once from
  `manga_translator/config.py` and kept in sync manually, same as the
  front end likely already duplicates some of this shape in
  `front/app/types.ts` — check for reuse there first). Worker process
  spawn/watchdog (`start_translator_client_proc`, `watch_worker`) ports
  directly to Node's `child_process.spawn` + a `setInterval` poll.
  Static `result/` serving and the zip endpoints
  (`/results/download-all`, `/translate/batch/images`) need a zip
  library (`archiver` or `jszip`) in place of Python's `zipfile`.

### Suggested sequencing

1. Land the pickle-removal change (Python-only, see above) and re-verify
   all existing endpoints still work against the current Python
   `server/` — this de-risks the rewrite by removing the one piece that
   isn't a mechanical port.
2. Stand up the new TS server as `server-ts/` (or similar) alongside the
   existing Python one, targeting the *same* worker process and the
   *same* routes/response shapes, so the front end (`front/`) needs zero
   changes to switch between them — this makes A/B testing and rollback
   trivial.
3. Port route-by-route, cross-checking each against the Python
   version's behavior for the same request (there's no test suite for
   `server/` today — `test/test_translation.py` covers `manga_translator/`
   internals, not the HTTP layer — so this has to be manual/curl-based
   verification per endpoint, including the streaming and batch ones,
   which are the most likely to have subtle framing bugs).
4. Once parity is confirmed, flip `scripts/start-web-server.bat` (and
   the manual-start instructions above) over to the TS server, then
   delete the Python `server/` tree.

### Open questions to resolve before starting

- Whether to keep the worker on FastAPI/uvicorn (Python) indefinitely,
  or eventually also move `manga_translator/mode/share.py`'s *HTTP
  layer* (not the ML pipeline) to a thin TS shim that shells out to a
  Python subprocess per-call instead of long-running HTTP — deferred;
  not needed for this rewrite and adds risk for no clear benefit given
  the worker already works reliably as a long-lived process (see
  "Lesson learned" above on why long-lived out-of-session processes
  matter here).
- Whether `front/`'s dev server should reverse-proxy to the TS server
  directly (same-origin, avoiding the current CORS-wildcard
  `allow_origins=["*"]` on the Python server) now that both sides are
  Node-ecosystem — worth reconsidering `CORSMiddleware`'s wildcard as
  part of this rewrite rather than porting it as-is.
