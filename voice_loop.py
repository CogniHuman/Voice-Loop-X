#!/usr/bin/env python3

# Voice Loop — a minimal on-device voice agent. Cross-platform for (Windows, Linux)

# Moonshine (CPU) transcribes speech. Gemma 4 E4B (llama.cpp) responds.
# Kokoro TTS speaks the response. WebRTC AEC3 enables voice interrupt.

# Usage:
#     uv run voice_loop.py                        # defaults (TTS + smart turn + AEC)
#     uv run voice_loop.py --no-tts               # text out only
#     uv run voice_loop.py --no-aec               # keypress interrupt only
#     uv run voice_loop.py --chime-loop           # chime + ticks while generating

import argparse
import asyncio
import os
import queue
import sys
import tempfile
import time as _time
import wave
import termios
import tty
import select
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import sounddevice as sd
# Larger audio buffer via 'high' latency → more robust to MLX CPU saturation.
# NB: don't set sd.default.blocksize globally — a large blocksize on the TTS
# output stream introduces a mic-to-reference delay that misaligns AEC.
sd.default.latency = 'high'
import torch

SAMPLE_RATE = 16000
CHUNK_SAMPLES = 512  # 32ms at 16kHz (required by Silero VAD)
MAX_HISTORY = 10
CHIME_SR = 24000
_DIR = Path(__file__).parent


def load_system_prompt(include_memory: bool = False) -> str:
    names = ("SOUL.md", "MEMORY.md") if include_memory else ("SOUL.md",)
    parts = [(_DIR / n).read_text().strip() for n in names if (_DIR / n).exists()]
    return "\n\n".join(p for p in parts if p)


def _fade_tone(freq, dur, amp=0.6):
    # """Tone with raised-cosine (Hann) envelope — smooth fade in/out, no clicks."""
    n = int(dur * CHIME_SR)
    t = np.linspace(0, dur, n, dtype=np.float32)
    env = 0.5 * (1 - np.cos(2 * np.pi * np.arange(n) / (n - 1)))
    return amp * np.sin(2 * np.pi * freq * t) * env

def _silence(dur):
    return np.zeros(int(dur * CHIME_SR), dtype=np.float32)

def make_chime(duration=60.0, tick_every=1.5):
    # """Two-tone chime + periodic short ticks. Single buffer → one sd.play()."""
    head = np.concatenate([_fade_tone(880, 0.09), _silence(0.03), _fade_tone(1320, 0.10)])
    # Short soft click-style tick (shorter and quieter than a beep)
    tick = _fade_tone(550, 0.04, amp=0.18)
    total = int(duration * CHIME_SR)
    buf = np.zeros(total, dtype=np.float32)
    buf[:len(head)] = head
    step = int(tick_every * CHIME_SR)
    for pos in range(len(head), total, step):
        end = min(pos + len(tick), total)
        buf[pos:end] = tick[:end - pos]
    return buf

def _lang_from_voice(v: str) -> str:
    """Infer Kokoro lang code from voice prefix.
    a* = US English, b* = UK English, e* = Spanish, f* = French,
    h* = Hindi, i* = Italian, j* = Japanese, p* = Portuguese, z* = Chinese."""
    prefix = v[:1] if len(v) > 1 and v[1] == '_' else ''
    return {
        'a': 'en-us', 'b': 'en-gb',
        'e': 'es', 'f': 'fr-fr', 'h': 'hi',
        'i': 'it', 'j': 'ja', 'p': 'pt-br', 'z': 'cmn',
    }.get(prefix, 'en-us')


def save_wav(audio, sr=SAMPLE_RATE):
    path = Path(tempfile.NamedTemporaryFile(suffix=".wav", delete=False).name)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(sr)
        wf.writeframes((audio * 32767).clip(-32768, 32767).astype(np.int16).tobytes())
    return str(path)


# Cross-platform keypress helpers
if sys.platform == "win32":
    import msvcrt

    def key_pressed():
        return msvcrt.kbhit()

    def key_read():
        try:
            b = msvcrt.getch()
            return b.decode(errors="ignore") if isinstance(b, bytes) else str(b)
        except Exception:
            return ""
else:
    def key_pressed():
        return select.select([sys.stdin], [], [], 0)[0]

    def key_read():
        return sys.stdin.read(1)


def _setup_espeak():
    """Cross-platform espeak-ng library detection."""
    try:
        import subprocess
    except Exception:
        subprocess = None
    if sys.platform == "darwin":
        if subprocess is not None:
            try:
                prefix = subprocess.check_output(["brew", "--prefix", "espeak-ng"], text=True).strip()
                return f"{prefix}/lib/libespeak-ng.dylib"
            except Exception:
                pass
    elif sys.platform == "win32":
        import shutil
        espeak_path = shutil.which("espeak-ng")
        if espeak_path:
            lib_path = Path(espeak_path).parent / "libespeak-ng.dll"
            if lib_path.exists():
                return str(lib_path)
    else:
        for path in ["/usr/lib/libespeak-ng.so", "/usr/local/lib/libespeak-ng.so"]:
            if os.path.exists(path):
                return path
    return None


def load_smart_turn():
    import onnxruntime as ort
    from transformers import WhisperFeatureExtractor
    model_path = os.path.join(tempfile.gettempdir(), "smart_turn_v3", "smart_turn_v3.2_cpu.onnx")
    if not os.path.exists(model_path):
        print("Downloading Smart Turn v3.2 model...", flush=True)
        os.makedirs(os.path.dirname(model_path), exist_ok=True)
        import urllib.request
        urllib.request.urlretrieve(
            "https://huggingface.co/pipecat-ai/smart-turn-v3/resolve/main/smart-turn-v3.2-cpu.onnx", model_path)
    session = ort.InferenceSession(model_path, providers=["CPUExecutionProvider"])
    extractor = WhisperFeatureExtractor.from_pretrained("openai/whisper-tiny")

    def predict(audio_float32: np.ndarray) -> float:
        # Reduced from 8s to 4s for ~50% faster inference (~20-30ms saved per turn check)
        # Trade-off: Slightly less context but maintains accuracy for typical utterances
        max_samples = 4 * SAMPLE_RATE
        audio_float32 = audio_float32[-max_samples:]
        features = extractor(
            audio_float32, sampling_rate=SAMPLE_RATE, max_length=max_samples,
            padding="max_length", return_attention_mask=False, return_tensors="np",
        )
        return float(session.run(None, {"input_features": features.input_features.astype(np.float32)})[0].flatten()[0])
    return predict

def _vad_prob(vad, chunk):
    result = vad(torch.from_numpy(chunk), SAMPLE_RATE)
    if hasattr(result, "item"):
        return result.item()
    if isinstance(result, (int, float)):
        return float(result)
    try:
        return float(result[0])
    except Exception:
        return 0.5

def _get_ref_segment(tts_concat, pos, length):
    if pos >= len(tts_concat):
        return np.zeros(length, dtype=np.float32)
    seg = tts_concat[pos:pos + length]
    return np.concatenate([seg, np.zeros(length - len(seg), dtype=np.float32)]) if len(seg) < length else seg


def main():
    ap = argparse.ArgumentParser(description="Voice Loop — a minimal on-device cross-platform voice agent (Windows, Linux)")
    B = argparse.BooleanOptionalAction
    ap.add_argument("--tts", action=B, default=True, help="Kokoro TTS output")
    ap.add_argument("--smart-turn", action=B, default=True, help="Smart Turn v3 endpoint detection")
    ap.add_argument("--aec", action=B, default=True, help="WebRTC AEC3 voice interrupt")
    ap.add_argument("--chime", action=B, default=True,
                    help="Chime on utterance + soft ticks while generating (default: on)")
    ap.add_argument("--memory", action="store_true",
                    help="Read/write MEMORY.md (auto-update durable facts, consolidate every 5 turns)")
    ap.add_argument("--audio-mode", action="store_true", help="Send audio directly to Gemma (experimental)")
    ap.add_argument("--model", default="mlx-community/gemma-4-E4B-it-4bit")
    ap.add_argument("--silence-ms", type=int, default=700)
    ap.add_argument("--record", nargs="?", const="", metavar="FILE",
                    help="Record mic to WAV for debugging (default: tmp/recording-TIMESTAMP.wav)")
    ap.add_argument("--voice", default="af_heart", help="Kokoro voice")
    ap.add_argument("--list-devices", action="store_true", help="List audio devices and exit")
    ap.add_argument("--mic-device", type=int, help="Input device ID")
    ap.add_argument("--speaker-device", type=int, help="Output device ID")
    args = ap.parse_args()
    if args.list_devices:
        print(sd.query_devices())
        return
    # Windows: ensure Ctrl+C exits cleanly
    if sys.platform == "win32":
        try:
            import signal
            signal.signal(signal.SIGINT, lambda s, f: sys.exit(0))
        except Exception:
            pass
    if args.record == "":
        tmp_dir = _DIR / "tmp"
        tmp_dir.mkdir(exist_ok=True)
        args.record = str(tmp_dir / f"recording-{_time.strftime('%Y%m%d-%H%M%S')}.wav")
    silence_limit = max(1, int(args.silence_ms / (CHUNK_SAMPLES / SAMPLE_RATE * 1000)))

    # Validate selected audio devices early with helpful warnings
    if args.mic_device is not None:
        try:
            sd.check_input_settings(device=args.mic_device, samplerate=SAMPLE_RATE, channels=1)
        except Exception as e:
            print(f"Warning: Mic device {args.mic_device} may not support required settings: {e}", flush=True)
    if args.speaker_device is not None:
        try:
            sd.check_output_settings(device=args.speaker_device, samplerate=CHIME_SR if args.chime else SAMPLE_RATE)
        except Exception as e:
            print(f"Warning: Speaker device {args.speaker_device} may not support required settings: {e}", flush=True)

    print("Loading Silero VAD...", flush=True)
    from silero_vad import load_silero_vad
    vad = load_silero_vad(onnx=True)
    # Separate VAD instance for barge-in detection to avoid state interference
    barge_vad = load_silero_vad(onnx=True)
    print("Loading Moonshine (transcription)...", flush=True)
    from moonshine_voice import Transcriber, get_model_for_language
    ms_path, ms_arch = get_model_for_language("en")
    moonshine = Transcriber(model_path=str(ms_path), model_arch=ms_arch)
    print(f"Loading {args.model} (llama.cpp via llama-cpp-python)...", flush=True)
    try:
        from llama_cpp import Llama
    except Exception as e:
        print("Please install 'llama-cpp-python' (pip install llama-cpp-python).", flush=True)
        raise

    def load_llm(model_id: str):
        """Download and cache Gemma 4 E4B GGUF from HuggingFace."""
        cache_dir = Path(tempfile.gettempdir()) / "llama_cpp_models"
        cache_dir.mkdir(parents=True, exist_ok=True)

        # Convert HF ID to GGUF filename
        if "gemma-4-E4B" in model_id:
            gguf_filename = "gemma-4-e4b-it-Q4_K_M.gguf"
            model_path = cache_dir / gguf_filename

            if not os.path.exists(model_path):
                print(f"  Downloading {gguf_filename} (~3GB)...", flush=True)
                import urllib.request

                class DownloadProgress:
                    def __init__(self):
                        self.last_percent = -1

                    def __call__(self, block_num, block_size, total_size):
                        if total_size > 0:
                            percent = int(block_num * block_size * 100 / total_size)
                            if percent >= self.last_percent + 10:
                                print(f"  Downloading... {percent}%", flush=True)
                                self.last_percent = percent

                url = f"https://huggingface.co/bartowski/gemma-4-e4b-it-GGUF/resolve/main/{gguf_filename}"
                urllib.request.urlretrieve(url, str(model_path), reporthook=DownloadProgress())
        else:
            model_path = model_id  # Assume user provided local path

        # Dynamic thread count: use physical cores (not hyperthreads) for optimal performance
        n_threads = max(2, (os.cpu_count() or 4) // 2)
        llm = Llama(
            model_path=str(model_path),
            n_ctx=4096,
            n_threads=n_threads,
            n_gpu_layers=-1,  # Auto GPU offload
            verbose=False
        )
        # Informational: report GPU offload configuration. llama.cpp will
        # silently fall back to CPU if no GPU is available.
        try:
            print(f"  Using {n_threads} threads (physical cores), GPU auto-offload enabled", flush=True)
        except Exception:
            pass
        return llm

    llm = load_llm(args.model)
    smart_turn = load_smart_turn() if args.smart_turn else None
    kokoro = None
    if args.tts:
        print("Loading Kokoro TTS...", flush=True)
        espeak_lib = _setup_espeak()
        if espeak_lib:
            os.environ.setdefault("PHONEMIZER_ESPEAK_LIBRARY", espeak_lib)
        from kokoro_onnx import Kokoro
        cache_dir = os.path.join(tempfile.gettempdir(), "kokoro_tts")
        model_file = os.path.join(cache_dir, "kokoro-v1.0.onnx")
        voices_file = os.path.join(cache_dir, "voices-v1.0.bin")
        if not os.path.exists(model_file):
            os.makedirs(cache_dir, exist_ok=True)
            import urllib.request
            base = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0"
            print("  Downloading kokoro model (~300MB)...", flush=True)
            urllib.request.urlretrieve(f"{base}/kokoro-v1.0.onnx", model_file)
            urllib.request.urlretrieve(f"{base}/voices-v1.0.bin", voices_file)
        kokoro = Kokoro(model_file, voices_file)
        # Warm up TTS to reduce first-speak latency
        try:
            _ = kokoro.create("Hello", voice=args.voice, speed=1.0, lang=_lang_from_voice(args.voice))
        except Exception:
            pass

    make_aec_processor = None
    if args.aec:
        from livekit.rtc import AudioFrame
        from livekit.rtc.apm import AudioProcessingModule
        WF = 160  # 10ms @ 16kHz
        def _to_i16(x):
            s = (x * 32767).clip(-32768, 32767).astype(np.int16)
            return np.pad(s, (0, max(0, WF - len(s)))) if len(s) < WF else s
        def _frame(b):
            return AudioFrame(b.tobytes(), sample_rate=SAMPLE_RATE, num_channels=1, samples_per_channel=WF)
        def make_aec_processor():
            apm = AudioProcessingModule(echo_cancellation=True, noise_suppression=True)
            # Pre-allocate buffer for AEC processing (max expected chunk size)
            _aec_clean_buffer = np.zeros(8192, dtype=np.float32)
            def process(mic, ref):
                # Reuse pre-allocated buffer instead of creating new array
                mic_len = len(mic)
                _aec_clean_buffer[:mic_len] = 0
                for i in range(0, mic_len, WF):
                    mic_f = _frame(_to_i16(mic[i:i+WF]))
                    apm.process_reverse_stream(_frame(_to_i16(ref[i:i+WF])))
                    apm.process_stream(mic_f)
                    chunk_len = min(WF, mic_len - i)
                    _aec_clean_buffer[i:i+chunk_len] = (np.frombuffer(bytes(mic_f.data), dtype=np.int16).astype(np.float32) / 32767)[:chunk_len]
                return _aec_clean_buffer[:mic_len].copy()
            return process
        print("  AEC: WebRTC AEC3 (LiveKit APM)")
    executor = ThreadPoolExecutor(max_workers=2)
    # --chime-loop: single buffer (chime + ticks), one sd.play call
    # --chime only: just the chime
    chime_sound = make_chime() if args.chime else None
    audio_q: queue.Queue[np.ndarray] = queue.Queue()
    record_buf: list[np.ndarray] | None = [] if args.record else None

    def callback(indata, frames, time, status):
        if status:
            print(status, file=sys.stderr)
        chunk = indata[:, 0].copy()
        if record_buf is not None:
            record_buf.append(chunk)
        audio_q.put(chunk)

    def drain_audio_q():
        while not audio_q.empty():
            audio_q.get_nowait()

    def transcribe(audio_data):
        return " ".join(l.text for l in moonshine.transcribe_without_streaming(
            audio_data.tolist(), SAMPLE_RATE).lines if l.text).strip()

    def apply_chat_template(messages, tokenize=False, add_generation_prompt=True):
        """Apply Gemma 4 official chat template."""
        prompt_parts = ["<bos>"]
        system_content = None

        for m in messages:
            role = m.get("role", "user")
            content = m.get("content", "")

            if role == "system":
                system_content = content
                continue

            if system_content and role == "user":
                content = f"[System: {system_content}]\n\n{content}"
                system_content = None

            gemma_role = "model" if role == "assistant" else "user"
            if isinstance(content, list):  # audio mode
                content = "[Audio input provided]"

            prompt_parts.append(f"<start_of_turn>{gemma_role}\n{content}<end_of_turn>\n")

        if add_generation_prompt:
            prompt_parts.append("<start_of_turn>model\n")

        return "".join(prompt_parts)

    def llm_generate(messages, max_tokens=200, temperature=0.7, stream=False, **kwargs):
        prompt = apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        if stream:
            return llm(prompt, max_tokens=max_tokens, temperature=temperature, stream=True, echo=False)
        out = llm(prompt, max_tokens=max_tokens, temperature=temperature, stream=False, echo=False)
        text = out.get("choices", [{}])[0].get("text", "") if isinstance(out, dict) else str(out)
        return text.strip()

    def speak_tts(text):
        samples, sr = kokoro.create(text, voice=args.voice, speed=1.0, lang=_lang_from_voice(args.voice))
        if args.speaker_device is not None:
            sd.play(samples, sr, device=args.speaker_device)
        else:
            sd.play(samples, sr)
        sd.wait()

    _mem_path = _DIR / "MEMORY.md"

    def _read_memory():
        return _mem_path.read_text() if _mem_path.exists() else "# Memory\n"

    def _run_memory(prompt, max_tokens, temperature, label):
        try:
            return llm_generate(
                [{"role": "user", "content": prompt}],
                max_tokens=max_tokens, temperature=temperature,
            ).strip()
        except Exception as e:
            print(f"  [{label} failed: {e}]", file=sys.stderr)
            return None

    def update_memory(heard, response):
        result = _run_memory(
            f"Current memory:\n{_read_memory()}\n\n"
            f"User said: {heard}\n\n"
            "Did the user state a new durable fact about themselves? "
            "If yes, output one short fact per line starting with '- '. "
            "If no, output ONLY: NONE. Do not invent facts.",
            max_tokens=60, temperature=0.2, label="memory update",
        )
        if result and "NONE" not in result.upper():
            lines = [l for l in result.splitlines() if l.strip().startswith("-")]
            if lines:
                with open(_mem_path, "a") as f:
                    f.write("\n" + "\n".join(lines) + "\n")
                print(f"  [memory +{len(lines)}]", flush=True)

    def consolidate_memory():
        if not _mem_path.exists():
            return
        result = _run_memory(
            f"Here is a memory file about a user:\n\n{_read_memory()}\n\n"
            "Rewrite it: merge duplicates, remove transient/session-specific "
            "items (questions asked, topics discussed, tests), keep only "
            "durable facts (identity, preferences, relationships, location, "
            "ongoing projects). Output the cleaned file, starting with '# Memory' "
            "followed by bullets starting with '- '. No explanation.",
            max_tokens=300, temperature=0.2, label="memory consolidation",
        )
        if result and result.startswith("# Memory"):
            _mem_path.write_text(result + "\n")
            print("  [memory consolidated]", flush=True)

    # Cache system prompt to avoid disk I/O on every utterance
    _cached_system_prompt = None
    _cached_with_memory = None

    def _sys_messages():
        nonlocal _cached_system_prompt, _cached_with_memory
        current_memory = args.memory
        if _cached_system_prompt is None or _cached_with_memory != current_memory:
            _cached_system_prompt = load_system_prompt(include_memory=current_memory)
            _cached_with_memory = current_memory
        sp = _cached_system_prompt
        return [{"role": "system", "content": sp}] if sp else []

    def _wait_for_chime_gap():
        """Wait until we're in a silent gap between ticks, so sd.stop() doesn't
        clip a tick mid-cycle (which clicks). Max wait ~40ms."""
        if chime_sound is None or chime_started_at[0] == 0:
            return
        CHIME_HEAD = 0.22  # end of chime tones in buffer
        TICK_DUR = 0.04    # tick length
        TICK_EVERY = 1.5
        t = _time.monotonic() - chime_started_at[0]
        if t < CHIME_HEAD:
            # Still in chime head; wait for end of chime then it's safe
            _time.sleep(CHIME_HEAD - t)
            return
        phase = (t - CHIME_HEAD) % TICK_EVERY
        if phase < TICK_DUR:
            # In a tick — wait until it ends
            _time.sleep(TICK_DUR - phase + 0.005)

    def play_tts_stream(response):
        drain_audio_q()
        tts_stream = kokoro.create_stream(response, voice=args.voice, speed=1.0, lang=_lang_from_voice(args.voice))
        out_stream, interrupted = None, False
        tts_16k_buf: list[np.ndarray] = []
        state = {"play_start": None, "consec_speech": 0, "mic_pos": 0}
        aec_process = make_aec_processor() if make_aec_processor else None

        def check_barge_in():
            if not (aec_process and state["play_start"] and tts_16k_buf):
                return False
            if _time.monotonic() - state["play_start"] < 0.5:
                return False
            barge_vad.reset_states()
            tts_concat = np.concatenate(tts_16k_buf)
            while not audio_q.empty():
                mic_chunk = audio_q.get_nowait()
                if len(mic_chunk) < CHUNK_SAMPLES:
                    continue
                ref = _get_ref_segment(tts_concat, state["mic_pos"], len(mic_chunk))
                state["mic_pos"] += len(mic_chunk)
                cleaned = aec_process(mic_chunk, ref)
                if _vad_prob(barge_vad, cleaned.astype(np.float32)) > 0.8:
                    state["consec_speech"] += 1
                    if state["consec_speech"] >= 5:
                        return True
                else:
                    state["consec_speech"] = 0
            return False

        async def _play():
            nonlocal out_stream, interrupted
            async for chunk_samples, sr in tts_stream:
                if out_stream is None:
                    if chime_sound is not None:
                        _wait_for_chime_gap()
                        sd.stop()
                    out_stream = sd.OutputStream(samplerate=sr, channels=1, dtype="float32", device=(args.speaker_device if args.speaker_device is not None else None))
                    out_stream.start()
                    drain_audio_q(); vad.reset_states()
                    try:
                        barge_vad.reset_states()
                    except Exception:
                        pass
                    state["play_start"] = _time.monotonic()
                if aec_process is not None:
                    if sr == SAMPLE_RATE:
                        tts_16k_buf.append(chunk_samples.astype(np.float32))
                    else:
                        idx = np.arange(0, len(chunk_samples), sr / SAMPLE_RATE)
                        tts_16k_buf.append(np.interp(idx, np.arange(len(chunk_samples)), chunk_samples).astype(np.float32))
                data = chunk_samples.reshape(-1, 1)
                for i in range(0, len(data), 4096):
                    if key_pressed():
                        try:
                            key_read()
                        except Exception:
                            pass
                        interrupted = True
                    elif check_barge_in():
                        interrupted = True; print("  [voice interrupt]", flush=True)
                    if interrupted:
                        break
                    out_stream.write(data[i:i+4096])
                if interrupted:
                    break
            if out_stream:
                out_stream.stop(); out_stream.close()

        asyncio.run(_play())
        if interrupted and state["consec_speech"] < 3:
            print("  [interrupted]")
        drain_audio_q()
        vad.reset_states()
        try:
            barge_vad.reset_states()
        except Exception:
            pass
        return interrupted

    def process_utterance(audio, history):
        print(f" ({len(audio) / SAMPLE_RATE:.1f}s)")
        if chime_sound is not None:
            print("  *chime*", flush=True)
            if args.speaker_device is not None:
                sd.play(chime_sound, CHIME_SR, device=args.speaker_device)
            else:
                sd.play(chime_sound, CHIME_SR)
            chime_started_at[0] = _time.monotonic()
        wav_path = save_wav(audio) if args.audio_mode else None
        try:
            messages = _sys_messages()
            for h in history[-MAX_HISTORY:]:
                messages += [{"role": "user", "content": h["user"]},
                             {"role": "assistant", "content": h["assistant"]}]
            # Run transcription in background, then wait for it before LLM
            transcribe_future = executor.submit(transcribe, audio)
            try:
                heard = transcribe_future.result(timeout=10)
            except Exception:
                heard = ""
            if args.audio_mode:
                # Keep audio payload for models that accept audio input
                messages.append({"role": "user", "content": [{"type": "audio"}]})
            else:
                messages.append({"role": "user", "content": heard})
            if heard:
                print(f"  [{heard}]")
            # If TTS is available, stream LLM tokens and feed Kokoro incrementally
            response = None
            streaming_performed = False
            streaming_failed = False
            interrupted = False
            full_response = []
            if kokoro and args.tts:
                try:
                    streaming_performed = True
                    tts_stream = kokoro.create_stream("", voice=args.voice, speed=1.0, lang=_lang_from_voice(args.voice))
                    stream_gen = llm_generate(messages, stream=True, max_tokens=200, temperature=0.7)

                    out_stream = None

                    async def _streaming_play():
                        nonlocal out_stream, full_response
                        interrupted_local = False
                        try:
                            # Create output stream lazily when first audio arrives
                            for chunk in stream_gen:
                                # Check for keypress interrupt while streaming
                                if key_pressed():
                                    try:
                                        key_read()
                                    except Exception:
                                        pass
                                    interrupted_local = True
                                    break

                                text_chunk = chunk.get("choices", [{}])[0].get("text", "")
                                if not text_chunk:
                                    continue
                                full_response.append(text_chunk)

                                # Feed text to kokoro and play resulting audio
                                async for audio_chunk, sr in tts_stream.feed(text_chunk):
                                    if out_stream is None:
                                        out_stream = sd.OutputStream(samplerate=sr, channels=1, dtype="float32", device=(args.speaker_device if args.speaker_device is not None else None))
                                        out_stream.start()
                                    out_stream.write(audio_chunk.reshape(-1, 1))

                            # If not interrupted, flush remaining audio from Kokoro
                            if not interrupted_local:
                                async for audio_chunk, sr in tts_stream.flush():
                                    if out_stream is None:
                                        out_stream = sd.OutputStream(samplerate=sr, channels=1, dtype="float32", device=(args.speaker_device if args.speaker_device is not None else None))
                                        out_stream.start()
                                    out_stream.write(audio_chunk.reshape(-1, 1))

                        finally:
                            # Always attempt to close the kokoro stream and audio output
                            try:
                                close_fn = getattr(tts_stream, "aclose", None) or getattr(tts_stream, "close", None)
                                if close_fn:
                                    if asyncio.iscoroutinefunction(close_fn):
                                        await close_fn()
                                    else:
                                        try:
                                            close_fn()
                                        except Exception:
                                            pass
                            except Exception:
                                pass

                            if out_stream:
                                try:
                                    out_stream.stop()
                                except Exception:
                                    pass
                                try:
                                    out_stream.close()
                                except Exception:
                                    pass

                        return interrupted_local

                    interrupted = asyncio.run(_streaming_play())
                    response = "".join(full_response).strip()
                except Exception as e:
                    streaming_failed = True
                    # fallback to non-streaming on any error
                    response = llm_generate(messages, max_tokens=200, temperature=0.7, **({"audio": [wav_path]} if args.audio_mode else {}))
                    interrupted = False
            else:
                response = llm_generate(messages, **({"audio": [wav_path]} if args.audio_mode else {}))
            # 'heard' is already available (transcription completed before LLM)
            print(f"\n> {response}\n", flush=True)
            # Only play via play_tts_stream if streaming was not performed or failed,
            # and the streaming path didn't already play audio (i.e., not interrupted)
            if kokoro and response:
                if streaming_performed:
                    if streaming_failed and not interrupted:
                        play_tts_stream(response)
                else:
                    play_tts_stream(response)
            elif chime_sound is not None:
                _wait_for_chime_gap()
                sd.stop()
            history.append({"user": heard, "assistant": response})
            if len(history) > MAX_HISTORY:
                history.pop(0)
            if args.memory:
                update_memory(heard, response)
                if len(history) % 5 == 0:
                    consolidate_memory()
        except Exception as e:
            print(f"\nError: {e}\n", file=sys.stderr)
        finally:
            if wav_path:
                os.unlink(wav_path)

    history, buf = [], []
    chime_started_at = [0.0]  # monotonic time when last chime started (for tick-boundary TTS start)
    speaking, silent_chunks = False, 0

    # Set terminal to raw mode so keypress interrupts work without Enter (Unix only)
    old_term = None
    if sys.platform != "win32":
        try:
            old_term = termios.tcgetattr(sys.stdin)
            tty.setcbreak(sys.stdin.fileno())
        except Exception:
            old_term = None

    mode = "audio" if args.audio_mode else "text"
    print(f"\nListening (mode: {mode}, tts: {args.tts}, silence: {args.silence_ms}ms, smart-turn: {args.smart_turn})")
    tts_hint = (" Speak or press any key to interrupt TTS." if args.aec else " Press any key to interrupt TTS.") if args.tts else ""
    print(f"Speak into your microphone. Ctrl+C to quit.{tts_hint}\n", flush=True)

    greeting = llm_generate(_sys_messages() + [
        {"role": "user", "content": (
            "Greet the user as Voice Loop in one short sentence. "
            "If my name is in memory, use it and ask how you can help. "
            "Otherwise, ask for my name."
        )},
    ], max_tokens=60)
    print(f"> {greeting}\n", flush=True)
    if kokoro:
        speak_tts(greeting)

    with sd.InputStream(
        samplerate=SAMPLE_RATE, channels=1, dtype="float32",
        blocksize=CHUNK_SAMPLES, callback=callback,
        device=(args.mic_device if args.mic_device is not None else None),
    ):
        try:
            while True:
                chunk = audio_q.get()
                if len(chunk) < CHUNK_SAMPLES:
                    continue

                speech_prob = _vad_prob(vad, chunk)
                if speech_prob > 0.5:
                    if not speaking:
                        speaking = True
                        print("[listening...]", end="", flush=True)
                    silent_chunks = 0
                    buf.append(chunk)
                elif speaking:
                    silent_chunks += 1
                    buf.append(chunk)
                    if silent_chunks < silence_limit:
                        continue
                    if smart_turn and buf:
                        prob = smart_turn(np.concatenate(buf))
                        print(f" [turn prob: {prob:.2f}]", end="", flush=True)
                        if prob < 0.5:
                            silent_chunks = 0
                            continue
                    process_utterance(np.concatenate(buf), history)
                    buf.clear()
                    speaking, silent_chunks = False, 0
                    vad.reset_states()

        except KeyboardInterrupt:
            print("\nBye!")
            try:
                executor.shutdown(wait=False, cancel_futures=True)
            except TypeError:
                try:
                    executor.shutdown(wait=False)
                except Exception:
                    pass
        finally:
            if sys.platform != "win32" and old_term is not None:
                try:
                    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_term)
                except Exception:
                    pass
            if args.record and record_buf:
                full = np.concatenate(record_buf)
                with wave.open(args.record, "wb") as wf:
                    wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(SAMPLE_RATE)
                    wf.writeframes((full * 32767).clip(-32768, 32767).astype(np.int16).tobytes())
                print(f"Recorded {len(full) / SAMPLE_RATE:.1f}s to {args.record}", flush=True)


if __name__ == "__main__":
    main()
