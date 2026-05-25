# Latency Profiler Usage Guide

## Overview

The latency profiler is now integrated into VoiceLoop-X. It measures every stage of the voice agent pipeline to identify bottlenecks and guide optimization priorities.

## Quick Start

### Basic Usage

```bash
# Run with profiling enabled
python voice_loop.py --profile

# Run and save detailed report
python voice_loop.py --profile --profile-save my_report.json
```

### What Gets Measured

The profiler tracks these pipeline stages:

1. **VAD Detection** - Speech vs silence detection
2. **Buffer Accumulation** - Silence threshold wait time
3. **Smart Turn** - Endpoint detection inference
4. **Transcription** - Speech-to-text (Moonshine)
5. **LLM First Token** - Time to first LLM response token
6. **LLM Full Generation** - Complete LLM response generation
7. **TTS First Chunk** - Time to first audio synthesis
8. **TTS Full Synthesis** - Complete audio generation
9. **AEC Processing** - Echo cancellation (if enabled)
10. **Total TTFA** - End-to-end time-to-first-audio

## Example Output

```
================================================================================
VOICELOOP-X LATENCY PROFILING REPORT
CogniHuman Research Foundation
================================================================================

SUMMARY:
  Mean TTFA:        847ms
  Median TTFA:      823ms
  P95 TTFA:         1243ms
  P99 TTFA:         1456ms
  Min/Max TTFA:     687ms / 1523ms
  Utterances:       15/15
  Primary Bottleneck: llm_first_token

STAGE BREAKDOWN:
Stage                          Mean       P50        P95        %        Samples 
--------------------------------------------------------------------------------
llm_first_token                523.4      512.1      687.2      61.8     15      
transcription                  234.5      228.3      312.1      27.7     15      
smart_turn                     45.2       43.8       58.3       5.3      15      
tts_first_chunk                67.3       65.2       89.4       7.9      15      
buffer_accumulation            712.3      705.1      850.2      84.1     15      
...

BOTTLENECKS (>15% of total time):
  * llm_first_token: 61.8% (523ms)
  * transcription: 27.7% (235ms)

OPTIMIZATION RECOMMENDATIONS:
  #1 LLM first token is 61.8% of latency (523ms). Consider: (a) KV cache 
     optimization for conversation context reuse, (b) Speculative decoding with 
     draft model, (c) GPU acceleration (CUDA/Metal/Vulkan), (d) Smaller model 
     variant (E2B vs E4B).

  #2 Transcription is 27.7% of latency (235ms). Consider: (a) Streaming ASR 
     with partial results, (b) Smaller Moonshine model, (c) GPU acceleration, 
     (d) Start LLM with partial transcription.

================================================================================
```

## Interpreting Results

### Key Metrics

- **Mean TTFA**: Average time from speech end to first audio output
- **P95/P99**: 95th/99th percentile (worst-case scenarios)
- **Percentage**: How much each stage contributes to total latency
- **Bottlenecks**: Stages taking >15% of total time

### What to Look For

1. **Primary Bottleneck**: Focus optimization here first
2. **High P95/P99**: Indicates inconsistent performance
3. **Percentage Distribution**: Shows where time is spent

## Using the JSON Report

The `--profile-save` option creates a detailed JSON report:

```json
{
  "summary": {
    "mean_ttfa_ms": 847.3,
    "p95_ttfa_ms": 1243.1,
    "total_utterances": 15,
    "primary_bottleneck": "llm_first_token"
  },
  "stages": {
    "llm_first_token": {
      "mean_ms": 523.4,
      "p95_ms": 687.2,
      "percentage": 61.8,
      "samples": 15
    },
    ...
  },
  "bottlenecks": [...],
  "recommendations": [...]
}
```

### Analyzing JSON Data

```python
import json

# Load report
with open('my_report.json') as f:
    report = json.load(f)

# Find biggest bottleneck
bottleneck = report['bottlenecks'][0]
print(f"Optimize: {bottleneck['stage']} ({bottleneck['percentage']:.1f}%)")

# Compare before/after
before_ttfa = 950  # ms
after_ttfa = report['summary']['mean_ttfa_ms']
improvement = (before_ttfa - after_ttfa) / before_ttfa * 100
print(f"Improvement: {improvement:.1f}%")
```

## Research Workflow

### Step 1: Baseline Measurement

```bash
# Collect baseline data (10+ utterances)
python voice_loop.py --profile --profile-save baseline.json
```

### Step 2: Identify Bottlenecks

Review the report and identify the primary bottleneck (usually LLM or transcription).

### Step 3: Implement Optimization

Based on recommendations, implement one optimization at a time.

### Step 4: Measure Impact

```bash
# After optimization
python voice_loop.py --profile --profile-save optimized.json
```

### Step 5: Compare Results

```python
import json

with open('baseline.json') as f:
    baseline = json.load(f)
with open('optimized.json') as f:
    optimized = json.load(f)

before = baseline['summary']['mean_ttfa_ms']
after = optimized['summary']['mean_ttfa_ms']
improvement = (before - after) / before * 100

print(f"TTFA: {before:.0f}ms → {after:.0f}ms ({improvement:+.1f}%)")
```

### Compare Two Profile Files

Use the profile comparison utility for baseline versus candidate runs:

```bash
python compare_profiles.py baseline.json optimized.json

# Save machine-readable comparison output too
python compare_profiles.py baseline.json optimized.json --baseline-label baseline --candidate-label streamfold --output comparison.json
```

For low-RAM laptop experiments, follow:
- [BASELINE_EXPERIMENT_PROTOCOL.md](../research/BASELINE_EXPERIMENT_PROTOCOL.md)

## Tips for Accurate Profiling

1. **Warm-up**: Run 2-3 utterances before profiling (models need warm-up)
2. **Sample Size**: Collect 10+ utterances for statistical significance
3. **Consistency**: Use same hardware, model, and settings for comparisons
4. **Isolation**: Close other applications to reduce noise
5. **Variety**: Test with short, medium, and long utterances

## Common Bottlenecks & Solutions

### LLM First Token (>50%)
- **Cause**: CPU-only inference, no KV cache
- **Solutions**: 
  - Implement KV cache optimization
  - Enable GPU acceleration
  - Use smaller model (E2B vs E4B)
  - Speculative decoding

### Transcription (>25%)
- **Cause**: Moonshine processing time
- **Solutions**:
  - Streaming ASR with partial results
  - GPU acceleration
  - Smaller model variant

### Buffer Accumulation (>20%)
- **Cause**: Fixed 700ms silence threshold
- **Solutions**:
  - Adaptive silence threshold
  - Reduce `--silence-ms` for fast speakers
  - Context-aware detection

### Smart Turn (>10%)
- **Cause**: 4s window Whisper feature extraction
- **Solutions**:
  - Reduce window to 3s or 2s
  - Cache features
  - Adaptive window size

## Integration with Research

The profiler is designed for research use:

```python
from research.latency_profiler import profiler

# In your optimization code
profiler.enable()

# ... run voice agent ...

# Generate report
report = profiler.generate_report()
profiler.save_report("experiment_results.json")
```

## Next Steps

After profiling:

1. Review **RESEARCH_ROADMAP.md** for optimization opportunities
2. Implement highest-impact optimization first
3. Measure before/after with profiler
4. Document results for publication
5. Repeat for next bottleneck

## Support

For questions or issues:
- GitHub Issues: [VoiceLoop-X Issues]
- Research: research@cognihuman.org

---

**CogniHuman Research Foundation**  
*Advancing Voice AI for Public Benefit*
