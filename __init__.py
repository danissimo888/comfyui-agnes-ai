"""
ComfyUI Agnes AI Extension
===========================
Provides 7 custom nodes to call Agnes AI models within ComfyUI:

- AgnesAPIKeyConfig     : Persist API key to plugin config file
- AgnesLLMChat          : LLM dialogue (agnes-2.0-flash)
- AgnesImageReverse     : Image reverse prompt analysis
- AgnesImageToImage     : Image-to-image / image editing (multi-image)
- AgnesTextToImage      : Text-to-image generation
- AgnesImageToVideo     : Image-to-video generation (multi-image)
- AgnesTextToVideo      : Text-to-video generation

Author: ComfyUI Agnes AI Plugin
Version: 1.1.0
"""

import os

# Web directory for frontend extensions
WEB_DIRECTORY = os.path.join(os.path.dirname(__file__), "web", "js")

from .nodes.llm_chat import AgnesLLMChat
from .nodes.image_reverse import AgnesImageReverse
from .nodes.img2img import AgnesImageToImage
from .nodes.text2img import AgnesTextToImage
from .nodes.img2video import AgnesImageToVideo
from .nodes.text2video import AgnesTextToVideo
from .nodes.api_key_config import AgnesAPIKeyConfig

NODE_CLASS_MAPPINGS = {
    "AgnesAPIKeyConfig": AgnesAPIKeyConfig,
    "AgnesLLMChat": AgnesLLMChat,
    "AgnesImageReverse": AgnesImageReverse,
    "AgnesImageToImage": AgnesImageToImage,
    "AgnesTextToImage": AgnesTextToImage,
    "AgnesImageToVideo": AgnesImageToVideo,
    "AgnesTextToVideo": AgnesTextToVideo,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "AgnesAPIKeyConfig": "Agnes API Key Config",
    "AgnesLLMChat": "Agnes LLM Chat",
    "AgnesImageReverse": "Agnes Image Reverse Prompt",
    "AgnesImageToImage": "Agnes Image-to-Image",
    "AgnesTextToImage": "Agnes Text-to-Image",
    "AgnesImageToVideo": "Agnes Image-to-Video",
    "AgnesTextToVideo": "Agnes Text-to-Video",
}

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]
