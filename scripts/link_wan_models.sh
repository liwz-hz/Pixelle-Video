#!/bin/bash
# 将 Wan 模型从 checkpoints/ 链接到 unet/ 目录
# ComfyUI 模型目录
MODELS_DIR="/Users/lwz/Documents/ComfyUI/models"

echo "创建 unet 目录..."
mkdir -p "$MODELS_DIR/unet"

echo "链接 Wan 2.1 模型..."
ln -sf "$MODELS_DIR/checkpoints/wan_v2.1_1.3b_480p_f16.ckpt" "$MODELS_DIR/unet/wan_v2.1_1.3b_480p_f16.ckpt"

echo "链接 Wan 2.2 模型..."
ln -sf "$MODELS_DIR/checkpoints/wan_v2.2_5b_ti2v_q8p.ckpt" "$MODELS_DIR/unet/wan_v2.2_5b_ti2v_q8p.ckpt"

echo "✅ 模型链接完成！"
echo ""
echo "验证:"
ls -lh "$MODELS_DIR/unet/"
