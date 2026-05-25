#!/usr/bin/env python3
"""
Collect a real-device frontend baseline for VoiceLoop-X using recorded WAV files.

This script profiles the front half of the pipeline that is currently runnable
on the host machine:

- Smart Turn endpoint inference
- Moonshine transcription

It exists because the full end-to-end baseline is currently blocked by the
llama-cpp-python install on Python 3.13 / Windows.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
import wave
from pathlib import Path
from typing import Iterable

import numpy as np
import psutil

sys.path.insert(0, str(Path(__file__).parent / "src"))

from voiceloop.latency_profiler import LatencyProfiler

SAMPLE_RATE = 16000


def load_wav_audio(path: str | Path) -> np.ndarray:
    wav_path = Path(path)
    with wave.open(str(wav_path), "rb") as wf:
        n_channels = wf.getnchannels()
        sample_width = wf.getsampwidth()
        sample_rate = wf.getframerate()
        frames = wf.readframes(wf.getnframes())
    if sample_width != 2:
        raise ValueError(f"Unsupported WAV sample width {sample_width * 8} bits in {wav_path}")
    audio = np.frombuffer(frames, dtype=np.int16).astype(np.float32)
    if n_channels > 1:
        audio = audio.reshape(-1, n_channels).mean(axis=1)
    audio = audio / 32768.0
    if sample_rate != SAMPLE_RATE:
        ratio = SAMPLE_RATE / sample_rate
        idx = np.arange(0, len(audio) * ratio, ratio, dtype=np.float32)
        idx = np.clip(idx, 0, max(len(audio) - 1, 0))
        audio = np.interp(idx, np.arange(len(audio), dtype=np.float32), audio).astype(np.float32)
    return audio.astype(np.float32)


def load_smart_turn():
    import onnxruntime as ort
    from transformers import WhisperFeatureExtractor

    model_path = os.path.join(tempfile.gettempdir(), "smart_turn_v3", "smart_turn_v3.2_cpu.onnx")
    if not os.path.exists(model_path):
        print("Downloading Smart Turn v3.2 model...", flush=True)
        os.makedirs(os.path.dirname(model_path), exist_ok=True)
        import urllib.request

        urllib.request.urlretrieve(
            "https://huggingface.co/pipecat-ai/smart-turn-v3/resolve/main/smart-turn-v3.2-cpu.onnx",
            model_path,
        )
    session = ort.InferenceSession(model_path, providers=["CPUExecutionProvider"])
    extractor = WhisperFeatureExtractor.from_pretrained("openai/whisper-tiny")

    def predict(audio_float32: np.ndarray) -> float:
        max_samples = 8 * SAMPLE_RATE
        audio_float32 = audio_float32[-max_samples:]
        features = extractor(
            audio_float32,
            sampling_rate=SAMPLE_RATE,
            max_length=max_samples,
            padding="max_length",
            return_attention_mask=False,
            return_tensors="np",
        )
        return float(
            session.run(None, {"input_features": features.input_features.astype(np.float32)})[0].flatten()[0]
        )

    return predict


def iter_audio_files(paths: Iterable[str]) -> list[Path]:
    resolved: list[Path] = []
    for raw in paths:
        p = Path(raw)
        if p.is_dir():
            resolved.extend(sorted(p.glob("*.wav")))
        else:
            resolved.append(p)
    return resolved


def main() -> None:
    ap = argparse.ArgumentParser(description="Collect a frontend-only VoiceLoop-X baseline from WAV files")
    ap.add_argument("inputs", nargs="+", help="One or more WAV files or directories containing WAV files")
    ap.add_argument("--output", default="data/profiles/frontend_baseline.json", help="Output JSON path")
    ap.add_argument(
        "--warmup-count",
        type=int,
        default=0,
        help="Number of initial files to run as warm-up without recording profiler results",
    )
    args = ap.parse_args()

    audio_files = iter_audio_files(args.inputs)
    if not audio_files:
        raise SystemExit("No WAV files found")

    print("Loading Smart Turn...", flush=True)
    smart_turn = load_smart_turn()
    print("Loading Moonshine...", flush=True)
    from moonshine_voice import Transcriber, get_model_for_language

    ms_path, ms_arch = get_model_for_language("en")
    moonshine = Transcriber(model_path=str(ms_path), model_arch=ms_arch)

    profiler = LatencyProfiler()
    transcripts = []

    warmup_count = max(0, min(args.warmup_count, len(audio_files)))
    warmup_paths = audio_files[:warmup_count]
    measured_paths = audio_files[warmup_count:]

    for wav_path in warmup_paths:
        print(f"[warmup] {wav_path}", flush=True)
        audio = load_wav_audio(wav_path)
        _ = smart_turn(audio)
        _ = " ".join(
            l.text for l in moonshine.transcribe_without_streaming(audio.tolist(), SAMPLE_RATE).lines if l.text
        ).strip()

    for wav_path in measured_paths:
        print(f"[frontend] {wav_path}", flush=True)
        audio = load_wav_audio(wav_path)
        profiler.increment_utterance()

        profiler.start_stage("smart_turn")
        turn_prob = smart_turn(audio)
        profiler.end_stage("smart_turn")

        profiler.start_stage("transcription")
        transcript = " ".join(
            l.text for l in moonshine.transcribe_without_streaming(audio.tolist(), SAMPLE_RATE).lines if l.text
        ).strip()
        profiler.end_stage("transcription")

        transcripts.append(
            {
                "path": str(wav_path),
                "duration_sec": round(len(audio) / SAMPLE_RATE, 3),
                "smart_turn_probability": round(turn_prob, 4),
                "transcript": transcript,
            }
        )

    report = profiler.generate_report()
    vm = psutil.virtual_memory()
    report.setdefault("metadata", {}).update(
        {
            "experiment_type": "frontend_partial_baseline",
            "platform": sys.platform,
            "python_version": sys.version.split()[0],
            "cpu_count": os.cpu_count() or 0,
            "total_ram_gb": round(vm.total / (1024 ** 3), 2),
            "available_ram_gb": round(vm.available / (1024 ** 3), 2),
            "input_count": len(measured_paths),
            "input_paths": [str(p) for p in measured_paths],
            "warmup_count": warmup_count,
            "warmup_paths": [str(p) for p in warmup_paths],
            "llm_runtime_blocked": True,
            "notes": "Frontend-only baseline because llama-cpp-python is not currently installable on this host Python 3.13 setup.",
        }
    )
    report["summary"] = {
        "experiment_type": "frontend_partial_baseline",
        "utterance_count": len(measured_paths),
        "mean_smart_turn_ms": round(report.get("stages", {}).get("smart_turn", {}).get("mean_ms", 0.0), 2),
        "mean_transcription_ms": round(report.get("stages", {}).get("transcription", {}).get("mean_ms", 0.0), 2),
        "primary_bottleneck": report["bottlenecks"][0]["stage"] if report.get("bottlenecks") else "None",
    }
    report["per_file"] = transcripts

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"\nFrontend baseline saved to {output_path}", flush=True)


if __name__ == "__main__":
    main()
