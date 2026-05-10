# ComfyUI 本地视频生成配置指南

## 当前状态

✅ **已有模型**:
- Wan 2.1 (2.7GB) - checkpoints/wan_v2.1_1.3b_480p_f16.ckpt
- Wan 2.2 (5.0GB) - checkpoints/wan_v2.2_5b_ti2v_q8p.ckpt
- Text Encoder (6.3GB) - text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors
- VAE 2.1 (256MB) - vae/wan_2.1_vae.safetensors
- VAE 2.2 (1.3GB) - vae/wan2.2_vae.safetensors

❌ **缺失组件**:
- custom_nodes/ 为空 - 需要安装必要节点
- 模型路径映射 - 需要将 checkpoints/ 链接到 unet/

---

## 步骤 1: 链接模型文件

运行以下命令将 checkpoints 中的模型链接到 unet/ 目录：

```bash
bash /Users/lwz/Liwz/Code/Pixelle-Video/scripts/link_wan_models.sh
```

这会在 `unet/` 目录创建指向 checkpoints 的符号链接。

---

## 步骤 2: 安装必要的 ComfyUI 自定义节点

进入 ComfyUI 的 custom_nodes 目录并安装必要节点：

```bash
cd /Users/lwz/Documents/ComfyUI/custom_nodes

# 1. Wan 视频生成节点 (必需)
git clone https://github.com/1038lab/ComfyUI-Wan.git

# 2. Video Helper Suite (视频合成, 必需)
git clone https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite.git

# 3. ComfyUI-Easy-Use (提供 easy int 等节点)
git clone https://github.com/yolain/ComfyUI-Easy-Use.git

# 4. ComfyUI Essentials (提供 PrimitiveStringMultiline 等节点)
git clone https://github.com/cubiq/ComfyUI_essentials.git
```

---

## 步骤 3: 重启 ComfyUI

```bash
cd /Users/lwz/Documents/ComfyUI
python main.py --listen 127.0.0.1 --port 8188
```

---

## 步骤 4: 配置 Pixelle-Video

在 `config.yaml` 中配置 ComfyUI 地址：

```yaml
comfyui:
  comfyui_url: http://127.0.0.1:8188
  media:
    default_workflow: selfhost/video_wan2.1_local.json
```

---

## 可用的工作流

已为你创建适配的工作流：

| 工作流文件 | 模型 | 特点 |
|-----------|------|------|
| `selfhost/video_wan2.1_local.json` | Wan 2.1 1.3B | 轻量级，速度快 |
| `selfhost/video_wan2.2_local.json` | Wan 2.2 5B | 质量更高，需要更多显存 |

---

## 显存需求

| 模型 | 最小显存 | 推荐显存 |
|------|---------|---------|
| Wan 2.1 1.3B | 8GB | 12GB+ |
| Wan 2.2 5B | 16GB | 24GB+ |

---

## 测试工作流

在 ComfyUI Web 界面测试：
1. 打开 http://127.0.0.1:8188
2. 加载工作流：`workflows/selfhost/video_wan2.1_local.json`
3. 点击 Queue Prompt 测试

如果遇到节点缺失错误，请检查 custom_nodes 是否正确安装。
