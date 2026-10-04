"""
OCR & Multi-Modal Document Parser Service
Dual-engine architecture:
1. RapidOCR (ONNX Neural Engine): High-speed, high-accuracy, runs embedded with zero OS dependencies.
2. Tesseract-OCR (Binary Fallback): Host-level tesseract engine if installed.
"""

import os
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from PIL import Image
import numpy as np

# RapidOCR (ONNX neural runtime)
try:
    from rapidocr_onnxruntime import RapidOCR
    _RAPIDOCR_AVAILABLE = True
except ImportError:
    _RAPIDOCR_AVAILABLE = False

# Pytesseract
try:
    import pytesseract
    _PYTESSERACT_AVAILABLE = True
except ImportError:
    _PYTESSERACT_AVAILABLE = False


class OCRDocumentParserService:
    """Service handling multi-modal OCR with RapidOCR and Tesseract engines."""

    def __init__(self, tesseract_cmd: Optional[str] = None):
        self.tesseract_cmd = tesseract_cmd or self._find_tesseract_binary()
        self.is_tesseract_available = False
        self.rapid_ocr = None

        if _RAPIDOCR_AVAILABLE:
            try:
                self.rapid_ocr = RapidOCR()
            except Exception:
                self.rapid_ocr = None

        self._configure_tesseract()

    def _find_tesseract_binary(self) -> Optional[str]:
        """Locates tesseract executable on Windows or Linux."""
        env_cmd = os.getenv("TESSERACT_CMD")
        if env_cmd and os.path.exists(env_cmd):
            return env_cmd

        which_cmd = shutil.which("tesseract")
        if which_cmd:
            return which_cmd

        candidates = [
            Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe"),
            Path(r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"),
            Path(os.path.expanduser(r"~\AppData\Local\Programs\Tesseract-OCR\tesseract.exe")),
            Path(os.path.expanduser(r"~\AppData\Local\Tesseract-OCR\tesseract.exe")),
        ]
        for candidate in candidates:
            if candidate.exists():
                return str(candidate)
        return None

    def _configure_tesseract(self) -> bool:
        if _PYTESSERACT_AVAILABLE:
            cmd = self._find_tesseract_binary()
            if cmd and os.path.exists(cmd):
                self.tesseract_cmd = cmd
                pytesseract.pytesseract.tesseract_cmd = str(cmd)
                self.is_tesseract_available = True
                return True
        return False

    @property
    def is_ocr_available(self) -> bool:
        return (self.rapid_ocr is not None) or self.is_tesseract_available

    def ocr_image(
        self, image: Image.Image
    ) -> Tuple[str, Optional[float], Optional[str], List[Dict[str, Any]]]:
        """
        Runs OCR on a PIL Image.
        Returns:
            (extracted_text, average_confidence, error_message, detected_boxes)
        """
        detected_boxes: List[Dict[str, Any]] = []

        # 1. Try RapidOCR (high accuracy neural ONNX engine)
        if self.rapid_ocr is not None:
            try:
                img_np = np.array(image.convert("RGB"))
                ocr_result, _ = self.rapid_ocr(img_np)

                if ocr_result:
                    text_lines: List[str] = []
                    conf_scores: List[float] = []

                    for idx, item in enumerate(ocr_result):
                        # item: [box, text, confidence]
                        box = item[0]
                        text = item[1]
                        conf = float(item[2])
                        text_lines.append(text)
                        conf_scores.append(conf)

                        # Flatten box to [x0, y0, x1, y1]
                        xs = [pt[0] for pt in box]
                        ys = [pt[1] for pt in box]
                        bbox = [min(xs), min(ys), max(xs), max(ys)]

                        detected_boxes.append(
                            {
                                "index": idx + 1,
                                "text": text,
                                "confidence": round(conf * 100, 1),
                                "bbox": [round(c, 2) for c in bbox],
                            }
                        )

                    full_text = "\n".join(text_lines)
                    avg_conf = (
                        round(sum(conf_scores) / len(conf_scores) * 100, 1)
                        if conf_scores
                        else None
                    )
                    return full_text, avg_conf, None, detected_boxes
            except Exception as e:
                # If RapidOCR fails, fall through to Tesseract
                pass

        # 2. Try Tesseract-OCR if available
        if self._configure_tesseract():
            try:
                text = pytesseract.image_to_string(image, lang="eng").strip()
                confidence = None
                try:
                    data = pytesseract.image_to_data(
                        image, output_type=pytesseract.Output.DICT
                    )
                    conf_values = [
                        int(c)
                        for c in data.get("conf", [])
                        if str(c).isdigit() and int(c) >= 0
                    ]
                    if conf_values:
                        confidence = round(sum(conf_values) / len(conf_values), 1)
                except Exception:
                    pass

                return text, confidence, None, []
            except Exception as e:
                return "", None, f"Tesseract OCR failed: {str(e)}", []

        return (
            "",
            None,
            "No active OCR engine available. Install Tesseract-OCR or verify RapidOCR ONNX runtime.",
            [],
        )

    def get_service_status(self) -> Dict[str, Any]:
        """Return status and active engines."""
        self._configure_tesseract()
        active_engine = (
            "RapidOCR (ONNX Neural Engine)"
            if self.rapid_ocr is not None
            else ("Tesseract-OCR" if self.is_tesseract_available else "none")
        )
        return {
            "name": "OCR & Document Parser Service",
            "phase": "Milestone 2",
            "status": "ready" if self.is_ocr_available else "inactive",
            "active_engine": active_engine,
            "rapidocr_available": self.rapid_ocr is not None,
            "tesseract_available": self.is_tesseract_available,
            "tesseract_path": self.tesseract_cmd,
            "capabilities": [
                "RapidOCR deep learning text recognition",
                "Bounding box polygon extraction",
                "Tesseract-OCR fallback",
                "Scanned borehole log digitization",
            ],
        }
