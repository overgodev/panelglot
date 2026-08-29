import base64
import io
import json
from typing import Mapping, Optional, Callable, List

import aiohttp
from PIL.Image import Image
from fastapi import HTTPException

from manga_translator import Config

_CONFIG_EXTRA_ATTRS = ('_original_filename', '_is_web_frontend', '_web_frontend_optimized')

def _config_extra(config: Config) -> dict:
    extra = {}
    for attr in _CONFIG_EXTRA_ATTRS:
        value = getattr(config, attr, None)
        if value is not None:
            extra[attr] = value
    return extra

def encode_image_b64(image: Image) -> str:
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("utf-8")

NotifyType = Optional[Callable[[int, Optional[bytes]], None]]

async def fetch_data_stream(url, image: Image, config: Config, output_format: str, sender: NotifyType, headers: Mapping[str, str] = {}):
    body = {
        "image_b64": encode_image_b64(image),
        "config": config.model_dump(mode="json"),
        "config_extra": _config_extra(config),
        "output_format": output_format,
    }
    data = json.dumps(body).encode("utf-8")

    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=data, headers={**headers, "Content-Type": "application/json"}) as response:
            if response.status == 200:
                await process_stream(response, sender)
            else:
                raise HTTPException(response.status, detail=await response.text())

async def fetch_data(url, image: Image, config: Config, output_format: str, headers: Mapping[str, str] = {}) -> bytes:
    """Returns the final wire bytes for a single translate call - already
    serialized worker-side into whichever output_format was requested."""
    body = {
        "image_b64": encode_image_b64(image),
        "config": config.model_dump(mode="json"),
        "config_extra": _config_extra(config),
        "output_format": output_format,
    }
    data = json.dumps(body).encode("utf-8")

    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=data, headers={**headers, "Content-Type": "application/json"}) as response:
            if response.status == 200:
                return await response.read()
            else:
                raise HTTPException(response.status, detail=await response.text())

async def fetch_data_raw(url, body: dict, headers: Mapping[str, str] = {}) -> List[Optional[bytes]]:
    """Batch counterpart of fetch_data - the worker responds with
    {"results": [base64-or-null, ...]}; returns the decoded byte list."""
    data = json.dumps(body).encode("utf-8")

    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=data, headers={**headers, "Content-Type": "application/json"}) as response:
            if response.status == 200:
                payload = json.loads(await response.read())
                return [base64.b64decode(item) if item is not None else None for item in payload["results"]]
            else:
                raise HTTPException(response.status, detail=await response.text())

async def fetch_data_stream_raw(url, body: dict, sender: NotifyType, headers: Mapping[str, str] = {}):
    """Streaming counterpart of fetch_data_raw."""
    data = json.dumps(body).encode("utf-8")

    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=data, headers={**headers, "Content-Type": "application/json"}) as response:
            if response.status == 200:
                await process_stream(response, sender)
            else:
                raise HTTPException(response.status, detail=await response.text())

async def process_stream(response, sender: NotifyType):
    buffer = b''

    async for chunk in response.content.iter_any():
        if chunk:
            buffer += chunk
            buffer = handle_buffer(buffer, sender)



def handle_buffer(buffer, sender: NotifyType):
    while len(buffer) >= 5:
        status, expected_size = extract_header(buffer)

        if len(buffer) >= 5 + expected_size:
            data = buffer[5:5 + expected_size]
            sender(status, data)
            buffer = buffer[5 + expected_size:]
        else:
            break
    return buffer


def extract_header(buffer):
    """Extract the status and expected size from the buffer."""
    status = int.from_bytes(buffer[0:1], byteorder='big')
    expected_size = int.from_bytes(buffer[1:5], byteorder='big')
    return status, expected_size
