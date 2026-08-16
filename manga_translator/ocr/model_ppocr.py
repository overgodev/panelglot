from typing import List

import cv2
import numpy as np

from .common import OfflineOCR
from ..config import OcrConfig
from ..utils import TextBlock, Quadrilateral


class ModelPPOCR(OfflineOCR):
    """PP-OCRv6 (via the rapidocr package) - a single model that reads mixed
    EN/Chinese/Japanese/Korean text in one pass. Manages its own model download/cache
    (see rapidocr's own cache dir), so _MODEL_MAPPING is intentionally left empty."""

    async def _load(self, device: str):
        from rapidocr import RapidOCR, EngineType, ModelType, OCRVersion
        from rapidocr.ch_ppocr_rec.typings import TextRecInput

        params = {
            'Rec.engine_type': EngineType.ONNXRUNTIME,
            'Rec.ocr_version': OCRVersion.PPOCRV6,
            'Rec.model_type': ModelType.SMALL,
        }
        if device.startswith('cuda'):
            # Requires onnxruntime-gpu to actually take effect; silently falls back to CPU
            # otherwise (rapidocr doesn't error if the CUDA provider isn't available).
            params['Rec.engine_cfg.use_cuda'] = True
        engine = RapidOCR(params=params)
        # Use the recognizer directly rather than the full RapidOCR() det+rec pipeline: our
        # textlines are already tightly cropped single lines by our own detector, and PP-OCR's
        # own detection step (built for finding text within a larger scene) behaves poorly fed
        # a crop that's *already* just the text - producing missed/garbled results in testing.
        self.rec = engine.text_rec
        self._TextRecInput = TextRecInput

    async def _unload(self):
        del self.rec

    def _estimate_colors(self, region_img: np.ndarray):
        """No dedicated color-prediction model here (unlike the 32px/48px models), so estimate
        foreground/background from the crop directly: Otsu-threshold into two clusters and take
        the mean color of each side, assuming the smaller cluster is the text strokes."""
        gray = cv2.cvtColor(region_img, cv2.COLOR_RGB2GRAY)
        _, mask = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        fg_mask = mask if cv2.countNonZero(mask) < mask.size / 2 else cv2.bitwise_not(mask)
        bg_mask = cv2.bitwise_not(fg_mask)
        fg = cv2.mean(region_img, mask=fg_mask)[:3] if cv2.countNonZero(fg_mask) else (0, 0, 0)
        bg = cv2.mean(region_img, mask=bg_mask)[:3] if cv2.countNonZero(bg_mask) else (255, 255, 255)
        return tuple(int(c) for c in fg), tuple(int(c) for c in bg)

    async def _infer(self, image: np.ndarray, textlines: List[Quadrilateral], config: OcrConfig, verbose: bool = False, ignore_bubble: int = 0) -> List[Quadrilateral]:
        text_height = 48
        quadrilaterals = list(self._generate_text_direction(textlines))
        output = []

        for q, d in quadrilaterals:
            region_img = q.get_transformed_region(image, d, text_height)
            if region_img is None or region_img.size == 0:
                continue

            result = self.rec(self._TextRecInput(img=region_img))
            texts = result.txts or ()
            scores = result.scores or []
            text = ''.join(texts)
            prob = float(np.mean(scores)) if scores else 0.0

            if verbose:
                self.logger.info(f'prob: {prob} {text}')

            fg, bg = self._estimate_colors(region_img)
            cur_region = q if isinstance(q, Quadrilateral) else q
            if isinstance(cur_region, Quadrilateral):
                cur_region.text = text
                cur_region.prob = prob
                cur_region.fg_r, cur_region.fg_g, cur_region.fg_b = fg
                cur_region.bg_r, cur_region.bg_g, cur_region.bg_b = bg
            else:  # TextBlock
                cur_region.text.append(text)
                cur_region.update_font_colors(np.array(fg), np.array(bg))
            output.append(cur_region)

        return output
