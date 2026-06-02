"""
Agnes AI API Client
==================
Wrapper for all Agnes AI API endpoints.

Endpoints:
- Chat Completions:  POST /v1/chat/completions
- Image Generation:  POST /v1/images/generations
- Video Generation:  POST /v1/video/generations (async with polling)

Supported Models:
- agnes-2.0-flash        : LLM chat / vision
- agnes-image-2.1-flash  : Text-to-image, image-to-image
- agnes-video-v2.0      : Text-to-video, image-to-video
"""

import base64
import json
import os
import time
import tempfile
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

import requests
from PIL import Image

# torch / numpy are only needed inside ComfyUI (tensor conversions).
# Lazy-import them to allow the API module to be tested standalone.
_torch = None
_np = None

def _get_torch():
    global _torch
    if _torch is None:
        import torch as _t
        _torch = _t
    return _torch

def _get_np():
    global _np
    if _np is None:
        import numpy as _n
        _np = _n
    return _np

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

BASE_URL = "https://apihub.agnes-ai.com/v1"

CHAT_MODEL = "agnes-2.0-flash"
IMAGE_MODEL = "agnes-image-2.1-flash"
VIDEO_MODEL = "agnes-video-v2.0"

DEFAULT_SIZE = "1024x1024"
DEFAULT_VIDEO_FRAMES = 121
DEFAULT_VIDEO_FPS = 24

AVAILABLE_CHAT_MODELS = [CHAT_MODEL]
AVAILABLE_IMAGE_MODELS = [IMAGE_MODEL]
AVAILABLE_VIDEO_MODELS = [VIDEO_MODEL]

MIME_MAP = {
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "webp": "image/webp",
    "gif": "image/gif",
    "bmp": "image/bmp",
}


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def tensor_to_pil(tensor) -> Image.Image:
    """
    Convert a ComfyUI IMAGE tensor [B, H, W, C] (float32, 0..1) to a PIL Image.
    Returns the first image in the batch.
    """
    np = _get_np()
    # Take first image: [H, W, C]
    img = tensor[0].cpu().numpy()
    img = (img * 255).astype(np.uint8)
    return Image.fromarray(img)


def pil_to_tensor(pil_img: Image.Image):
    """Convert a PIL Image to a ComfyUI IMAGE tensor [1, H, W, C] float32."""
    torch = _get_torch()
    np = _get_np()
    img = np.array(pil_img.convert("RGB")).astype(np.float32) / 255.0
    return torch.from_numpy(img).unsqueeze(0)


def pil_to_base64_uri(pil_img: Image.Image, fmt: str = "png") -> str:
    """Convert a PIL Image to a base64 data URI string."""
    buf = BytesIO()
    pil_img.save(buf, format=fmt.upper())
    b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
    mime = MIME_MAP.get(fmt.lower(), "image/png")
    return f"data:{mime};base64,{b64}"


def download_url_to_pil(url: str, timeout: int = 120) -> Optional[Image.Image]:
    """Download an image from a URL and return as PIL Image."""
    try:
        resp = requests.get(url, timeout=timeout)
        if resp.status_code == 200:
            return Image.open(BytesIO(resp.content)).convert("RGB")
    except Exception:
        pass
    return None


def download_url_to_bytes(url: str, timeout: int = 120) -> Optional[bytes]:
    """Download content from a URL and return raw bytes."""
    try:
        resp = requests.get(url, timeout=timeout)
        if resp.status_code == 200:
            return resp.content
    except Exception:
        pass
    return None


# ---------------------------------------------------------------------------
# API Client
# ---------------------------------------------------------------------------

class AgnesClient:
    """Unified client for all Agnes AI API endpoints."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": api_key,
            "Content-Type": "application/json",
        })

    # ------------------------------------------------------------------
    # Chat / LLM
    # ------------------------------------------------------------------

    def chat(
        self,
        messages: List[Dict[str, Any]],
        model: str = CHAT_MODEL,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        stream: bool = False,
    ) -> str:
        """
        Call the chat completions endpoint.

        Args:
            messages: OpenAI-format message list.
            model: Model identifier.
            temperature: Sampling temperature.
            max_tokens: Maximum output tokens.
            stream: Whether to stream (returns full text for simplicity).

        Returns:
            The assistant's text response.
        """
        url = f"{BASE_URL}/chat/completions"
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream,
        }
        resp = self.session.post(url, json=payload, timeout=300)
        if resp.status_code != 200:
            raise RuntimeError(f"Chat API error ({resp.status_code}): {resp.text}")

        data = resp.json()
        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError):
            raise RuntimeError(f"Unexpected chat response format: {data}")

    # ------------------------------------------------------------------
    # Image Generation
    # ------------------------------------------------------------------

    def generate_image(
        self,
        prompt: str,
        mode: str = "text2img",
        reference_images: Optional[List[Image.Image]] = None,
        size: str = DEFAULT_SIZE,
        n: int = 1,
        model: str = IMAGE_MODEL,
    ) -> List[Image.Image]:
        """
        Generate images via the Agnes image generation API.

        Args:
            prompt: Generation prompt.
            mode: "text2img" or "img2img".
            reference_images: List of PIL Images for img2img (as data URIs).
            size: Output size, e.g. "1024x1024".
            n: Number of images to generate (1-10).
            model: Model identifier.

        Returns:
            List of generated PIL Images.
        """
        url = f"{BASE_URL}/images/generations"
        payload = {
            "model": model,
            "prompt": prompt,
            "size": size,
            "n": n,
        }

        if mode == "img2img" and reference_images:
            image_uris = [pil_to_base64_uri(img) for img in reference_images]
            payload["extra_body"] = {
                "image": image_uris,
                "response_format": "url",
            }

        resp = self.session.post(url, json=payload, timeout=300)
        if resp.status_code != 200:
            raise RuntimeError(f"Image API error ({resp.status_code}): {resp.text}")

        data = resp.json()
        images = []
        for item in data.get("data", []):
            image_url = item.get("url")
            if image_url:
                pil_img = download_url_to_pil(image_url)
                if pil_img:
                    images.append(pil_img)

        return images

    # ------------------------------------------------------------------
    # Video Generation (async with polling)
    # ------------------------------------------------------------------

    def generate_video(
        self,
        prompt: str,
        mode: str = "text2video",
        reference_images: Optional[List[Image.Image]] = None,
        model: str = VIDEO_MODEL,
        num_frames: int = DEFAULT_VIDEO_FRAMES,
        frame_rate: int = DEFAULT_VIDEO_FPS,
        seed: Optional[int] = None,
        poll_interval: int = 10,
        max_wait: int = 600,
        output_dir: Optional[str] = None,
    ) -> Optional[str]:
        """
        Generate a video via the Agnes video generation API (async).

        After submitting the task, this method polls until completion or timeout.

        Args:
            prompt: Video description.
            mode: "text2video" or "img2video".
            reference_images: List of PIL Images for img2video.
            model: Model identifier.
            num_frames: Number of frames (must be 8n+1, max 441).
            frame_rate: Frame rate (fps).
            seed: Optional seed for reproducibility.
            poll_interval: Seconds between status checks.
            max_wait: Maximum seconds to wait for completion.
            output_dir: Directory to save the video. Defaults to
                        ComfyUI output dir or system temp dir.

        Returns:
            Local file path to the downloaded MP4 video, or None on failure.
        """
        # Validate num_frames
        if (num_frames - 1) % 8 != 0:
            raise ValueError("num_frames must satisfy (num_frames - 1) % 8 == 0")
        if num_frames > 441:
            raise ValueError("num_frames must be <= 441")

        # --- Submit task ---
        url = f"{BASE_URL}/video/generations"
        payload = {
            "model": model,
            "prompt": prompt,
            "num_frames": num_frames,
            "frame_rate": frame_rate,
            "response_format": "url",
        }
        if seed is not None:
            payload["seed"] = seed

        if mode == "img2video" and reference_images:
            image_uris = [pil_to_base64_uri(img) for img in reference_images]
            payload["extra_body"] = {
                "image": image_uris,
            }

        resp = self.session.post(url, json=payload, timeout=60)
        if resp.status_code not in (200, 201, 202):
            raise RuntimeError(f"Video submit error ({resp.status_code}): {resp.text}")

        data = resp.json()
        task_id = data.get("id") or data.get("task_id")
        if not task_id:
            raise RuntimeError(f"No task_id in submit response: {data}")

        # --- Poll for result ---
        status_url = f"{BASE_URL}/video/generations/{task_id}"
        elapsed = 0

        while elapsed < max_wait:
            time.sleep(poll_interval)
            elapsed += poll_interval

            status_resp = self.session.get(status_url, timeout=30)
            if status_resp.status_code != 200:
                continue

            status_data = status_resp.json()
            state = status_data.get("status") or status_data.get("state")

            if state in ("completed", "succeeded"):
                video_url = None
                # Try multiple response formats
                for key in ("url", "video_url", "output_url"):
                    if key in status_data:
                        video_url = status_data[key]
                        break
                if not video_url:
                    data_items = status_data.get("data", [])
                    if data_items:
                        video_url = data_items[0].get("url")

                if video_url:
                    video_bytes = download_url_to_bytes(video_url)
                    if video_bytes:
                        # Determine output directory
                        if output_dir:
                            save_dir = output_dir
                        else:
                            save_dir = tempfile.gettempdir()

                        os.makedirs(save_dir, exist_ok=True)
                        timestamp = int(time.time())
                        filename = f"agnes_video_{mode}_{timestamp}_{task_id[:8]}.mp4"
                        save_path = os.path.join(save_dir, filename)
                        with open(save_path, "wb") as f:
                            f.write(video_bytes)
                        return save_path

                raise RuntimeError(f"Video completed but no downloadable URL found.")

            elif state in ("failed", "error"):
                error_msg = status_data.get("error", "Unknown error")
                raise RuntimeError(f"Video generation failed: {error_msg}")

        raise TimeoutError(f"Video generation timed out after {max_wait}s (task: {task_id})")

    # ------------------------------------------------------------------
    # Image Understanding / Reverse Prompt (via vision chat)
    # ------------------------------------------------------------------

    def reverse_prompt(
        self,
        image: Image.Image,
        model: str = CHAT_MODEL,
        detail: str = "detailed",
    ) -> str:
        """
        Analyze an image and generate a prompt that could reproduce it.

        Args:
            image: Input PIL Image.
            model: Vision-capable model identifier.
            detail: "brief" or "detailed" analysis level.

        Returns:
            Generated prompt / description.
        """
        image_uri = pil_to_base64_uri(image)

        if detail == "detailed":
            system_prompt = (
                "You are an expert at analyzing images and writing prompts for "
                "AI image generation models. Describe the image in extreme detail: "
                "subject, composition, lighting, color palette, style, mood, camera angle, "
                "depth of field, textures, and any distinctive elements. "
                "Output ONLY the prompt, no additional commentary."
            )
        else:
            system_prompt = (
                "You are an expert at analyzing images and writing prompts for "
                "AI image generation models. Write a concise prompt describing the key "
                "elements of this image. Output ONLY the prompt, no additional commentary."
            )

        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": image_uri}},
                    {
                        "type": "text",
                        "text": "Please describe this image as an AI image generation prompt.",
                    },
                ],
            },
        ]

        return self.chat(messages, model=model, temperature=0.3, max_tokens=2048)


# ---------------------------------------------------------------------------
# Global state helper (shared across nodes)
# ---------------------------------------------------------------------------

# Path to the persistent API key config file (in plugin root).
_PLUGIN_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_API_KEY_CONFIG_FILE = os.path.join(_PLUGIN_DIR, "api_key_config.json")

_GLOBAL_CONFIG: Dict[str, Any] = {
    "api_key": os.environ.get("AGNES_API_KEY", ""),
    "chat_model": CHAT_MODEL,
    "image_model": IMAGE_MODEL,
    "video_model": VIDEO_MODEL,
}

# Attempt to load API key from config file on module init.
# Priority: env var > config file.
def _load_key_from_config_file() -> str:
    """Try to load the API key from the plugin's api_key_config.json."""
    try:
        if os.path.exists(_API_KEY_CONFIG_FILE):
            with open(_API_KEY_CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("api_key", "")
    except Exception:
        pass
    return ""

# Load from config file if env var not set.
if not _GLOBAL_CONFIG["api_key"]:
    _GLOBAL_CONFIG["api_key"] = _load_key_from_config_file()


def get_api_key() -> str:
    """Get the current API key. Checks: env var → config file → fallback."""
    key = _GLOBAL_CONFIG["api_key"]
    if not key:
        key = _load_key_from_config_file()
        if key:
            _GLOBAL_CONFIG["api_key"] = key
    return key


def set_api_key(key: str) -> None:
    _GLOBAL_CONFIG["api_key"] = key


def get_client() -> AgnesClient:
    key = get_api_key()
    if not key:
        raise ValueError(
            "Agnes API key is not set. Please provide your API key in the node settings.\n"
            "Get a free key at: https://platform.agnes-ai.com/"
        )
    return AgnesClient(key)


def get_global_config() -> Dict[str, Any]:
    return dict(_GLOBAL_CONFIG)


def set_global_model(model_type: str, model_name: str) -> None:
    _GLOBAL_CONFIG[model_type] = model_name
