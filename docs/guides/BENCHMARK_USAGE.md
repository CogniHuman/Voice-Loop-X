# VoiceBench Usage Guide

## Overview

VoiceBench is a standardized benchmark suite for evaluating on-device voice agents. It provides reproducible methodology for measuring performance across different implementations and hardware.

## Quick Start

### Basic Usage

```python
from research.benchmark_suite import VoiceBench

# Initialize benchmark
bench = VoiceBench()

# Define your voice agent function
def my_voice_agent(audio):
    # Your voice agent processing
    transcription = transcribe(audio)
    response = generate_response(transcription)
    return {
        "transcription": transcription,
        "response": response
    }

# Run benchmark
results = bench.benchmark_system(my_voice_agent)

# Print results
bench.print_results(results)

# Save detailed results
bench.save_results(results, "my_results.json")
```

## Test Set Structure

### Categories

VoiceBench organizes test cases into categories:

1. **short_queries** - 1-3 words (greetings, simple commands)
2. **medium_queries** - 5-10 words (typical questions)
3. **long_queries** - 15-30 words (complex questions)
4. **multi_turn** - Conversation sequences
5. **interruptions** - Barge-in test cases

### Test Case Format

Each test case includes:

```json
{
  "id": "short_001",
  "audio_path": "audio/what_time.wav",
  "ground_truth_text": "what time is it",
  "expected_response_type": "factual",
  "duration_sec": 1.2,
  "category": "short",
  "metadata": {"difficulty": "easy"}
}
```

## Creating Test Cases

### Step 1: Record Audio

```bash
# Record at 16kHz, mono, WAV format
# Use high-quality microphone in quiet environment
# Speak naturally and clearly
```

### Step 2: Add to Test Set

```python
# Edit research/test_sets/short_queries.json
{
  "id": "short_004",
  "audio_path": "audio/my_test.wav",
  "ground_truth_text": "hello world",
  "expected_response_type": "conversational",
  "duration_sec": 1.5,
  "category": "short",
  "metadata": {"speaker": "male", "accent": "american"}
}
```

### Step 3: Place Audio File

```bash
# Copy audio to test_sets/audio/
cp my_test.wav research/test_sets/audio/
```

## Benchmark Results

### Example Output

```
VOICEBENCH RESULTS

SHORT QUERIES:
  Tests: 3/3 successful
  TTFA:
    Mean:   687ms
    Median: 675ms
    P95:    823ms
    P99:    845ms
    Range:  623ms - 756ms
  WER:
    Mean:   0.023
    Median: 0.000
  Memory:
    Peak:   12.3MB

MEDIUM QUERIES:
  Tests: 2/2 successful
  TTFA:
    Mean:   892ms
    Median: 892ms
    P95:    1012ms
    P99:    1034ms
    Range:  834ms - 950ms
  WER:
    Mean:   0.031
    Median: 0.031
  Memory:
    Peak:   15.7MB
```

### Metrics Explained

- **TTFA (Time to First Audio)**: End-to-end latency from audio input to first audio output
- **WER (Word Error Rate)**: Transcription accuracy (0.0 = perfect, 1.0 = completely wrong)
- **Memory**: Peak memory usage during processing
- **P95/P99**: 95th/99th percentile (worst-case performance)

## Advanced Usage

### Custom Categories

```python
# Run specific categories only
results = bench.benchmark_system(
    my_voice_agent,
    categories=["short_queries", "medium_queries"]
)
```

### Verbose Output

```python
# Disable progress printing
results = bench.benchmark_system(
    my_voice_agent,
    verbose=False
)
```

### Custom Test Sets

```python
# Use custom test set location
bench = VoiceBench(test_set_path="/path/to/my/tests")
```

## Comparing Results

### Before/After Optimization

```python
import json

# Load baseline
with open('baseline_results.json') as f:
    baseline = json.load(f)

# Load optimized
with open('optimized_results.json') as f:
    optimized = json.load(f)

# Compare
for category in baseline.keys():
    if category in optimized:
        before_ttfa = baseline[category]['ttfa']['mean']
        after_ttfa = optimized[category]['ttfa']['mean']
        improvement = (before_ttfa - after_ttfa) / before_ttfa * 100
        
        print(f"{category}:")
        print(f"  TTFA: {before_ttfa:.0f}ms → {after_ttfa:.0f}ms ({improvement:+.1f}%)")
```

### Cross-Hardware Comparison

```python
# Collect results on different hardware
results_laptop = bench.benchmark_system(agent, verbose=False)
results_desktop = bench.benchmark_system(agent, verbose=False)

# Compare
for category in results_laptop.keys():
    laptop_ttfa = results_laptop[category]['ttfa']['mean']
    desktop_ttfa = results_desktop[category]['ttfa']['mean']
    speedup = laptop_ttfa / desktop_ttfa
    
    print(f"{category}: {speedup:.2f}x faster on desktop")
```

## Research Workflow

### 1. Establish Baseline

```bash
# Run on current system
python -c "
from research.benchmark_suite import VoiceBench
from my_agent import voice_agent

bench = VoiceBench()
results = bench.benchmark_system(voice_agent)
bench.save_results(results, 'baseline.json')
"
```

### 2. Implement Optimization

Make changes to your voice agent based on profiler recommendations.

### 3. Measure Impact

```bash
# Run again after optimization
python -c "
from research.benchmark_suite import VoiceBench
from my_agent import voice_agent

bench = VoiceBench()
results = bench.benchmark_system(voice_agent)
bench.save_results(results, 'optimized.json')
"
```

### 4. Analyze Results

```python
import json
import matplotlib.pyplot as plt

# Load results
with open('baseline.json') as f:
    baseline = json.load(f)
with open('optimized.json') as f:
    optimized = json.load(f)

# Plot comparison
categories = list(baseline.keys())
baseline_ttfa = [baseline[c]['ttfa']['mean'] for c in categories]
optimized_ttfa = [optimized[c]['ttfa']['mean'] for c in categories]

plt.figure(figsize=(10, 6))
x = range(len(categories))
plt.bar([i-0.2 for i in x], baseline_ttfa, width=0.4, label='Baseline')
plt.bar([i+0.2 for i in x], optimized_ttfa, width=0.4, label='Optimized')
plt.xticks(x, categories, rotation=45)
plt.ylabel('TTFA (ms)')
plt.legend()
plt.title('Performance Comparison')
plt.tight_layout()
plt.savefig('comparison.png')
```

## Best Practices

### 1. Consistent Environment

- Use same hardware for comparisons
- Close unnecessary applications
- Disable power saving modes
- Use consistent model settings

### 2. Statistical Significance

- Run multiple iterations (3-5 times)
- Report mean and standard deviation
- Use P95/P99 for worst-case analysis

### 3. Test Set Quality

- Use diverse speakers (gender, accent, age)
- Include various acoustic conditions
- Cover different query types
- Maintain high audio quality (16kHz, low noise)

### 4. Ground Truth Accuracy

- Double-check transcriptions
- Use professional transcription services
- Include punctuation and capitalization
- Normalize text (lowercase, remove punctuation for WER)

## Integration with Profiler

Combine with latency profiler for detailed analysis:

```python
from research.latency_profiler import profiler
from research.benchmark_suite import VoiceBench

# Enable profiler
profiler.enable()

# Run benchmark
bench = VoiceBench()
results = bench.benchmark_system(my_voice_agent)

# Get profiling report
profiler.print_report()
profiler.save_report("profile_during_benchmark.json")
```

## Troubleshooting

### Issue: Audio files not found

```
FileNotFoundError: Audio file not found: audio/test.wav
```

**Solution**: Ensure audio files are in `research/test_sets/audio/` directory.

### Issue: High WER

```
WER: 0.850 (very high)
```

**Solution**: 
- Check ground truth transcription accuracy
- Verify audio quality
- Test transcription model separately

### Issue: Inconsistent results

```
P95 much higher than mean
```

**Solution**:
- Run more iterations
- Check for background processes
- Verify hardware consistency

## Contributing Test Cases

To contribute test cases to VoiceBench:

1. Record high-quality audio (16kHz, mono, WAV)
2. Provide accurate ground truth transcription
3. Include metadata (speaker info, difficulty)
4. Submit via pull request

### Quality Criteria

- Audio: 16kHz, mono, WAV format
- Duration: Match category (short: <2s, medium: 2-4s, long: 4-8s)
- Quality: SNR > 20dB, no clipping
- Transcription: Professionally verified
- Diversity: Various speakers, accents, conditions

## Citation

If you use VoiceBench in research, please cite:

```bibtex
@software{voicebench2024,
  title={VoiceBench: Standardized Benchmark Suite for On-Device Voice Agents},
  author={CogniHuman Research Foundation},
  year={2024},
  url={https://github.com/cognihuman/voiceloop-x}
}
```

## Support

For questions or issues:
- GitHub Issues: [VoiceLoop-X Issues]
- Research: research@cognihuman.org
- Documentation: [VoiceLoop-X Wiki]

---

**CogniHuman Research Foundation**  
*Advancing Voice AI for Public Benefit*
