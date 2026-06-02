# ComfyUI Agnes AI Extension

ComfyUI 自定义节点插件，让你在 ComfyUI 中直接调用 Agnes AI 的全模态模型。

## 功能节点

| 节点名称 | 功能 | 模型 |
|---------|------|------|
| **Agnes API Key Config** | 🔑 持久化保存 API Key（推荐首次运行） | — |
| **Agnes LLM Chat** | LLM 文本对话 | agnes-2.0-flash |
| **Agnes Image Reverse Prompt** | 图像反推提示词 | agnes-2.0-flash (vision) |
| **Agnes Image-to-Image** | 图生图 / 图片编辑（支持多图输入） | agnes-image-2.1-flash |
| **Agnes Text-to-Image** | 文生图 | agnes-image-2.1-flash |
| **Agnes Image-to-Video** | 图生视频（支持多图/关键帧） | agnes-video-v2.0 |
| **Agnes Text-to-Video** | 文生视频 | agnes-video-v2.0 |

## 安装方法

### 方法一：Git 克隆

```bash
cd ComfyUI/custom_nodes
git clone https://github.com/yourusername/comfyui_agnes_ai.git
cd comfyui_agnes_ai
pip install -r requirements.txt
```

### 方法二：手动安装

1. 下载此插件文件夹
2. 将其放入 `ComfyUI/custom_nodes/` 目录
3. 安装依赖：`pip install -r requirements.txt`
4. 重启 ComfyUI

### 方法三：ComfyUI Manager

在 ComfyUI Manager 中搜索 "Agnes AI" 并安装。

## 获取 API Key

1. 访问 [https://platform.agnes-ai.com/](https://platform.agnes-ai.com/)
2. 注册/登录账号
3. 创建 API Key（目前免费）

## 快速开始：配置 API Key

**推荐方式** — 使用 `Agnes API Key Config` 节点：

1. 在节点菜单 → **Agnes AI** → 添加 **Agnes API Key Config**
2. 在 `api_key` 输入框填入你的 API Key（例如 `sk-xxx...`）
3. 运行一次（Ctrl+Enter / Queue Prompt）
4. Key 会自动保存到插件目录的 `api_key_config.json` 文件中
5. 之后所有其他 Agnes 节点的 `api_key` 字段留空即可自动加载

**备用方式** — 环境变量或直接输入：
- 环境变量：设置 `AGNES_API_KEY`（优先级最高）
- 直接输入：在每个节点的 `api_key` 字段手动填写（单次有效）

### API Key 加载优先级

```
环境变量 AGNES_API_KEY  >  api_key_config.json  >  节点输入框默认值
```

## 节点使用说明

### 🔑 Agnes API Key Config
- **首次运行即可**，将 API Key 持久化保存
- Key 以明文存储在 `api_key_config.json`（仅本机可访问）
- 设置 `clear_key = YES` 可清除已保存的 Key
- 输出 status 和 masked_key 供确认

### Agnes LLM Chat
- 输入文本消息，获取 LLM 回复
- 可选设置 System Prompt 控制 AI 行为
- 可调节 temperature 和 max_tokens

### Agnes Image Reverse Prompt
- 输入图片，自动分析并生成可复现该图片的提示词
- 同时输出详细版和简洁版提示词
- 可用于批量反推生成数据集的 prompt

### Agnes Image-to-Image
- 输入参考图 + 文本描述，生成编辑后的图片
- 支持最多 4 张参考图同时输入
- Strength 控制修改程度（0=尽量保持原图，1=自由发挥）

### Agnes Text-to-Image
- 纯文本描述生成图片
- 支持多种输出尺寸
- 可一次生成最多 4 张

### Agnes Image-to-Video
- 一张图或多张图生成视频动画
- 支持设置关键帧（start -> end）
- 可调节帧数、帧率、seed

### Agnes Text-to-Video
- 纯文本描述生成视频
- 支持帧数 9-441（8n+1 格式）
- 可调节帧率（8-60fps）
- 可设置 seed 复现结果
- 生成时间较长，请耐心等待

## 注意事项

- 视频生成是异步任务，通常需要 2-10 分钟
- 建议首次使用先测试文生图，确认 API Key 正常工作
- 多张图片同时生成会增加等待时间
- 免费 API 可能有频率限制

## 许可证

MIT License
