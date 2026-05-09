# Pixelle-Video 快速配置指南

## 🎯 你的目标配置

**完整流程**：LLM + 本地Qwen-TTS MLX + 静态模板

---

## 🔑 需要的API Keys（共1个）

### LLM API Key
- **用途**：脚本生成
- **配置位置**：config.yaml → `llm.api_key`
- **当前值**：✅ 已配置 `sk-954696513d35492ab823431a10622ac3`

---

## ✅ 已配置项

### TTS配置（本地Qwen-TTS MLX）
```yaml
comfyui:
  tts:
    inference_mode: qwen_tts  ✅ 使用本地MLX
    qwen_tts:
      conda_env: audio        ✅ Conda环境已就绪
      speaker: vivian         ✅ 默认音色
      speed: 1.0              ✅ 正常速度
      temperature: 0.9        ✅ 稳定度
```

---

## 🔧 Web UI配置步骤

1. **启动应用**：
   ```bash
   uv run streamlit run web/app.py
   ```

2. **打开浏览器**：http://localhost:8501

3. **配置系统设置**（展开「⚙️ 系统配置」面板）：

   **左侧 - LLM配置**：
   - 选择预设（如 GPT、DeepSeek 等）
   - 填写 API Key
   - Base URL 和 Model 会自动填充

   **中间 - ComfyUI配置**（可选）：
   - 本地 ComfyUI URL：可跳过（不使用本地）
   - RunningHub API Key：如需云端图片/视频生成可填写

4. **保存配置**：点击「💾 保存配置」

---

## 🧪 快速测试

### 测试1：TTS语音生成
1. 在「🎤 配音合成」区域
2. 选择模式：`qwen_tts`
3. Speaker：`vivian`
4. 输入测试文本：「这是一段测试语音」
5. 点击「预览语音」
6. ✅ 应听到语音播放

### 测试2：视频生成（完整流程）
1. 在「📝 视频脚本」区域
2. 选择模式：`AI 创作`
3. 输入主题：「一只可爱的小猫在花园玩耍」
4. 在「🎤 配音合成」选择 `qwen_tts` + `vivian`
5. 在「📐 分镜模板」选择默认模板
6. 点击右侧「🎬 生成视频」
7. ⏳ 等待2-5分钟生成完成

---

## 📊 生成流程详解

```
输入主题: "一只小猫在花园玩耍"
    ↓
[Step 1] LLM生成脚本（需API Key）
    ├─ LLM API调用
    ├─ 生成3-5个分镜脚本
    └─ 每个分镜包含：旁白文本 + 画面描述
    ↓
[Step 2] TTS语音合成（本地）
    ├─ 使用Qwen-TTS MLX
    ├─ 每个分镜生成音频文件
    └─ 自动计算时长
    ↓
[Step 3] 视频合成（本地ffmpeg）
    ├─ 使用静态模板合成画面
    ├─ 添加TTS音频轨道
    ├─ 应用模板样式
    └─ 输出最终视频 → output/xxx.mp4
```

---

## ⚠️ 当前问题

**LLM API Key无效（401错误）**
- 当前配置的key测试失败
- 可能原因：
  1. Key已过期
  2. Key格式错误
  3. Key权限不足

**解决方案**：
1. 确认或重新生成API Key
2. 在Web UI更新配置
3. 或直接编辑 config.yaml

---

## 💡 建议配置检查清单

- [ ] LLM API Key有效且未过期
- [ ] Conda环境 `audio` 包含 mlx-audio
- [ ] ffmpeg已安装（`ffmpeg -version`）
- [ ] 模板文件存在（templates/1080x1920/image_default.html）

---

## 🎬 下一步

完成配置后，打开Web UI测试：
1. 先测试TTS预览（不依赖LLM）
2. 然后测试完整视频生成流程
3. 查看output/目录中的生成结果

有问题随时反馈！