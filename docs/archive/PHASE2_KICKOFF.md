# 🚀 Phase 2 Kickoff - Audio Collection & Baseline

**Status**: Phase 2 Started  
**Current Task**: Audio Test Case Collection  
**Your Action Required**: Collect/download audio files

---

## 🎯 What You Need to Do Now

### Step 1: Collect Audio Test Cases

**Choose ONE of these options:**

#### **Option A: Record Your Own (Easiest - 30 minutes)**

1. **Download Audacity** (free): https://www.audacityteam.org/download/
   - OR use Windows Voice Recorder (built-in)

2. **Settings**:
   - Format: WAV
   - Sample Rate: 16000 Hz
   - Channels: Mono

3. **Record these queries** (speak naturally):

   **Short (5-10 samples, 1-3 seconds)**:
   - "What time is it?"
   - "Hello"
   - "Thank you"
   - "Goodbye"
   - "Help me"

   **Medium (5-10 samples, 3-5 seconds)**:
   - "What's the weather like today?"
   - "Tell me a joke"
   - "How are you doing?"
   - "Set a timer for five minutes"

   **Long (3-5 samples, 5-10 seconds)**:
   - "Can you explain how photosynthesis works?"
   - "What are the differences between Python and JavaScript?"

4. **Save files** to:
   ```
   research/test_sets/audio/
   ```

5. **Name files** like:
   ```
   short_what_time.wav
   medium_weather_query.wav
   long_explain_photosynthesis.wav
   ```

#### **Option B: Download Public Dataset (Larger - 1-2 hours)**

**LibriSpeech (Recommended)**:
1. Download: https://www.openslr.org/12/ → `test-clean.tar.gz` (346 MB)
2. Extract and find utterances 1-10 seconds long
3. Copy 10-20 files to `research/test_sets/audio/`
4. Rename to match pattern above

**Common Voice**:
1. Download: https://commonvoice.mozilla.org/en/datasets
2. Select "Validated" English clips
3. Filter by duration (1-10 seconds)
4. Copy to `research/test_sets/audio/`

**Google Speech Commands**:
1. Download: http://download.tensorflow.org/data/speech_commands_v0.02.tar.gz (2.3 GB)
2. Extract and select diverse commands
3. Copy to `research/test_sets/audio/`

---

### Step 2: Add Test Cases to JSON

**Easy way** - Use helper script:
```bash
cd research
python add_test_case.py
```

Follow prompts for each audio file you added.

**Manual way** - Edit JSON files:
- `research/test_sets/short_queries.json`
- `research/test_sets/medium_queries.json`
- `research/test_sets/long_queries.json`

---

### Step 3: Run Baseline Benchmark

Once you have audio files:

```bash
# Run with profiler
python voice_loop.py --profile --profile-save baseline_profile.json

# Speak your test queries (or play audio files)
# Let the agent respond
# Repeat 10+ times
# Exit (Ctrl+C)
```

---

## 📁 Files Created for You

### New Guide
- **`docs/guides/PHASE2_AUDIO_COLLECTION.md`** - Complete audio collection guide

### Helper Script
- **`research/add_test_case.py`** - Easy way to add test cases to JSON

### Updated Docs
- **`RESEARCH_CONTEXT.md`** - Updated with Phase 2 status

---

## 📊 What Happens After Audio Collection

Once you complete audio collection and baseline:

1. **Profiler will show** which stage is the bottleneck:
   - LLM First Token (most likely) → Implement KV Cache
   - Transcription → Implement Streaming ASR
   - Overall speed → Implement GPU Acceleration

2. **I will implement** the first optimization based on data

3. **We'll measure** improvement with before/after benchmarks

4. **We'll document** results for research paper

---

## 🎯 Success Criteria

You're ready for the next step when:
- ✅ 10-20 audio files in `research/test_sets/audio/`
- ✅ All files are 16kHz mono WAV format
- ✅ Test cases added to JSON files
- ✅ Baseline profiler report generated
- ✅ Primary bottleneck identified

---

## ⏱️ Time Estimate

- **Option A (Record)**: 30-60 minutes
- **Option B (Download)**: 1-2 hours
- **Add to JSON**: 15-30 minutes
- **Run Baseline**: 15-30 minutes
- **Total**: 1-3 hours

---

## 📞 Questions?

**Read the complete guide**:
- `docs/guides/PHASE2_AUDIO_COLLECTION.md`

**Check current status**:
- `RESEARCH_CONTEXT.md`

**Need help with profiler**:
- `docs/guides/PROFILER_USAGE.md`

---

## 🚀 Quick Start Commands

```bash
# 1. Record audio (use Audacity or Voice Recorder)
# Save to: research/test_sets/audio/

# 2. Add test cases
cd research
python add_test_case.py

# 3. Run baseline
cd ..
python voice_loop.py --profile --profile-save baseline_profile.json

# 4. Let me know when done!
```

---

## 📝 What to Tell Me When Done

Once you've completed audio collection and baseline:

**Share**:
1. Number of test cases collected
2. Profiler output (primary bottleneck)
3. Baseline TTFA (mean)
4. Any issues encountered

**Then I will**:
1. Analyze the bottleneck
2. Implement the appropriate optimization
3. Measure improvement
4. Update documentation

---

**Status**: ⏳ Waiting for audio collection  
**Next**: Implement first optimization based on profiler data  

**CogniHuman Research Foundation**  
*Let's make VoiceLoop-X faster together!* 🚀
