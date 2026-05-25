"""
VoiceLoop-X: On-Device Voice Agent Research Platform

CogniHuman Research Foundation
License: Apache 2.0
Contact: research@cognihuman.org

A comprehensive research platform for on-device voice AI optimization,
featuring real-time latency profiling, standardized benchmarking, and
novel optimization algorithms for streaming voice agents.

Modules:
    - latency_profiler: Research-grade pipeline performance measurement
    - benchmark_suite: VoiceBench standardized evaluation suite
    - kv_cache_optimizer: KV cache management for multi-turn conversations

Usage:
    from voiceloop import profiler, VoiceBench
"""

__version__ = "1.0.0"
__author__ = "CogniHuman Research Foundation"
__license__ = "Apache 2.0"

# Expose core components for easy import
try:
    from .latency_profiler import profiler
except ImportError:
    profiler = None

try:
    from .benchmark_suite import VoiceBench
except ImportError:
    VoiceBench = None

try:
    from .profile_tools import compare_reports, render_text_report
except ImportError:
    compare_reports = None
    render_text_report = None

try:
    from .kv_cache_optimizer import OptimizedKVCacheManager, CacheStatistics
except ImportError:
    OptimizedKVCacheManager = None
    CacheStatistics = None
    KVCacheSession = None
    ConversationContextCache = None
