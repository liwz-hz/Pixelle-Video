#!/usr/bin/env python3
"""
Qwen-TTS Server - Keeps model in memory for consistent voice generation

Usage:
    python pixelle_video/services/qwen_tts_server.py --port 9876

Uses async server with model loaded in main thread (MLX requirement).
"""

import argparse
import asyncio
import json
import os
import sys
import time
from pathlib import Path

import numpy as np
import scipy.io.wavfile

MODELS_DIR = os.path.expanduser("~/.cache/modelscope/hub/models/mlx-community")

VALID_SPEAKERS = [
    "serena", "vivian", "uncle_fu", "ryan", "aiden",
    "ono_anna", "sohee", "eric", "dylan",
]

_model = None
_model_path = None
_request_queue = asyncio.Queue()
_result_queues = {}


def _find_model_path(model_type: str = "custom_voice", quant: str = "bf16", size: str = "1.7B") -> str | None:
    variant_map = {
        "custom_voice": "CustomVoice",
        "voice_design": "VoiceDesign",
        "base": "Base",
    }
    variant = variant_map[model_type]
    
    for q in [quant] + [x for x in ["8bit", "6bit", "4bit"] if x != quant]:
        name = f"Qwen3-TTS-12Hz-{size}-{variant}-{q}"
        for candidate_name in [name, name.replace(".", "___")]:
            path = os.path.join(MODELS_DIR, candidate_name)
            if os.path.isdir(path) and any(f.endswith(".safetensors") for f in os.listdir(path)):
                return path
    return None


def load_model_once(quant: str = "bf16"):
    global _model, _model_path
    
    if _model is not None:
        return _model
    
    from mlx_audio.tts.utils import load_model
    
    _model_path = _find_model_path("custom_voice", quant=quant)
    if not _model_path:
        raise RuntimeError(f"CustomVoice model not found in {MODELS_DIR}")
    
    print(f"[Server] Loading model from {_model_path}...", file=sys.stderr)
    t0 = time.time()
    
    _model = load_model(_model_path)
    
    print(f"[Server] Model loaded in {time.time() - t0:.1f}s", file=sys.stderr)
    return _model


def generate_audio_sync(params: dict) -> dict:
    import mlx.core as mx
    
    text = params["text"]
    speaker = params.get("speaker", "vivian")
    language = params.get("language", "Chinese")
    instruct = params.get("instruct", "")
    output_path = params["output_path"]
    quant = params.get("quant", "bf16")
    speed = params.get("speed", 1.0)
    temperature = params.get("temperature", 0.9)
    seed = params.get("seed", 42)
    
    if not text or not text.strip():
        return {"error": "text is empty"}
    if speaker not in VALID_SPEAKERS:
        return {"error": f"invalid speaker '{speaker}'"}
    if not output_path:
        return {"error": "output_path is required"}
    
    model = load_model_once(quant)
    
    if seed is not None:
        mx.random.seed(seed)
    
    t0 = time.time()
    
    results = list(model.generate_custom_voice(
        text=text,
        speaker=speaker,
        language=language,
        instruct=instruct if instruct else None,
        temperature=temperature,
        top_k=20,
        top_p=0.9,
    ))
    
    result = results[0]
    
    audio_data = np.array(result.audio, dtype=np.float32)
    sample_rate = getattr(result, "sample_rate", 24000)
    
    if speed != 1.0:
        new_len = int(len(audio_data) / speed)
        indices = np.linspace(0, len(audio_data) - 1, new_len, dtype=np.float32)
        audio_data = np.interp(indices, np.arange(len(audio_data)), audio_data).astype(np.float32)
    
    out_dir = os.path.dirname(output_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    
    scipy.io.wavfile.write(output_path, sample_rate, audio_data)
    
    duration_sec = len(audio_data) / sample_rate
    gen_time = time.time() - t0
    
    return {
        "output_path": output_path,
        "duration": duration_sec,
        "gen_time": gen_time,
    }


async def handle_client(reader, writer):
    try:
        data = await reader.read(65536)
        if not data:
            return
        
        request_str = data.decode().strip()
        if not request_str:
            return
        
        params = json.loads(request_str)
        request_id = id(writer)
        result_queue = asyncio.Queue()
        _result_queues[request_id] = result_queue
        
        await _request_queue.put((params, request_id))
        
        result = await result_queue.get()
        
        del _result_queues[request_id]
        
        response = json.dumps(result) + "\n"
        writer.write(response.encode())
        await writer.drain()
        
    except Exception as e:
        error_response = json.dumps({"error": str(e)}) + "\n"
        writer.write(error_response.encode())
        await writer.drain()
    finally:
        writer.close()
        await writer.wait_closed()


async def process_requests():
    while True:
        params, request_id = await _request_queue.get()
        
        try:
            result = generate_audio_sync(params)
        except Exception as e:
            result = {"error": str(e)}
        
        if request_id in _result_queues:
            await _result_queues[request_id].put(result)


async def main():
    parser = argparse.ArgumentParser(description="Qwen-TTS Server")
    parser.add_argument("--port", type=int, default=9876, help="Server port")
    parser.add_argument("--quant", type=str, default="bf16", help="Model quantization")
    args = parser.parse_args()
    
    print(f"[Server] Starting Qwen-TTS server on port {args.port}", file=sys.stderr)
    
    load_model_once(args.quant)
    
    asyncio.create_task(process_requests())
    
    server = await asyncio.start_server(
        handle_client, '127.0.0.1', args.port
    )
    
    print(f"[Server] Ready to accept connections", file=sys.stderr)
    
    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())
