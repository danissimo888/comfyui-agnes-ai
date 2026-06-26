"""
Agnes Text-to-Image Node
========================
Generate images from text descriptions using Agnes AI image generation models.
Supports quality (1K/2K/4K) and aspect ratio selection.
"""

import time
import torch

from ..api import (
    AgnesClient,
    get_api_key,
    IMAGE_MODEL,
    AVAILABLE_IMAGE_MODELS,
    ASPECT_RATIOS,
    compute_size,
    pil_to_tensor,
)


class AgnesTextToImage:
    """Agnes AI Text-to-Image node for ComfyUI."""

    CATEGORY = "Agnes AI"
    RETURN_TYPES = ("IMAGE", "STRING",)
    RETURN_NAMES = ("images", "resolution",)
    FUNCTION = "generate"

    @classmethod
    def IS_CHANGED(cls, seed=0, **kwargs):
        if seed == 0:
            return time.time()
        return seed

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
                "prompt": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "placeholder": "A beautiful sunset over mountains...",
                    "tooltip": "Text description of the image to generate",
                }),
                "model": (AVAILABLE_IMAGE_MODELS, {
                    "default": IMAGE_MODEL,
                    "tooltip": "Image generation model",
                }),
                "quality": (["1K", "2K", "4K"], {
                    "default": "1K",
                    "tooltip": "Image quality / short-side resolution. 1K=1024px, 2K=2048px, 4K=4096px",
                }),
                "aspect_ratio": (ASPECT_RATIOS, {
                    "default": "1:1",
                    "tooltip": "Output aspect ratio (width:height). E.g. 16:9 for widescreen, 2:3 for portrait",
                }),
                "n": ("INT", {
                    "default": 1,
                    "min": 1,
                    "max": 4,
                    "step": 1,
                    "tooltip": "Number of images to generate (more takes longer)",
                }),
                "seed": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 999,
                    "step": 1,
                    "tooltip": "Random seed (0 = random). Set a fixed value for reproducible results.",
                }),
            },
            "optional": {
                "negative_prompt": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "placeholder": "ugly, blurry, distorted, low quality...",
                    "tooltip": "Things to avoid in the generated image",
                }),
            },
        }

    def generate(
        self,
        api_key: str,
        prompt: str,
        model: str = IMAGE_MODEL,
        quality: str = "1K",
        aspect_ratio: str = "1:1",
        n: int = 1,
        seed: int = 0,
        negative_prompt: str = "",
    ):
        if not prompt.strip():
            raise ValueError("Prompt is empty. Please provide an image description.")

        # Runtime fallback: try config file if widget value is empty
        if not api_key.strip():
            api_key = get_api_key()
        if not api_key.strip():
            raise ValueError("API key is required.")

        size = compute_size(quality, aspect_ratio)

        client = AgnesClient(api_key)
        pil_images = client.generate_image(
            prompt=prompt.strip(),
            mode="text2img",
            size=size,
            n=n,
            model=model,
            negative_prompt=negative_prompt.strip(),
            seed=seed if seed > 0 else None,
        )

        if not pil_images:
            raise RuntimeError("No images were generated. Check your prompt and try again.")

        # Convert to ComfyUI tensor batch
        tensors = [pil_to_tensor(img) for img in pil_images]
        batch = tensors[0] if len(tensors) == 1 else torch.cat(tensors, dim=0)

        return (batch, size)
