# Copyright (C) 2025 AIDC-AI
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Standalone Qwen3-TTS MLX Runner

Invoked via subprocess from the conda 'audio' environment.
Accepts JSON parameters via stdin, generates audio, saves to file.

Usage:
    conda run -n audio python pixelle_video/services/qwen_tts_runner.py

Input is a JSON object via stdin:
{
    "text": "你好，世界！",
    "speaker": "vivian",
    "language": "Chinese",
    "instruct": "",
    "output_path": "/path/to/output.wav"
}

On success, prints the output path to stdout.
On failure, prints error to stderr and exits with code 1.

Model paths are auto-discovered from the ModelScope cache:
    ~/.cache/modelscope/hub/models/mlx-community/
"""

import json
import os
import sys
import time
from contextlib import contextmanager

import numpy as np
import scipy.io.wavfile

MODELS_DIR = os.path.expanduser("~/.cache/modelscope/hub/models/mlx-community")

VALID_SPEAKERS = [
    "serena", "vivian", "uncle_fu", "ryan", "aiden",
    "ono_anna", "sohee", "eric", "dylan",
]


@contextmanager
def _suppress_stdout():
    """Redirect stdout to stderr (library prints init messages to stdout)."""
    saved_stdout = sys.stdout
    sys.stdout = sys.stderr
    try:
        yield
    finally:
        sys.stdout = saved_stdout


def _find_model_path(model_type: str, quant: str = "bf16", size: str = "1.7B") -> str | None:
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


def main():
    from mlx_audio.tts.utils import load_model
    
    t0 = time.time()
    
    params = json.loads(sys.stdin.read())
    
    text = params["text"]
    speaker = params.get("speaker", "vivian")
    language = params.get("language", "Chinese")
    instruct = params.get("instruct", "")
    output_path = params["output_path"]
    quant = params.get("quant", "bf16")
    speed = params.get("speed", 1.0)
    temperature = params.get("temperature", 0.9)
    
    if not text or not text.strip():
        print("ERROR: text is empty", file=sys.stderr)
        sys.exit(1)
    if speaker not in VALID_SPEAKERS:
        print(f"ERROR: invalid speaker '{speaker}', must be one of {VALID_SPEAKERS}", file=sys.stderr)
        sys.exit(1)
    if not output_path:
        print("ERROR: output_path is required", file=sys.stderr)
        sys.exit(1)
    
    model_path = _find_model_path("custom_voice", quant=quant)
    if not model_path:
        print(f"ERROR: CustomVoice model not found in {MODELS_DIR}", file=sys.stderr)
        sys.exit(1)
    
    print(f"Loading model from {model_path}...", file=sys.stderr)
    
    with _suppress_stdout():
        model = load_model(model_path)
    load_time = time.time() - t0
    print(f"Model loaded in {load_time:.1f}s", file=sys.stderr)
    
    gen_start = time.time()

    results = list(model.generate_custom_voice(
        text=text,
        speaker=speaker,
        language=language,
        instruct=instruct if instruct else None,
        temperature=temperature,
    ))
    
    result = results[0]
    gen_time = time.time() - gen_start
    
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
    total_time = time.time() - t0
    
    print(f"Audio saved: {output_path} ({duration_sec:.1f}s, load={load_time:.1f}s, gen={gen_time:.1f}s, total={total_time:.1f}s)", file=sys.stderr)
    
    print(output_path)


if __name__ == "__main__":
    main()
