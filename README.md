# ComfyUI Agnes AI Extension

Custom node plugin for ComfyUI that lets you call Agnes AI's multimodal models directly within ComfyUI.

## Nodes

| Node Name | Function | Model |
|---------|------|------|
| **Agnes API Key Config** | Persistently save API Key (recommended on first run) | — |
| **Agnes LLM Chat** | LLM text conversation | agnes-2.0-flash |
| **Agnes Image Reverse Prompt** | Image-to-prompt analysis | agnes-2.0-flash (vision) |
| **Agnes Image-to-Image** | Image editing (supports multi-image input) | agnes-image-2.1-flash |
| **Agnes Text-to-Image** | Text-to-image generation | agnes-image-2.1-flash |
| **Agnes Image-to-Video** | Image-to-video (supports multi-image/keyframes) | agnes-video-v2.0 |
| **Agnes Text-to-Video** | Text-to-video generation | agnes-video-v2.0 |

## Installation

### Option 1: Git Clone

```bash
cd ComfyUI/custom_nodes
git clone https://github.com/danissimo888/comfyui-agnes-ai.git
cd comfyui-agnes-ai
pip install -r requirements.txt
```

### Option 2: Manual Install

1. Download this plugin folder
2. Place it in the `ComfyUI/custom_nodes/` directory
3. Install dependencies: `pip install -r requirements.txt`
4. Restart ComfyUI

## Getting an API Key

1. Visit [https://platform.agnes-ai.com/](https://platform.agnes-ai.com/)
2. Register / Log in
3. Create an API Key (currently free)

## Quick Start: Configure API Key

**Recommended** — Use the `Agnes API Key Config` node:

1. In the node menu → **Agnes AI** → add **Agnes API Key Config**
2. Enter your API Key in the `api_key` field (e.g. `sk-xxx...`)
3. Run once (Ctrl+Enter / Queue Prompt)
4. The key is automatically saved to `api_key_config.json` in the plugin directory
5. Leave the `api_key` field empty on all other Agnes nodes — they will auto-load it

**Alternative** — Environment variable or direct input:
- Environment variable: set `AGNES_API_KEY` (highest priority)
- Direct input: manually enter the key in each node's `api_key` field

### API Key Loading Priority

```
Environment variable AGNES_API_KEY  >  api_key_config.json  >  Runtime fallback load  >  Node input field
```

> Note: The `api_key` widget always shows a gray placeholder `sk-...` and will never display the actual key in plain text.

## Node Usage Guide

### Agnes API Key Config
- **Run once** to persistently save your API Key
- Key is stored in plain text in `api_key_config.json` (local access only)
- Set `clear_key = YES` to delete the saved key
- Outputs `status` and `masked_key` for confirmation

### Agnes LLM Chat
- Input a text message, get an LLM response
- Optionally set a System Prompt to control AI behavior
- Adjustable temperature (0.0-2.0) and max_tokens

### Agnes Image Reverse Prompt
- Input an image, automatically analyze and generate a reproducible prompt
- Outputs both a detailed and a brief version of the prompt

### Agnes Image-to-Image (Multi-Image Input)
- Input reference image(s) + text description to generate edited images
- **Supports up to 4 reference images simultaneously**
- **Quality selection**: 1K / 2K / 4K
- **Aspect ratios**: 1:1, 2:3, 3:4, 4:5, 9:16, 9:21, 3:2, 4:3, 5:4, 16:9, 21:9
- Strength controls modification degree (0 = keep original, 1 = full creative freedom)
- Output: `images` (IMAGE) + `resolution` (STRING)

### Agnes Text-to-Image
- Generate images from pure text descriptions
- **Quality selection**: 1K / 2K / 4K
- **Aspect ratios**: 1:1, 2:3, 3:4, 4:5, 9:16, 9:21, 3:2, 4:3, 5:4, 16:9, 21:9
- Generate up to 4 images at once
- Output: `images` (IMAGE) + `resolution` (STRING)

### Agnes Image-to-Video (Multi-Image/Keyframes)
- Generate video animation from one or more images
- Supports keyframe setup (start -> end)
- **Quality selection**: 1K / 2K
- **Aspect ratios**: 1:1, 2:3, 3:4, 4:5, 9:16, 9:21, 3:2, 4:3, 5:4, 16:9, 21:9
- Adjustable frame count (9-441, 8n+1 format) and frame rate (8-60fps)
- Output: `video` (VIDEO) + `resolution` (STRING)
- Videos saved to `ComfyUI/output/agnes_videos/` directory

### Agnes Text-to-Video
- Generate videos from pure text descriptions
- **Quality selection**: 1K / 2K
- **Aspect ratios**: 1:1, 2:3, 3:4, 4:5, 9:16, 9:21, 3:2, 4:3, 5:4, 16:9, 21:9
- Adjustable frame count (9-441, 8n+1), frame rate (8-60fps), and seed
- Output: `video` (VIDEO) + `resolution` (STRING)
- Videos saved to `ComfyUI/output/agnes_videos/` directory

## Video Output Type

Video nodes automatically select the output type by priority:

| Environment | Output Type | Description |
|------|---------|------|
| ComfyUI v1.7+ built-in | `VIDEO` | Native VideoFromFile, can connect directly to `SaveVideo` |
| VHS installed | `VHS_VIDEOINFO` | Dict format, compatible with video workflows |
| Neither | `STRING` | File path string |

## Quality x Aspect Ratio Reference

### Image Generation (1K / 2K / 4K)

| Ratio | 1K | 2K | 4K |
|------|------|------|------|
| 1:1 | 1024x1024 | 2048x2048 | 4096x4096 |
| 16:9 | 1816x1024 | 3640x2048 | 7280x4096 |
| 9:16 | 1024x1816 | 2048x3640 | 4096x7280 |
| 21:9 | 2384x1024 | 4776x2048 | 9552x4096 |
| 9:21 | 1024x2384 | 2048x4776 | 4096x9552 |

### Video Generation (1K / 2K)

| Ratio | 1K | 2K |
|------|------|------|
| 1:1 | 1024x1024 | 2048x2048 |
| 16:9 | 1816x1024 | 3640x2048 |
| 9:16 | 1024x1816 | 2048x3640 |

## Error Handling

- **API 5xx errors** (502/503/504/524): Auto-retry 3 times with exponential backoff (3s/6s/12s)
- **Connection timeout**: Auto-retry with descriptive error messages
- **Cloudflare error pages**: Automatically parsed into readable messages
- **CUDA OOM (server-side)**: Automatically detected with suggestions to reduce parameters

## Project Structure

```
comfyui_agnes_ai/
├── __init__.py              # Plugin entry point, registers 7 nodes
├── config.yaml              # Default configuration
├── requirements.txt         # Dependencies
├── README.md                # This document
├── api/
│   └── __init__.py          # AgnesClient API wrapper (Chat / Image / Video)
├── nodes/
│   ├── __init__.py
│   ├── api_key_config.py    # API Key persistence node
│   ├── llm_chat.py          # LLM chat
│   ├── image_reverse.py     # Image reverse prompt
│   ├── text2img.py          # Text-to-image
│   ├── img2img.py           # Image-to-image (multi-image)
│   ├── text2video.py        # Text-to-video
│   └── img2video.py         # Image-to-video (multi-image/keyframes)
└── web/js/                  # Frontend extension directory (reserved)
```

## Changelog

### v1.6.0 — Native VIDEO Type Output
- Video node output supports ComfyUI native `VIDEO` type (v1.7+)
- Three-level detection chain: comfy_api VIDEO → VHS_VIDEOINFO → STRING
- Fixed `remixed_from_video_id` field name (actual URL field returned by API)
- VIDEO type errors now raise instead of returning string (prevents downstream `SaveVideo` crash)

### v1.4.0 — API Error Handling Improvements
- HTML error pages (Cloudflare 5xx) automatically parsed into readable messages
- 5xx/429 auto-retry 3 times, connection timeout auto-retry
- Chat / Image / Video APIs all use unified retry mechanism

### v1.3.0 — Image Node Quality & Resolution
- `text2img` / `img2img` now support quality (1K/2K/4K) + aspect_ratio (11 options)
- Auto-calculate actual pixels (aligned to multiples of 8)
- Added `resolution` output

### v1.2.0 — Video Output Path Optimization
- Videos now save to `ComfyUI/output/agnes_videos/` instead of system temp directory
- `generate_video()` added `output_dir` parameter

### v1.1.0 — API Key Persistence
- Added `AgnesAPIKeyConfig` node, key saved to `api_key_config.json`
- `api_key` widget unified to empty string, auto-loads from config at runtime

### v1.0.0 — Initial Release
- 7 nodes: API Key Config, LLM Chat, Image Reverse, Text-to-Image, Image-to-Image, Text-to-Video, Image-to-Video

## Notes

- Video generation is asynchronous and typically takes 2-6 minutes
- Free API may experience queuing (503) or GPU OOM (500) during peak hours — reducing quality/frames improves success rate
- Recommended to test text-to-image first to confirm your API Key works
- Generating multiple images simultaneously increases wait time

## License

MIT License
