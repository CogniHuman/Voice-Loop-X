# VoiceLoop-X: Developer Quick Reference

## Performance Metrics

### Real-Time Monitoring

During conversation, you'll see:
```
[listening...] (2.3s) [turn prob: 0.87, 42ms]
  [Hello, how can I help you?]
  [TTFA: 720ms]

> I can help you with that!
```

**Metrics Explained**:
- `(2.3s)` - Duration of captured speech
- `[turn prob: 0.87, 42ms]` - Smart Turn confidence (0-1) and latency
- `[TTFA: 720ms]` - Time from speech end to first audio output
- `[voice interrupt]` - AEC detected user speaking during TTS

### Exit Summary

On Ctrl+C, you'll see:
```
Performance Summary:
  Smart Turn avg latency: 45ms (n=12)
  Smart Turn min/max: 38ms / 58ms
```

---

## Architecture Overview

### Pipeline Flow
```
User Speech
    ↓
Silero VAD (speech detection)
    ↓
Buffer accumulation (700ms silence)
    ↓
Smart Turn v3 (endpoint detection, ~42ms)
    ↓
Moonshine (transcription, ~200-500ms)
    ↓
Gemma 4 E2B (LLM inference, ~500-1000ms first token)
    ↓
Kokoro TTS (streaming synthesis, ~50-100ms/chunk)
    ↓
Audio Output (with AEC for interruption)
```

### Thread Safety

**Protected Resources**:
- `record_buf` - Protected by `record_lock`
- `tts_16k_buf` - Protected by `tts_buf_lock`
- `audio_q` - Thread-safe queue (no lock needed)

**Lock Usage**:
```python
# Recording buffer
with record_lock:
    record_buf.append(chunk)

# TTS buffer
with tts_buf_lock:
    tts_16k_buf.append(chunk_samples)
```

---

## Performance Targets

### Latency Budgets
- **TTFA**: < 800ms (target: 720ms)
- **Smart Turn**: < 60ms (target: 42ms)
- **Audio Callback**: < 5ms (target: 2-3ms)
- **AEC Processing**: < 10ms per chunk

### Memory Budgets
- **Total RAM**: ~3.2GB
  - Gemma 4 E2B: ~3.1GB
  - Kokoro TTS: ~300MB
  - Moonshine: ~150MB
  - VAD/Smart Turn: ~100MB

### Allocation Targets
- **AEC**: < 10 allocations/sec (target: 2-5)
- **Audio Callback**: 0 allocations
- **Main Loop**: < 100 allocations/sec

---

## Optimization Techniques

### 1. Zero-Allocation AEC
```python
# Pre-allocate all buffers
_aec_clean_buffer = np.zeros(8192, dtype=np.float32)
_i16_buffer = np.zeros(WF, dtype=np.int16)
_f32_buffer = np.zeros(WF, dtype=np.float32)

# Use in-place operations
np.multiply(mic[i:i+chunk_len], 32767, out=_f32_buffer[:chunk_len])
np.clip(_f32_buffer[:chunk_len], -32768, 32767, out=_f32_buffer[:chunk_len])

# Return view, not copy
return _aec_clean_buffer[:mic_len]
```

### 2. Non-Blocking Audio Callback
```python
def callback(indata, frames, time, status):
    # Minimal processing - no I/O, no blocking
    chunk = indata[:, 0].copy()
    if record_buf is not None:
        with record_lock:
            record_buf.append(chunk)
    audio_q.put_nowait(chunk)  # Non-blocking
```

### 3. Smart Turn 4s Window
```python
# Reduced from 8s to 4s for ~50% faster inference
max_samples = 4 * SAMPLE_RATE  # 64,000 samples at 16kHz
audio_float32 = audio_float32[-max_samples:]
```

---

## Debugging Tips

### Enable Verbose Logging
```python
# Add at top of main()
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Profile Memory Usage
```python
import tracemalloc
tracemalloc.start()

# ... run code ...

snapshot = tracemalloc.take_snapshot()
top_stats = snapshot.statistics('lineno')
for stat in top_stats[:10]:
    print(stat)
```

### Measure Specific Sections
```python
import time
t0 = time.monotonic()
# ... code to measure ...
print(f"Elapsed: {(time.monotonic() - t0) * 1000:.0f}ms")
```

---

## Common Issues

### Issue: High TTFA (> 1000ms)
**Causes**:
- Slow transcription (check Moonshine performance)
- Slow LLM first token (check CPU usage)
- Slow TTS synthesis (check Kokoro performance)

**Debug**:
```python
# Check individual stages
print(f"Transcribe: {(metrics.transcribe_end - metrics.vad_end) * 1000:.0f}ms")
print(f"LLM first token: {(metrics.llm_first_token - metrics.transcribe_end) * 1000:.0f}ms")
print(f"TTS first chunk: {(metrics.tts_first_chunk - metrics.llm_first_token) * 1000:.0f}ms")
```

### Issue: Audio Dropouts
**Causes**:
- Blocking operations in audio callback
- High CPU usage
- Insufficient audio buffer

**Fix**:
- Ensure callback is non-blocking
- Reduce CPU load (lower model sizes)
- Increase `sd.default.latency`

### Issue: High Smart Turn Latency (> 80ms)
**Causes**:
- Using 8s window instead of 4s
- Slow CPU
- ONNX runtime not optimized

**Fix**:
- Verify `max_samples = 4 * SAMPLE_RATE`
- Use faster CPU or reduce window further
- Check ONNX providers

---

## Testing Checklist

### Performance Testing
- [ ] TTFA < 800ms consistently
- [ ] Smart Turn < 60ms average
- [ ] No audio dropouts under load
- [ ] Memory usage < 3.5GB

### Concurrency Testing
- [ ] No race conditions with recording
- [ ] No race conditions with TTS buffer
- [ ] Clean exit with Ctrl+C
- [ ] No corrupted recordings

### Error Handling
- [ ] Graceful streaming failure recovery
- [ ] Partial response preservation
- [ ] Download verification works
- [ ] Error messages are clear

### Cross-Platform
- [ ] Works on Windows
- [ ] Works on Linux
- [ ] Works on macOS
- [ ] Audio devices detected correctly

---

## Performance Tuning

### For Lower Latency
```bash
# Reduce silence threshold
python voice_loop.py --silence-ms 500

# Disable Smart Turn (saves ~42ms)
python voice_loop.py --no-smart-turn
```

### For Lower Memory
```bash
# Use smaller model (if available)
python voice_loop.py --model gemma-4-E2B  # 3.1GB vs 4.2GB for E4B
```

### For Better Quality
```bash
# Increase silence threshold (less false triggers)
python voice_loop.py --silence-ms 900

# Enable memory for context
python voice_loop.py --memory
```

---

## Metrics API

### Access Metrics Programmatically
```python
# In your code
metrics = Metrics()

# After utterance
ttfa = metrics.ttfa()
if ttfa:
    print(f"TTFA: {ttfa:.0f}ms")

# Smart Turn latency
if metrics.smart_turn_latency:
    avg = sum(metrics.smart_turn_latency) / len(metrics.smart_turn_latency)
    print(f"Smart Turn avg: {avg:.0f}ms")
```

### Custom Metrics
```python
class CustomMetrics(Metrics):
    def __init__(self):
        super().__init__()
        self.custom_metric = []
    
    def add_custom(self, value):
        self.custom_metric.append(value)
```

---

## Best Practices

### 1. Always Use Locks for Shared State
```python
# ❌ Bad
shared_list.append(item)

# ✅ Good
with lock:
    shared_list.append(item)
```

### 2. Minimize Audio Callback Work
```python
# ❌ Bad
def callback(indata, frames, time, status):
    print("Processing...")  # I/O in callback!
    process_audio(indata)   # Heavy work in callback!

# ✅ Good
def callback(indata, frames, time, status):
    chunk = indata[:, 0].copy()
    audio_q.put_nowait(chunk)  # Minimal work
```

### 3. Pre-Allocate Buffers
```python
# ❌ Bad
def process(data):
    buffer = np.zeros(len(data))  # Allocates every call
    return buffer

# ✅ Good
buffer = np.zeros(8192)  # Pre-allocate once
def process(data):
    buffer[:len(data)] = data
    return buffer[:len(data)]
```

### 4. Use In-Place Operations
```python
# ❌ Bad
result = data * 32767  # Allocates new array

# ✅ Good
np.multiply(data, 32767, out=buffer)  # In-place
```

---

## Resources

- **[IMPROVEMENTS.md](IMPROVEMENTS.md)** - Detailed implementation guide
- **[TECHNICAL_REVIEW.md](TECHNICAL_REVIEW.md)** - Comprehensive technical review
- **[CONTRIBUTION_SUMMARY.md](CONTRIBUTION_SUMMARY.md)** - Contribution overview
- **[validate_improvements.py](validate_improvements.py)** - Automated validation

---

**Last Updated**: 2024  
**Version**: 1.0 (Production-Ready)  
**Status**: ✅ All improvements verified
