#!/usr/bin/env python3
"""
Comprehensive Latency Profiler for VoiceLoop-X
CogniHuman Research Foundation

Measures every stage of the voice agent pipeline to identify bottlenecks
and guide optimization priorities.
"""

import time
import numpy as np
import json
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional
import sys

@dataclass
class StageMetrics:
    """Metrics for a single pipeline stage"""
    name: str
    timings: List[float]  # milliseconds
    
    @property
    def mean(self) -> float:
        return float(np.mean(self.timings)) if self.timings else 0.0
    
    @property
    def median(self) -> float:
        return float(np.median(self.timings)) if self.timings else 0.0
    
    @property
    def p50(self) -> float:
        return float(np.percentile(self.timings, 50)) if self.timings else 0.0
    
    @property
    def p95(self) -> float:
        return float(np.percentile(self.timings, 95)) if self.timings else 0.0
    
    @property
    def p99(self) -> float:
        return float(np.percentile(self.timings, 99)) if self.timings else 0.0
    
    @property
    def std(self) -> float:
        return float(np.std(self.timings)) if self.timings else 0.0
    
    @property
    def min_val(self) -> float:
        return float(np.min(self.timings)) if self.timings else 0.0
    
    @property
    def max_val(self) -> float:
        return float(np.max(self.timings)) if self.timings else 0.0

class LatencyProfiler:
    """Comprehensive latency profiler for voice agent pipeline"""
    
    def __init__(self):
        self.stages = {
            "vad_detection": StageMetrics("VAD Detection", []),
            "buffer_accumulation": StageMetrics("Buffer Accumulation", []),
            "smart_turn": StageMetrics("Smart Turn Detection", []),
            "transcription": StageMetrics("Transcription (ASR)", []),
            "llm_first_token": StageMetrics("LLM First Token", []),
            "llm_full_generation": StageMetrics("LLM Full Generation", []),
            "tts_first_chunk": StageMetrics("TTS First Chunk", []),
            "tts_full_synthesis": StageMetrics("TTS Full Synthesis", []),
            "aec_processing": StageMetrics("AEC Processing", []),
            "total_ttfa": StageMetrics("Total TTFA", []),
            "end_to_end": StageMetrics("End-to-End Latency", []),
        }
        self.current_utterance = {}
        self.utterance_count = 0
        self.enabled = True
    
    def enable(self):
        """Enable profiling"""
        self.enabled = True
    
    def disable(self):
        """Disable profiling"""
        self.enabled = False
    
    def start_stage(self, stage_name: str):
        """Mark start of a pipeline stage"""
        if not self.enabled:
            return
        if stage_name in self.stages:
            self.current_utterance[stage_name] = time.monotonic()
    
    def end_stage(self, stage_name: str) -> Optional[float]:
        """Mark end of a pipeline stage and record timing"""
        if not self.enabled:
            return None
        if stage_name in self.current_utterance and stage_name in self.stages:
            elapsed = (time.monotonic() - self.current_utterance[stage_name]) * 1000
            self.stages[stage_name].timings.append(elapsed)
            del self.current_utterance[stage_name]
            return elapsed
        return None
    
    def record_ttfa(self, vad_end_time: float, audio_start_time: float) -> float:
        """Record total time-to-first-audio"""
        if not self.enabled:
            return 0.0
        ttfa = (audio_start_time - vad_end_time) * 1000
        self.stages["total_ttfa"].timings.append(ttfa)
        return ttfa
    
    def record_end_to_end(self, start_time: float, end_time: float) -> float:
        """Record total end-to-end latency"""
        if not self.enabled:
            return 0.0
        latency = (end_time - start_time) * 1000
        self.stages["end_to_end"].timings.append(latency)
        return latency
    
    def increment_utterance(self):
        """Increment utterance counter"""
        self.utterance_count += 1
    
    def generate_report(self) -> Dict:
        """Generate comprehensive performance report"""
        report = {
            "summary": {},
            "stages": {},
            "bottlenecks": [],
            "recommendations": [],
            "metadata": {
                "total_utterances": self.utterance_count,
                "profiled_utterances": len(self.stages["total_ttfa"].timings) if self.stages["total_ttfa"].timings else 0
            }
        }
        
        # Calculate stage statistics
        total_time = 0
        for stage_name, metrics in self.stages.items():
            if not metrics.timings:
                continue
            
            stage_report = {
                "mean_ms": round(metrics.mean, 2),
                "median_ms": round(metrics.median, 2),
                "p50_ms": round(metrics.p50, 2),
                "p95_ms": round(metrics.p95, 2),
                "p99_ms": round(metrics.p99, 2),
                "std_ms": round(metrics.std, 2),
                "min_ms": round(metrics.min_val, 2),
                "max_ms": round(metrics.max_val, 2),
                "samples": len(metrics.timings)
            }
            report["stages"][stage_name] = stage_report
            
            # Don't include total_ttfa and end_to_end in percentage calculation
            if stage_name not in ["total_ttfa", "end_to_end"]:
                total_time += metrics.mean
        
        # Calculate percentages (relative to sum of component stages)
        for stage_name, stage_report in report["stages"].items():
            if stage_name not in ["total_ttfa", "end_to_end"]:
                percentage = (stage_report["mean_ms"] / total_time * 100) if total_time > 0 else 0
                stage_report["percentage"] = round(percentage, 1)
            else:
                stage_report["percentage"] = 0.0
        
        # Identify bottlenecks (stages taking >15% of total time)
        for stage_name, stage_report in report["stages"].items():
            if stage_name not in ["total_ttfa", "end_to_end"] and stage_report["percentage"] > 15:
                report["bottlenecks"].append({
                    "stage": stage_name,
                    "percentage": stage_report["percentage"],
                    "mean_ms": stage_report["mean_ms"]
                })
        
        # Sort bottlenecks by percentage
        report["bottlenecks"].sort(key=lambda x: x["percentage"], reverse=True)
        
        # Generate recommendations
        report["recommendations"] = self._generate_recommendations(report)
        
        # Summary statistics
        if self.stages["total_ttfa"].timings:
            report["summary"] = {
                "mean_ttfa_ms": round(self.stages["total_ttfa"].mean, 2),
                "median_ttfa_ms": round(self.stages["total_ttfa"].median, 2),
                "p95_ttfa_ms": round(self.stages["total_ttfa"].p95, 2),
                "p99_ttfa_ms": round(self.stages["total_ttfa"].p99, 2),
                "min_ttfa_ms": round(self.stages["total_ttfa"].min_val, 2),
                "max_ttfa_ms": round(self.stages["total_ttfa"].max_val, 2),
                "total_utterances": self.utterance_count,
                "profiled_utterances": len(self.stages["total_ttfa"].timings),
                "primary_bottleneck": report["bottlenecks"][0]["stage"] if report["bottlenecks"] else "None"
            }
        
        return report
    
    def _generate_recommendations(self, report: Dict) -> List[str]:
        """Generate optimization recommendations based on profiling data"""
        recommendations = []
        
        for i, bottleneck in enumerate(report["bottlenecks"][:3], 1):  # Top 3 bottlenecks
            stage = bottleneck["stage"]
            percentage = bottleneck["percentage"]
            mean_ms = bottleneck["mean_ms"]
            
            if stage == "llm_first_token":
                recommendations.append(
                    f"#{i} LLM first token is {percentage:.1f}% of latency ({mean_ms:.0f}ms). "
                    "Consider: (a) KV cache optimization for conversation context reuse, "
                    "(b) Speculative decoding with draft model, "
                    "(c) GPU acceleration (CUDA/Metal/Vulkan), "
                    "(d) Smaller model variant (E2B vs E4B)."
                )
            elif stage == "llm_full_generation":
                recommendations.append(
                    f"#{i} LLM full generation is {percentage:.1f}% of latency ({mean_ms:.0f}ms). "
                    "Consider: (a) Streaming TTS integration (already implemented), "
                    "(b) Response length limits, "
                    "(c) GPU acceleration."
                )
            elif stage == "transcription":
                recommendations.append(
                    f"#{i} Transcription is {percentage:.1f}% of latency ({mean_ms:.0f}ms). "
                    "Consider: (a) Streaming ASR with partial results, "
                    "(b) Smaller Moonshine model, "
                    "(c) GPU acceleration, "
                    "(d) Start LLM with partial transcription."
                )
            elif stage == "smart_turn":
                recommendations.append(
                    f"#{i} Smart Turn is {percentage:.1f}% of latency ({mean_ms:.0f}ms). "
                    "Consider: (a) Reducing window size (currently 4s, try 3s or 2s), "
                    "(b) Caching Whisper features, "
                    "(c) Adaptive window based on utterance length."
                )
            elif stage == "tts_first_chunk":
                recommendations.append(
                    f"#{i} TTS first chunk is {percentage:.1f}% of latency ({mean_ms:.0f}ms). "
                    "Consider: (a) Model warm-up on startup, "
                    "(b) Voice embedding caching, "
                    "(c) Faster synthesis model."
                )
            elif stage == "tts_full_synthesis":
                recommendations.append(
                    f"#{i} TTS full synthesis is {percentage:.1f}% of latency ({mean_ms:.0f}ms). "
                    "Consider: (a) Streaming already implemented (good!), "
                    "(b) Parallel synthesis of sentence chunks."
                )
            elif stage == "buffer_accumulation":
                recommendations.append(
                    f"#{i} Buffer accumulation is {percentage:.1f}% of latency ({mean_ms:.0f}ms). "
                    "This is mostly silence detection time (700ms default). "
                    "Consider: (a) Adaptive silence threshold based on speaker, "
                    "(b) Reduce --silence-ms for faster speakers."
                )
            elif stage == "aec_processing":
                recommendations.append(
                    f"#{i} AEC processing is {percentage:.1f}% of latency ({mean_ms:.0f}ms). "
                    "Consider: (a) Further buffer pre-allocation, "
                    "(b) SIMD optimizations, "
                    "(c) Reduce processing frequency."
                )
        
        # Add general recommendations if no major bottlenecks
        if not recommendations:
            recommendations.append(
                "No major bottlenecks detected (all stages <15%). "
                "System is well-balanced. Consider overall optimizations: "
                "GPU acceleration, model quantization, or streaming improvements."
            )
        
        return recommendations
    
    def save_report(self, filepath: str):
        """Save report to JSON file"""
        report = self.generate_report()
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"\n[Profiler] Report saved to {filepath}")
    
    def print_report(self):
        """Print human-readable report"""
        report = self.generate_report()
        
        print("\n" + "="*80)
        print("VOICELOOP-X LATENCY PROFILING REPORT")
        print("CogniHuman Research Foundation")
        print("="*80)
        
        if report["summary"]:
            print("\nSUMMARY:")
            print(f"  Mean TTFA:        {report['summary']['mean_ttfa_ms']:.0f}ms")
            print(f"  Median TTFA:      {report['summary']['median_ttfa_ms']:.0f}ms")
            print(f"  P95 TTFA:         {report['summary']['p95_ttfa_ms']:.0f}ms")
            print(f"  P99 TTFA:         {report['summary']['p99_ttfa_ms']:.0f}ms")
            print(f"  Min/Max TTFA:     {report['summary']['min_ttfa_ms']:.0f}ms / {report['summary']['max_ttfa_ms']:.0f}ms")
            print(f"  Utterances:       {report['summary']['profiled_utterances']}/{report['summary']['total_utterances']}")
            print(f"  Primary Bottleneck: {report['summary']['primary_bottleneck']}")
        
        print("\nSTAGE BREAKDOWN:")
        print(f"{'Stage':<30} {'Mean':<10} {'P50':<10} {'P95':<10} {'%':<8} {'Samples':<8}")
        print("-"*80)
        
        # Sort stages by mean time (descending) for better readability
        sorted_stages = sorted(
            [(name, metrics) for name, metrics in report["stages"].items()],
            key=lambda x: x[1]["mean_ms"],
            reverse=True
        )
        
        for stage_name, metrics in sorted_stages:
            percentage_str = f"{metrics['percentage']:.1f}" if metrics['percentage'] > 0 else "-"
            print(f"{stage_name:<30} {metrics['mean_ms']:<10.1f} "
                  f"{metrics['p50_ms']:<10.1f} {metrics['p95_ms']:<10.1f} "
                  f"{percentage_str:<8} {metrics['samples']:<8}")
        
        if report["bottlenecks"]:
            print("\nBOTTLENECKS (>15% of total time):")
            for bottleneck in report["bottlenecks"]:
                print(f"  * {bottleneck['stage']}: {bottleneck['percentage']:.1f}% "
                      f"({bottleneck['mean_ms']:.0f}ms)")
        
        if report["recommendations"]:
            print("\nOPTIMIZATION RECOMMENDATIONS:")
            for rec in report["recommendations"]:
                # Wrap long recommendations
                lines = self._wrap_text(rec, 76)
                for i, line in enumerate(lines):
                    if i == 0:
                        print(f"  {line}")
                    else:
                        print(f"     {line}")
                print()
        
        print("="*80)
        print("For detailed JSON report, use --profile-save <filename>")
        print("="*80 + "\n")
    
    def _wrap_text(self, text: str, width: int) -> List[str]:
        """Wrap text to specified width"""
        words = text.split()
        lines = []
        current_line = []
        current_length = 0
        
        for word in words:
            if current_length + len(word) + 1 <= width:
                current_line.append(word)
                current_length += len(word) + 1
            else:
                if current_line:
                    lines.append(" ".join(current_line))
                current_line = [word]
                current_length = len(word)
        
        if current_line:
            lines.append(" ".join(current_line))
        
        return lines
    
    def reset(self):
        """Reset all metrics"""
        for stage in self.stages.values():
            stage.timings.clear()
        self.current_utterance.clear()
        self.utterance_count = 0

# Global profiler instance
profiler = LatencyProfiler()

# Convenience functions
def start_stage(stage_name: str):
    """Start timing a stage"""
    profiler.start_stage(stage_name)

def end_stage(stage_name: str) -> Optional[float]:
    """End timing a stage and return elapsed time in ms"""
    return profiler.end_stage(stage_name)

def record_ttfa(vad_end_time: float, audio_start_time: float) -> float:
    """Record TTFA"""
    return profiler.record_ttfa(vad_end_time, audio_start_time)

def print_report():
    """Print profiling report"""
    profiler.print_report()

def save_report(filepath: str):
    """Save profiling report to file"""
    profiler.save_report(filepath)
