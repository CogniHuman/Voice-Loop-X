# VoiceLoop-X: Claude Code Working Context

**Project**: VoiceLoop-X — CogniHuman Research Foundation  
**Purpose**: On-device voice AI optimization research  
**Contact**: research@cognihuman.org

---

## Project Context

VoiceLoop-X is a **research platform**, not a product. Every change must serve one or more of these goals:
1. Enable novel research contributions (algorithmic)
2. Measure a hypothesis with statistical rigor
3. Improve benchmark coverage or reproducibility
4. Maintain or expand cross-platform compatibility

**CogniHuman is not a wrapper project.** We build novel algorithms, conduct systematic studies, and publish reproducible results. If a change is purely integrating a third-party API or adding a feature without a research justification, it doesn't belong here.

---

## Directory Structure

```
VoiceLoop-X/
├── voice_loop.py          # Main entry point (don't move)
├── SPEC.md                # Project specification (this file context)
│
├── src/voiceloop/         # Published Python package
│   ├── __init__.py        # Package init + version
│   ├── latency_profiler.py       # Research-grade profiler
│   ├── benchmark_suite.py        # VoiceBench suite
│   ├── kv_cache_optimizer.py     # KV cache research module
│   └── add_test_case.py          # Test case helper
│
├── tests/                 # Validation scripts
│   ├── test_profiler.py
│   ├── test_benchmark.py
│   └── validate_improvements.py
│
├── data/                  # Experimental data (not committed large files)
│   ├── benchmarks/        # Benchmark run results
│   ├── profiles/          # Profiler JSON outputs
│   └── test_cases/        # Audio samples + JSON ground truth
│
├── docs/                  # Documentation
│   ├── research/          # Strategic planning (roadmap, summaries)
│   ├── technical/         # Implementation details
│   ├── guides/            # User-facing how-tos
│   ├── about/             # CogniHuman foundation info
│   └── archive/           # Legacy/outdated docs
│
├── paper/                 # Academic paper drafts (future)
│   └── benchmarks/        # Paper figures and tables
│
└── SOUL.md                # Agent persona configuration
```

---

## CogniHuman Research Standards

### Before Writing Any Code

1. **Read the relevant context files:**
   - `PROJECT_OVERVIEW.md` — overall research status
   - `docs/research/RESEARCH_ROADMAP.md` — optimization plan
   - The relevant `*.md` doc in `docs/technical/` for implementation details

2. **Check the baseline data:**
   - `data/profiles/` has historical profiler outputs
   - `data/benchmarks/` has benchmark results
   - **Never make performance claims without data backing them**

3. **Identify the bottleneck:**
   - The LLM dominates at **89.3%** of total latency (measured)
   - The 0.4 GB free RAM is the **root constraint** — no optimization works without freeing memory first
   - Speculative Decoding is the **highest-priority optimization**

### When Implementing Optimizations

1. **Measure before and after** — Always run `--profile --profile-save` before and after any change. Save the JSON to `data/profiles/`.

2. **Document the change** — Update:
   - `CHANGELOG.md` — one entry per change (what, why, measured impact)
   - `docs/technical/IMPROVEMENTS.md` — technical implementation details
   - The module's header docstring (author, date, research contribution, venue)

3. **Attribution is mandatory** — Every new file must include a header:
   ```python
   """
   Module Name: Brief Description
   CogniHuman Research Foundation
   Research Paper: "Paper Title"
   Target Venue: INTERSPEECH / ACL / etc.
   """
   ```

4. **Never skip the changelog** — For every PR or feature:
   ```markdown
   ### [Unreleased]
   #### Added
   - New feature or optimization (file: path)
   - Research justification: [what hypothesis it tests]
   ```

5. **Keep data files in `data/`** — Any new JSON, CSV, audio, or profiling output goes in `data/benchmarks/` or `data/profiles/`. Don't scatter data files at the root.

### Code Quality

- No `print()` for debugging — use structured logging or profiler
- No magic numbers — define constants at the top of modules
- Prefer `np.float32` over `np.float64` — this is a memory-constrained system
- Always use `time.monotonic()` for latency measurement, never `time.time()`
- Thread-safety is mandatory for any shared state — see `threading.Lock()` patterns in `voice_loop.py`

### Commit Message Format

```
<type>(<scope>): <short description>

<optional longer body>

Research context: [what hypothesis this tests]
Data: [mention any measurement files changed]
Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
```

Types: `feat`, `fix`, `docs`, `refactor`, `test`, `data`, `chore`

---

## Critical Constraints

### Hardware Reality
- **Available RAM**: 0.4 GB (out of 7.7 GB total) — **this is the ceiling for all optimizations**
- **CPU-only**: No GPU acceleration (yet); CUDA/Metal support is a planned optimization
- **Memory bandwidth bound**: LLM throughput is 1.7 tokens/sec — improving this requires either:
  - Speculative decoding (draft-verify, reduces serial computation)
  - Quantization (reduces memory footprint per token)
  - Better memory management (frees RAM for cache)

### What's NOT a Priority
- Adding more voice options, personas, or UI features
- Integrating additional third-party APIs
- Writing wrapper code around existing libraries
- Optimizations not backed by benchmark data

---

## Optimization Priority Order (as of April 2026)

| Priority | Optimization | Expected Impact |
|----------|-------------|----------------|
| 🚨 Critical | Memory Optimization | Free 1.5-2 GB RAM |
| 🚨 Critical | Speculative Decoding | 3-5x LLM speedup |
| 🔴 High | Streaming ASR | 30-40% TTFA reduction |
| 🟡 Medium | KV Cache Fix | 40-60% multi-turn reduction |
| 🟡 Medium | Quantization Study | Q2-Q8 comparison dataset |
| 🔴 High | GPU Acceleration | 3-5x on CUDA/Metal |
| 📋 Planned | Adaptive VAD | 40-60% fewer false triggers |
| 📋 Planned | Memory-Efficient Streaming | O(1) memory for long responses |
| 📋 Planned | Adaptive Model Selection | 30-50% efficiency for simple queries |

---

## File Naming Conventions

- **Python modules**: `snake_case.py`
- **Documentation**: `KEBAB-CASE.md` (all lowercase, dashes)
- **Data files**: `snake_case.json`, `snake_case.csv`
- **Test cases**: descriptive, e.g., `weather_query.json`, `long_complex_question.wav`

---

## VoiceBench Test Cases

Standard test cases live in `data/test_cases/`:
- `short_queries.json` + `audio/` — 1-3 word queries
- `medium_queries.json` + `audio/` — 5-15 word queries
- `long_queries.json` + `audio/` — 15-30 word queries

To add a new test case, use `python src/voiceloop/add_test_case.py` or manually add to the JSON with ground truth transcription and WER reference.

---

## Key Commands

```bash
# Run with research profiling
python voice_loop.py --profile --profile-save data/profiles/my_run.json

# Run benchmark suite
python -c "import sys; sys.path.insert(0, 'src'); from voiceloop.benchmark_suite import VoiceBench; ..."

# Add a test case
python src/voiceloop/add_test_case.py --audio data/test_cases/audio/new.wav --text "transcription"

# Validate test suite
cd tests && python test_profiler.py && python test_benchmark.py
```

---

## Getting Help

- **Research context**: `PROJECT_OVERVIEW.md` or `docs/research/RESEARCH_ROADMAP.md`
- **Implementation details**: files in `docs/technical/`
- **Performance data**: files in `data/profiles/` and `data/benchmarks/`
- **Research contact**: research@cognihuman.org