# Setup Guide

How to get panelglot running locally from a clean machine. This covers only
what's specific to this fork (LM Studio-backed local translation, the two
frontends). For anything not covered here — Docker, CLI flags, the full
language/model support matrix — see `docs/UPSTREAM_README.md`.

## 1. Requirements

- **Python 3.10–3.12** (3.12 confirmed working; avoid the very latest Python
  release, PyTorch support usually lags behind it).
- **Git**.
- **A CUDA-capable Nvidia GPU** (recommended). CPU-only works but is
  significantly slower for detection/OCR/inpainting. Tested on an RTX 3060
  12GB.
- **Microsoft C++ Build Tools** (Windows only) — some pip dependencies
  compile native extensions. [Download](https://visualstudio.microsoft.com/vs/),
  select "Desktop development with C++".
- **LM Studio** — <https://lmstudio.ai/> — runs the local LLM that does the
  actual translation. (Ollama also works as an OpenAI-compatible alternative,
  but LM Studio is what this fork is set up/tested against.)
- **Bun** — <https://bun.sh/> — only needed if you want the new `front/`
  (Nuxt 3) UI. Not required to run the server or the legacy web UI.

## 2. Recommended LLM models (LM Studio)

Translation quality/speed depends entirely on the model you load in LM
Studio — the pipeline (detection/OCR/inpainting) is fixed, only the
translation step goes through the LLM.

| Model | Size (Q4_K_M) | Notes |
|---|---|---|
| **sugoi-14b-ultra** | ~9 GB | Fast, fits fully in 12GB VRAM. Good default — use this unless you have a specific reason not to. |
| **sugoitoolkit/sugoi-32b-ultra** | ~20 GB | More accurate, but won't fully fit in 12GB VRAM — partially offloads to system RAM, noticeably slower. Use when quality matters more than speed and you can tolerate the wait. |

Both are fine-tuned specifically for Japanese manga/light-novel-style
translation, which is why they're preferred over generic instruction models.
If you don't have either downloaded yet, search for them by name in LM
Studio's model browser.

General-purpose alternatives (untuned for manga, but usable in a pinch if
you don't want to download a Sugoi model): `Qwen2.5-14B-Instruct` or
`Qwen2.5-32B-Instruct` — decent multilingual output, but expect less
consistent tone/register than Sugoi.

Model VRAM budget is roughly: model size (from the table/quant) + ~1–2GB
overhead for context + whatever the translation pipeline itself needs
resident at the same time (detection/OCR/inpainting models, a few hundred
MB–1GB). If you're tight on VRAM, prefer the 14B model.

## 3. Backend setup

```powershell
# Clone
git clone <your-fork-url> panelglot
cd panelglot

# Create and activate a venv
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# GPU: install a CUDA-matched PyTorch build (skip if CPU-only)
# Check your CUDA version, then follow https://pytorch.org/get-started/locally/
# e.g. for CUDA 12.1:
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121 --upgrade --force-reinstall
```

Models for detection/OCR/inpainting/rendering download automatically to
`./models` on first run — no manual step needed for those.

### Configure the LLM endpoint

Copy `examples/Example.env` to `.env` in the repo root and adjust if needed:

```powershell
copy examples\Example.env .env
```

Defaults already point at LM Studio's default address
(`http://localhost:1234/v1`). If you're using Ollama instead, change
`CUSTOM_OPENAI_API_BASE` to `http://localhost:11434/v1`. Set
`CUSTOM_OPENAI_MODEL` to the exact model name as LM Studio reports it (or
leave blank and pick it per-request from the web UI dropdown instead).

### Start LM Studio

Open LM Studio → **Server** tab → load a Sugoi model (see table above) →
start the server. It also auto-loads the model on first translation request
if you forget this step, but that adds a delay to your first request.

### Start the backend server

Double-click `scripts/start-web-server.bat`. This starts the server on
`0.0.0.0:8000` (LAN-accessible) with GPU enabled.

Manual equivalent (useful if you need to redirect output to a file):

```powershell
cd server
..\venv\Scripts\python.exe main.py --start-instance --host 0.0.0.0 --use-gpu
```

Drop `--use-gpu` if you don't have a CUDA GPU.

**Don't run this as a background task inside an AI assistant session** — it
gets killed when the session's task-tracking reaps old processes. Always
launch it as its own OS process (the `.bat` file, or `Start-Process` in
PowerShell).

The legacy web UI is now available at `http://localhost:8000/`.

## 4. Frontend setup (optional — new Nuxt 3 UI)

With the backend already running:

```powershell
cd front
bun install
bun run dev
```

Opens at `http://localhost:3000`. Its dev server proxies `/api/**` requests
to the backend on `:8000` (see `front/nuxt.config.ts`) — you still need the
backend running for this to do anything.

## 5. Verify it works

1. LM Studio's Server tab shows "Server running" with a model loaded (or set
   to auto-load).
2. Open `http://localhost:8000/` (legacy UI) or `http://localhost:3000/`
   (new UI, if set up).
3. Upload a manga/comic page, pick a target language, translate.
4. First request after starting LM Studio's server will be slow (model
   load); subsequent ones should be much faster.

## Troubleshooting

- **pip install fails compiling a package (Windows)** — install the C++
  Build Tools (step 1) and retry.
- **GPU not being used** — confirm `torch.cuda.is_available()` returns
  `True` in a Python shell inside the venv; if not, your PyTorch build
  doesn't match your CUDA version (see the GPU install step above).
- **Translation returns English / wrong language, or garbled output** —
  usually means LM Studio doesn't have the right model loaded, or the
  server needs a restart after a `.env`/config change.
- **Server unreachable from another machine on your LAN** — make sure you
  started it with `--host 0.0.0.0` (the `.bat` file already does this) and
  that your firewall allows inbound connections on port 8000.
