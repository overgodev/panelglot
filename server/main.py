import base64
import io
import os
import secrets
import shutil
import signal
import subprocess
import sys
from argparse import Namespace
import asyncio
from typing import Optional

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


from fastapi import FastAPI, Request, HTTPException, Header, UploadFile, File, Form, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from manga_translator import Config
from manga_translator.mode.response import TranslationResponse
from server.core.instance import ExecutorInstance, executor_instances
from server.core.myqueue import task_queue
from server.api.request_extraction import get_ctx, while_streaming, TranslateRequest, BatchTranslateRequest, get_batch_ctx
from server.api.llm_probe import router as llm_probe_router

app = FastAPI()
app.include_router(llm_probe_router)
nonce = None

BASE_DIR = Path(__file__).resolve().parent
RESULT_ROOT = (BASE_DIR.parent / "result").resolve()
RESULT_ROOT.mkdir(parents=True, exist_ok=True)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 添加result文件夹静态文件服务
if RESULT_ROOT.exists():
    app.mount("/result", StaticFiles(directory=str(RESULT_ROOT)), name="result")

@app.post("/register", response_description="no response", tags=["internal-api"])
async def register_instance(instance: ExecutorInstance, req: Request, req_nonce: str = Header(alias="X-Nonce")):
    if req_nonce != nonce:
        raise HTTPException(401, detail="Invalid nonce")
    instance.ip = req.client.host
    executor_instances.register(instance)

@app.post("/translate/json", response_model=TranslationResponse, tags=["api", "json"],response_description="json strucure inspired by the ichigo translator extension")
async def json(req: Request, data: TranslateRequest):
    result_bytes = await get_ctx(req, data.config, data.image, output_format="json")
    return Response(content=result_bytes, media_type="application/json")

@app.post("/translate/bytes", response_class=StreamingResponse, tags=["api", "json"],response_description="custom byte structure for decoding look at examples in 'examples/response.*'")
async def bytes(req: Request, data: TranslateRequest):
    result_bytes = await get_ctx(req, data.config, data.image, output_format="bytes")
    return Response(content=result_bytes, media_type="application/octet-stream")

@app.post("/translate/image", response_description="the result image", tags=["api", "json"],response_class=StreamingResponse)
async def image(req: Request, data: TranslateRequest) -> Response:
    result_bytes = await get_ctx(req, data.config, data.image, output_format="image")
    return Response(content=result_bytes, media_type="image/png")

@app.post("/translate/json/stream", response_class=StreamingResponse,tags=["api", "json"], response_description="A stream over elements with strucure(1byte status, 4 byte size, n byte data) status code are 0,1,2,3,4 0 is result data, 1 is progress report, 2 is error, 3 is waiting queue position, 4 is waiting for translator instance")
async def stream_json(req: Request, data: TranslateRequest) -> StreamingResponse:
    return await while_streaming(req, data.config, data.image, output_format="json")

@app.post("/translate/bytes/stream", response_class=StreamingResponse, tags=["api", "json"],response_description="A stream over elements with strucure(1byte status, 4 byte size, n byte data) status code are 0,1,2,3,4 0 is result data, 1 is progress report, 2 is error, 3 is waiting queue position, 4 is waiting for translator instance")
async def stream_bytes(req: Request, data: TranslateRequest)-> StreamingResponse:
    return await while_streaming(req, data.config, data.image, output_format="bytes")

@app.post("/translate/image/stream", response_class=StreamingResponse, tags=["api", "json"], response_description="A stream over elements with strucure(1byte status, 4 byte size, n byte data) status code are 0,1,2,3,4 0 is result data, 1 is progress report, 2 is error, 3 is waiting queue position, 4 is waiting for translator instance")
async def stream_image(req: Request, data: TranslateRequest) -> StreamingResponse:
    return await while_streaming(req, data.config, data.image, output_format="image")

@app.post("/translate/with-form/json", response_model=TranslationResponse, tags=["api", "form"],response_description="json strucure inspired by the ichigo translator extension")
async def json_form(req: Request, image: UploadFile = File(...), config: str = Form("{}")):
    img = await image.read()
    conf = Config.parse_raw(config)
    conf._original_filename = image.filename
    result_bytes = await get_ctx(req, conf, img, output_format="json")
    return Response(content=result_bytes, media_type="application/json")

@app.post("/translate/with-form/ocr-preview", tags=["api", "form"], response_description="Recognized text regions (bbox + raw OCR text, no translation/inpainting/rendering) for the web UI's Preview OCR button. Forces config.ocr_preview_only=true regardless of what the client sent.")
async def ocr_preview_form(req: Request, image: UploadFile = File(...), config: str = Form("{}")):
    img = await image.read()
    conf = Config.parse_raw(config)
    conf._original_filename = image.filename
    conf.ocr_preview_only = True
    result_bytes = await get_ctx(req, conf, img, output_format="ocr_preview")
    return Response(content=result_bytes, media_type="application/json")

@app.post("/translate/with-form/bytes", response_class=StreamingResponse, tags=["api", "form"],response_description="custom byte structure for decoding look at examples in 'examples/response.*'")
async def bytes_form(req: Request, image: UploadFile = File(...), config: str = Form("{}")):
    img = await image.read()
    conf = Config.parse_raw(config)
    conf._original_filename = image.filename
    result_bytes = await get_ctx(req, conf, img, output_format="bytes")
    return Response(content=result_bytes, media_type="application/octet-stream")

@app.post("/translate/with-form/image", response_description="the result image", tags=["api", "form"],response_class=StreamingResponse)
async def image_form(req: Request, image: UploadFile = File(...), config: str = Form("{}")) -> Response:
    img = await image.read()
    conf = Config.parse_raw(config)
    conf._original_filename = image.filename
    result_bytes = await get_ctx(req, conf, img, output_format="image")
    return Response(content=result_bytes, media_type="image/png")

@app.post("/translate/with-form/json/stream", response_class=StreamingResponse, tags=["api", "form"],response_description="A stream over elements with strucure(1byte status, 4 byte size, n byte data) status code are 0,1,2,3,4 0 is result data, 1 is progress report, 2 is error, 3 is waiting queue position, 4 is waiting for translator instance")
async def stream_json_form(req: Request, image: UploadFile = File(...), config: str = Form("{}")) -> StreamingResponse:
    img = await image.read()
    conf = Config.parse_raw(config)
    # 标记这是Web前端调用，用于占位符优化
    conf._is_web_frontend = True
    conf._original_filename = image.filename
    return await while_streaming(req, conf, img, output_format="json")



@app.post("/translate/with-form/bytes/stream", response_class=StreamingResponse,tags=["api", "form"], response_description="A stream over elements with strucure(1byte status, 4 byte size, n byte data) status code are 0,1,2,3,4 0 is result data, 1 is progress report, 2 is error, 3 is waiting queue position, 4 is waiting for translator instance")
async def stream_bytes_form(req: Request, image: UploadFile = File(...), config: str = Form("{}"))-> StreamingResponse:
    img = await image.read()
    conf = Config.parse_raw(config)
    conf._original_filename = image.filename
    return await while_streaming(req, conf, img, output_format="bytes")

@app.post("/translate/with-form/image/stream", response_class=StreamingResponse, tags=["api", "form"], response_description="Standard streaming endpoint - returns complete image data. Suitable for API calls and scripts.")
async def stream_image_form(req: Request, image: UploadFile = File(...), config: str = Form("{}")) -> StreamingResponse:
    """通用流式端点：返回完整图片数据，适用于API调用和comicread脚本"""
    img = await image.read()
    conf = Config.parse_raw(config)
    # 标记为通用模式，不使用占位符优化
    conf._web_frontend_optimized = False
    conf._original_filename = image.filename
    return await while_streaming(req, conf, img, output_format="image")

@app.post("/translate/with-form/image/stream/web", response_class=StreamingResponse, tags=["api", "form"], response_description="Web frontend optimized streaming endpoint - uses placeholder optimization for faster response.")
async def stream_image_form_web(req: Request, image: UploadFile = File(...), config: str = Form("{}")) -> StreamingResponse:
    """Web前端专用端点：使用占位符优化，提供极速体验"""
    img = await image.read()
    conf = Config.parse_raw(config)
    # 标记为Web前端优化模式，使用占位符优化
    conf._web_frontend_optimized = True
    conf._original_filename = image.filename
    return await while_streaming(req, conf, img, output_format="image")

@app.post("/queue-size", response_model=int, tags=["api", "json"])
async def queue_size() -> int:
    return len(task_queue.queue)


@app.api_route("/result/{folder_name}/final.png", methods=["GET", "HEAD"], tags=["api", "file"])
async def get_result_by_folder(folder_name: str):
    """根据文件夹名称获取翻译结果图片"""
    result_dir = RESULT_ROOT
    if not result_dir.exists():
        raise HTTPException(404, detail="Result directory not found")

    folder_path = result_dir / folder_name
    if not folder_path.exists() or not folder_path.is_dir():
        raise HTTPException(404, detail=f"Folder {folder_name} not found")

    final_png_path = folder_path / "final.png"
    if not final_png_path.exists():
        raise HTTPException(404, detail="final.png not found in folder")

    async def file_iterator():
        with open(final_png_path, "rb") as f:
            yield f.read()

    return StreamingResponse(
        file_iterator(),
        media_type="image/png",
        headers={"Content-Disposition": f"inline; filename=final.png"}
    )

@app.post("/translate/batch/json", response_model=list[TranslationResponse], tags=["api", "json", "batch"])
async def batch_json(req: Request, data: BatchTranslateRequest):
    """Batch translate images and return JSON format results"""
    results = await get_batch_ctx(req, data.resolved_configs(), data.images, data.batch_size, output_format="json")
    return [TranslationResponse.model_validate_json(r) for r in results]

@app.post("/translate/batch/images", response_description="Zip file containing translated images", tags=["api", "batch"])
async def batch_images(req: Request, data: BatchTranslateRequest):
    """Batch translate images and return zip archive containing translated images"""
    import zipfile
    import tempfile

    results = await get_batch_ctx(req, data.resolved_configs(), data.images, data.batch_size, output_format="image")

    # Create temporary ZIP file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as tmp_file:
        with zipfile.ZipFile(tmp_file, 'w') as zip_file:
            for i, png_bytes in enumerate(results):
                if png_bytes is not None:
                    zip_file.writestr(f"translated_{i+1}.png", png_bytes)

        # Return ZIP file
        with open(tmp_file.name, 'rb') as f:
            zip_data = f.read()

        # Clean up temporary file
        os.unlink(tmp_file.name)

        return StreamingResponse(
            io.BytesIO(zip_data),
            media_type="application/zip",
            headers={"Content-Disposition": "attachment; filename=translated_images.zip"}
        )

@app.post("/translate/batch/json-images", response_model=list[Optional[str]], tags=["api", "json", "batch"])
async def batch_json_images(req: Request, data: BatchTranslateRequest):
    """Batch-translate all given images together (OCR'd up front, then translated as a single
    combined pass so the translator sees the whole story's text at once for better cross-page
    context) and return the final rendered pages as base64 PNG data URLs, in input order."""
    results = await get_batch_ctx(req, data.resolved_configs(), data.images, data.batch_size, output_format="image")
    encoded: list[Optional[str]] = []
    for png_bytes in results:
        if png_bytes is not None:
            encoded.append("data:image/png;base64," + base64.b64encode(png_bytes).decode("utf-8"))
        else:
            encoded.append(None)
    return encoded

@app.get("/", response_class=HTMLResponse,tags=["ui"])
async def index() -> HTMLResponse:
    script_directory = Path(__file__).parent
    html_file = script_directory / "web" / "index.html"
    html_content = html_file.read_text(encoding="utf-8")
    return HTMLResponse(content=html_content)

@app.get("/manual", response_class=HTMLResponse, tags=["ui"])
async def manual():
    script_directory = Path(__file__).parent
    html_file = script_directory / "web" / "manual.html"
    html_content = html_file.read_text(encoding="utf-8")
    return HTMLResponse(content=html_content)

def generate_nonce():
    return secrets.token_hex(16)

def _worker_cmd(host: str, port: int, nonce: str, params: Namespace):
    cmds = [
        sys.executable,
        '-m', 'manga_translator',
        'shared',
        '--host', host,
        '--port', str(port),
        '--nonce', nonce,
    ]
    if params.use_gpu:
        cmds.append('--use-gpu')
    if params.use_gpu_limited:
        cmds.append('--use-gpu-limited')
    if params.ignore_errors:
        cmds.append('--ignore-errors')
    if params.verbose:
        cmds.append('--verbose')
    if params.models_ttl:
        cmds.append('--models-ttl=%s' % params.models_ttl)
    if getattr(params, 'context_size', 0):
        cmds.extend(['--context-size', str(params.context_size)])
    if getattr(params, 'pre_dict', None):
        cmds.extend(['--pre-dict', params.pre_dict])
    if getattr(params, 'post_dict', None):
        cmds.extend(['--post-dict', params.post_dict])
    return cmds

# Worker crash-restart bookkeeping (single embedded worker started via --start-instance).
_worker_proc: Optional[subprocess.Popen] = None
_worker_spec: Optional[dict] = None  # host/port/nonce/params/cwd for respawning
_worker_restart_count = 0
_WORKER_MAX_RESTARTS = 5

def start_translator_client_proc(host: str, port: int, nonce: str, params: Namespace):
    global _worker_proc, _worker_spec
    base_path = os.path.dirname(os.path.abspath(__file__))
    parent = os.path.dirname(base_path)
    cmds = _worker_cmd(host, port, nonce, params)
    proc = subprocess.Popen(cmds, cwd=parent)
    connect_ip = '127.0.0.1' if host == '0.0.0.0' else host
    executor_instances.register(ExecutorInstance(ip=connect_ip, port=port, nonce=nonce))

    _worker_proc = proc
    _worker_spec = {'host': host, 'port': port, 'nonce': nonce, 'params': params, 'cwd': parent}

    def handle_exit_signals(signal, frame):
        proc.terminate()
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_exit_signals)
    signal.signal(signal.SIGTERM, handle_exit_signals)

    return proc

async def watch_worker():
    """Respawn the embedded translator worker if it crashes, instead of leaving requests hanging forever."""
    global _worker_proc, _worker_restart_count
    while True:
        await asyncio.sleep(3)
        if _worker_proc is None or _worker_spec is None:
            continue
        if _worker_proc.poll() is None:
            continue  # still alive

        if _worker_restart_count >= _WORKER_MAX_RESTARTS:
            print(f"Worker crashed (exit code {_worker_proc.returncode}) and hit the restart limit "
                  f"({_WORKER_MAX_RESTARTS}); giving up on auto-restart.")
            continue

        _worker_restart_count += 1
        spec = _worker_spec
        print(f"Worker crashed (exit code {_worker_proc.returncode}); restarting "
              f"(attempt {_worker_restart_count}/{_WORKER_MAX_RESTARTS})...")
        cmds = _worker_cmd(spec['host'], spec['port'], spec['nonce'], spec['params'])
        new_proc = subprocess.Popen(cmds, cwd=spec['cwd'])
        _worker_proc = new_proc
        for instance in executor_instances.list:
            if instance.port == spec['port']:
                instance.busy = False

@app.on_event("startup")
async def _start_worker_watchdog():
    asyncio.create_task(watch_worker())

def prepare(args):
    global nonce
    if args.nonce is None:
        nonce = os.getenv('MT_WEB_NONCE', generate_nonce())
    else:
        nonce = args.nonce
    if args.start_instance:
        return start_translator_client_proc(args.host, args.port + 1, nonce, args)
    folder_name= "upload-cache"
    if os.path.exists(folder_name):
        shutil.rmtree(folder_name)
    os.makedirs(folder_name)

@app.get("/results/list", tags=["api"])
async def list_results():
    """List all result directories"""
    result_dir = RESULT_ROOT
    if not result_dir.exists():
        return {"directories": []}
    
    try:
        directories = []
        for item_path in result_dir.iterdir():
            if item_path.is_dir():
                # Check if final.png exists in this directory
                final_png_path = item_path / "final.png"
                if final_png_path.exists():
                    directories.append(item_path.name)
        return {"directories": directories}
    except Exception as e:
        raise HTTPException(500, detail=f"Error listing results: {str(e)}")

@app.get("/results/download-all", tags=["api"])
async def download_all_results():
    """Zip up every finished result (final.png) and return it as one archive"""
    import zipfile

    result_dir = RESULT_ROOT
    if not result_dir.exists():
        raise HTTPException(404, detail="No results directory found")

    zip_buffer = io.BytesIO()
    count = 0
    used_names = set()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for item_path in sorted(result_dir.iterdir()):
            if item_path.is_dir():
                final_png_path = item_path / "final.png"
                if final_png_path.exists():
                    name_path = item_path / "original_name.txt"
                    if name_path.exists():
                        stem = Path(name_path.read_text(encoding="utf-8").strip()).stem or item_path.name
                    else:
                        stem = item_path.name
                    arcname = f"{stem}.png"
                    suffix = 2
                    while arcname in used_names:
                        arcname = f"{stem} ({suffix}).png"
                        suffix += 1
                    used_names.add(arcname)
                    zip_file.write(final_png_path, arcname=arcname)
                    count += 1

    if count == 0:
        raise HTTPException(404, detail="No finished results to download")

    zip_buffer.seek(0)
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=translated_results.zip"}
    )

@app.delete("/results/clear", tags=["api"])
async def clear_results():
    """Delete all result directories"""
    result_dir = RESULT_ROOT
    if not result_dir.exists():
        return {"message": "No results directory found"}
    
    try:
        deleted_count = 0
        for item_path in result_dir.iterdir():
            if item_path.is_dir():
                # Check if final.png exists in this directory
                final_png_path = item_path / "final.png"
                if final_png_path.exists():
                    shutil.rmtree(item_path)
                    deleted_count += 1
        
        return {"message": f"Deleted {deleted_count} result directories"}
    except Exception as e:
        raise HTTPException(500, detail=f"Error clearing results: {str(e)}")

@app.delete("/results/{folder_name}", tags=["api"])
async def delete_result(folder_name: str):
    """Delete a specific result directory"""
    result_dir = RESULT_ROOT
    folder_path = result_dir / folder_name
    
    if not folder_path.exists():
        raise HTTPException(404, detail="Result directory not found")
    
    try:
        # Check if final.png exists in this directory
        final_png_path = folder_path / "final.png"
        if not final_png_path.exists():
            raise HTTPException(404, detail="Result file not found")
        
        shutil.rmtree(folder_path)
        return {"message": f"Deleted result directory: {folder_name}"}
    except Exception as e:
        raise HTTPException(500, detail=f"Error deleting result: {str(e)}")

#todo: cache results
#todo: cleanup cache

if __name__ == '__main__':
    import uvicorn
    from args import parse_arguments

    args = parse_arguments()
    args.start_instance = True
    proc = prepare(args)
    print("Nonce: "+nonce)
    try:
        uvicorn.run(app, host=args.host, port=args.port)
    except Exception:
        if proc:
            proc.terminate()
