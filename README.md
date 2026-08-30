# panelglot

A local, LM Studio-backed manga/webtoon translator: web UI + FastAPI server +
translation pipeline (detection, OCR, inpainting, rendering).

This started as a fork of [zyddnys/manga-image-translator](https://github.com/zyddnys/manga-image-translator)
but has been reworked enough — server bugfixes, detector/renderer default
changes, a second OCR backend, cross-page LLM context, a reworked web UI,
crash-resilient worker process, dead-code removal — that it's tracked here as
its own project rather than a PR-sized fork. All credit for the original
pipeline, model training, and architecture goes to the upstream project and
its contributors; see `docs/UPSTREAM_README.md` for the original project's full
documentation (installation matrix, Docker, CLI flags, supported languages,
API reference, etc. — most of that still applies here unchanged).

## What's different from upstream

See `docs/HANDOFF.md` for the detailed log. Highlights:

- Local setup driven by **LM Studio** (OpenAI-compatible endpoint) instead of
  a hosted translation API — see `.env` and the `custom_openai` translator.
- Windows/LAN server fixes (worker registration, nonce auth, response
  parsing) in `server/*.py`.
- Detector/renderer defaults tuned from empirical testing (see `docs/HANDOFF.md`
  for what was tried and why).
- Cross-page translation context wired into `custom_openai`.
- Text detector and OCR model pickers exposed in the web UI (previously only
  configurable via the CLI/API), with per-option language guidance — e.g. the
  OCR dropdown says which model to reach for on Chinese vs. Japanese text.
- A second OCR backend (PP-OCRv6 / `rapidocr`) for multi-script (EN/Chinese/
  Japanese/Korean) pages.
- The `manga_translator/`↔`server/` wire protocol no longer uses pickle
  (JSON + base64 instead) — a preliminary step toward eventually porting
  `server/`'s orchestration layer to TypeScript; see `docs/HANDOFF.md`.
- The embedded translator worker process now auto-restarts if it crashes
  instead of leaving requests hanging (`server/main.py`).
- The original vanilla web UI (`server/web/index.html`, served at
  `:8000/`) picked up dark mode, batch download, source-language presets,
  and per-page upscaling — but is now legacy; see the next section.

### New frontend: `front/` (Nuxt 3)

The web UI was rebuilt from scratch in `front/` as a dark, tool-dense,
Clip Studio Paint-style app (top bar, left tool rail, canvas viewport, right
dock, page filmstrip) instead of the old single-column form. It talks to the
same `server/` backend via a dev-server proxy. New capabilities that only
exist here (not in the legacy `server/web/index.html`):

- **Saved custom-endpoint picker** for the `custom_openai` translator: test a
  base URL, pick a model from what the server actually reports, save it for
  reuse, and switch between saved LM Studio/**headless Ollama** endpoints
  with a load/unload lifecycle (unloads the previous model, warms up the new
  one) instead of hand-editing `.env`.
- **Stories**: save the current set of pages + results + settings as a named
  project (`Save as Story`), browse saved ones on a separate `/stories` page,
  and reopen one to keep working — all stored in the browser, no server-side
  persistence added.
- Zoom/pan on the canvas, including a double-click-to-type-a-percentage zoom
  field.
- A "Story Context" panel (project name, character/glossary notes) — saved
  locally today; not yet sent to the translator (flagged honestly in the UI,
  tracked in `docs/HANDOFF.md`).

## Running it

**Backend** — double-click **`scripts/start-web-server.bat`**. It starts the
web server on `0.0.0.0:8000` with GPU enabled. Make sure LM Studio's server
is running with a Sugoi model loaded first.

Manual equivalent:
```powershell
cd server
..\venv\Scripts\python.exe main.py --start-instance --host 0.0.0.0 --use-gpu
```

**Frontend** (the new `front/` UI) — with the backend already running:
```powershell
cd front
bun install
bun run dev
```
Opens at `http://localhost:3000`; its dev server proxies `/api/**` to the
backend on `:8000` (see `front/nuxt.config.ts`). The legacy vanilla UI is
still reachable directly at `http://localhost:8000/` if needed.

For dependency installation, Docker, CLI usage, and everything else not
specific to this fork's local setup, see `docs/UPSTREAM_README.md`.

## Acknowledgments

- [zyddnys/manga-image-translator](https://github.com/zyddnys/manga-image-translator) —
  the upstream project this fork started from; see above.
- [dmMaze/comic-text-detector](https://github.com/dmMaze/comic-text-detector) — the `ctd`
  text detector option is this model, vendored inference-only (no training/dataset code)
  at `manga_translator/detection/ctd.py` and `manga_translator/detection/ctd_utils/`.

## License

Same as upstream — see `LICENSE`.
