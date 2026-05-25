# Quick Start: First Two Research Optimizations

**For**: CogniHuman Research Foundation  
**Goal**: Implement foundation for significant research contribution  
**Timeline**: 2-3 weeks  
**Difficulty**: Moderate

---

## Priority #1: Comprehensive Latency Profiler

### Why Start Here?
- ✅ **Essential Foundation**: Can't optimize what you don't measure
- ✅ **Immediate Value**: Identifies real bottlenecks
- ✅ **Publishable**: "Performance Analysis of On-Device Voice Agents"
- ✅ **Low Risk**: Pure measurement, no system changes

### Implementation

Create `research/latency_profiler.py`:

```python
#!/usr/bin/env python3
"""
Comprehensive Latency Profiler for VoiceLoop-X
Measures every stage of the voice agent pipeline
"""

import time
import numpy as np
import json
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Dict

@dataclass
class StageMetrics:
    """Metrics for a single pipeline stage"""
    name: str
    timings: List[float]  # milliseconds
    
    @property
    def mean(self) -> float:
        return np.mean(self.timings) if self.timings else 0
    
    @property
    def median(self) -> float:
        return np.median(self.timings) if self.timings else 0
    
    @property
    def p95(self) -> float:
        return np.percentile(self.timings, 95) if self.timings else 0
    
    @property
    def p99(self) -> float:
        return np.percentile(self.timings, 99) if self.timings else 0
    
    @property
    def std(self) -> float:
        return np.std(self.timings) if self.timings else 0

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
        }
        self.current_utterance = {}
    
    def start_stage(self, stage_name: str):
        """Mark start of a pipeline stage"""
        self.current_utterance[stage_name] = time.monotonic()
    
    def end_stage(self, stage_name: str):
        """Mark end of a pipeline stage and record timing"""
        if stage_name in self.current_utterance:
            elapsed = (time.monotonic() - self.current_utterance[stage_name]) * 1000
            self.stages[stage_name].timings.append(elapsed)
            return elapsed
        return None
    
    def record_ttfa(self, vad_end_time: float, audio_start_time: float):
        """Record total time-to-first-audio"""
        ttfa = (audio_start_time - vad_end_time) * 1000
        self.stages["total_ttfa"].timings.append(ttfa)
        return ttfa
    
    def generate_report(self) -> Dict:
        """Generate comprehensive performance report"""
        report = {
            "summary": {},
            "stages": {},
            "bottlenecks": [],
            "recommendations": []
        }
        
        # Calculate stage statistics
        total_time = 0
        for stage_name, metrics in self.stages.items():
            if not metrics.timings:
                continue
            
            stage_report = {
                "mean_ms": round(metrics.mean, 2),
                "median_ms": round(metrics.median, 2),
                "p95_ms": round(metrics.p95, 2),
                "p99_ms": round(metrics.p99, 2),
                "std_ms": round(metrics.std, 2),
                "samples": len(metrics.timings)
            }
            report["stages"][stage_name] = stage_report
            total_time += metrics.mean
        
        # Calculate percentages
        for stage_name, stage_report in report["stages"].items():
            percentage = (stage_report["mean_ms"] / total_time * 100) if total_time > 0 else 0
            stage_report["percentage"] = round(percentage, 1)
        
        # Identify bottlenecks (stages taking >20% of total time)
        for stage_name, stage_report in report["stages"].items():
            if stage_report["percentage"] > 20:
                report["bottlenecks"].append({
                    "stage": stage_name,
                    "percentage": stage_report["percentage"],
                    "mean_ms": stage_report["mean_ms"]
                })
        
        # Generate recommendations
        report["recommendations"] = self._generate_recommendations(report)
        
        # Summary statistics
        if self.stages["total_ttfa"].timings:
            report["summary"] = {
                "mean_ttfa_ms": round(self.stages["total_ttfa"].mean, 2),
                "p95_ttfa_ms": round(self.stages["total_ttfa"].p95, 2),
                "total_utterances": len(self.stages["total_ttfa"].timings),
                "primary_bottleneck": report["bottlenecks"][0]["stage"] if report["bottlenecks"] else "None"
            }
        
        return report
    
    def _generate_recommendations(self, report: Dict) -> List[str]:
        """Generate optimization recommendations based on profiling data"""
        recommendations = []
        
        for bottleneck in report["bottlenecks"]:
            stage = bottleneck["stage"]
            
            if stage == "llm_first_token":
                recommendations.append(
                    f"LLM first token is {bottleneck['percentage']:.1f}% of latency. "
                    "Consider: KV cache optimization, speculative decoding, or GPU acceleration."
                )
            elif stage == "transcription":
                recommendations.append(
                    f"Transcription is {bottleneck['percentage']:.1f}% of latency. "
                    "Consider: streaming ASR, smaller model, or GPU acceleration."
                )
            elif stage == "smart_turn":
                recommendations.append(
                    f"Smart Turn is {bottleneck['percentage']:.1f}% of latency. "
                    "Consider: reducing window size (currently 4s) or caching features."
                )
            elif stage == "tts_first_chunk":
                recommendations.append(
                    f"TTS first chunk is {bottleneck['percentage']:.1f}% of latency. "
                    "Consider: model warm-up, caching, or faster synthesis."
                )
        
        return recommendations
    
    def save_report(self, filepath: str):
        """Save report to JSON file"""
        report = self.generate_report()
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"Report saved to {filepath}")
    
    def print_report(self):
        """Print human-readable report"""
        report = self.generate_report()
        
        print("\n" + "="*70)
        print("VOICELOOP-X LATENCY PROFILING REPORT")
        print("="*70)
        
        if report["summary"]:
            print("\nSUMMARY:")
            print(f"  Mean TTFA: {report['summary']['mean_ttfa_ms']:.0f}ms")
            print(f"  P95 TTFA: {report['summary']['p95_ttfa_ms']:.0f}ms")
            print(f"  Utterances: {report['summary']['total_utterances']}")
            print(f"  Primary Bottleneck: {report['summary']['primary_bottleneck']}")
        
        print("\nSTAGE BREAKDOWN:")
        print(f"{'Stage':<25} {'Mean':<10} {'P95':<10} {'%':<8} {'Samples':<8}")
        print("-"*70)
        
        for stage_name, metrics in report["stages"].items():
            print(f"{stage_name:<25} {metrics['mean_ms']:<10.1f} "
                  f"{metrics['p95_ms']:<10.1f} {metrics['percentage']:<8.1f} "
                  f"{metrics['samples']:<8}")
        
        if report["bottlenecks"]:
            print("\nBOTTLENECKS (>20% of total time):")
            for bottleneck in report["bottlenecks"]:
                print(f"  • {bottleneck['stage']}: {bottleneck['percentage']:.1f}% "
                      f"({bottleneck['mean_ms']:.0f}ms)")
        
        if report["recommendations"]:
            print("\nRECOMMENDATIONS:")
            for i, rec in enumerate(report["recommendations"], 1):
                print(f"  {i}. {rec}")
        
        print("\n" + "="*70 + "\n")

# Global profiler instance
profiler = LatencyProfiler()
```

### Integration with voice_loop.py

Add to imports:
```python
from research.latency_profiler import profiler
```

Instrument key stages:
```python
# In main loop, when speech detected
profiler.start_stage("buffer_accumulation")

# When Smart Turn called
profiler.start_stage("smart_turn")
prob = smart_turn(np.concatenate(buf))
profiler.end_stage("smart_turn")

# When transcription starts
profiler.start_stage("transcription")
heard = transcribe_future.result(timeout=10)
profiler.end_stage("transcription")

# When LLM starts
profiler.start_stage("llm_first_token")
# ... (end when first token arrives)

# When TTS starts
profiler.start_stage("tts_first_chunk")
# ... (end when first audio chunk ready)

# Record TTFA
ttfa = profiler.record_ttfa(metrics.vad_end, metrics.audio_first_write)

# On exit
profiler.print_report()
profiler.save_report("latency_report.json")
```

### Expected Output

```
======================================================================
VOICELOOP-X LATENCY PROFILING REPORT
======================================================================

SUMMARY:
  Mean TTFA: 847ms
  P95 TTFA: 1243ms
  Utterances: 15
  Primary Bottleneck: llm_first_token

STAGE BREAKDOWN:
Stage                     Mean       P95        %        Samples 
----------------------------------------------------------------------
vad_detection             3.2        5.1        0.4      15      
buffer_accumulation       712.3      850.2      84.1     15      
smart_turn                45.2       58.3       5.3      15      
transcription             234.5      312.1      27.7     15      
llm_first_token           523.4      687.2      61.8     15      
llm_full_generation       1834.2     2341.5     216.6    15      
tts_first_chunk           67.3       89.4       7.9      15      
tts_full_synthesis        423.1      534.2      49.9     15      
aec_processing            2.1        3.4        0.2      142     
total_ttfa                847.3      1243.1     100.0    15      

BOTTLENECKS (>20% of total time):
  • llm_first_token: 61.8% (523ms)
  • transcription: 27.7% (235ms)

RECOMMENDATIONS:
  1. LLM first token is 61.8% of latency. Consider: KV cache optimization, 
     speculative decoding, or GPU acceleration.
  2. Transcription is 27.7% of latency. Consider: streaming ASR, smaller 
     model, or GPU acceleration.

======================================================================
```

### Research Value

This profiler enables:
1. **Bottleneck Identification**: Know exactly where to optimize
2. **Comparative Analysis**: Before/after optimization measurements
3. **Hardware Comparison**: Profile across different devices
4. **Publishable Data**: Statistical analysis for papers

---

## Priority #2: Cross-Platform Benchmark Suite

### Why This Matters?
- ✅ **Reproducibility**: Others can verify your results
- ✅ **Standardization**: Compare across implementations
- ✅ **Community Impact**: Becomes reference benchmark
- ✅ **Publishable**: "VoiceBench: Standardized Benchmarks"

### Implementation

Create `research/benchmark_suite.py`:

```python
#!/usr/bin/env python3
"""
VoiceBench: Standardized Benchmark Suite for On-Device Voice Agents
"""

import json
import time
import numpy as np
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Dict, Tuple
import wave

@dataclass
class TestCase:
    """Single test case"""
    id: str
    audio_path: str
    ground_truth_text: str
    expected_response_type: str  # "factual", "conversational", "command"
    duration_sec: float
    category: str  # "short", "medium", "long", "multi_turn"

@dataclass
class BenchmarkResult:
    """Result for a single test case"""
    test_id: str
    ttfa_ms: float
    transcription: str
    response: str
    wer: float
    memory_peak_mb: float
    cpu_percent: float
    success: bool
    error: str = ""

class VoiceBench:
    """Standardized benchmark suite for voice agents"""
    
    def __init__(self, test_set_path: str = "research/test_sets"):
        self.test_set_path = Path(test_set_path)
        self.test_cases = self._load_test_cases()
    
    def _load_test_cases(self) -> Dict[str, List[TestCase]]:
        """Load all test cases organized by category"""
        test_cases = {
            "short_queries": [],
            "medium_queries": [],
            "long_queries": [],
            "multi_turn": [],
            "interruptions": []
        }
        
        # Load from JSON files
        for category in test_cases.keys():
            json_path = self.test_set_path / f"{category}.json"
            if json_path.exists():
                with open(json_path) as f:
                    data = json.load(f)
                    for item in data:
                        test_cases[category].append(TestCase(**item))
        
        return test_cases
    
    def benchmark_system(self, voice_agent, categories: List[str] = None) -> Dict:
        """Run comprehensive benchmark on voice agent"""
        if categories is None:
            categories = list(self.test_cases.keys())
        
        results = {}
        
        for category in categories:
            if category not in self.test_cases:
                continue
            
            print(f"\nBenchmarking category: {category}")
            print(f"Test cases: {len(self.test_cases[category])}")
            
            category_results = []
            
            for i, test_case in enumerate(self.test_cases[category], 1):
                print(f"  [{i}/{len(self.test_cases[category])}] {test_case.id}...", end=" ")
                
                try:
                    result = self._run_test_case(voice_agent, test_case)
                    category_results.append(result)
                    print(f"✓ TTFA: {result.ttfa_ms:.0f}ms, WER: {result.wer:.2f}")
                except Exception as e:
                    print(f"✗ Error: {e}")
                    category_results.append(BenchmarkResult(
                        test_id=test_case.id,
                        ttfa_ms=0,
                        transcription="",
                        response="",
                        wer=1.0,
                        memory_peak_mb=0,
                        cpu_percent=0,
                        success=False,
                        error=str(e)
                    ))
            
            results[category] = self._aggregate_results(category_results)
        
        return results
    
    def _run_test_case(self, voice_agent, test_case: TestCase) -> BenchmarkResult:
        """Run single test case and collect metrics"""
        import psutil
        import os
        
        # Load audio
        audio = self._load_audio(test_case.audio_path)
        
        # Monitor resources
        process = psutil.Process(os.getpid())
        mem_before = process.memory_info().rss / 1024 / 1024  # MB
        
        # Run voice agent
        t0 = time.monotonic()
        result = voice_agent.process_utterance(audio)
        ttfa = (time.monotonic() - t0) * 1000
        
        # Measure resources
        mem_after = process.memory_info().rss / 1024 / 1024  # MB
        cpu_percent = process.cpu_percent()
        
        # Calculate WER
        wer = self._calculate_wer(result["transcription"], test_case.ground_truth_text)
        
        return BenchmarkResult(
            test_id=test_case.id,
            ttfa_ms=ttfa,
            transcription=result["transcription"],
            response=result["response"],
            wer=wer,
            memory_peak_mb=mem_after - mem_before,
            cpu_percent=cpu_percent,
            success=True
        )
    
    def _load_audio(self, audio_path: str) -> np.ndarray:
        """Load audio file as numpy array"""
        with wave.open(audio_path, 'rb') as wf:
            frames = wf.readframes(wf.getnframes())
            audio = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
        return audio
    
    def _calculate_wer(self, hypothesis: str, reference: str) -> float:
        """Calculate Word Error Rate"""
        # Simple WER calculation (use jiwer library for production)
        hyp_words = hypothesis.lower().split()
        ref_words = reference.lower().split()
        
        # Levenshtein distance
        d = np.zeros((len(ref_words) + 1, len(hyp_words) + 1))
        
        for i in range(len(ref_words) + 1):
            d[i][0] = i
        for j in range(len(hyp_words) + 1):
            d[0][j] = j
        
        for i in range(1, len(ref_words) + 1):
            for j in range(1, len(hyp_words) + 1):
                if ref_words[i-1] == hyp_words[j-1]:
                    d[i][j] = d[i-1][j-1]
                else:
                    d[i][j] = min(d[i-1][j], d[i][j-1], d[i-1][j-1]) + 1
        
        return d[len(ref_words)][len(hyp_words)] / len(ref_words) if ref_words else 0
    
    def _aggregate_results(self, results: List[BenchmarkResult]) -> Dict:
        """Aggregate results for a category"""
        successful = [r for r in results if r.success]
        
        if not successful:
            return {"error": "All tests failed"}
        
        ttfa_values = [r.ttfa_ms for r in successful]
        wer_values = [r.wer for r in successful]
        memory_values = [r.memory_peak_mb for r in successful]
        
        return {
            "total_tests": len(results),
            "successful": len(successful),
            "failed": len(results) - len(successful),
            "ttfa": {
                "mean": float(np.mean(ttfa_values)),
                "median": float(np.median(ttfa_values)),
                "p95": float(np.percentile(ttfa_values, 95)),
                "p99": float(np.percentile(ttfa_values, 99)),
                "std": float(np.std(ttfa_values))
            },
            "wer": {
                "mean": float(np.mean(wer_values)),
                "median": float(np.median(wer_values))
            },
            "memory_mb": {
                "mean": float(np.mean(memory_values)),
                "peak": float(np.max(memory_values))
            }
        }
    
    def save_results(self, results: Dict, filepath: str):
        """Save benchmark results to JSON"""
        with open(filepath, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\nResults saved to {filepath}")
    
    def print_results(self, results: Dict):
        """Print human-readable results"""
        print("\n" + "="*70)
        print("VOICEBENCH RESULTS")
        print("="*70)
        
        for category, metrics in results.items():
            if "error" in metrics:
                print(f"\n{category.upper()}: {metrics['error']}")
                continue
            
            print(f"\n{category.upper()}:")
            print(f"  Tests: {metrics['successful']}/{metrics['total_tests']} successful")
            print(f"  TTFA: {metrics['ttfa']['mean']:.0f}ms (mean), "
                  f"{metrics['ttfa']['p95']:.0f}ms (p95)")
            print(f"  WER: {metrics['wer']['mean']:.3f} (mean)")
            print(f"  Memory: {metrics['memory_mb']['peak']:.1f}MB (peak)")
        
        print("\n" + "="*70 + "\n")

# Create sample test set
def create_sample_test_set():
    """Create sample test cases for demonstration"""
    test_sets = {
        "short_queries": [
            {
                "id": "short_001",
                "audio_path": "test_audio/what_time.wav",
                "ground_truth_text": "what time is it",
                "expected_response_type": "factual",
                "duration_sec": 1.2,
                "category": "short"
            },
            # Add more...
        ],
        "medium_queries": [
            {
                "id": "medium_001",
                "audio_path": "test_audio/weather_query.wav",
                "ground_truth_text": "what's the weather like today in san francisco",
                "expected_response_type": "factual",
                "duration_sec": 2.8,
                "category": "medium"
            },
            # Add more...
        ]
    }
    
    # Save to JSON
    Path("research/test_sets").mkdir(parents=True, exist_ok=True)
    for category, cases in test_sets.items():
        with open(f"research/test_sets/{category}.json", 'w') as f:
            json.dump(cases, f, indent=2)
```

### Usage

```python
# Run benchmark
from research.benchmark_suite import VoiceBench

bench = VoiceBench()
results = bench.benchmark_system(voice_agent)
bench.print_results(results)
bench.save_results(results, "benchmark_results.json")
```

---

## Next Steps

### Week 1: Implement Profiler
1. Add `research/latency_profiler.py`
2. Instrument voice_loop.py
3. Run on 10+ utterances
4. Generate first report

### Week 2: Implement Benchmark
1. Add `research/benchmark_suite.py`
2. Create 20-30 test cases
3. Run baseline benchmark
4. Document results

### Week 3: Analysis & Documentation
1. Analyze bottlenecks
2. Write technical report
3. Plan next optimizations
4. Prepare for publication

---

## Expected Deliverables

1. **Latency Profiling Report** (JSON + PDF)
2. **Benchmark Results** (JSON + comparison table)
3. **Technical Report** (5-10 pages)
4. **Optimization Roadmap** (prioritized list)

This foundation enables all future research optimizations!
