from asyncio import Event, Lock
from typing import List, Optional

from PIL import Image
from pydantic import BaseModel

from manga_translator import Config
from server.core.sent_data_internal import fetch_data_stream, NotifyType, fetch_data, fetch_data_raw, fetch_data_stream_raw, encode_image_b64

_CONFIG_EXTRA_ATTRS = ('_original_filename', '_is_web_frontend', '_web_frontend_optimized')

def _config_extra(config: Config) -> dict:
    """Ad hoc, non-field attributes server/main.py sets directly on a Config
    instance. model_dump() only covers declared fields, so these ride alongside
    as a separate dict for the worker to reapply."""
    extra = {}
    for attr in _CONFIG_EXTRA_ATTRS:
        value = getattr(config, attr, None)
        if value is not None:
            extra[attr] = value
    return extra

class ExecutorInstance(BaseModel):
    ip: str
    port: int
    busy: bool = False
    nonce: Optional[str] = None

    def free_executor(self):
        self.busy = False

    def _headers(self):
        return {"X-Nonce": self.nonce} if self.nonce else {}

    async def sent(self, image: Image, config: Config, output_format: str):
        return await fetch_data("http://"+self.ip+":"+str(self.port)+"/simple_execute/translate", image, config, output_format, headers=self._headers())

    async def sent_stream(self, image: Image, config: Config, output_format: str, sender: NotifyType):
        await fetch_data_stream("http://"+self.ip+":"+str(self.port)+"/execute/translate", image, config, output_format, sender, headers=self._headers())

    async def sent_batch(self, images: List[Image.Image], configs: List[Config], batch_size: int, output_format: str):
        """发送批量翻译请求 - one config per image, so each page can carry its own settings
        and manual text boxes."""
        body = {
            "images_b64": [encode_image_b64(image) for image in images],
            "configs": [c.model_dump(mode="json") for c in configs],
            "configs_extra": [_config_extra(c) for c in configs],
            "batch_size": batch_size,
            "output_format": output_format,
        }
        return await fetch_data_raw("http://"+self.ip+":"+str(self.port)+"/simple_execute/translate_batch",
                               body, headers=self._headers())

    async def sent_batch_stream(self, images: List[Image.Image], configs: List[Config], batch_size: int, output_format: str, sender: NotifyType):
        """发送批量翻译流式请求 - one config per image, so each page can carry its own settings
        and manual text boxes."""
        body = {
            "images_b64": [encode_image_b64(image) for image in images],
            "configs": [c.model_dump(mode="json") for c in configs],
            "configs_extra": [_config_extra(c) for c in configs],
            "batch_size": batch_size,
            "output_format": output_format,
        }
        await fetch_data_stream_raw("http://"+self.ip+":"+str(self.port)+"/execute/translate_batch",
                               body, sender, headers=self._headers())

class Executors:
    def __init__(self):
        self.list: List[ExecutorInstance] = []
        self.lock: Lock = Lock()
        self.event = Event()

    def register(self, instance: ExecutorInstance):
        self.list.append(instance)

    def free_executors(self) -> int:
        return len([item for item in self.list if not item.busy])

    async def _find_instance(self):
        while True:
            instance = next((x for x in self.list if x.busy == False), None)
            if instance is not None:
                return instance
            #todo: cricial error: warn should never happen
            await self.event.wait()

    async def find_executor(self) -> ExecutorInstance:
        async with self.lock:  # Using async with for lock management
            instance = await self._find_instance()
            instance.busy = True
            return instance

    async def free_executor(self, instance: ExecutorInstance):
        from server.core.myqueue import task_queue
        instance.free_executor()
        self.event.set()
        self.event.clear()
        await task_queue.update_event()

executor_instances: Executors = Executors()
