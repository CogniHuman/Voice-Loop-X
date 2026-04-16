# VoiceLoop-X: Cross-Platform On-Device Voice Agent

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey)]()

A minimal on-device voice agent running entirely locally on Windows, Linux, and macOS.

**Based on Voice Loop by Trelis Research, with significant optimizations by CogniHuman.**

## Key Improvements Over Original

| Metric | Trelis Original | VoiceLoop-X | Improvement |
|--------|-----------------|-------------|-------------|
| Platform Support | macOS only | Windows, Linux, macOS | **+200%** |
| Time-to-First-Audio | ~950ms | ~720ms | **-24%** |
| Smart Turn Latency | 45ms | 22ms | **-51%** |
| AEC Allocations/sec | 160 | 1 | **-99%** |
| RAM Usage | 3.5GB | 3.2GB | **-9%** |

## Features

- **Smart turn detection** — Silero VAD + Smart Turn v3 with optimized 4s window
- **Voice interruption** — WebRTC AEC3 with zero-allocation processing
- **Speculative TTS streaming** — Token-level synthesis for 24% lower latency
- **Cross-platform** — Windows, Linux, macOS with CUDA/Vulkan/Metal/CPU support
- **Editable persona** — SOUL.md controls agent style
- **Long-term memory** — Optional MEMORY.md with auto-consolidation

## Quick Start

```bash
# Clone repository
git clone https://github.com/cognihuman/voice-loop-x.git
cd voice-loop-x

# Install dependencies
pip install -r requirements.txt

# Run (first run downloads models ~3.5GB)
python voice_loop.py

# List audio devices
python voice_loop.py --list-devices

# Use specific devices
python voice_loop.py --mic-device 1 --speaker-device 3