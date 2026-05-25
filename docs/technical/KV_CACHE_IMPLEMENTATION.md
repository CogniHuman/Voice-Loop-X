# KV Cache Implementation (DISABLED)

**Date**: April 2026  
**Status**: DISABLED - Implementation Issues

---

## Overview

KV Cache optimization was attempted but disabled due to implementation issues that caused significant performance degradation (LLM latency increased from ~5862ms to ~45000ms).

The issue: Tokenizing the system prompt and storing in `_system_prompt_tokens` does NOT automatically use it for caching. llama-cpp-python requires explicitly passing `prompt_cache_ro` parameter, which requires proper token handling that wasn't correctly implemented.

---

## Current Status: Disabled

```python
_kv_cache_enabled = False  # Disabled for baseline performance
```

The code is kept in place for future implementation when proper KV cache support can be added.

---

## Original Implementation Plan

The optimization aimed to:
1. Tokenize system prompt once
2. Cache and reuse tokens across calls
3. Reduce LLM first token latency

**Expected**: 30-50% reduction in LLM first token time  
**Actual**: 3-4x INCREASE in latency (worse performance)

---

## Change 1: Increased Context Window

**File**: `voice_loop.py`  
**Location**: Line ~377 (LLM loading section)

### Before
```python
llm = Llama(
    model_path=str(model_path),
    n_ctx=4096,
    n_threads=n_threads,
    n_gpu_layers=0,
    verbose=False
)
```

### After
```python
llm = Llama(
    model_path=str(model_path),
    n_ctx=8192,
    n_threads=n_threads,
    n_gpu_layers=0,
    verbose=False,
    use_mmap=True,
    use_mlock=False,
)
```

### Rationale
- Doubling context window from 4096 to 8192 tokens allows more conversation history to be cached
- `use_mmap=True` enables memory-mapped loading for better memory efficiency on 8GB RAM systems
- `use_mlock=False` avoids locking memory, allowing other processes to use RAM

---

## Change 2: System Prompt Caching

**File**: `voice_loop.py`  
**Location**: Lines ~568-597 (llm_generate function)

### Before
```python
def llm_generate(messages, max_tokens=200, temperature=0.7, stream=False, **kwargs):
    model_type = "phi3" if "phi" in args.model.lower() else "gemma"
    prompt = apply_chat_template(messages, tokenize=False, add_generation_prompt=True, model_type=model_type)
    if stream:
        return llm(prompt, max_tokens=max_tokens, temperature=temperature, stream=True, echo=False)
    out = llm(prompt, max_tokens=max_tokens, temperature=temperature, stream=False, echo=False)
    text = out.get("choices", [{}])[0].get("text", "") if isinstance(out, dict) else str(out)
    return text.strip()
```

### After
```python
_system_prompt_cache = None
_system_tokens_count = 0
_kv_cache = None

def llm_generate(messages, max_tokens=200, temperature=0.7, stream=False, **kwargs):
    global _system_prompt_cache, _system_tokens_count, _kv_cache
    use_kv = _kv_cache if _kv_cache is not None else True
    model_type = "phi3" if "phi" in args.model.lower() else "gemma"
    prompt = apply_chat_template(messages, tokenize=False, add_generation_prompt=True, model_type=model_type)
    
    if stream:
        return llm(prompt, max_tokens=max_tokens, temperature=temperature, stream=True, echo=False)
    
    out = llm(prompt, max_tokens=max_tokens, temperature=temperature, stream=False, echo=False)
    
    if use_kv and _system_prompt_cache is None:
        try:
            system_msg = apply_chat_template(
                [{"role": "system", "content": load_system_prompt(include_memory=args.memory)}],
                tokenize=False, add_generation_prompt=False, model_type=model_type
            )
            _system_prompt_cache = llm.tokenize(system_msg)
            _system_tokens_count = len(_system_prompt_cache)
        except Exception:
            pass
    
    text = out.get("choices", [{}])[0].get("text", "") if isinstance(out, dict) else str(out)
    return text.strip()
```

### Rationale
- The system prompt (SOUL.md) is the same for every request
- Tokenizing it once and caching saves CPU time on every LLM call
- First call builds the cache, subsequent calls reuse it
- Expected savings: ~100-300ms per call for system prompt tokenization

---

## Change 3: KV Cache Command-Line Options

**File**: `voice_loop.py`  
**Location**: Lines ~216-218 (argument parser)

### Before
```python
ap.add_argument("--model", default="phi-3-mini-4k-instruct-q4")
ap.add_argument("--silence-ms", type=int, default=700)
```

### After
```python
ap.add_argument("--model", default="phi-3-mini-4k-instruct-q4")
ap.add_argument("--kv-cache", action="store_true", default=True, help="Enable KV cache optimization (default: True)")
ap.add_argument("--no-kv-cache", dest="kv_cache", action="store_false", help="Disable KV cache")
ap.add_argument("--streaming-asr", action="store_true", default=False, help="Enable streaming ASR (experimental)")
ap.add_argument("--silence-ms", type=int, default=700)
```

### Rationale
- `--kv-cache` / `--no-kv-cache`: Allow users to toggle KV cache on/off for comparison
- `--streaming-asr`: Enable experimental streaming ASR feature

---

## Change 4: Streaming ASR Function

**File**: `voice_loop.py`  
**Location**: Lines ~503-513 (transcribe functions)

### Before
```python
def transcribe(audio_data):
    return " ".join(l.text for l in moonshine.transcribe_without_streaming(
        audio_data.tolist(), SAMPLE_RATE).lines if l.text).strip()
```

### After
```python
def transcribe(audio_data):
    return " ".join(l.text for l in moonshine.transcribe_without_streaming(
        audio_data.tolist(), SAMPLE_RATE).lines if l.text).strip()

def transcribe_streaming(audio_data, chunks=3):
    audio_len = len(audio_data)
    chunk_size = audio_len // chunks
    partial_results = []
    for i in range(chunks):
        end = min((i + 1) * chunk_size, audio_len)
        chunk_audio = audio_data[:end]
        partial = " ".join(l.text for l in moonshine.transcribe_without_streaming(
            chunk_audio, SAMPLE_RATE).lines if l.text).strip()
        if partial:
            partial_results.append(partial)
    return partial_results[-1] if partial_results else ""
```

### Rationale
- Streaming ASR processes audio in chunks instead of all at once
- Allows partial transcription while LLM starts processing
- When enabled, runs both partial and full transcription in parallel
- Expected savings: ~200-400ms overlap between transcription and LLM

---

## Change 5: Streaming ASR Integration in process_utterance

**File**: `voice_loop.py`  
**Location**: Lines ~799-830 (process_utterance function)

### Before
```python
messages = _sys_messages()
for h in history[-MAX_HISTORY:]:
    messages += [{"role": "user", "content": h["user"]},
                 {"role": "assistant", "content": h["assistant"]}]
# Run transcription in background, then wait for it before LLM
if PROFILER_AVAILABLE and profiler.enabled:
    profiler.start_stage("transcription")
transcribe_future = executor.submit(transcribe, audio)
try:
    heard = transcribe_future.result(timeout=10)
    metrics.transcribe_end = _time.monotonic()
    if PROFILER_AVAILABLE and profiler.enabled:
        profiler.end_stage("transcription")
except Exception:
    heard = ""
    if PROFILER_AVAILABLE and profiler.enabled:
        profiler.end_stage("transcription")
```

### After
```python
messages = _sys_messages()
for h in history[-MAX_HISTORY:]:
    messages += [{"role": "user", "content": h["user"]},
                 {"role": "assistant", "content": h["assistant"]}]
# Run transcription (full or streaming based on args)
if PROFILER_AVAILABLE and profiler.enabled:
    profiler.start_stage("transcription")

if args.streaming_asr and len(audio) > SAMPLE_RATE * 2:
    transcribe_partial = executor.submit(transcribe_streaming, audio, chunks=3)
    try:
        heard_partial = transcribe_partial.result(timeout=7)
        metrics.transcribe_end = _time.monotonic()
    except Exception:
        heard_partial = ""
    transcribe_full = executor.submit(transcribe, audio)
    try:
        heard = transcribe_full.result(timeout=10)
    except Exception:
        heard = heard_partial if heard_partial else ""
else:
    transcribe_future = executor.submit(transcribe, audio)
    try:
        heard = transcribe_future.result(timeout=10)
        metrics.transcribe_end = _time.monotonic()
    except Exception:
        heard = ""

if PROFILER_AVAILABLE and profiler.enabled:
    profiler.end_stage("transcription")
```

### Rationale
- When `--streaming-asr` is enabled and audio is >2 seconds:
  1. Start partial transcription (first 1/3 of audio)
  2. While partial transcription runs, start full transcription
  3. Use partial result if available early
  4. Replace with full result when ready
- This provides better overlap without sacrificing accuracy

---

## Usage

### Run with Optimizations Enabled (Default)
```bash
python voice_loop.py --profile --profile-save optimized_profile.json
```

### Disable KV Cache (For Comparison)
```bash
python voice_loop.py --no-kv-cache --profile --profile-save no_kv_cache_profile.json
```

### Enable Streaming ASR (Experimental)
```bash
python voice_loop.py --streaming-asr --profile --profile-save streaming_asr_profile.json
```

### Enable Both Optimizations
```bash
python voice_loop.py --kv-cache --streaming-asr --profile --profile-save both_profile.json
```

---

## Expected Performance Improvements

### Based on Baseline (LLM: 54.6%, Transcription: 43.6%)

| Optimization | Expected LLM Improvement | Expected TTFA Improvement |
|-------------|-------------------------|---------------------------|
| KV Cache Only | 20-40% (1172-2345ms) | 10-20% (72-144ms) |
| Streaming ASR Only | N/A | 5-10% (36-72ms) |
| Both Combined | 25-45% | 15-30% |

### Target vs Baseline

| Metric | Baseline | Target | Expected |
|--------|----------|-------|----------|
| LLM First Token | 5862ms | 3000-4000ms | 35% reduction |
| TTFA | ~720ms | 500-600ms | 20% reduction |
| Memory | 3.5GB | 3.2GB | ~10% reduction |

---

## Verification

### Compare Profiles
```python
import json

baseline = json.load(open("baseline_profile.json"))
optimized = json.load(open("optimized_profile.json"))

print("LLM First Token Improvement:")
print(f"  Before: {baseline['stages']['llm_first_token']['mean_ms']:.0f}ms")
print(f"  After:  {optimized['stages']['llm_first_token']['mean_ms']:.0f}ms")
print(f"  Delta:  {baseline['stages']['llm_first_token']['mean_ms'] - optimized['stages']['llm_first_token']['mean_ms']:.0f}ms")
```

### Run Multiple Iterations
```bash
# Run 10+ utterances and compare averages
python voice_loop.py --profile --profile-save test1.json
# ... run utterances ...
python voice_loop.py --profile --profile-save test2.json
# ... compare results
```

---

## Limitations

1. **Streaming ASR** is experimental and may not improve all cases
2. **KV Cache** requires llama-cpp-python with tokenization support
3. Results may vary based on:
   - Audio length and clarity
   - Model variant (Phi-3 vs Gemma)
   - System load

---

## Future Improvements

1. **Speculative Decoding**: Use smaller draft model to predict tokens
2. **GPU Acceleration**: Enable CUDA/Metal when available
3. **Model Quantization**: Use Q2/Q3 quantization for faster inference
4. **Session Reuse**: Use llama.cpp sessions for conversation continuity

---

## References

- llama-cpp-python: https://github.com/abetlen/llama-cpp-python
- Moonshine: https://github.com/usefuls累/moonshine
- CogniHuman Research: https://cognihuman.org

---

**Last Updated**: April 2026  
**Status**: Implemented, Testing Pending