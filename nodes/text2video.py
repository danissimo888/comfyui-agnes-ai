"""
Agnes Text-to-Video Node
========================
Generate videos from text descriptions using Agnes AI video generation models.
Uses async API with polling - can take several minutes to complete.

Output: Saves MP4 to ComfyUI's output/agnes_videos/ directory so users can
preview and download from the web UI.
"""

import os
import time

from ..api import (
    AgnesClient,
    get_api_key,
    VIDEO_MODEL,
    AVAILABLE_VIDEO_MODELS,
    DEFAULT_VIDEO_FPS,
    VIDEO_ASPECT_RATIOS,
    VIDEO_RESOLUTION_TIERS,
    compute_video_dimensions,
    duration_to_num_frames,
)

_HAS_VIDEO_TYPE = False
try:
    from comfy_api.input_impl import VideoFromFile
    _HAS_VIDEO_TYPE = True
except ImportError:
    VideoFromFile = None

_COMFYUI_OUTPUT_DIR = None


def _get_output_dir() -> str:
    """Get ComfyUI's output directory for saving video files."""
    global _COMFYUI_OUTPUT_DIR
    if _COMFYUI_OUTPUT_DIR is not None:
        return _COMFYUI_OUTPUT_DIR

    try:
        from folder_paths import get_output_directory
        base = get_output_directory()
    except ImportError:
        base = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "output")

    _COMFYUI_OUTPUT_DIR = os.path.join(base, "agnes_videos")
    return _COMFYUI_OUTPUT_DIR


class AgnesTextToVideo:
    """Agnes AI Text-to-Video node for ComfyUI."""

    CATEGORY = "Agnes AI"
    RETURN_TYPES = ("VIDEO", "STRING", "STRING",)
    RETURN_NAMES = ("video", "video_path", "filename",)
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
                    "placeholder": "A cinematic drone shot flying over a misty forest at sunrise...",
                    "tooltip": "Text description of the video to generate",
                }),
                "model": (AVAILABLE_VIDEO_MODELS, {
                    "default": VIDEO_MODEL,
                    "tooltip": "Video generation model",
                }),
                "aspect_ratio": (VIDEO_ASPECT_RATIOS, {
                    "default": "16:9",
                    "tooltip": "Video aspect ratio",
                }),
                "resolution": (VIDEO_RESOLUTION_TIERS, {
                    "default": "720p",
                    "tooltip": "Resolution tier (short-side pixel count)",
                }),
                "duration_seconds": ("FLOAT", {
                    "default": 5.0,
                    "min": 1.0,
                    "max": 18.0,
                    "step": 0.5,
                    "tooltip": "Video duration in seconds (converted to valid frame count internally)",
                }),
                "frame_rate": ("INT", {
                    "default": DEFAULT_VIDEO_FPS,
                    "min": 1,
                    "max": 60,
                    "step": 1,
                    "tooltip": "Frame rate in fps",
                }),
                "seed": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 999,
                    "step": 1,
                    "tooltip": "Random seed (0 = random). Set a fixed value for reproducible results.",
                }),
                "max_wait_seconds": ("INT", {
                    "default": 600,
                    "min": 60,
                    "max": 3600,
                    "step": 30,
                    "tooltip": "Maximum time to wait for video generation (in seconds)",
                }),
            },
            "optional": {
                "width_override": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 4096,
                    "step": 8,
                    "tooltip": "Override width in pixels (0 = use aspect_ratio/resolution). Must set both width and height.",
                }),
                "height_override": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 4096,
                    "step": 8,
                    "tooltip": "Override height in pixels (0 = use aspect_ratio/resolution). Must set both width and height.",
                }),
                "negative_prompt": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "placeholder": "blurry, low quality, distorted...",
                    "tooltip": "Things to avoid in the generated video",
                }),
            },
        }

    def generate(
        self,
        api_key: str,
        prompt: str,
        model: str = VIDEO_MODEL,
        aspect_ratio: str = "16:9",
        resolution: str = "720p",
        duration_seconds: float = 5.0,
        frame_rate: int = DEFAULT_VIDEO_FPS,
        seed: int = 0,
        max_wait_seconds: int = 600,
        width_override: int = 0,
        height_override: int = 0,
        negative_prompt: str = "",
    ):
        if not prompt.strip():
            raise ValueError("Prompt is empty.")

        if not api_key.strip():
            api_key = get_api_key()
        if not api_key.strip():
            raise ValueError("API key is required.")

        if width_override > 0 and height_override > 0:
            width = (width_override // 8) * 8
            height = (height_override // 8) * 8
        else:
            width, height = compute_video_dimensions(resolution, aspect_ratio)

        num_frames = duration_to_num_frames(duration_seconds, frame_rate)
        output_dir = _get_output_dir()

        client = AgnesClient(api_key)
        video_path = client.generate_video(
            prompt=prompt.strip(),
            mode="text2video",
            model=model,
            num_frames=num_frames,
            frame_rate=frame_rate,
            width=width,
            height=height,
            seed=seed if seed > 0 else None,
            negative_prompt=negative_prompt.strip() if negative_prompt else "",
            max_wait=max_wait_seconds,
            output_dir=output_dir,
        )

        if not video_path:
            raise RuntimeError("No video returned from API.")

        filename = os.path.basename(video_path)

        if not _HAS_VIDEO_TYPE:
            raise RuntimeError(
                "ComfyUI VIDEO type not available. Update ComfyUI to v1.7+ for video support."
            )

        video_output = VideoFromFile(video_path)
        return (video_output, video_path, filename)
