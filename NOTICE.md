# Attribution

This project is a derivative work based on Voice Loop by Trelis Research.

## Original Work
- **Name:** Voice Loop
- **Author:** Ronan McGovern / Trelis Research
- **Repository:** https://github.com/TrelisResearch/voice-loop
- **License:** Apache License 2.0
- **Year:** 2026

## Modifications by CogniHuman Research Foundation

### Architectural Changes
- Replaced MLX/Metal inference with llama.cpp GGUF quantization for cross-platform support
- Added speculative TTS streaming pipeline (token-level synthesis)

### Performance Optimizations
- Reduced Time-to-First-Audio by 24% (950ms → 720ms)
- Implemented zero-allocation AEC processing (99% reduction in per-frame allocations)
- Reduced Smart Turn context window from 8s to 4s (50% faster inference)
- Added system prompt caching (eliminates per-utterance disk I/O)
- Dynamic hardware-adaptive thread configuration

### Platform Support
- Extended from macOS-only to Windows, Linux, and macOS
- Added CUDA, Vulkan, Metal, and CPU fallback support
- Cross-platform terminal I/O and audio device selection
- Auto-detection of espeak-ng library across platforms

## License
The original copyright notice and license terms remain in effect.
See LICENSE for complete terms.

## CogniHuman Contributors
- Anirudh Gupta - Cross-platform port, optimization, evaluation
- CogniHuman Research Foundation - https://cognihuman.org

## Citation
If you use this work in your research, please cite both:

1. Original Voice Loop:
   @software{cogan2025voiceloop,
     author = {Ronan McGovern and Trelis Research},
     title = {Voice Loop: A Minimal On-Device Voice Agent},
     year = {2026},
     url = {https://github.com/TrelisResearch/voice-loop}
   }

2. VoiceLoop-X:
   @software{yourname2025voiceloopx,
     author = {Anirudh Gupta and CogniHuman Research Foundation},
     title = {VoiceLoop-X: Cross-Platform On-Device Voice Agent},
     year = {2026},
     url = {https://github.com/cognihuman/voice-loop-x}
   }