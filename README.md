# panelglot

A local, LM Studio-backed manga/webtoon translator: web UI + FastAPI server +
translation pipeline (detection, OCR, inpainting, rendering).

This started as a fork of [zyddnys/manga-image-translator](https://github.com/zyddnys/manga-image-translator)
but has been reworked enough — server bugfixes, detector/renderer default
changes, a second OCR backend, cross-page LLM context, a reworked web UI,
crash-resilient worker process, dead-code removal — that it's tracked here as
its own project rather than a PR-sized fork. All credit for the original
pipeline, model training, and architecture goes to the upstream project and
its contributors; see `UPSTREAM_README.md` for the original project's full
documentation (installation matrix, Docker, CLI flags, supported languages,
API reference, etc. — most of that still applies here unchanged).

## What's different from upstream

See `HANDOFF.md` for the detailed log. Highlights:

- Local setup driven by **LM Studio** (OpenAI-compatible endpoint) instead of
  a hosted translation API — see `.env` and the `custom_openai` translator.
- Windows/LAN server fixes (worker registration, nonce auth, response
  parsing) in `server/*.py`.
- Detector/renderer defaults tuned from empirical testing (see `HANDOFF.md`
  for what was tried and why).
- Cross-page translation context wired into `custom_openai`.
- A second OCR backend (PP-OCRv6 / `rapidocr`) for multi-script pages.
- Reworked web UI: dark mode, batch download, source-language presets,
  per-page upscaling.
- The embedded translator worker process now auto-restarts if it crashes
  instead of leaving requests hanging (`server/main.py`).

## Running it

Double-click **`start-web-server.bat`**. It starts the web server on
`0.0.0.0:8000` with GPU enabled. Make sure LM Studio's server is running with
a Sugoi model loaded first.

Manual equivalent:
```powershell
cd server
..\venv\Scripts\python.exe main.py --start-instance --host 0.0.0.0 --use-gpu
```

For dependency installation, Docker, CLI usage, and everything else not
specific to this fork's local setup, see `UPSTREAM_README.md`.

## License

Same as upstream — see `LICENSE`.
