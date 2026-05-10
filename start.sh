#!/bin/bash

# Pixelle-Video 一键启动脚本

PROJECT_DIR="/Users/lwz/Liwz/Code/Pixelle-Video"
LOG_FILE="$PROJECT_DIR/pixelle_video.log"

echo "================================"
echo "🎬 Pixelle-Video 启动中..."
echo "================================"

# 启动 ComfyUI（如果未运行）
if ! lsof -ti:8000 > /dev/null 2>&1; then
    echo "🚀 启动 ComfyUI..."
    open -a ComfyUI
fi

# 等待 ComfyUI 启动
echo "⏳ 等待 ComfyUI 启动 (约10秒)..."
sleep 10

# 切换到项目目录
cd "$PROJECT_DIR"

# 启动 Pixelle-Video
echo "🚀 启动 Pixelle-Video..."
nohup uv run streamlit run web/app.py --server.port 8501 > "$LOG_FILE" 2>&1 &

# 等待启动
sleep 5

echo ""
echo "================================"
echo "✅ 启动完成！"
echo "================================"
echo ""
echo "📱 访问地址:"
echo "   Pixelle-Video: http://localhost:8501"
echo "   ComfyUI:       http://localhost:8000"
echo ""
echo "日志文件: $LOG_FILE"
echo ""
echo "================================"
