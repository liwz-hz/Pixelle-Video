#!/bin/bash

PROJECT_DIR="/Users/lwz/Liwz/Code/Pixelle-Video"
LOG_FILE="$PROJECT_DIR/pixelle_video.log"
TTS_SERVER_PORT=9876

echo "================================"
echo "🎬 Pixelle-Video 启动中..."
echo "================================"

if ! lsof -ti:8000 > /dev/null 2>&1; then
    echo "🚀 启动 ComfyUI..."
    open -a ComfyUI
fi

echo "⏳ 等待 ComfyUI 启动 (约10秒)..."
sleep 10

cd "$PROJECT_DIR"

if ! lsof -ti:$TTS_SERVER_PORT > /dev/null 2>&1; then
    echo "🎤 启动 Qwen-TTS 服务器 (端口 $TTS_SERVER_PORT)..."
    CONDA_BASE="/opt/homebrew/Caskroom/miniconda/base"
    TTS_SERVER="$PROJECT_DIR/pixelle_video/services/qwen_tts_server.py"
    nohup "$CONDA_BASE/envs/audio/bin/python" "$TTS_SERVER" --port $TTS_SERVER_PORT >> "$LOG_FILE" 2>&1 &
    sleep 3
fi

echo "🚀 启动 Pixelle-Video..."
nohup uv run streamlit run web/app.py --server.port 8501 >> "$LOG_FILE" 2>&1 &

sleep 5

echo ""
echo "================================"
echo "✅ 启动完成！"
echo "================================"
echo ""
echo "📱 访问地址:"
echo "   Pixelle-Video:   http://localhost:8501"
echo "   ComfyUI:         http://localhost:8000"
echo "   Qwen-TTS Server: 127.0.0.1:$TTS_SERVER_PORT"
echo ""
echo "日志文件: $LOG_FILE"
echo ""
echo "================================"
