import asyncio
import base64
import io
import json
import secrets
from threading import Lock
from typing import List, Optional

import uvicorn
from fastapi import FastAPI, HTTPException, Path, Request, Response
from PIL import Image

from starlette.responses import StreamingResponse

from manga_translator import Config, Context, MangaTranslator
from manga_translator.mode.response import to_translation


def _decode_image(image_b64: str) -> Image.Image:
    return Image.open(io.BytesIO(base64.b64decode(image_b64)))


def _encode_image(image: Image.Image) -> bytes:
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    return buf.getvalue()


def _serialize_context(ctx: Context, output_format: str) -> Optional[bytes]:
    if output_format == "image":
        return _encode_image(ctx.result) if ctx.result is not None else None
    if output_format == "json":
        return to_translation(ctx).model_dump_json().encode("utf-8")
    if output_format == "bytes":
        return to_translation(ctx).to_bytes()
    raise HTTPException(status_code=400, detail=f"Unknown output_format: {output_format}")


def _pack_batch_results(items: List[Optional[bytes]]) -> bytes:
    encoded = [base64.b64encode(item).decode("utf-8") if item is not None else None for item in items]
    return json.dumps({"results": encoded}).encode("utf-8")


class MangaShare:
    def __init__(self, params: dict = None):
        self.manga = MangaTranslator(params)
        self.host = params.get('host', '127.0.0.1')
        self.port = int(params.get('port', '5003'))
        nonce = params.get('nonce', None)
        if not nonce:
            nonce = secrets.token_hex(16)
        if nonce == "None":
            nonce = None
        self.nonce = nonce

        # each chunk has a structure like this status_code(int/1byte),len(int/4bytes),bytechunk
        # status codes are 0 for result, 1 for progress report, 2 for error
        self.progress_queue = asyncio.Queue()
        self.lock = Lock()

        async def hook(state: str, finished: bool):
            state_data = state.encode("utf-8")
            progress_data = b'\x01' + len(state_data).to_bytes(4, 'big') + state_data
            await self.progress_queue.put(progress_data)
            await asyncio.sleep(0)

        self.manga.add_progress_hook(hook)

    async def progress_stream(self):
        """
        loops until the status is != 1 which is eiter an error or the result
        """
        while True:
            progress = await self.progress_queue.get()
            yield progress
            if progress[0] != 1:
                break

    async def _call(self, method_name: str, body: dict):
        """Decode the wire-shaped request body into real kwargs for the named
        manga_translator method, call it, and return the raw result
        (Context for translate, List[Context] for translate_batch)."""
        if method_name == "translate":
            image = _decode_image(body["image_b64"])
            config = self._build_config(body)
            return await self.manga.translate(image, config)
        elif method_name == "translate_batch":
            config = self._build_config(body)
            images_with_configs = [(_decode_image(b), config) for b in body["images_b64"]]
            batch_size = body.get("batch_size", 4)
            return await self.manga.translate_batch(images_with_configs, batch_size)
        else:
            raise HTTPException(status_code=404, detail="Method not found")

    @staticmethod
    def _build_config(body: dict) -> Config:
        """Config carries a few ad hoc, non-field attributes (_original_filename,
        _is_web_frontend, _web_frontend_optimized) set directly on the instance by
        server/main.py. model_dump() only covers declared fields, so those ride
        alongside as a separate "config_extra" dict and get reapplied here."""
        config = Config.model_validate(body["config"])
        for key, value in body.get("config_extra", {}).items():
            setattr(config, key, value)
        return config

    def _serialize(self, method_name: str, result, output_format: str) -> bytes:
        if method_name == "translate_batch":
            return _pack_batch_results([_serialize_context(ctx, output_format) for ctx in result])
        return _serialize_context(result, output_format) or b""

    async def run_method(self, method_name: str, body: dict):
        try:
            result = await self._call(method_name, body)
            output_format = body.get("output_format", "json")
            result_bytes = self._serialize(method_name, result, output_format)
            encoded_result = b'\x00' + len(result_bytes).to_bytes(4, 'big') + result_bytes
            await self.progress_queue.put(encoded_result)
        except Exception as e:
            err_bytes = str(e).encode("utf-8")
            encoded_result = b'\x02' + len(err_bytes).to_bytes(4, 'big') + err_bytes
            await self.progress_queue.put(encoded_result)
        finally:
            self.lock.release()

    def check_nonce(self, request: Request):
        if self.nonce:
            nonce = request.headers.get('X-Nonce')
            if nonce != self.nonce:
                raise HTTPException(401, detail="Nonce does not match")

    def check_lock(self):
        if not self.lock.acquire(blocking=False):
            raise HTTPException(status_code=429, detail="some Method is already being executed.")

    async def listen(self, translation_params: dict = None):
        app = FastAPI()

        @app.get("/is_locked")
        async def is_locked():
            if self.lock.locked():
                return {"locked": True}
            return {"locked": False}

        @app.post("/simple_execute/{method_name}")
        async def execute_method(request: Request, method_name: str = Path(...)):
            self.check_nonce(request)
            self.check_lock()
            body = json.loads(await request.body())
            try:
                result = await self._call(method_name, body)
                output_format = body.get("output_format", "json")
                result_bytes = self._serialize(method_name, result, output_format)
                self.lock.release()
                return Response(content=result_bytes, media_type="application/octet-stream")
            except HTTPException:
                self.lock.release()
                raise
            except Exception as e:
                self.lock.release()
                raise HTTPException(status_code=500, detail=str(e))

        @app.post("/execute/{method_name}")
        async def execute_method_streaming(request: Request, method_name: str = Path(...)):
            self.check_nonce(request)
            self.check_lock()
            body = json.loads(await request.body())

            self.manga._is_streaming_mode = bool(body.get("config_extra", {}).get('_web_frontend_optimized', False))

            # streaming response
            streaming_response = StreamingResponse(self.progress_stream(), media_type="application/octet-stream")
            asyncio.create_task(self.run_method(method_name, body))
            return streaming_response

        config = uvicorn.Config(app, host=self.host, port=self.port)
        server = uvicorn.Server(config)
        await server.serve()
