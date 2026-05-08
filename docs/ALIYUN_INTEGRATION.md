# 阿里云万相API集成指南

## 📋 目录

1. [概述](#概述)
2. [代码集成详解](#代码集成详解)
3. [配置方法](#配置方法)
4. [运行方法](#运行方法)
5. [核心流程图](#核心流程图)
6. [关键入口函数](#关键入口函数)
7. [质量优化建议](#质量优化建议)
8. [成本分析](#成本分析)

---

## 概述

### 什么是阿里云万相API集成？

Pixelle-Video 工程原本支持 ComfyUI 和 RunningHub 进行视频生成，我们通过以下架构扩展，实现了阿里云万相视频生成 API 的无缝集成：

- **无需本地部署 ComfyUI**
- **直接调用阿里云云端API**
- **自动编排多镜头动态视频**
- **保留Pipeline编排能力**

### 核心价值

✅ **真正的AI动态视频**：每个镜头都是阿里云万相生成的动态AI视频，不是静态图片拼接
✅ **Pipeline自动编排**：从主题到最终视频全自动，体现工程核心价值
✅ **成本可控**：按秒计费，720P分辨率成本合理
✅ **易于集成**：最小化代码改动，遵循工程现有架构

---

## 代码集成详解

### 集成架构

```
原有架构：
config.yaml → PixelleVideoCore → Pipeline → MediaService → ComfyKit → ComfyUI/RunningHub

扩展架构：
config.yaml → PixelleVideoCore → Pipeline → MediaService → AliyunVideoService → 阿里云万相API
                                                              ↓
                                                         ComfyKit (保留)
```

### 新增文件清单

#### 1. 阿里云视频服务核心实现

**文件**: `pixelle_video/services/aliyun_video.py`

**核心代码结构**:
```python
@dataclass
class AliyunVideoResult:
    url: str           # 生成的视频URL
    duration: float    # 实际时长
    task_id: str       # 任务ID
    model: str         # 使用的模型

class AliyunVideoService:
    BASE_URL = "https://dashscope.aliyuncs.com"
    API_ENDPOINT = "/api/v1/services/aigc/video-generation/video-synthesis"
    
    async def generate(
        self,
        prompt: str,
        duration: int = 5,
        resolution: str = "720P",
        ratio: str = "16:9",      # 新增：宽高比参数
        prompt_extend: bool = True,
        seed: Optional[int] = None
    ) -> AliyunVideoResult:
        # 1. 提交异步任务
        task_id = await self._submit_task(...)
        
        # 2. 轮询等待完成
        video_url, duration = await self._wait_for_completion(task_id)
        
        # 3. 返回结果
        return AliyunVideoResult(url=video_url, ...)
```

**关键实现逻辑**:
- 异步提交任务 → 获取task_id
- 10秒间隔轮询状态 → 等待SUCCEEDED
- 下载视频URL → 返回结果

#### 2. 工作流Wrapper配置

**文件**: `workflows/aliyun/video_wan2.7.json`

```json
{
  "source": "aliyun",
  "model": "wan2.7-t2v",
  "description": "阿里云万相文生视频 - wan2.7-t2v模型（最新版）",
  "parameters": {
    "duration": 5,
    "resolution": "720P",
    "prompt_extend": true
  }
}
```

**Wrapper格式设计**：
- 参考 RunningHub 的 wrapper 格式
- 通过 `source` 字段标识服务来源
- MediaService 根据 `source` 分支执行

---

### 修改文件清单

#### 1. 配置Schema扩展

**文件**: `pixelle_video/config/schema.py`

**新增配置类**:
```python
class AliyunConfig(BaseModel):
    api_key: str = Field(default="", description="阿里云DashScope API Key")
    model: str = Field(default="wan2.7-t2v", description="视频生成模型")
    timeout: int = Field(default=600, ge=60, le=1200, description="API超时时间（秒）")
    max_wait_attempts: int = Field(default=60, ge=10, le=120, description="最大等待轮询次数")

class PixelleVideoConfig(BaseModel):
    project_name: str = Field(default="Pixelle-Video")
    llm: LLMConfig = Field(default_factory=LLMConfig)
    aliyun: AliyunConfig = Field(default_factory=AliyunConfig)  # 新增
    comfyui: ComfyUIConfig = Field(default_factory=ComfyUIConfig)
    template: TemplateConfig = Field(default_factory=TemplateConfig)
```

#### 2. MediaService集成

**文件**: `pixelle_video/services/media.py`

**关键分支逻辑**:
```python
async def __call__(self, prompt: str, workflow: Optional[str] = None, ...):
    # 1. 解析workflow wrapper
    workflow_info = self._resolve_workflow(workflow)
    
    # 2. 特殊处理阿里云来源
    if workflow_info["source"] == "aliyun":
        # 3. 获取阿里云服务实例
        aliyun_service = self.core.get_aliyun_video_service()
        
        # 4. 自动检测ratio（宽高比）
        template_path = self.core.config.get("template", {}).get("default_template", "")
        if "1080x1920" in template_path:
            ratio = "9:16"   # 竖屏
        elif "1920x1080" in template_path:
            ratio = "16:9"   # 横屏
        else:
            ratio = "1:1"    # 方形
        
        # 5. 调用阿里云API
        result = await aliyun_service.generate(
            prompt=prompt,
            duration=int(duration) if duration else 5,
            resolution="720P",
            ratio=ratio,              # 自动匹配模板
            prompt_extend=True
        )
        
        return MediaResult(
            media_type="video",
            url=result.url,
            duration=result.duration
        )
    
    # 6. 默认ComfyKit执行路径（保留）
    kit = await self.core._get_or_create_comfykit()
    ...
```

#### 3. ComfyBaseService扩展

**文件**: `pixelle_video/services/comfy_base_service.py`

**wrapper解析逻辑**:
```python
def _parse_workflow_file(self, workflow_path: Path) -> dict:
    content = json.loads(workflow_path.read_text())
    
    workflow_info = {
        "key": workflow_path.stem,
        "path": str(workflow_path),
        "source": "selfhost",  # 默认
    }
    
    # 检查wrapper格式（RunningHub, Aliyun等）
    if "source" in content:
        workflow_info["source"] = content["source"]
        
        # 阿里云wrapper识别
        if content["source"] == "aliyun":
            workflow_info["source"] = "aliyun"
        
        # RunningHub wrapper识别
        elif "workflow_id" in content:
            workflow_info["workflow_id"] = content["workflow_id"]
    
    return workflow_info
```

#### 4. PixelleVideoCore初始化

**文件**: `pixelle_video/service.py`

**服务实例化逻辑**:
```python
class PixelleVideoCore:
    def __init__(self, config_path: str = "config.yaml"):
        self.config = config_manager.config.to_dict()
        
        # Aliyun video service (for direct API calls)
        self._aliyun_video: Optional[AliyunVideoService] = None
        
        # Core services (initialized in initialize())
        ...
    
    async def initialize(self):
        # 1. 初始化LLM/TTS服务
        self.llm = LLMService(self.config)
        self.tts = TTSService(self.config, core=self)
        
        # 2. 初始化阿里云服务（条件初始化）
        aliyun_config = self.config.get("aliyun", {})
        if aliyun_config.get("api_key"):
            self._aliyun_video = AliyunVideoService(
                api_key=aliyun_config["api_key"],
                model=aliyun_config.get("model", "wan2.7-t2v"),
                timeout=aliyun_config.get("timeout", 600),
                max_wait_attempts=aliyun_config.get("max_wait_attempts", 60)
            )
            logger.info(f"✅ Aliyun video service initialized (model: {aliyun_config.get('model')})")
        
        # 3. 初始化Media服务
        self.media = MediaService(self.config, core=self)
        
        # 4. 注册Pipelines
        self.pipelines = {
            "standard": StandardPipeline(self),
            "custom": CustomPipeline(self),
            "asset_based": AssetBasedPipeline(self),
        }
    
    def get_aliyun_video_service(self) -> Optional[AliyunVideoService]:
        return self._aliyun_video
```

---

## 配置方法

### 1. config.yaml配置

**完整配置示例**:
```yaml
# ==================== LLM Configuration ====================
llm:
  api_key: "sk-your-qwen-api-key"
  base_url: "https://dashscope.aliyuncs.com/compatible-mode/v1"
  model: "qwen-max"

# ==================== Aliyun Video API Configuration ====================
aliyun:
  api_key: "sk-your-dashscope-api-key"
  model: "wan2.7-t2v"
  timeout: 600
  max_wait_attempts: 60

# ==================== ComfyUI Configuration ====================
comfyui:
  comfyui_url: http://127.0.0.1:8188
  comfyui_api_key: ""
  runninghub_api_key: ""
  runninghub_concurrent_limit: 1
  
  video:
    default_workflow: "aliyun/video_wan2.7.json"
    prompt_prefix: ""

# ==================== Template Configuration ====================
template:
  default_template: "1080x1920/video_default.html"
```

### 2. 关键配置项说明

| 配置项 | 必填 | 说明 |
|-------|------|------|
| `llm.api_key` | ✅ | 通义千问API Key，用于文案生成 |
| `llm.base_url` | ✅ | 通义千问API地址 |
| `llm.model` | ✅ | 模型名称（qwen-max推荐） |
| `aliyun.api_key` | ✅ | 阿里云DashScope API Key |
| `aliyun.model` | ⚪ | 视频模型（wan2.7-t2v默认） |
| `aliyun.timeout` | ⚪ | API超时时间（默认600秒） |
| `template.default_template` | ⚪ | 模板路径（影响ratio自动选择） |

### 3. API Key获取方法

#### 通义千问API Key
1. 访问：https://dashscope.aliyuncs.com/
2. 注册/登录阿里云账号
3. 开通DashScope服务
4. 获取API Key（sk-开头）

#### 阿里云万相API Key
- **同一个Key**：DashScope API Key 同时支持通义千问和万相视频生成
- **权限**：需开通视频生成服务权限

---

## 运行方法

### 1. 环境准备

#### 安装依赖
```bash
# 使用uv管理依赖（推荐）
uv sync

# 或使用pip
pip install -e .
```

#### 安装系统依赖
```bash
# ffmpeg（视频处理）
sudo apt install ffmpeg  # Ubuntu/Debian
# 或
brew install ffmpeg      # macOS

# playwright浏览器
playwright install chromium
```

### 2. 基础运行

#### Python API调用
```python
from pixelle_video import pixelle_video
import asyncio

async def main():
    # 1. 初始化
    await pixelle_video.initialize()
    
    # 2. 生成视频
    result = await pixelle_video.generate_video(
        text="小狐狸的星空之旅",
        pipeline="standard",
        n_scenes=5,
        frame_template="1080x1920/video_default.html",
        media_workflow="aliyun/video_wan2.7.json"
    )
    
    print(f"视频路径: {result.video_path}")
    print(f"视频时长: {result.duration}秒")
    
    # 3. 清理
    await pixelle_video.cleanup()

asyncio.run(main())
```

#### Web UI运行
```bash
# Streamlit Web界面
streamlit run pixelle_video/webui/app.py

# 或使用快捷命令
pixelle-video
pvideo
```

#### CLI命令行
```bash
# 命令行工具
pixelle-video --text "森林精灵的奇遇" --n-scenes 3
```

### 3. 参数说明

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `text` | 必填 | 视频主题/故事梗概 |
| `pipeline` | "standard" | Pipeline类型（standard/custom/asset_based） |
| `n_scenes` | 5 | 镜头数量 |
| `frame_template` | "1080x1920/video_default.html" | 视频模板 |
| `media_workflow` | "aliyun/video_wan2.7.json" | 媒体生成workflow |

---

## 核心流程图

### Standard Pipeline 8步骤流程

```
┌─────────────────────────────────────────────────────────┐
│  Phase 1: Preparation                                   │
├─────────────────────────────────────────────────────────┤
│  Step 1: setup_environment                              │
│    → 创建任务目录                                         │
│    → 初始化上下文                                         │
├─────────────────────────────────────────────────────────┤
│  Phase 2: Content Creation                              │
├─────────────────────────────────────────────────────────┤
│  Step 2: generate_content                               │
│    → LLM生成文案（通义千问）                               │
│    → 生成n_scenes条narrations                            │
│                                                          │
│  Step 3: determine_title                                │
│    → 自动生成标题                                         │
├─────────────────────────────────────────────────────────┤
│  Phase 3: Visual Planning                               │
├─────────────────────────────────────────────────────────┤
│  Step 4: plan_visuals                                   │
│    → LLM生成image_prompts（英文视觉描述）                  │
│    → 检测模板类型（static/video）                         │
│                                                          │
│  Step 5: initialize_storyboard                          │
│    → 创建Storyboard配置                                   │
│    → 创建Frames对象                                       │
├─────────────────────────────────────────────────────────┤
│  Phase 4: Asset Production                              │
├─────────────────────────────────────────────────────────┤
│  Step 6: produce_assets                                 │
│    → 循环处理每个Frame                                    │
│      ├─ 生成音频（TTS）                                   │
│      ├─ 生成视频（阿里云万相API）                          │
│      ├─ HTML模板渲染                                      │
│      └─ 创建视频片段                                      │
│    → 并行/串行处理（根据配置）                             │
├─────────────────────────────────────────────────────────┤
│  Phase 5: Post Production                               │
├─────────────────────────────────────────────────────────┤
│  Step 7: post_production                                │
│    → ffmpeg拼接所有片段                                   │
│    → 生成final.mp4                                       │
│                                                          │
│  Step 8: finalize                                       │
│    → 持久化任务元数据                                     │
│    → 保存Storyboard                                      │
│    → 返回VideoGenerationResult                           │
└─────────────────────────────────────────────────────────┘
```

### 阿里云API调用子流程

```
produce_assets (Frame处理)
    │
    ├─ 1. generate_audio (TTS)
    │     → Edge-TTS生成音频
    │     → 获取音频时长（作为视频目标时长）
    │
    ├─ 2. generate_media (阿里云视频)
    │     │
    │     ├─ MediaService.__call__()
    │     │     ├─ 解析workflow (aliyun/video_wan2.7.json)
    │     │     ├─ 检测source == "aliyun"
    │     │     ├─ 自动选择ratio（根据模板）
    │     │     │
    │     ├─ AliyunVideoService.generate()
    │     │     ├─ _submit_task()
    │     │     │     ├─ 构建payload (resolution, ratio, duration)
    │     │     │     ├─ POST API提交任务
    │     │     │     ├─ 返回task_id
    │     │     │
    │     │     ├─ _wait_for_completion()
    │     │     │     ├─ 每10秒轮询状态
    │     │     │     ├─ 等待SUCCEEDED
    │     │     │     ├─ 获取视频URL
    │     │     │
    │     │     └─ 返回AliyunVideoResult
    │     │           (url, duration, task_id)
    │     │
    │     └─ MediaResult
    │           (media_type="video", url, duration)
    │
    ├─ 3. compose_frame (HTML渲染)
    │     → Playwright渲染video_default.html
    │     → 生成composed.png
    │
    └─ 4. create_video_segment (视频片段)
          → ffmpeg叠加HTML层到视频
          → 合并音频
          → 生成XX_segment.mp4
```

---

## 关键入口函数

### 1. 主入口：PixelleVideoCore

**位置**: `pixelle_video/service.py`

```python
class PixelleVideoCore:
    def __init__(self, config_path: str = "config.yaml"):
        """初始化核心引擎"""
        
    async def initialize(self):
        """初始化所有服务"""
        
    async def generate_video(
        self,
        text: str,
        pipeline: str = "standard",
        **kwargs
    ) -> VideoGenerationResult:
        """视频生成主入口"""
        
    async def llm(self, prompt: str) -> str:
        """LLM文本生成"""
        
    async def tts(self, text: str) -> str:
        """TTS语音合成"""
        
    async def media(
        self,
        prompt: str,
        workflow: Optional[str] = None,
        media_type: str = "image"
    ) -> MediaResult:
        """媒体生成入口"""
```

### 2. Pipeline入口：StandardPipeline

**位置**: `pixelle_video/pipelines/standard.py`

```python
class StandardPipeline(LinearPipeline):
    async def __call__(
        self,
        text: str,
        progress_callback: Optional[Callable] = None,
        **kwargs
    ) -> VideoGenerationResult:
        """Pipeline执行入口"""
        
    async def setup_environment(self, ctx: PipelineContext):
        """Step 1: 环境初始化"""
        
    async def generate_content(self, ctx: PipelineContext):
        """Step 2: 内容生成"""
        
    async def plan_visuals(self, ctx: PipelineContext):
        """Step 4: 视觉规划"""
        
    async def produce_assets(self, ctx: PipelineContext):
        """Step 6: 资源生产"""
```

### 3. 阿里云服务入口：AliyunVideoService

**位置**: `pixelle_video/services/aliyun_video.py`

```python
class AliyunVideoService:
    async def generate(
        self,
        prompt: str,
        duration: int = 5,
        resolution: str = "720P",
        ratio: str = "16:9",
        prompt_extend: bool = True,
        seed: Optional[int] = None
    ) -> AliyunVideoResult:
        """阿里云视频生成入口"""
        
    async def download_video(
        self,
        video_url: str,
        save_path: Path
    ) -> Path:
        """下载视频到本地"""
```

### 4. 媒体服务入口：MediaService

**位置**: `pixelle_video/services/media.py`

```python
class MediaService(ComfyBaseService):
    async def __call__(
        self,
        prompt: str,
        workflow: Optional[str] = None,
        media_type: str = "image",
        duration: Optional[float] = None
    ) -> MediaResult:
        """媒体生成统一入口"""
```

---

## 质量优化建议

### 1. 分辨率与宽高比匹配

**问题**：阿里云生成720P横屏(1280×720)，但模板需要竖屏(1080×1920)

**解决方案**：自动ratio匹配
```python
# media.py中的自动检测逻辑
template_path = self.core.config.get("template", {}).get("default_template", "")
if "1080x1920" in template_path:
    ratio = "9:16"   # 竖屏（完美匹配模板）
elif "1920x1080" in template_path:
    ratio = "16:9"   # 横屏
else:
    ratio = "1:1"    # 方形
```

**效果**：
- 720P + 9:16 = 720×1280（竖屏）
- 直接适配模板，减少裁剪损失

### 2. Prompt优化

**官方公式**：
```
进阶公式 = 主体(主体描述) + 场景(场景描述) + 运动(运动描述) + 美学控制 + 风格化
```

**优化建议**：
1. 启用 `prompt_extend=true`（默认）
2. 使用 `negative_prompt` 排除低质量元素
3. 固定 `seed` 提升可复现性

### 3. ffmpeg编码优化

**当前参数**：
- preset='medium', crf=23

**优化建议**（如需更高质量）：
- preset='slow', crf=18-20
- bitrate提升到3-4Mbps

---

## 成本分析

### 阿里云万相API计费

**计费方式**：按秒计费

**分辨率对比**：
| 分辨率 | 成本 | 质量 | 推荐场景 |
|--------|------|------|---------|
| 480P | 低 | 较低 | 快速测试 |
| 720P | 中 | 标准 | **推荐（成本可控）** |
| 1080P | 高 | 高质量 | 商业输出 |

**时长影响**：
- 5秒视频 ≈ 基础费用×5
- 10秒视频 ≈ 基础费用×10

### 成本优化建议

1. **测试阶段**：
   - 使用720P + 5秒镜头
   - 验证创意效果

2. **正式输出**：
   - 720P + 5-10秒镜头
   - 成本与质量平衡

3. **批量生成**：
   - 记录满意的seed值
   - 减少重新生成次数

---

## 总结

### 集成要点

✅ **最小改动**：遵循工程架构，扩展而非重构
✅ **无缝集成**：通过wrapper格式和source分支实现
✅ **自动化**：ratio自动匹配模板，无需手动配置
✅ **成本可控**：720P分辨率 + 按秒计费

### 使用建议

1. 配置好API Key后直接使用Pipeline生成
2. 720P + ratio自动匹配已优化质量
3. 成本优先，质量次之可保持当前配置
4. 如需更高质量可升级到1080P

---

**文档版本**: v1.0
**更新日期**: 2026-05-08
**作者**: Pixelle-Video 集成团队