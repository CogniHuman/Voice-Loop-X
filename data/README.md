# Data Directory Guide

This directory contains research artifacts, benchmark outputs, and evaluation inputs.

## Subdirectories

- `benchmarks/`
  Historical benchmark JSONs and comparative outputs.

- `profiles/`
  Saved profiler outputs and baseline measurement artifacts.

- `derived/`
  Generated local artifacts that are useful for development and research, but are not canonical source data.

- `test_cases/`
  Evaluation manifests and audio assets.

## Important Warning

The current `test_cases/audio/` directory should be treated as **suspect** until the speech recordings are restored or replaced.

Reason:

- benchmark test scaffolding previously overwrote files with synthetic sine-wave audio

See:

- [ASR validity investigation](../docs/research/ASR_VALIDITY_INVESTIGATION.md)
