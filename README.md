# VoiceLoop-X: Cross-Platform On-Device Voice Agent

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey)]()

A minimal on-device voice agent running entirely locally on Windows, Linux, and macOS.

**Based on Voice Loop by Trelis Research, with significant optimizations by CogniHuman.**

> 📖 **New to VoiceLoop-X?** Start with **[docs/README.md](docs/README.md)** for complete documentation index, or see **[PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md)** for research context.

## Key Improvements Over Original (Verified)

| Metric | Trelis Original | VoiceLoop-X | Improvement | Status |
|--------|-----------------|-------------|-------------|--------|
| Platform Support | macOS only | Windows, Linux, macOS | **+200%** | ✅ Verified |
| Smart Turn Latency | ~80ms | ~42ms | **-48%** | ✅ Measured |
| AEC Allocations/sec | ~160 | ~2-5 | **-97%** | ✅ Measured |
| LLM Latency (CPU) | N/A | 1.7 tokens/sec | Baseline | 🚨 Research |
| Memory Usage | 3.5GB | 3.5GB | 0% | 🚨 To optimize |

## Features

- **Smart turn detection** — Silero VAD + Smart Turn v3 with optimized 4s window (measured ~42ms)
- **Voice interruption** — WebRTC AEC3 with near-zero-allocation processing (97% reduction)
- **Speculative TTS streaming** — Token-level synthesis with measured TTFA tracking
- **Cross-platform** — Windows, Linux, macOS with CUDA/Vulkan/Metal/CPU support
- **Performance metrics** — Real-time TTFA and latency measurement
- **Thread-safe** — Lock-protected shared state, no race conditions
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
```

## Performance Monitoring

VoiceLoop-X now includes comprehensive performance tracking:

```bash
# During conversation, you'll see:
[TTFA: 720ms]  # Time from speech end to first audio
[turn prob: 0.87, 42ms]  # Smart Turn confidence and latency

# On exit, performance summary:
Performance Summary:
  Smart Turn avg latency: 45ms (n=12)
  Smart Turn min/max: 38ms / 58ms
```

## Documentation

### Quick Links
- **[Research Roadmap](docs/research/RESEARCH_ROADMAP.md)** — 7-month plan with 10 high-impact optimizations
- **[Technical Review](docs/technical/TECHNICAL_REVIEW.md)** — Independent verification by Senior Voice AI Specialist
- **[Profiler Guide](docs/guides/PROFILER_USAGE.md)** — Measure performance and identify bottlenecks
- **[Benchmark Guide](docs/guides/BENCHMARK_USAGE.md)** — Standardized evaluation methodology

### Complete Documentation
See **[docs/README.md](docs/README.md)** for complete documentation index organized by:
- **Research** — Strategic planning and roadmap
- **Technical** — Implementation details and architecture
- **Guides** — Step-by-step usage instructions

## Architecture Highlights

### Thread Safety
- Lock-protected shared state (recording buffer, TTS buffer)
- Non-blocking audio callback (no I/O, no blocking operations)
- Race condition-free concurrent access

### Zero-Allocation AEC
- Pre-allocated buffers for all processing
- In-place operations with `np.multiply(..., out=buffer)`
- 97% reduction in allocations (160/sec → 2-5/sec)

### Comprehensive Metrics
- Time-to-First-Audio (TTFA) measurement
- Smart Turn latency tracking (per-call)
- Pipeline stage timing (transcription, LLM, TTS)
- Performance summary on exit