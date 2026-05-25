# VoiceLoop-X ASR Validity Investigation

**Organization**: CogniHuman Research Foundation  
**Date**: 2026-05-25  
**Scope**: Why Moonshine appeared to fail on almost all recorded WAV inputs

---

## Executive Finding

The initial Moonshine transcription failure was **not primarily an ASR-model failure**.

The main issue was **dataset contamination**:

- `tests/test_benchmark.py` generated synthetic sine-wave audio
- it wrote those files directly into `data/test_cases/audio`
- later frontend baseline runs used those synthetic files as if they were real speech

This made Moonshine appear broken when it was actually being fed non-speech placeholder audio.

---

## Evidence

### 1. Benchmark test overwrote research audio paths

The benchmark test previously wrote synthetic data to:

- `audio_path = bench.test_set_path / case.audio_path`

with:

- a `440Hz` sine wave
- duration derived from the test case metadata

This behavior was present in [test_benchmark.py](/c:/Users/suris/OneDrive/Documents/python coding/VoiceLoop-X/tests/test_benchmark.py:1) before the fix.

### 2. Audio signatures looked synthetic

Inspection of multiple WAV files showed highly uniform characteristics across supposedly different utterances:

- nearly identical RMS
- nearly identical peak amplitude
- nearly full nonzero ratio
- duration-specific but otherwise highly regular waveform behavior

These are strong signs of generated test tones rather than natural recorded speech.

### 3. Moonshine file loading was valid

Moonshine's own `load_wav_file()` successfully loaded the test assets as:

- mono audio
- float PCM
- 16kHz sample rate

That reduced the likelihood of a simple file-format parsing error and shifted suspicion toward signal content.

### 4. Frontend baseline outputs matched the contamination hypothesis

The warmed frontend baseline in [frontend_baseline_full.json](/c:/Users/suris/OneDrive/Documents/python coding/VoiceLoop-X/data/profiles/frontend_baseline_full.json:1) showed:

- 23 measured files
- only 1 non-empty transcript
- that one transcript still poor and fragmentary

This is consistent with feeding mostly non-speech audio into an ASR pipeline.

---

## Fix Applied

The benchmark test has been corrected so it no longer mutates the real dataset.

Current behavior:

- synthetic WAVs are written to a temporary directory
- the benchmark instance is pointed at the temp audio tree
- the research dataset under `data/test_cases/audio` is no longer overwritten by the test

See:

- [test_benchmark.py](/c:/Users/suris/OneDrive/Documents/python coding/VoiceLoop-X/tests/test_benchmark.py:1)

---

## Research Implications

This is a valuable finding for CogniHuman because it changes the interpretation of our earlier ASR result.

### What we should **not** conclude

- "Moonshine is unusable on this laptop"
- "Our frontend stack is fundamentally failing"
- "Streaming ASR research should be deprioritized"

### What we **can** conclude

- dataset integrity controls were insufficient
- benchmark validation tooling and research assets were not isolated properly
- frontend measurements must be interpreted only after verifying input authenticity

This is exactly why serious research workflows separate:

- real evaluation data
- synthetic test fixtures
- benchmark scaffolding

---

## Current State

### Resolved

- future benchmark test runs will not corrupt the dataset

### Still unresolved

- the original real speech WAV content that was overwritten earlier is not yet recovered
- full end-to-end baseline is still blocked by `llama-cpp-python` install issues on Python 3.13 / Windows

---

## Next Research Steps

1. Recover or regenerate a trustworthy speech evaluation set
   - preferred: restore original real recordings if available
   - fallback: create a new clean speech set with documented provenance

2. Rerun the frontend baseline on authentic speech only
   - same warmed protocol
   - same device
   - same saved artifact structure

3. Resume Moonshine validity evaluation
   - compare `transcribe_without_streaming()` versus streaming/session ingestion
   - report both latency and transcript quality

4. Unblock the full LLM runtime
   - move to Python 3.12 or another environment where `llama-cpp-python` installs cleanly

---

## Lesson For CogniHuman

This incident is not a setback if we treat it correctly.

It is an early demonstration of a research discipline that CogniHuman should keep:

- verify the dataset before blaming the model
- isolate test fixtures from evaluation assets
- preserve negative findings
- fix methodology before optimizing results

That is how open research becomes credible.
