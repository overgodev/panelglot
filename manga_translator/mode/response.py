import base64
import struct
from typing import Dict, List, Annotated

import cv2
import numpy as np
from pydantic import BaseModel, Field, WithJsonSchema

from manga_translator import Context
from manga_translator.utils import TextBlock


#input:PIL,
#result:PIL
#img_colorized: PIL
#upscaled:PIL
#img_rgb:array
#img_alpha:None
#textlines:list[Quadrilateral]
#text_regions:list[TextBlock]
#translations: map[str, arr[str]]
#img_inpainted: array
#gimp_mask:array
#img_rendered: array
#mask_raw: array
#mask:array
NumpyNdarray = Annotated[
    np.ndarray,
    WithJsonSchema({'type': 'string', "format": "base64","examples": ["data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAA..."]}),
]

class TextColor(BaseModel):
    fg: tuple[int, int, int]
    bg: tuple[int, int, int]

class Translation(BaseModel):
    minX: int
    minY: int
    maxX: int
    maxY: int
    is_bulleted_list: bool
    angle: float | int
    prob: float
    text_color: TextColor
    text: dict[str, str]
    background: NumpyNdarray = Field(
        ...,
        description="Background image encoded as a base64 string",
        examples=["data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAA..."]
    )

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            np.ndarray: lambda array: Translation.encode_background(array)
        }

    @staticmethod
    def encode_background(array: np.ndarray) -> str:
        retval, buffer = cv2.imencode('.png', array)
        jpg_as_text = base64.b64encode(buffer).decode("utf-8")
        background = f"data:image/png;base64,{jpg_as_text}"
        return background

    def to_bytes(self):
        coords_bytes = struct.pack('4i', self.minX, self.minY, self.maxX, self.maxY)
        is_bulleted_list_byte = struct.pack('?', self.is_bulleted_list)
        angle_bytes = struct.pack('f', float(self.angle) if isinstance(self.angle, int) else self.angle)
        prob_bytes = struct.pack('f', self.prob)
        fg = struct.pack('3B', self.text_color.fg[0], self.text_color.fg[1], self.text_color.fg[2])
        bg = struct.pack('3B', self.text_color.bg[0], self.text_color.bg[1], self.text_color.bg[2])
        text_bytes = struct.pack('i', len(self.text.items()))
        for key, value in self.text.items():
            text_bytes += struct.pack('I', len(key.encode('utf-8'))) + key.encode('utf-8')
            text_bytes += struct.pack('I', len(value.encode('utf-8'))) + value.encode('utf-8')
        background_bytes = struct.pack('I', len(self.background.tobytes())) + self.background.tobytes()
        return coords_bytes +is_bulleted_list_byte+ angle_bytes+prob_bytes+fg + bg + text_bytes + background_bytes

class TranslationResponse(BaseModel):
    translations: List[Translation]
    debug_folder: str = None  # 添加debug_folder字段

    def to_bytes(self):
        items= [v.to_bytes() for v in self.translations]
        return struct.pack('i', len(items)) + b''.join(items)

def to_translation(ctx: Context) -> TranslationResponse:
    text_regions:list[TextBlock] = ctx.text_regions
    inpaint = ctx.img_inpainted
    translations:Dict[str, List[str]] = ctx.translations
    results = []
    for i, blk in enumerate(text_regions):
        minX, minY, maxX, maxY = blk.xyxy
        text_region = text_regions[i]
        # ctx.translations (a separately tracked {lang: [str, ...]} dict) is not populated by
        # every translation code path (e.g. the context-injection branch for chatgpt/
        # custom_openai bypasses it entirely), and even when present can desync from
        # text_regions under retries/rebuilds. text_region.translation is set unconditionally
        # by every path as translation completes and is the authoritative source - always use
        # it as the primary target-language value, falling back to the indexed dict only for
        # any *other* languages it happens to carry.
        if 'translations' in ctx and translations:
            trans = {key: value[i] for key, value in translations.items() if i < len(value)}
        else:
            trans = {}
        target_lang = getattr(text_region, 'target_lang', None)
        if target_lang and getattr(text_region, 'translation', None):
            trans[target_lang] = text_region.translation
        trans[text_region.source_lang] = text_regions[i].text
        text_region.adjust_bg_color = False
        color1, color2 = text_region.get_font_colors()
        results.append(Translation(text=trans,
                    minX=int(minX),minY=int(minY),maxX=int(maxX),maxY=int(maxY),
                    background=inpaint[minY:maxY, minX:maxX],
                    is_bulleted_list=text_region.is_bulleted_list,
                    text_color=TextColor(fg=color1.tolist(), bg=color2.tolist()),
                    prob=text_region.prob,
                    angle=text_region.angle
        ))
        #todo: background angle

    # 获取debug_folder信息
    debug_folder = getattr(ctx, 'debug_folder', None)

    return TranslationResponse(translations=results, debug_folder=debug_folder)


class OcrPreviewRegion(BaseModel):
    minX: int
    minY: int
    maxX: int
    maxY: int
    text: str


class OcrPreviewResponse(BaseModel):
    regions: List[OcrPreviewRegion]


def to_ocr_preview(ctx: Context) -> OcrPreviewResponse:
    """Serializes a Context stopped early (Config.ocr_preview_only) right after OCR/
    textline-merge - no translation, inpainting, or rendering has run, so there's no
    ctx.img_inpainted to build a Translation from. Coordinates are scaled back from
    ctx.img_rgb (post colorize/upscale) to ctx.input's original size, since the web UI
    overlays these boxes on the original uploaded image, not an internal upscaled copy."""
    text_regions = ctx.text_regions or []
    in_w, in_h = ctx.input.size
    img_h, img_w = ctx.img_rgb.shape[:2]
    scale_x, scale_y = img_w / in_w, img_h / in_h
    regions = []
    for blk in text_regions:
        minX, minY, maxX, maxY = blk.xyxy
        regions.append(OcrPreviewRegion(
            minX=int(minX / scale_x), minY=int(minY / scale_y),
            maxX=int(maxX / scale_x), maxY=int(maxY / scale_y),
            text=blk.text,
        ))
    return OcrPreviewResponse(regions=regions)
