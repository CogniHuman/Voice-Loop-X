# VoiceLoop-X: Research Project Overview

**Organization**: CogniHuman Research Foundation  
**Project Type**: On-Device Voice AI Research  
**Status**: Phase 1 Complete ✅ | Phase 2 In Progress 🔄 | KV Cache: Needs Fix ❌
**Contribution Score**: 7.5/10 → Target: 9.0/10  
**Last Updated**: April 2026

---

## 🎯 Project Mission

Transform VoiceLoop-X from a solid engineering project into a **significant research contribution** for on-device Voice AI through systematic optimizations, novel algorithms, and standardized evaluation methodology.

### Core Principles
- ✅ **Real Research** - Novel algorithms, not API wrappers
- ✅ **Measurable Impact** - Data-driven optimization with verified results
- ✅ **Open Science** - Reproducible methodology, open-source code
- ✅ **Community Benefit** - Standardized benchmarks, educational resources

---

## 📊 Current Status

### Phase 1 Complete ✅

**Foundation Infrastructure**:
- ✅ **Latency Profiler** - Measures 10 pipeline stages, identifies bottlenecks
- ✅ **Benchmark Suite** - Standardized test sets with WER calculation
- ✅ **Cross-Platform Support** - Windows, Linux, macOS
- ✅ **Thread-Safe Architecture** - Lock-protected shared state
- ✅ **Performance Metrics** - Real-time TTFA and latency tracking
- ✅ **Hardware Detection** - Adaptive configuration based on CPU/RAM/GPU

**Research Capabilities**:
- ✅ Comprehensive performance measurement
- ✅ Bottleneck identification (automatic)
- ✅ Standardized evaluation methodology
- ✅ Reproducible benchmarks (JSON export)
- ✅ Statistical analysis (mean, median, P95, P99)
- ✅ **KV Cache Module** - Research-grade `research/kv_cache_optimizer.py`
- ✅ **ComprehensiveMetrics** - Publication-ready latency reports

### Phase 2 In Progress 🔄

**Immediate Priority — Memory Optimization** (Required before any other optimization works)
- Target: Free 1.5-2GB RAM (current: 0.4GB available)
- Actions: Q3 quantization, buffer reduction, mmap optimization

**Core Optimizations** (Months 3-4):
1. 🔄 **Speculative Decoding** - 3-5x LLM speedup (HIGHEST PRIORITY)
2. 🔄 **Streaming ASR** - 30-40% TTFA reduction
3. ❌ **KV Cache** - Needs fix (infrastructure exists, not working; causes +24% regression)

**Advanced Features** (Months 5-6):
4. 📋 Adaptive VAD - 40-60% false trigger reduction
5. 📋 Memory-Efficient Streaming - Constant memory architecture
6. 📋 Quantization Study - Systematic Q2-Q8 comparison

**Intelligence Layer** (Month 7):
7. 📋 Adaptive Model Selection - 30-50% efficiency gain

---

## 🔬 Research Context

### Origin
VoiceLoop-X is based on **Trelis Research's Voice Loop** (macOS-only) with optimizations by CogniHuman:
- Cross-platform support (+200%)
- Smart Turn optimization (-48% latency)
- AEC allocation reduction (-97%)
- Thread-safe architecture

### KV Cache Implementation: NOT WORKING ❌

**Status**: The KV cache implementation causes a **+24% regression** instead of improvement.

**Root Cause** (identified April 2026):
1. `_kv_cache_mgr` is created but **never called** from `llm_generate()` (line 820 bypasses it)
2. Hash computation from `get_cache_key()` adds overhead without benefit
3. llama.cpp native cache parameters (`n_ctx_set`/`prompt_cache_ro`) not configured

**Measured Results**:
| File | LLM Mean | % Total |
|------|----------|---------|
| `baseline.json` (no cache) | 71,807ms | 89.3% |
| `kv_test.json` (with cache) | 89,100ms | 91.0% |

**Correct Implementation Order**:
1. Memory Optimization → free 1.5-2GB RAM
2. Enable llama.cpp native caching (`n_ctx_set=8192`)
3. Test properly with benchmark protocol

See `docs/technical/IMPROVEMENTS.md` for detailed analysis.

---

## 📈 Performance Metrics

### Measured Baseline Performance (April 2026)

Hardware: Windows 11, 12-core CPU, 7.7GB RAM (0.4GB available), CPU-only, Phi-3 Mini Q4

| Stage | Mean | P95 | % Total | Priority |
|-------|------|-----|---------|----------|
| Smart Turn | 354ms | 776ms | 0.4% | ✅ Stable |
| Transcription | 8,233ms | 10,503ms | 10.2% | ⚠️ Moderate |
| **LLM First Token** | **71,807ms** | **105,431ms** | **89.3%** | 🚨 CRITICAL |

**Conclusion**: LLM is 89.3% of total latency. Speculative decoding is the highest-impact optimization.

### Target Performance (After Full Optimization)
| Metric | Baseline | With Spec Decoding | With All Opts | Improvement |
|--------|----------|-------------------|--------------|-------------|
| LLM First Token | 71,807ms | 20,000-25,000ms | 14,000ms | **3-5x** |
| TTFA | ~80s | 35-45s | 20-30s | **2-3x** |
| Memory | 3.5GB | 5.0GB | 2.4GB | -32% (Q3) |
| Tokens/sec | 1.7 | 5-8 | 10-15 | **3-8x** |

---

## 🗂️ Project Structure

```
VoiceLoop-X/
├── voice_loop.py              # Main voice agent (profiler-integrated)
├── SOUL.md                    # Agent persona configuration
├── MEMORY.md                  # Long-term memory (optional)
├── CogniHuman.md              # Foundation information
├── PROJECT_OVERVIEW.md        # This file
├── README.md                  # Quick start guide
│
├── research/                  # Research modules
│   ├── latency_profiler.py    # Performance measurement
│   ├── benchmark_suite.py     # Standardized evaluation
│   └── test_sets/             # Benchmark test cases
│       ├── short_queries.json
│       ├── medium_queries.json
│       ├── long_queries.json
│       └── audio/             # Test audio files
│
├── tests/                     # Validation scripts
│   ├── test_profiler.py       # Profiler validation
│   ├── test_benchmark.py      # Benchmark validation
│   └── validate_improvements.py
│
├── docs/                      # Documentation
│   ├── README.md              # Documentation index
│   ├── research/              # Research planning
│   │   ├── RESEARCH_ROADMAP.md
│   │   ├── EXECUTIVE_SUMMARY.md
│   │   ├── VISUAL_ROADMAP.md
│   │   └── FOUNDATION_COMPLETE.md
│   ├── technical/             # Technical details
│   │   ├── IMPROVEMENTS.md
│   │   ├── TECHNICAL_REVIEW.md
│   │   ├── INDEPENDENT_VERIFICATION.md
│   │   ├── PROFILER_IMPLEMENTATION.md
│   │   ├── BENCHMARK_IMPLEMENTATION.md
│   │   └── Trelis_Voice_Loop.md
│   └── guides/                # User guides
│       ├── QUICK_START_RESEARCH.md
│       ├── PROFILER_USAGE.md
│       ├── BENCHMARK_USAGE.md
│       └── DEVELOPER_GUIDE.md
│
└── paper/                     # Research papers (future)
    ├── benchmarks/
    └── figures/
```

---

## 🎓 Research Contributions

### Planned Publications (4-5 Papers)

1. **"Comprehensive Performance Analysis of On-Device Voice Agent Pipelines"**
   - Venue: INTERSPEECH / ICASSP
   - Content: Latency breakdown, bottleneck identification, optimization opportunities
   - Status: Foundation complete, data collection in progress

2. **"Efficient KV Cache Management and Speculative Decoding for Streaming Voice Agents"**
   - Venue: ACL / EMNLP
   - Content: Novel optimization techniques for LLM inference
   - Status: Planned for Phase 2-3

3. **"Optimal Quantization Strategies for On-Device Voice AI"**
   - Venue: MLSys / NeurIPS Workshop
   - Content: Systematic quantization study (Q2/Q3/Q4/Q8)
   - Status: Planned for Phase 2

4. **"VoiceBench: A Standardized Benchmark Suite for On-Device Voice Agents"**
   - Venue: LREC / SLT
   - Content: Benchmark design, methodology, baseline results
   - Status: Foundation complete, expanding test sets

5. **"Adaptive and Resource-Aware Voice Agent Architecture"**
   - Venue: INTERSPEECH / CHI
   - Content: Complete system with adaptive VAD and model selection
   - Status: Planned for Phase 4

### Open-Source Contributions

**Code Releases**:
- VoiceLoop-X Optimized (complete implementation)
- VoiceBench (standardized benchmark suite)
- Latency Profiler (standalone tool)
- Quantization Study (systematic evaluation)

**Datasets**:
- Voice Agent Test Set (standardized queries with ground truth)
- Latency Benchmark Results (cross-platform, cross-hardware)
- Quantization Quality Study (perplexity and human eval)

**Documentation**:
- Optimization Guide (step-by-step implementation)
- Benchmark Methodology (reproducible evaluation)
- Hardware Recommendations (device-specific guidance)

---

## 🛠️ Technology Stack

### Core Components
- **ASR**: Moonshine (on-device transcription)
- **LLM**: Gemma 2 2B E2B (Q4_K_M quantization)
- **TTS**: Kokoro (token-level streaming synthesis)
- **VAD**: Silero VAD (voice activity detection)
- **Smart Turn**: Smart Turn v3 (4s window optimization)
- **AEC**: WebRTC AEC3 (echo cancellation)

### Infrastructure
- **Language**: Python 3.11+
- **Audio**: sounddevice, numpy
- **ML**: llama-cpp-python, torch
- **Profiling**: Custom latency profiler
- **Benchmarking**: Custom VoiceBench suite

### Platform Support
- Windows (CUDA/CPU)
- Linux (CUDA/Vulkan/CPU)
- macOS (Metal/CPU)

---

## 📅 Timeline

### Phase 1: Foundation (Months 1-2) ✅ COMPLETE
- Week 1-2: Latency Profiler implementation
- Week 3-4: Benchmark Suite implementation
- Week 5-8: Documentation and validation
- **Deliverable**: Foundation infrastructure + technical report

### Phase 2: Core Optimizations (Months 3-4) 🔄 IN PROGRESS
- Week 9-10: Memory Optimization (prerequisite for all other optimizations)
- Week 11-13: Speculative Decoding (3-5x LLM speedup — HIGHEST PRIORITY)
- Week 14-15: Streaming ASR integration
- Week 16: GPU Acceleration for CUDA/Metal systems
- **Deliverable**: Paper on optimization techniques

### Phase 3: Advanced Features (Months 5-6) 📋 PLANNED
- Week 17-19: KV Cache Fix (after memory optimization)
- Week 20-21: Quantization Study (Q2-Q8 systematic comparison)
- Week 22-23: Adaptive VAD
- Week 24: Memory-Efficient Streaming
- **Deliverable**: Paper on novel algorithms

### Phase 4: Intelligence Layer (Month 7) 📋 PLANNED
- Week 25-27: Adaptive Model Selection
- Week 28: Integration & Testing
- **Deliverable**: Complete system paper + VoiceBench paper

---

## 🤝 Collaboration

### How to Get Involved

**For Researchers**:
- Implement optimizations from roadmap
- Conduct systematic studies
- Write technical reports and papers
- Expand benchmark test sets

**For Developers**:
- Contribute code improvements
- Add platform support
- Create test cases
- Improve documentation

**For Organizations**:
- Research collaborations
- CSR partnerships
- Dataset contributions
- Community building

### Contact
- **Research**: research@cognihuman.org
- **Technical**: GitHub Issues
- **Partnerships**: partners@cognihuman.org

---

## 📊 Success Metrics

### Technical Metrics
- [ ] TTFA < 400ms (mean)
- [ ] Memory < 2.5GB
- [ ] WER < 5% on benchmark
- [ ] Cross-platform support (5+ platforms)

### Research Metrics
- [ ] 4-5 papers published
- [ ] VoiceBench adopted by 3+ projects
- [ ] 100+ GitHub stars
- [ ] 10+ citations within 1 year

### Community Metrics
- [ ] 5+ external contributors
- [ ] 3+ derivative projects
- [ ] Featured in 2+ conferences
- [ ] Mentioned in 5+ blog posts

---

## 🎯 Why This Matters

### For CogniHuman
- Establishes research credibility
- Demonstrates "not a wrapper" philosophy
- Aligns with mission (digital divide, open science)
- Creates foundation for future work

### For Voice AI Field
- First comprehensive on-device voice agent study
- Standardized benchmarks (VoiceBench)
- Novel optimization techniques
- Open-source reference implementation

### For On-Device AI
- Reduces resource requirements (broader access)
- Enables mobile deployment
- Demonstrates CPU optimization
- Shows practical edge AI

---

## 📚 Key Documents

### Start Here
1. **[README.md](README.md)** - Quick start and basic usage
2. **[PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md)** - This document
3. **[docs/README.md](docs/README.md)** - Complete documentation index

### For Research Context
1. **[docs/research/EXECUTIVE_SUMMARY.md](docs/research/EXECUTIVE_SUMMARY.md)** - High-level overview
2. **[docs/research/RESEARCH_ROADMAP.md](docs/research/RESEARCH_ROADMAP.md)** - Detailed 7-month plan
3. **[docs/research/FOUNDATION_COMPLETE.md](docs/research/FOUNDATION_COMPLETE.md)** - Phase 1 status

### For Implementation
1. **[docs/guides/PROFILER_USAGE.md](docs/guides/PROFILER_USAGE.md)** - Measure performance
2. **[docs/guides/BENCHMARK_USAGE.md](docs/guides/BENCHMARK_USAGE.md)** - Evaluate system
3. **[docs/technical/IMPROVEMENTS.md](docs/technical/IMPROVEMENTS.md)** - Implementation details

---

## 📄 License

- **Code**: Apache 2.0
- **Documentation**: CC BY 4.0
- **Datasets**: CC BY-SA 4.0
- **Model Weights**: Apache 2.0 or MIT

---

**CogniHuman Research Foundation**  
*Advancing Voice AI for Public Benefit - Not a Wrapper*

**Last Updated**: April 2026 — Phase 2 In Progress  
**Next Milestone**: Speculative Decoding Implementation (Week 11)
**Research Contact**: research@cognihuman.org
