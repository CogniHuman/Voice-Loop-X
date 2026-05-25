# VoiceLoop-X Research Audit

**Organization**: CogniHuman Research Foundation  
**Project**: VoiceLoop-X  
**Audit Date**: 2026-05-25  
**Audit Scope**: Repository-wide review of research direction, implementation reality, technical debt, and publication readiness

---

## Purpose

This document is the onboarding and governance audit for VoiceLoop-X. Its role is to establish a single source of truth for:

- What is genuinely implemented
- What is partially implemented or broken
- Which documents are stale or contradictory
- Which research directions are publishable
- What must be fixed first to make CogniHuman's claims rigorous

This audit is intentionally conservative. It treats the codebase and runnable artifacts as the primary source of truth, and treats roadmap documents as plans unless supported by code and measurements.

---

## Executive Verdict

VoiceLoop-X is a **promising research platform**, not yet a finished research contribution.

The repository already contains:

- A real local voice-agent prototype
- A useful latency profiling framework
- A useful benchmark harness
- Saved profiling artifacts showing a real LLM latency bottleneck
- A credible optimization agenda around latency, memory, and hardware constraints

However, the repository also contains:

- Multiple contradictions between docs and code
- A disabled or non-integrated KV cache path
- Validation scripts that no longer match the current application
- Performance claims that are only partially supported
- Research narratives that are stronger than the present implementation state

**Current research maturity**:

- Measurement infrastructure: `moderate to strong`
- Main application correctness/consistency: `mixed`
- Novelty already demonstrated: `limited`
- Publishability after cleanup and experiments: `strong potential`

---

## Research Thesis Reconstructed

Across the roadmap and project docs, the central scientific question is consistent:

**How can an on-device voice agent achieve materially lower latency on constrained hardware without relying on the cloud?**

The repo frames this through five recurring themes:

1. **Latency decomposition**
   Identify which stages dominate end-to-end interaction.

2. **LLM bottleneck reduction**
   Use memory-aware optimization, cache reuse, pipeline overlap, and possibly speculative decoding.

3. **Resource-aware deployment**
   Make the system practical on consumer or low-resource hardware.

4. **Standardized evaluation**
   Build reusable benchmark and profiling methodology for the community.

5. **Open science**
   Keep the work reproducible, inspectable, and educational.

This is a valid and worthwhile research direction for CogniHuman.

---

## What Is Implemented

### 1. Main local voice-agent prototype

The main app in [voice_loop.py](/c:/Users/suris/OneDrive/Documents/python coding/VoiceLoop-X/voice_loop.py:1) is a functioning single-process voice-agent prototype with:

- Silero VAD
- Moonshine transcription
- llama.cpp LLM loading
- Kokoro TTS
- Optional StreamFold-style overlap path
- Cross-platform branches for Windows and Unix-like systems

This is a real system, not just a paper design.

### 2. Latency profiler

The module in [latency_profiler.py](/c:/Users/suris/OneDrive/Documents/python coding/VoiceLoop-X/src/voiceloop/latency_profiler.py:1) is a meaningful research asset:

- Stage timing
- Mean, median, p50, p95, p99, std
- Bottleneck detection
- Recommendation generation
- JSON report generation

The standalone test in [test_profiler.py](/c:/Users/suris/OneDrive/Documents/python coding/VoiceLoop-X/tests/test_profiler.py:1) ran successfully in local validation.

### 3. Benchmark harness

The module in [benchmark_suite.py](/c:/Users/suris/OneDrive/Documents/python coding/VoiceLoop-X/src/voiceloop/benchmark_suite.py:1) is also a meaningful research asset:

- Structured test cases
- WER calculation
- Category-level aggregation
- Resource usage hooks
- JSON export

The standalone test in [test_benchmark.py](/c:/Users/suris/OneDrive/Documents/python coding/VoiceLoop-X/tests/test_benchmark.py:1) ran successfully in local validation.

### 4. Saved profiling and benchmark artifacts

The repository includes stored outputs that support the core bottleneck thesis:

- [research_baseline.json](/c:/Users/suris/OneDrive/Documents/python coding/VoiceLoop-X/data/profiles/research_baseline.json:1)
- [baseline.json](/c:/Users/suris/OneDrive/Documents/python coding/VoiceLoop-X/data/benchmarks/baseline.json:1)
- [kv_test.json](/c:/Users/suris/OneDrive/Documents/python coding/VoiceLoop-X/data/benchmarks/kv_test.json:1)

These artifacts consistently indicate that the LLM path dominates latency.

### 5. StreamFold-style partial overlap concept

There is partial implementation of a pipeline-overlap idea in [voice_loop.py](/c:/Users/suris/OneDrive/Documents/python coding/VoiceLoop-X/voice_loop.py:696):

- transcription is started in the executor
- a 2.5s timeout can trigger a background LLM path
- this is exposed through `--streamfold`

This is not yet a completed research result, but it is a real implementation direction.

---

## What Is Broken Or Incomplete

### 1. KV cache is not integrated into the actual LLM path

The most important broken research claim is KV cache.

The module [kv_cache_optimizer.py](/c:/Users/suris/OneDrive/Documents/python coding/VoiceLoop-X/src/voiceloop/kv_cache_optimizer.py:140) exists, but [voice_loop.py](/c:/Users/suris/OneDrive/Documents/python coding/VoiceLoop-X/voice_loop.py:498) still calls `llm(...)` directly inside `llm_generate`.

That means:

- the cache manager is not the active generation path
- the claimed optimization is not actually governing inference
- the roadmap is correct to treat KV cache as unfinished

### 2. Smart Turn 4s claim does not match code

Several documents say Smart Turn was reduced from 8 seconds to 4 seconds, but the real code still contains:

- `max_samples = 8 * SAMPLE_RATE` in [voice_loop.py](/c:/Users/suris/OneDrive/Documents/python coding/VoiceLoop-X/voice_loop.py:171)

This matters because it weakens both:

- the optimization claim
- confidence in the surrounding docs

### 3. Validation script is stale relative to the current app

The file [validate_improvements.py](/c:/Users/suris/OneDrive/Documents/python coding/VoiceLoop-X/tests/validate_improvements.py:1) expects:

- a `Metrics` class in `voice_loop.py`
- explicit thread locks
- non-blocking `audio_q.put_nowait`
- TTFA instrumentation fields in the app
- download verification paths

Those expected patterns are not present in the current `voice_loop.py`.

Local run result:

- `0/10` checks passed

This means the validation story in the repository is currently unreliable.

### 4. Audio callback still does more than current docs claim

The callback in [voice_loop.py](/c:/Users/suris/OneDrive/Documents/python coding/VoiceLoop-X/voice_loop.py:431) still includes:

- `print(status, file=sys.stderr)`
- `audio_q.put(chunk)`

So the app does not match docs that claim:

- no callback I/O
- non-blocking queue writes

### 5. GPU support is still aspirational

The system is still CPU-only in practice:

- `n_gpu_layers=0` in [voice_loop.py](/c:/Users/suris/OneDrive/Documents/python coding/VoiceLoop-X/voice_loop.py:357)

So any current language implying CUDA, Metal, or Vulkan support should be treated as roadmap language, not active implementation.

### 6. Main-app profiling is incomplete relative to research ambitions

The standalone profiler module is good, but the live application integration is incomplete or inconsistent:

- `record_ttfa()` exists in the profiler module
- the main app does not clearly use it as the canonical end-to-end TTFA path
- saved profile artifacts show empty `summary` sections in some files
- `profiled_utterances` remains `0` in stored artifacts despite stage timings being present

This suggests partial integration rather than a fully closed measurement loop.

### 7. Benchmark artifacts include simulated outputs

The file [benchmark_results.json](/c:/Users/suris/OneDrive/Documents/python coding/VoiceLoop-X/data/benchmarks/benchmark_results.json:1) contains simulated outputs such as:

- placeholder response text
- zero ASR latency
- zero cache hit rate
- empty hypothesized text

This is acceptable for scaffolding, but it is not valid evidence for a scientific claim.

---

## Stale Or Contradictory Documentation

### High-priority stale docs

These documents should not currently be treated as ground truth without revision:

- [IMPROVEMENTS.md](/c:/Users/suris/OneDrive/Documents/python coding/VoiceLoop-X/docs/technical/IMPROVEMENTS.md:1)
- [FOUNDATION_COMPLETE.md](/c:/Users/suris/OneDrive/Documents/python coding/VoiceLoop-X/docs/research/FOUNDATION_COMPLETE.md:1)
- [EXECUTIVE_SUMMARY.md](/c:/Users/suris/OneDrive/Documents/python coding/VoiceLoop-X/docs/research/EXECUTIVE_SUMMARY.md:1)
- [docs/README.md](/c:/Users/suris/OneDrive/Documents/python coding/VoiceLoop-X/docs/README.md:1)

### Typical contradiction patterns

1. **“Implemented” in docs, but not in current code**
   Smart Turn 4s, callback cleanup, validation checks, some TTFA integration details.

2. **“Complete and validated” in docs, but validation fails locally**
   Especially around `validate_improvements.py`.

3. **“GPU support” in high-level descriptions, but CPU-only in runtime**
   Current llama.cpp settings do not enable GPU acceleration.

4. **“KV cache optimization” described as implemented module**
   True as a module artifact, false as an active inference path.

### Documents that remain useful

These are still valuable if read as planning or review documents rather than current-state truth:

- [RESEARCH_ROADMAP.md](/c:/Users/suris/OneDrive/Documents/python coding/VoiceLoop-X/docs/research/RESEARCH_ROADMAP.md:1)
- [TECHNICAL_REVIEW.md](/c:/Users/suris/OneDrive/Documents/python coding/VoiceLoop-X/docs/technical/TECHNICAL_REVIEW.md:1)
- [INDEPENDENT_VERIFICATION.md](/c:/Users/suris/OneDrive/Documents/python coding/VoiceLoop-X/docs/technical/INDEPENDENT_VERIFICATION.md:1)

These are especially useful because they contain skepticism and identify limitations that the current code still reflects.

---

## What The Data Actually Supports

### Strongly supported

1. **LLM inference dominates latency**
   Saved artifacts repeatedly place the LLM first-token stage at roughly `86% to 89%` of measured latency.

2. **This repo has meaningful profiling and benchmarking infrastructure**
   The standalone tests passed and the modules are non-trivial.

3. **Memory pressure is a plausible major factor**
   The docs and runtime configuration both point to constrained-memory operation, and the observed LLM latency is consistent with severe resource pressure.

4. **VoiceLoop-X is a useful research platform for optimization experiments**
   Especially for CPU-bound local voice-agent work.

### Partially supported

1. **StreamFold-style overlap can reduce perceived latency**
   The concept is credible and partially implemented, but no rigorous experiment package currently proves the gain.

2. **Cross-platform support exists**
   OS branches exist, but optimization parity across platforms is not established.

### Not yet supported strongly enough

1. **KV cache as a working improvement**
2. **Smart Turn 4s optimization in current app**
3. **GPU acceleration**
4. **Production-readiness claims**
5. **Benchmark-based scientific conclusions from simulated outputs**

---

## Publishable Directions

This repository can still become the foundation for strong research output if the work is refocused around what is genuinely differentiating.

### Direction 1. Voice-agent latency anatomy on constrained hardware

**Strength**: highest near-term credibility

Potential paper:

- "Latency Anatomy of On-Device Voice Agent Pipelines Under Memory Pressure"

Why this is publishable:

- the repo already has profiling infrastructure
- the bottleneck story is measurable
- the hardware-constrained setting aligns with CogniHuman's mission
- the work can be framed as systems analysis with reproducible methodology

Needed before submission:

- clean live profiling integration
- reproducible runs on real audio
- per-stage ablations across hardware tiers

### Direction 2. VoiceBench as a reproducible benchmark protocol

**Strength**: strong if benchmark artifacts become real, not simulated

Potential paper:

- "VoiceBench: A Reproducible Benchmark for On-Device Voice Agents"

Why this is publishable:

- benchmark standardization is valuable
- the field still lacks stable, open evaluation recipes
- CogniHuman can contribute public-good infrastructure

Needed before submission:

- replace simulated benchmark outputs with real runs
- improve test set coverage
- define metrics and protocols rigorously
- document limitations and hardware setup carefully

### Direction 3. StreamFold as pipeline overlap for local voice agents

**Strength**: strongest candidate for a novel systems contribution

Potential paper:

- "StreamFold: ASR-LLM Pipeline Overlap for CPU-Bound On-Device Voice Agents"

Why this is promising:

- it is closer to a novel systems idea than a pure integration claim
- it targets perceived latency, which matters directly for voice UX
- it can be evaluated with ablations and controlled experiments

Needed before submission:

- formalize the algorithm
- define trigger policy and fallback policy clearly
- compare against a strict baseline
- test across utterance lengths and hardware constraints

### Direction 4. Quantization tradeoff study for local voice agents

**Strength**: high value, lower novelty, still publishable

Potential paper:

- "Quantization Tradeoffs for On-Device Voice Agent Pipelines"

Why this is valuable:

- practical relevance is very high
- results can directly help low-resource deployments
- it aligns with digital-divide goals

Needed before submission:

- actual quantized model sweep
- latency, memory, and quality curves
- consistent protocol and hardware logging

---

## Highest-Priority Fixes

### Priority 0: Restore truth alignment between code, docs, and validation

This is the first research leadership responsibility.

Required actions:

1. Update stale docs to clearly distinguish:
   - implemented
   - partial
   - planned

2. Either repair or retire `tests/validate_improvements.py`

3. Remove or soften claims that exceed current code reality

Without this step, every future result will be harder to trust.

### Priority 1: Make the live profiler scientifically reliable

Required actions:

1. Define the canonical TTFA measurement path in the main app
2. Ensure `summary` and `profiled_utterances` are populated correctly
3. Standardize stage boundaries across runs
4. Save hardware metadata with profile outputs

This unlocks credible experiments.

### Priority 2: Decide the fate of KV cache

Required actions:

1. Either integrate `OptimizedKVCacheManager` properly into `llm_generate`
2. Or explicitly mark KV cache as experimental and inactive everywhere

Current half-state creates confusion and weakens the research narrative.

### Priority 3: Bring callback and concurrency claims in line with implementation

Required actions:

1. Remove callback I/O if safe
2. Decide whether queue writes should be blocking or non-blocking
3. Document the real concurrency model of the app

This improves both correctness and credibility.

### Priority 4: Build a real experiment baseline pack

Required actions:

1. Run the current app with real audio inputs
2. Save reproducible profile outputs
3. Record exact hardware configuration
4. Define baseline runs for:
   - CPU-only
   - different RAM tiers
   - different utterance lengths

This is the bridge from prototype to publishable science.

---

## Recommended Research Program For CogniHuman

### Phase A: Scientific cleanup

Goal:

- Make the repository internally truthful and reproducible

Deliverables:

- corrected docs
- repaired validation story
- reliable main-app profiler outputs

### Phase B: Baseline science

Goal:

- Publish the strongest descriptive result first

Deliverables:

- latency anatomy report
- benchmark protocol draft
- hardware-constrained evaluation matrix

### Phase C: First real novel systems contribution

Goal:

- Turn StreamFold or another overlap-based optimization into a clearly defined contribution

Deliverables:

- formal algorithm description
- implementation
- ablation tables
- negative-result analysis

### Phase D: Broader open-science platform

Goal:

- Make CogniHuman known for reproducible voice-AI systems research

Deliverables:

- benchmark package
- datasets or dialectal extensions
- quantization and low-resource deployment studies
- transparent research notebooks and reports

---

## Leadership Guidance For CogniHuman

If CogniHuman wants to reach the contribution value of strong research organizations, the path is not to imitate their branding language first. The path is to outperform average open-source repos on:

- honesty
- reproducibility
- rigor
- usefulness to others
- clarity about what is and is not solved

This repository already contains the beginnings of that culture, especially in the critical review documents. The next step is to make the implementation and the narrative match each other perfectly.

That is the most credible foundation for world-class contribution.

---

## Immediate Next Actions

1. Treat this audit as the current onboarding source of truth.
2. Revise top-level research/docs language using this audit.
3. Repair live profiling integration in `voice_loop.py`.
4. Produce a clean baseline experiment package with real runs.
5. Choose one flagship research track for implementation:
   - `StreamFold`
   - `VoiceBench`
   - `Quantization study`
   - `KV cache reimplementation`

**Recommended flagship track**: `StreamFold + rigorous latency evaluation`

Reason:

- highest chance of meaningful near-term novelty
- best fit with current bottleneck evidence
- strongest path from prototype to publishable systems result

---

## Audit Conclusion

VoiceLoop-X is not yet a finished research contribution, but it is absolutely capable of becoming one.

Its strongest current value is:

- a real local voice-agent prototype
- real measurement tooling
- a valid bottleneck diagnosis
- a credible agenda for open, public-interest Voice AI systems research

Its biggest current weakness is not lack of ambition. It is lack of alignment between implementation, validation, and documentation.

Once that alignment is repaired, CogniHuman can build from this repo toward genuinely significant Voice AI contributions.
