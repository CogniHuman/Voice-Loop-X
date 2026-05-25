# VoiceLoop-X Baseline Experiment Protocol

**Organization**: CogniHuman Research Foundation  
**Purpose**: Collect low-noise baseline and `StreamFold` latency evidence on constrained hardware  
**Primary target device**: 8 GB RAM laptop, CPU-first execution

---

## Why This Protocol Exists

Large labs do not treat latency measurement as an afterthought. They define:

- a concrete latency target
- a repeatable input set
- a fixed hardware context
- a before/after comparison protocol
- a quality guardrail, not just a speed claim

For VoiceLoop-X, this protocol is the minimum standard for claiming improvements on constrained local hardware.

---

## Research Principles

This protocol is designed around three ideas that show up repeatedly in current voice research:

1. **Latency must be measured explicitly**
2. **Streaming systems should overlap work**
3. **Systems research needs throughput and streamability evidence**

Sources:

- [Google on-device streaming ASR](https://research.google/pubs/a-streaming-on-device-end-to-end-model-surpassing-server-side-conventional-model-quality-and-latency/)
- [FastEmit](https://research.google/pubs/fastemit-low-latency-streaming-asr-with-sequence-level-emission-regularization/)
- [Moshi](https://arxiv.org/abs/2410.00037)
- [OpenAI low-latency voice infrastructure](https://openai.com/index/delivering-low-latency-voice-ai-at-scale/)
- [VoxServe](https://arxiv.org/abs/2602.00269)

---

## Hardware Context For Current Phase

Current CogniHuman baseline device:

- RAM: `8.0 GB`
- Available RAM during normal use: about `1.5 GB`
- CPU-bound execution expected
- Severe memory pressure possible

This matters because:

- large-model latency can be dominated by memory pressure rather than compute alone
- “works on a flagship workstation” is not aligned with CogniHuman’s mission
- improvements that help this class of device are especially valuable

---

## Primary Experiment Question

**Does `StreamFold` reduce TTFA and end-to-end latency on constrained CPU-only hardware without making the system less stable?**

---

## Experiment Design

### Comparison arms

1. `baseline`  
   `python voice_loop.py --profile --profile-save data/profiles/baseline_live.json`

2. `streamfold`  
   `python voice_loop.py --streamfold --profile --profile-save data/profiles/streamfold_live.json`

Keep everything else identical across both runs.

### Controlled variables

- same laptop
- same power mode if possible
- same microphone and speaker devices
- same environment and background noise level
- same voice persona and TTS settings
- same model
- same `--silence-ms`

### Input set

Use the same utterance list for both runs:

- 5 short utterances
- 5 medium utterances
- 5 long utterances

Recommended focus for `StreamFold`:

- medium and long utterances
- especially turns where transcription takes longer than 2.5s

### Warm-up policy

Before saving any profile:

- run 2 to 3 warm-up utterances
- discard those measurements

---

## Data Collection Rules

### Minimum sample size

For each arm:

- target at least `15 measured utterances`
- minimum acceptable: `10`

### Notes to record manually

For each run, log:

- date and local time
- whether the laptop was on battery or plugged in
- approximate available RAM before start
- whether major background apps were open
- whether audible glitches or interruptions occurred

### Output files

Store profiles in:

- `data/profiles/baseline_live.json`
- `data/profiles/streamfold_live.json`

Store comparison output in:

- `data/profiles/streamfold_vs_baseline.json`

Generate comparison with:

```bash
python compare_profiles.py data/profiles/baseline_live.json data/profiles/streamfold_live.json --baseline-label baseline --candidate-label streamfold --output data/profiles/streamfold_vs_baseline.json
```

---

## Primary Metrics

### Must report

1. `mean_ttfa_ms`
2. `p95_ttfa_ms`
3. `end_to_end mean`
4. `transcription mean`
5. `llm_first_token mean`
6. `llm_full_generation mean`

### Interpretation rule

For `StreamFold`, the strongest positive signal is:

- TTFA down
- end-to-end not significantly worse
- no obvious increase in instability

---

## Decision Criteria

### Positive result

Treat the experiment as a positive signal if:

- mean TTFA improves by at least `10%`
- p95 TTFA also improves
- no repeated audio failures or profiling anomalies appear

### Mixed result

Treat the experiment as mixed if:

- mean TTFA improves but p95 degrades
- improvement appears only on long queries
- the run shows instability or noisy stage accounting

### Negative result

Treat the experiment as negative if:

- TTFA does not improve materially
- end-to-end latency worsens significantly
- the background overlap path increases instability

Negative results are still useful and should be documented.

---

## Resource-Constrained Operating Guidance

To respect the current 8 GB hardware:

- close browsers and heavy background apps during experiments
- avoid running simultaneous benchmarks while profiling the live app
- keep one experiment objective per session
- prefer CPU-stable repeatability over aggressive configuration changes

CogniHuman’s advantage is not pretending to have ideal hardware. It is producing results that matter for ordinary devices.

---

## Next Step After Baseline

Once both profiles exist and compare cleanly:

1. summarize gains by utterance length bucket
2. identify whether the benefit comes from transcription overlap or another path effect
3. write a short internal note:
   - hypothesis
   - setup
   - result
   - failure cases
   - next revision
