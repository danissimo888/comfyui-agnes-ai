"""
Agnes Image Reverse Prompt Node
===============================
Analyzes an input image and generates a detailed AI image generation prompt
that describes the image. Uses Agnes-2.0-Flash vision capability.
"""

import time
from typing import Tuple

from ..api import AgnesClient, get_api_key, CHAT_MODEL, AVAILABLE_CHAT_MODELS, tensor_to_pil


class AgnesImageReverse:
    """Agnes AI Image Reverse Prompt node - generates prompts from images."""

    CATEGORY = "Agnes AI"
    RETURN_TYPES = ("STRING", "STRING",)
    RETURN_NAMES = ("prompt", "brief_prompt",)
    FUNCTION = "reverse"

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return time.time()

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "api_key": ("STRING", {
                    "multiline": False,
                    "default": "",
                    "placeholder": "sk-...",
                    "tooltip": "Your Agnes AI API key",
                }),
                "image": ("IMAGE", {
                    "tooltip": "Input image to analyze for prompt generation",
                }),
                "model": (AVAILABLE_CHAT_MODELS, {
                    "default": CHAT_MODEL,
                    "tooltip": "Vision-capable model for image analysis",
                }),
                "temperature": ("FLOAT", {
                    "default": 0.3,
                    "min": 0.0,
                    "max": 2.0,
                    "step": 0.05,
                    "tooltip": "Sampling temperature (lower = more consistent descriptions)",
                }),
                "max_tokens": ("INT", {
                    "default": 2048,
                    "min": 64,
                    "max": 8192,
                    "step": 64,
                    "tooltip": "Maximum tokens for prompt generation",
                }),
            },
        }

    def reverse(self, api_key: str, image, model: str = CHAT_MODEL, temperature: float = 0.3, max_tokens: int = 2048) -> Tuple[str, str]:
        # Runtime fallback: try config file if widget value is empty
        if not api_key.strip():
            api_key = get_api_key()
        if not api_key.strip():
            err = "[Error: API key is required]"
            return (err, err)

        try:
            # Convert ComfyUI tensor to PIL
            pil_img = tensor_to_pil(image)

            client = AgnesClient(api_key)

            detailed = client.reverse_prompt(pil_img, model=model, detail="detailed", temperature=temperature, max_tokens=max_tokens)
            brief = client.reverse_prompt(pil_img, model=model, detail="brief", temperature=temperature, max_tokens=max_tokens)

            return (detailed, brief)
        except Exception as e:
            err = f"[Error] {str(e)}"
            return (err, err)
