# Phase 2: Audio Collection & Baseline Benchmark Guide

**Status**: Ready to begin Phase 2  
**Goal**: Collect real audio test cases and establish baseline performance  
**Timeline**: Week 1-2 of Phase 2

---

## 🎯 Overview

Phase 2 starts with collecting real audio test cases and running baseline benchmarks. This data will guide all future optimizations.

---

## 📋 Step 1: Collect Audio Test Cases

### Option A: Record Your Own (Recommended)

**Why**: Best for testing VoiceLoop-X with realistic queries

**Tools Needed**:
- Audacity (free): https://www.audacityteam.org/download/
- OR Windows Voice Recorder (built-in)
- OR any audio recording software

**Recording Settings**:
```
Format: WAV (16-bit PCM)
Sample Rate: 16000 Hz (16 kHz)
Channels: Mono
Bit Depth: 16-bit
```

**What to Record**:

**Short Queries (5-10 samples, 1-3 seconds each)**:
- "What time is it?"
- "Hello"
- "Thank you"
- "Goodbye"
- "Yes"
- "No"
- "Help me"
- "Stop"

**Medium Queries (5-10 samples, 3-5 seconds each)**:
- "What's the weather like today?"
- "Tell me a joke"
- "How are you doing?"
- "What can you do for me?"
- "Set a timer for five minutes"
- "What's the capital of France?"

**Long Queries (3-5 samples, 5-10 seconds each)**:
- "Can you explain how photosynthesis works?"
- "What are the main differences between Python and JavaScript?"
- "Tell me about the history of artificial intelligence"
- "How do I make chocolate chip cookies from scratch?"

**File Naming Convention**:
```
short_<description>.wav
medium_<description>.wav
long_<description>.wav

Examples:
short_what_time.wav
medium_weather_query.wav
long_explain_photosynthesis.wav
```

**Where to Save**:
```
research/test_sets/audio/
```

---

### Option B: Download Public Datasets

**1. LibriSpeech (Clean Speech)**
- URL: https://www.openslr.org/12/
- Download: `test-clean.tar.gz` (346 MB)
- Contains: Clean read speech from audiobooks
- Steps:
  1. Download and extract
  2. Find utterances 1-10 seconds long
  3. Convert to 16kHz mono WAV if needed
  4. Copy to `research/test_sets/audio/`

**2. Common Voice (Mozilla)**
- URL: https://commonvoice.mozilla.org/en/datasets
- Download: English dataset (select "Validated" clips)
- Contains: Real user recordings
- Steps:
  1. Download and extract
  2. Filter by duration (1-10 seconds)
  3. Already in correct format
  4. Copy to `research/test_sets/audio/`

**3. Google Speech Commands**
- URL: http://download.tensorflow.org/data/speech_commands_v0.02.tar.gz
- Download: v0.02 (2.3 GB)
- Contains: Short commands (1 second)
- Perfect for short queries
- Steps:
  1. Download and extract
  2. Select diverse commands
  3. Copy to `research/test_sets/audio/`

---

### Option C: Use VoiceLoop-X to Record

**Steps**:
1. Modify `voice_loop.py` to save recordings
2. Run VoiceLoop-X
3. Speak test queries
4. Audio will be saved automatically

**Code to Add** (optional):
```python
# In voice_loop.py, after transcription
import wave
def save_recording(audio_data, filename):
    with wave.open(filename, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(16000)
        wf.writeframes(audio_data.tobytes())

# After transcription
save_recording(audio_buffer, f"research/test_sets/audio/recording_{timestamp}.wav")
```

---

## 📝 Step 2: Add Test Cases to JSON

### Method A: Use Helper Script (Easy)

```bash
cd research
python add_test_case.py
```

Follow the prompts:
```
Test ID: short_004
Audio filename: what_time.wav
Ground truth text: what time is it
Category: 1 (short)
Response type: 1 (factual)
Duration: 1.2
Difficulty: 1 (easy)
```

### Method B: Edit JSON Manually

Edit `research/test_sets/short_queries.json`:

```json
{
  "id": "short_004",
  "audio_path": "audio/what_time.wav",
  "ground_truth_text": "what time is it",
  "expected_response_type": "factual",
  "duration_sec": 1.2,
  "category": "short",
  "metadata": {
    "difficulty": "easy"
  }
}
```

---

## 🎯 Step 3: Run Baseline Benchmark

### 3.1: Run with Profiler

```bash
# Run VoiceLoop-X with profiler enabled
python voice_loop.py --profile --profile-save baseline_profile.json

# Speak 5-10 test queries
# Let the agent respond
# Exit when done (Ctrl+C)
```

**Expected Output**:
```
======================================================================
VOICELOOP-X LATENCY PROFILING REPORT
======================================================================

SUMMARY:
  Mean TTFA: 847ms
  P95 TTFA: 1243ms
  Utterances: 10
  Primary Bottleneck: llm_first_token

STAGE BREAKDOWN:
Stage                     Mean       P95        %        Samples 
----------------------------------------------------------------------
smart_turn                45.2       58.3       5.3      10      
transcription             234.5      312.1      27.7     10      
llm_first_token           523.4      687.2      61.8     10      
tts_first_chunk           67.3       89.4       7.9      10      
total_ttfa                847.3      1243.1     100.0    10      

BOTTLENECKS (>20% of total time):
  • llm_first_token: 61.8% (523ms)
  • transcription: 27.7% (235ms)

RECOMMENDATIONS:
  1. LLM first token is 61.8% of latency. Consider: KV cache optimization, 
     speculative decoding, or GPU acceleration.
  2. Transcription is 27.7% of latency. Consider: streaming ASR, smaller 
     model, or GPU acceleration.
======================================================================
```

### 3.2: Run Benchmark Suite

```python
# Create benchmark script
from research.benchmark_suite import VoiceBench

# Initialize benchmark
bench = VoiceBench()

# Run benchmark (this will use your audio files)
results = bench.benchmark_system(voice_agent)

# Print results
bench.print_results(results)

# Save results
bench.save_results(results, "baseline_benchmark.json")
```

**Expected Output**:
```
======================================================================
VOICEBENCH RESULTS
======================================================================

SHORT_QUERIES:
  Tests: 10/10 successful
  TTFA: 687ms (mean), 892ms (p95)
  WER: 0.023 (mean)
  Memory: 3.2GB (peak)

MEDIUM_QUERIES:
  Tests: 8/8 successful
  TTFA: 892ms (mean), 1156ms (p95)
  WER: 0.031 (mean)
  Memory: 3.3GB (peak)

LONG_QUERIES:
  Tests: 5/5 successful
  TTFA: 1243ms (mean), 1687ms (p95)
  WER: 0.045 (mean)
  Memory: 3.4GB (peak)
======================================================================
```

---

## 📊 Step 4: Analyze Results

### Identify Primary Bottleneck

Based on profiler output, the bottleneck will likely be one of:

**1. LLM First Token (Most Likely)**
- If >50% of latency
- **Solution**: KV Cache Optimization or GPU Acceleration
- **Expected Impact**: 40-60% reduction

**2. Transcription (Likely)**
- If >25% of latency
- **Solution**: Streaming ASR or GPU Acceleration
- **Expected Impact**: 300-500ms reduction

**3. TTS First Chunk (Less Likely)**
- If >15% of latency
- **Solution**: Model warm-up or caching
- **Expected Impact**: 100-200ms reduction

### Document Baseline

Create `baseline_report.md`:

```markdown
# VoiceLoop-X Baseline Performance Report

**Date**: [Today's Date]
**Hardware**: [Your CPU/GPU]
**Test Cases**: [Number of test cases]

## Performance Metrics

### TTFA (Time to First Audio)
- Mean: XXXms
- P95: XXXms
- P99: XXXms

### Bottlenecks
1. [Primary bottleneck]: XX% (XXXms)
2. [Secondary bottleneck]: XX% (XXXms)

### Recommendations
1. Implement [Optimization #1]
2. Implement [Optimization #2]

## Next Steps
- Implement [Primary optimization]
- Expected improvement: XX%
- Timeline: X weeks
```

---

## 🚀 Step 5: Choose First Optimization

Based on profiler results:

### If LLM is Bottleneck (>50%)
→ **Implement KV Cache Optimization**
- Expected: 40-60% latency reduction
- Difficulty: Medium
- Timeline: 2-3 weeks

### If Transcription is Bottleneck (>25%)
→ **Implement Streaming ASR**
- Expected: 300-500ms latency reduction
- Difficulty: Easy
- Timeline: 1-2 weeks

### If Overall Speed is Issue
→ **Implement GPU Acceleration**
- Expected: 3-5x speedup
- Difficulty: Medium
- Timeline: 2-3 weeks

---

## 📋 Checklist

### Audio Collection
- [ ] Recorded/downloaded 5-10 short queries
- [ ] Recorded/downloaded 5-10 medium queries
- [ ] Recorded/downloaded 3-5 long queries
- [ ] All audio files in `research/test_sets/audio/`
- [ ] All audio files are 16kHz mono WAV

### Test Case Setup
- [ ] Updated `short_queries.json`
- [ ] Updated `medium_queries.json`
- [ ] Updated `long_queries.json`
- [ ] Verified ground truth text is accurate

### Baseline Benchmark
- [ ] Ran VoiceLoop-X with profiler
- [ ] Collected 10+ utterances
- [ ] Saved profiler report (`baseline_profile.json`)
- [ ] Ran benchmark suite
- [ ] Saved benchmark results (`baseline_benchmark.json`)

### Analysis
- [ ] Identified primary bottleneck
- [ ] Documented baseline performance
- [ ] Chose first optimization
- [ ] Created baseline report

---

## 🎯 Expected Timeline

**Week 1**:
- Day 1-2: Collect audio test cases (10-20 samples)
- Day 3: Add test cases to JSON files
- Day 4: Run baseline profiler
- Day 5: Run baseline benchmark
- Day 6-7: Analyze results and document

**Week 2**:
- Begin implementing first optimization

---

## 📞 Need Help?

If you encounter issues:

1. **Audio Format Issues**: Use Audacity to convert to 16kHz mono WAV
2. **Profiler Not Working**: Check `voice_loop.py` has profiler integration
3. **Benchmark Errors**: Verify audio files exist and JSON paths are correct
4. **Analysis Questions**: Review `docs/guides/PROFILER_USAGE.md`

---

## 🎉 Success Criteria

You're ready to proceed when:
- ✅ 10-20 audio test cases collected
- ✅ All test cases added to JSON files
- ✅ Baseline profiler report generated
- ✅ Baseline benchmark results saved
- ✅ Primary bottleneck identified
- ✅ First optimization chosen

---

**Next**: Once baseline is complete, we'll implement the first optimization based on your profiler results!

**CogniHuman Research Foundation**  
*Advancing Voice AI for Public Benefit*
