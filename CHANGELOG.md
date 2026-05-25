# VoiceLoop-X Research Changelog

**Organization**: CogniHuman Research Foundation  
**License**: Apache 2.0 (code), CC BY 4.0 (documentation)  
**Contact**: research@cognihuman.org

All notable research contributions to VoiceLoop-X are documented here. This follows [Keep a Changelog](https://keepachangelog.com/) conventions and is maintained as part of CogniHuman's commitment to open research.

---

## [Unreleased] — Development Branch

### Added
- Memory-optimized LLM loading (`voice_loop.py:load_llm`)
  - `use_mmap=True` — OS-level memory mapping for constrained systems
  - `use_mlock` adaptive — pins model in RAM only when >4GB free (avoids OOM)
  - `n_batch=256` when <4GB RAM, 512 otherwise — limits peak RSS under memory pressure
  - `n_ctx_max=8192` — enables llama.cpp native KV cache for multi-turn conversations
  - Memory availability printed on startup for diagnostics
- Hardware-adaptive LLM configuration via `psutil` memory detection
- Cross-platform termios/tty import fix (Windows now supported without crashes)
- StreamFold parallel execution (`voice_loop.py:process_utterance`)
  - `--streamfold` flag: run LLM in parallel with ASR completion
  - 2.5s initial timeout (vs baseline 10s) — saves 2.5-8s TTFA for short queries
  - When ASR >2.5s: background LLM thread starts while ASR computes
  - Falls back to partial response if ASR >15s (avoids indefinite blocking)

### Research Roadmap Updates
- Layer 1 (Memory Optimization): **Complete**
- Layer 2 (StreamFold Pipeline Parallelism): **Implemented** — targets 5-15s TTFA

### Known Issues
- **KV Cache: +24% regression** — Infrastructure exists but implementation is non-functional. Fixed by enabling llama.cpp native caching via `n_ctx_max=8192` (this change). Monitor multi-turn latency improvement.

---

## [1.0.0] — Initial Research Release (April 2026)

### Added

#### Research Infrastructure
- **Latency Profiler** (`research/latency_profiler.py`) — Research-grade pipeline measurement with per-stage statistics (mean, p50, p95, p99, std, min, max), bottleneck identification, and optimization recommendations. Generates JSON reports for reproducible research.
- **Benchmark Suite — VoiceBench** (`research/benchmark_suite.py`) — Standardized evaluation with 22 test cases across 3 categories (short/medium/long queries), WER calculation, and statistical aggregation. First standardized benchmark for on-device voice agents.
- **Hardware Detection System** (`HardwareDetector` class in `voice_loop.py`) — Automatic detection of CPU cores, RAM, GPU (CUDA/Metal), with optimal configuration generation for each hardware tier.

#### Pipeline Components
- **VAD** with Silero VAD (32ms chunk processing)
- **STT** with Moonshine (on-device transcription)
- **LLM** with llama.cpp (Phi-3 Mini, Gemma 4 support)
- **TTS** with Kokoro (40+ voices, streaming)
- **Smart Turn v3.2** for endpoint detection
- **WebRTC AEC3** for voice interrupt (LiveKit APM)

#### Cross-Platform Support
- Windows, Linux, macOS
- Command-line configuration for all features
- Audio device selection
- Recording for debugging

#### Documentation
- `docs/README.md` — Complete documentation index
- `docs/guides/PROFILER_USAGE.md` — Profiler usage guide
- `docs/guides/BENCHMARK_USAGE.md` — Benchmark usage guide
- `docs/guides/DEVELOPER_GUIDE.md` — Developer setup
- `docs/technical/IMPROVEMENTS.md` — Past improvements
- `docs/technical/PROFILER_IMPLEMENTATION.md` — Profiler technical details
- `docs/technical/BENCHMARK_IMPLEMENTATION.md` — Benchmark technical details

#### Research Datasets
- 22 audio test files in `research/test_sets/audio/`
- Ground truth transcriptions in `research/test_sets/*.json`
- Baseline profile data (`baseline.json`, `research_baseline.json`, `kv_test.json`)

### Baseline Performance (April 2026)

Measured on: Windows 11, 12 CPU cores, 7.7 GB RAM (0.4 GB available), CPU-only

| Stage | Mean Latency | % of Total |
|-------|-------------|-----------|
| Smart Turn | 354 ms | 0.4% |
| Transcription | 8,233 ms | 10.2% |
| LLM First Token | 71,807 ms | 89.3% |
| **Total Turn** | **~80,394 ms** | 100% |

This baseline establishes the **primary research target** (LLM optimization at 89.3% of latency).

### Research Papers (Planned)

| # | Title | Target Venue | Status |
|---|-------|-------------|--------|
| 1 | Baseline Performance Analysis of On-Device Voice Agent Pipelines | INTERSPEECH | ✅ Complete |
| 2 | Speculative Decoding for CPU-based Streaming Voice Agents | ACL | 📋 Planned |
| 3 | Optimal Quantization Strategies for On-Device Voice AI | MLSys | 📋 Planned |
| 4 | VoiceBench: A Standardized Benchmark for On-Device Voice Agents | LREC | 📋 Planned |
| 5 | Adaptive and Resource-Aware Voice Agent Architecture | INTERSPEECH | 📋 Planned |

### Optimization Roadmap

| # | Optimization | Priority | Status |
|---|-------------|----------|--------|
| 1 | Speculative Decoding | 🚨 Critical | 📋 To Implement |
| 2 | Memory Optimization | 🚨 Critical | 📋 To Implement |
| 3 | Streaming ASR | 🔴 High | ⚠️ Partial |
| 4 | KV Cache (fixed) | 🟡 Medium | ❌ Needs Fix |
| 5 | Quantization Study | 🔴 High | 📋 To Implement |
| 6 | GPU Acceleration | 🔴 High | 📋 To Implement |
| 7 | Adaptive VAD | 🟡 Medium | 📋 To Implement |
| 8 | Memory-Efficient Streaming | 🟢 Low | 📋 To Implement |
| 9 | Adaptive Model Selection | 🟢 Low | 📋 To Implement |

### Attribution

This research builds on the following open-source projects:

- **llama.cpp** — Georgi Gerganov and contributors (GGUF model support)
- **llama-cpp-python** — Andrei Betlen and contributors (Python bindings)
- **Moonshine** — On-device transcription model
- **Silero VAD** — Voice activity detection
- **Kokoro** — On-device TTS (MIT licensed)
- **Smart Turn** — Endpoint detection (pipecat-ai)
- **LiveKit** — WebRTC AEC3 (voice interrupt)
- **Kyutai** — Moshi and foundation model research

### Known Issues

1. **KV Cache causes +24% regression** — See `docs/technical/IMPROVEMENTS.md#kv-cache-implementation-status`
2. **0.4 GB available RAM** — Memory pressure limits all optimizations
3. **CPU-only acceleration** — No GPU utilization despite hardware detection

### Migration Notes

None — this is the initial release for research purposes.

---

## CogniHuman Research Foundation

**Mission**: Advance Voice AI as an open, ethical public good  
**Status**: Registered Section 8 Company, NITI Aayog (Darpan) enrolled  
**Tax Status**: 12A & 80G registered, CSR-1 compliant

### Contact
- Research: research@cognihuman.org
- General: inquiries@cognihuman.org
- Partnerships: partners@cognihuman.org

### Contributing
See [CONTRIBUTING.md](./CONTRIBUTING.md) and [docs/guides/DEVELOPER_GUIDE.md](./docs/guides/DEVELOPER_GUIDE.md) for contribution guidelines.

---

*Built with purpose. Open for collaboration.*