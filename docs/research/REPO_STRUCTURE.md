# VoiceLoop-X Repository Structure

**Organization**: CogniHuman Research Foundation  
**Purpose**: Define the active, stale, generated, and historical parts of the repository so the team can work from a shared structure.

---

## Structure At A Glance

```text
VoiceLoop-X/
├── src/voiceloop/              # Active Python package code
├── tests/                      # Validation and regression tests
├── data/
│   ├── benchmarks/             # Historical and comparative benchmark JSONs
│   ├── profiles/               # Saved profiling outputs and baseline artifacts
│   ├── derived/                # Generated local outputs that are useful but not source data
│   └── test_cases/             # Evaluation manifests and currently suspect audio assets
├── docs/
│   ├── research/               # Current research source-of-truth documents
│   ├── guides/                 # Usage and workflow docs
│   ├── technical/              # Architecture and implementation review docs
│   └── archive/                # Historical planning and superseded notes
├── voice_loop.py               # Main prototype entry point
├── collect_frontend_baseline.py# Research runner for frontend-only baseline collection
└── compare_profiles.py         # Convenience entry point for profile comparison
```

---

## What Is Active

These areas should be treated as current working surfaces:

- `src/voiceloop/`
- `tests/`
- `data/profiles/`
- `docs/research/RESEARCH_AUDIT.md`
- `docs/research/BASELINE_EXPERIMENT_PROTOCOL.md`
- `docs/research/ASR_VALIDITY_INVESTIGATION.md`
- `voice_loop.py`
- `collect_frontend_baseline.py`
- `compare_profiles.py`

---

## What Is Historical Or Stale

These files remain useful for context, but should not be treated as source-of-truth without cross-checking:

- `docs/research/EXECUTIVE_SUMMARY.md`
- `docs/research/FOUNDATION_COMPLETE.md`
- `docs/technical/IMPROVEMENTS.md`
- `tests/validate_improvements.py`

These reflect earlier project states and some claims no longer match the current codebase.

---

## What Is Generated

Generated outputs should live under `data/derived/` or `data/profiles/`, not at the repo root.

Examples:

- ad hoc benchmark results
- one-off profiler test reports
- local comparison JSONs
- temporary research run outputs

This keeps the root directory focused on code, docs, and top-level project identity.

---

## Data Integrity Status

### `data/test_cases/audio/`

This directory must currently be treated as **suspect**.

Reason:

- benchmark test scaffolding previously overwrote these files with synthetic sine-wave audio
- they should not be used as research-grade speech evaluation assets until restored or replaced

See:

- [ASR_VALIDITY_INVESTIGATION.md](./ASR_VALIDITY_INVESTIGATION.md)

---

## Team Conventions

1. **Never let tests mutate research assets**
   Synthetic fixture data must be written to temp directories or `data/derived/`.

2. **Keep source-of-truth docs small and explicit**
   The current truth-aligned research docs are the audit, protocol, and investigation notes.

3. **Store measured artifacts in predictable locations**
   - profiling: `data/profiles/`
   - generated comparisons: `data/derived/comparisons/`
   - local test outputs: `data/derived/test_outputs/`

4. **Promote docs deliberately**
   Move exploratory notes to `docs/archive/` when superseded.

5. **Treat dataset provenance as a first-class research concern**
   A bad dataset can invalidate a strong model conclusion.

---

## Recommended Next Cleanup Steps

1. Rebuild a clean speech evaluation set under a separate path.
2. Add dataset provenance metadata for every evaluation asset.
3. Update stale high-level research summaries so they point first to the audit.
4. Consider a dedicated `scripts/` directory in a later cleanup pass if the number of research runners grows.
