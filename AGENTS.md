# Pixelle-Video Project — AI Agent Context

## Project Overview

**Pixelle-Video** — AI-powered short video generation engine. Input a topic, automatically generates:
- Script (LLM)
- Visuals (ComfyUI/RunningHub)
- Voiceover (TTS)
- Background music (BGM)
- Final video composition

**Tech Stack**: Python 3.11+, Streamlit Web UI, ComfyUI workflows, ffmpeg video processing

---

## 🚀 Project Running Method

### Quick Start
```bash
# 1. Ensure ffmpeg installed (macOS: brew install ffmpeg)
# 2. Ensure uv installed (Python package manager)

# 3. Start Web UI (auto-install dependencies)
uv run streamlit run web/app.py

# 4. Access: http://localhost:8501
```

### Alternative: Direct Python
```bash
# If uv not available, use pip
pip install -r requirements.txt  # or pyproject.toml dependencies
streamlit run web/app.py
```

---

## 🎯 Current Focus: Qwen-TTS Local Voice Generation

### User's Priority
**Voice generation via local Qwen-TTS MLX** — Models already downloaded from ModelScope, located in local `mlx-audio` environment.

### TTS Configuration Status
Three inference modes supported:

| Mode | Status | User Priority |
|------|--------|---------------|
| **Local (Edge TTS)** | ✅ Working | Alternative fallback |
| **Qwen-TTS MLX** | 🎯 **PRIORITY** | Main focus, local models ready |
| **ComfyUI** | ✅ Working | Alternative |

### Qwen-TTS MLX Setup

**Model Location**:
- Primary: `/Users/lwz/Liwz/Code/mlx-audio/`
- Cache: `/Users/lwz/Library/Caches/com.apple.python/Users/lwz/Liwz/Code/qwen3-tts-mlx-studio/.venv/lib/python3.9/site-packages/mlx_audio`
- Downloaded from: ModelScope

**Conda Environment**: `audio` (contains mlx-audio)

**Configuration** (`config.yaml` under `comfyui.tts`):
```yaml
comfyui:
  tts:
    inference_mode: qwen_tts  # Use local Qwen-TTS MLX
    qwen_tts:
      conda_env: audio        # Conda env with mlx-audio
      speaker: vivian         # Default speaker
      language: Chinese       # Language setting
      speed: 1.0              # Speech speed (0.5-2.0)
      temperature: 0.9        # Stability control (0.5-1.5)
      instruct: ""            # Emotion/style instruction (optional)
      quant: bf16             # Model quantization
```

**UI Parameters** (Web Interface):
- Speaker selector (dropdown)
- Speed slider (0.5x - 2.0x)
- Temperature slider (0.5 - 1.5, lower=stable, higher=varied)
- Instruct input (emotion/style in natural language)

**Implementation Files**:
- `pixelle_video/services/tts_service.py` — TTS service with `_call_qwen_tts()`
- `pixelle_video/services/qwen_tts_runner.py` — MLX execution script
- `pixelle_video/config/schema.py` — `QwenTTSConfig` model
- `web/components/style_config.py` — UI controls for qwen-tts

---

## 🎬 Media Generation: Aliyun DashScope (通义万相视频生成)

### Architecture Overview

**Target Workflow**: LLM + Local TTS + Aliyun Media API

```
User Input → LLM Script → Qwen-TTS (Local) → Aliyun Video → Final Video
    ↓           ↓              ↓                ↓              ↓
  Topic    通义千问/GPT    MLX本地推理      通义万相API     ffmpeg合成
```

### Media Generation Strategy

**✅ No Local GPU Required** — All media generation uses **Aliyun DashScope API**:

| Service | Type | Models | Status |
|---------|------|--------|--------|
| **Aliyun DashScope** | Video | wan2.6-t2v, wan2.7-t2v (推荐) | ✅ **Primary** |
| **RunningHub** | Image/Video | FLUX, WAN 2.1 | ⚠️ Alternative (需要API key) |
| **Selfhost ComfyUI** | Image/Video | Custom | ⚠️ Fallback (需要本地GPU) |

### Aliyun DashScope Integration

**Configuration** (`config.yaml`):
```yaml
aliyun:
  api_key: "your-dashscope-api-key"  # Required (通义千问API Key)
  model: "wan2.7-t2v"                # 推荐使用最新模型
  timeout: 600                        # API超时（秒）
  max_wait_attempts: 60               # 最大轮询次数
```

**Features**:
- ✅ **零本地GPU** — 完全云端生成
- ✅ **通义万相视频生成** — 文生视频 (wan2.7-t2v推荐)
- ✅ **智能改写** — 自动优化prompt
- ✅ **多分辨率** — 480P/720P/1080P
- ✅ **多比例** — 16:9, 9:16, 1:1 (自动匹配模板)

**Models**:
- `wan2.7-t2v` — **推荐**，最新文生视频模型
- `wan2.6-t2v` — 文生视频
- `wan2.6-i2v` — 图生视频

**Implementation**:
- `pixelle_video/services/aliyun_video.py` — 阿里云视频服务
- `workflows/aliyun/video_wan2.7.json` — Workflow配置

**Workflow Usage**:
```python
# 视频生成 (通义万相)
result = await pixelle_video.media(
    prompt="a cat playing with a ball",
    workflow="aliyun/video_wan2.7.json",
    media_type="video",
    duration=5.0,  # 2-15秒
    ratio="9:16"   # 自动匹配模板
)
```

### RunningHub (Alternative - 需要API Key)

**仅作为备选方案**，用户优先使用阿里云：

```yaml
comfyui:
  runninghub_api_key: "your-key"  # Optional alternative
  
  image:
    default_workflow: runninghub/image_flux.json  # FLUX图片生成
  
  video:
    default_workflow: runninghub/video_wan2.1_fusionx.json  # WAN 2.1视频
```

---

## 🔧 Complete Production Workflow

### Full Pipeline Configuration

```yaml
# config.yaml — Complete setup for cloud-based production

# 1. LLM Script Generation (通义千问 recommended)
llm:
  api_key: "sk-xxx"
  base_url: "https://dashscope.aliyuncs.com/compatible-mode/v1"
  model: "qwen-max"

# 2. TTS Voice Generation (Local Qwen-TTS MLX)
comfyui:
  tts:
    inference_mode: qwen_tts
    qwen_tts:
      conda_env: audio
      speaker: vivian
      speed: 1.0
      temperature: 0.9

# 3. Media Generation (Aliyun DashScope - Primary)
aliyun:
  api_key: "your-dashscope-key"  # 通义万相视频生成
  model: "wan2.7-t2v"            # 推荐最新模型
  timeout: 600
  max_wait_attempts: 60

# 4. Image Generation (RunningHub as alternative)
comfyui:
  runninghub_api_key: "your-key"  # Optional for image generation
  
  image:
    default_workflow: runninghub/image_flux.json
  
  video:
    default_workflow: aliyun/video_wan2.7.json  # 使用阿里云
```

### Production Requirements Checklist

- ✅ **LLM API Key**: 通义千问/GPT/OpenAI compatible API
- ✅ **Qwen-TTS Local**: Conda env `audio` with mlx-audio + models
- ✅ **Aliyun API Key**: DashScope API (通义万相视频生成)
- ⚠️ **ffmpeg**: Local installation (video composition)
- ⚠️ **Streamlit**: Web UI framework

### No Local GPU Required

**User's Goal**: Generate short videos without local GPU infrastructure:
1. LLM script via API (通义千问 recommended)
2. TTS voice via local Qwen-TTS MLX (already setup)
3. Videos via Aliyun DashScope API (通义万相)
4. Composition via ffmpeg (lightweight local processing)

---

## 📁 Project Structure

```
Pixelle-Video/
├── web/
│   ├── app.py                  # Streamlit entry point
│   └── components/
│       └── style_config.py     # TTS/Image UI components
├── pixelle_video/
│   ├── config/
│   │   ├── schema.py           # Pydantic config models
│   │   └ config_manager.py     # Config loader
│   ├── services/
│   │   ├── tts_service.py      # TTS service (Edge/Qwen/ComfyUI)
│   │   ├── qwen_tts_runner.py  # Qwen-TTS MLX runner
│   │   ├── media.py            # Image/video generation
│   │   └ frame_processor.py   # Frame rendering
│   └── tts_voices.py           # Voice/speaker definitions
├── config.example.yaml         # Configuration template
├── templates/                  # Video templates (HTML)
├── workflows/                  # ComfyUI workflows
├── bgm/                        # Background music
├── output/                     # Generated videos
└── pyproject.toml              # Python dependencies
```

---

## 🔧 Key Dependencies

- `streamlit>=1.40.0` — Web UI framework
- `edge-tts==7.2.7` — Edge TTS for local fallback
- `comfykit>=0.1.12` — ComfyUI workflow execution
- `fastmcp>=2.0.0` — MCP server integration
- `ffmpeg-python>=0.2.0` — Video processing
- `openai>=2.6.0` — LLM API client

**Optional (Qwen-TTS MLX)**:
- `mlx-audio` — MLX-based TTS (in conda env `audio`)
- Local models from ModelScope

---

## 🎨 Web UI Workflow

1. **Left Column**: Content input (topic/script, BGM selection)
2. **Middle Column**: 
   - TTS settings (mode selector + parameters)
   - Visual settings (template, image/video workflow)
3. **Right Column**: Video generation + preview

**System Config**: LLM API + ComfyUI settings (expandable panel)

---

## ⚠️ Important Notes

### TTS Mode Priority
- User wants **Qwen-TTS MLX** as primary TTS method
- Models already downloaded, don't suggest re-downloading
- If issues arise, debug existing setup before suggesting alternatives

### Config Management
- User config in `config.yaml` (never commit to git)
- Template: `config.example.yaml`
- Hot-reload supported via `config_manager`

### Workflow Files
- `workflows/*.json` — ComfyUI workflows
- Naming: `tts_*.json` (TTS), `image_*.json` (images), `video_*.json` (videos)
- Prefix: `selfhost/` (local ComfyUI) or `runninghub/` (cloud)

---

## 📝 Recent Changes (2026-05-08)

- ✅ Added Qwen-TTS MLX support with UI configuration
- ✅ Implemented temperature + instruct parameters in UI
- ✅ Added `qwen_tts_runner.py` for MLX execution
- ✅ Updated config schema with `QwenTTSConfig`
- ✅ All TTS parameters now configurable from Web UI

---

# context-mode — MANDATORY routing rules

context-mode MCP tools available. Rules protect context window from flooding. One unrouted command dumps 56 KB into context.

## Think in Code — MANDATORY

Analyze/count/filter/compare/search/parse/transform data: **write code** via `context-mode_ctx_execute(language, code)`, `console.log()` only the answer. Do NOT read raw data into context. PROGRAM the analysis, not COMPUTE it. Pure JavaScript — Node.js built-ins only (`fs`, `path`, `child_process`). `try/catch`, handle `null`/`undefined`. One script replaces ten tool calls.

## BLOCKED — do NOT attempt

### curl / wget — BLOCKED
Shell `curl`/`wget` intercepted and blocked. Do NOT retry.
Use: `context-mode_ctx_fetch_and_index(url, source)` or `context-mode_ctx_execute(language: "javascript", code: "const r = await fetch(...)")`

### Inline HTTP — BLOCKED
`fetch('http`, `requests.get(`, `requests.post(`, `http.get(`, `http.request(` — intercepted. Do NOT retry.
Use: `context-mode_ctx_execute(language, code)` — only stdout enters context

### Direct web fetching — BLOCKED
Use: `context-mode_ctx_fetch_and_index(url, source)` then `context-mode_ctx_search(queries)`

## REDIRECTED — use sandbox

### Shell (>20 lines output)
Shell ONLY for: `git`, `mkdir`, `rm`, `mv`, `cd`, `ls`, `npm install`, `pip install`.
Otherwise: `context-mode_ctx_batch_execute(commands, queries)` or `context-mode_ctx_execute(language: "shell", code: "...")`

### File reading (for analysis)
Reading to **edit** → reading correct. Reading to **analyze/explore/summarize** → `context-mode_ctx_execute_file(path, language, code)`.

### grep / search (large results)
Use `context-mode_ctx_execute(language: "shell", code: "grep ...")` in sandbox.

## Tool selection

0. **MEMORY**: `context-mode_ctx_search(sort: "timeline")` — after resume, check prior context before asking user.
1. **GATHER**: `context-mode_ctx_batch_execute(commands, queries)` — runs all commands, auto-indexes, returns search. ONE call replaces 30+. Each command: `{label: "header", command: "..."}`.
2. **FOLLOW-UP**: `context-mode_ctx_search(queries: ["q1", "q2", ...])` — all questions as array, ONE call (default relevance mode).
3. **PROCESSING**: `context-mode_ctx_execute(language, code)` | `context-mode_ctx_execute_file(path, language, code)` — sandbox, only stdout enters context.
4. **WEB**: `context-mode_ctx_fetch_and_index(url, source)` then `context-mode_ctx_search(queries)` — raw HTML never enters context.
5. **INDEX**: `context-mode_ctx_index(content, source)` — store in FTS5 for later search.

## Parallel I/O batches

For multi-URL fetches or multi-API calls, **always** include `concurrency: N` (1-8):

- `context-mode_ctx_batch_execute(commands: [3+ network commands], concurrency: 5)` — gh, curl, dig, docker inspect, multi-region cloud queries
- `context-mode_ctx_fetch_and_index(requests: [{url, source}, ...], concurrency: 5)` — multi-URL batch fetch

**Use concurrency 4-8** for I/O-bound work (network calls, API queries). **Keep concurrency 1** for CPU-bound (npm test, build, lint) or commands sharing state (ports, lock files, same-repo writes).

GitHub API rate-limit: cap at 4 for `gh` calls.

## Output

Terse like caveman. Technical substance exact. Only fluff die.
Drop: articles, filler (just/really/basically), pleasantries, hedging. Fragments OK. Short synonyms. Code unchanged.
Pattern: [thing] [action] [reason]. [next step]. Auto-expand for: security warnings, irreversible actions, user confusion.
Write artifacts to FILES — never inline. Return: file path + 1-line description.
Descriptive source labels for `search(source: "label")`.

## Session Continuity

Skills, roles, and decisions persist for the entire session. Do not abandon them as the conversation grows.

## Memory

Session history is persistent and searchable. On resume, search BEFORE asking the user:

| Need | Command |
|------|---------|
| What did we decide? | `context-mode_ctx_search(queries: ["decision"], source: "decision", sort: "timeline")` |
| What constraints exist? | `context-mode_ctx_search(queries: ["constraint"], source: "constraint")` |

DO NOT ask "what were we working on?" — SEARCH FIRST.
If search returns 0 results, proceed as a fresh session.

## ctx commands

| Command | Action |
|---------|--------|
| `ctx stats` | Call `stats` MCP tool, display full output verbatim |
| `ctx doctor` | Call `doctor` MCP tool, run returned shell command, display as checklist |
| `ctx upgrade` | Call `upgrade` MCP tool, run returned shell command, display as checklist |
| `ctx purge` | Call `purge` MCP tool with confirm: true. Warns before wiping knowledge base. |

After /clear or /compact: knowledge base and session stats preserved. Use `ctx purge` to start fresh.
