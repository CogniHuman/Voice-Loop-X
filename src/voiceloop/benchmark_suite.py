#!/usr/bin/env python3
"""
VoiceBench: Standardized Benchmark Suite for On-Device Voice Agents
CogniHuman Research Foundation

Provides reproducible evaluation methodology for voice agent systems.
"""

import json
import time
import numpy as np
import wave
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Callable
import sys

@dataclass
class TestCase:
    """Single test case for benchmarking"""
    id: str
    audio_path: str
    ground_truth_text: str
    expected_response_type: str  # "factual", "conversational", "command"
    duration_sec: float
    category: str  # "short", "medium", "long", "multi_turn"
    metadata: Dict = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

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
    metadata: Dict = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class VoiceBench:
    """Standardized benchmark suite for voice agents"""
    
    def __init__(self, test_set_path: str = None):
        if test_set_path is None:
            test_set_path = Path(__file__).parent / "test_sets"
        self.test_set_path = Path(test_set_path)
        self.test_cases = {}
        self._load_test_cases()
    
    def _load_test_cases(self):
        """Load all test cases organized by category"""
        categories = ["short_queries", "medium_queries", "long_queries", "multi_turn", "interruptions"]
        
        for category in categories:
            json_path = self.test_set_path / f"{category}.json"
            if json_path.exists():
                with open(json_path) as f:
                    data = json.load(f)
                    self.test_cases[category] = [TestCase(**item) for item in data]
            else:
                self.test_cases[category] = []
    
    def benchmark_system(
        self, 
        voice_agent_fn: Callable,
        categories: List[str] = None,
        verbose: bool = True
    ) -> Dict:
        """
        Run comprehensive benchmark on voice agent
        
        Args:
            voice_agent_fn: Function that takes audio and returns result dict
            categories: List of categories to test (None = all)
            verbose: Print progress
        
        Returns:
            Dictionary with results by category
        """
        if categories is None:
            categories = [c for c in self.test_cases.keys() if self.test_cases[c]]
        
        results = {}
        
        for category in categories:
            if category not in self.test_cases or not self.test_cases[category]:
                if verbose:
                    print(f"Skipping {category}: No test cases")
                continue
            
            if verbose:
                print(f"\nBenchmarking category: {category}")
                print(f"Test cases: {len(self.test_cases[category])}")
            
            category_results = []
            
            for i, test_case in enumerate(self.test_cases[category], 1):
                if verbose:
                    print(f"  [{i}/{len(self.test_cases[category])}] {test_case.id}...", end=" ", flush=True)
                
                try:
                    result = self._run_test_case(voice_agent_fn, test_case)
                    category_results.append(result)
                    if verbose:
                        print(f"OK (TTFA: {result.ttfa_ms:.0f}ms, WER: {result.wer:.3f})")
                except Exception as e:
                    if verbose:
                        print(f"FAIL ({e})")
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
    
    def _run_test_case(
        self, 
        voice_agent_fn: Callable, 
        test_case: TestCase
    ) -> BenchmarkResult:
        """Run single test case and collect metrics"""
        try:
            import psutil
            import os
        except ImportError:
            psutil = None
        
        # Load audio
        audio = self._load_audio(test_case.audio_path)
        
        # Monitor resources
        if psutil:
            process = psutil.Process(os.getpid())
            mem_before = process.memory_info().rss / 1024 / 1024  # MB
        else:
            mem_before = 0
        
        # Run voice agent
        t0 = time.monotonic()
        result = voice_agent_fn(audio)
        ttfa = (time.monotonic() - t0) * 1000
        
        # Measure resources
        if psutil:
            mem_after = process.memory_info().rss / 1024 / 1024  # MB
            cpu_percent = process.cpu_percent()
        else:
            mem_after = mem_before
            cpu_percent = 0
        
        # Calculate WER
        wer = self._calculate_wer(
            result.get("transcription", ""), 
            test_case.ground_truth_text
        )
        
        return BenchmarkResult(
            test_id=test_case.id,
            ttfa_ms=ttfa,
            transcription=result.get("transcription", ""),
            response=result.get("response", ""),
            wer=wer,
            memory_peak_mb=mem_after - mem_before,
            cpu_percent=cpu_percent,
            success=True
        )
    
    def _load_audio(self, audio_path: str) -> np.ndarray:
        """Load audio file as numpy array"""
        audio_path = Path(audio_path)
        
        # Handle relative paths
        if not audio_path.is_absolute():
            audio_path = self.test_set_path / audio_path
        
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        with wave.open(str(audio_path), 'rb') as wf:
            frames = wf.readframes(wf.getnframes())
            audio = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
        return audio
    
    def _calculate_wer(self, hypothesis: str, reference: str) -> float:
        """Calculate Word Error Rate using Levenshtein distance"""
        hyp_words = hypothesis.lower().split()
        ref_words = reference.lower().split()
        
        if not ref_words:
            return 0.0 if not hyp_words else 1.0
        
        # Levenshtein distance matrix
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
        
        return float(d[len(ref_words)][len(hyp_words)] / len(ref_words))
    
    def _aggregate_results(self, results: List[BenchmarkResult]) -> Dict:
        """Aggregate results for a category"""
        successful = [r for r in results if r.success]
        
        if not successful:
            return {
                "error": "All tests failed",
                "total_tests": len(results),
                "successful": 0,
                "failed": len(results)
            }
        
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
                "p50": float(np.percentile(ttfa_values, 50)),
                "p95": float(np.percentile(ttfa_values, 95)),
                "p99": float(np.percentile(ttfa_values, 99)),
                "std": float(np.std(ttfa_values)),
                "min": float(np.min(ttfa_values)),
                "max": float(np.max(ttfa_values))
            },
            "wer": {
                "mean": float(np.mean(wer_values)),
                "median": float(np.median(wer_values)),
                "min": float(np.min(wer_values)),
                "max": float(np.max(wer_values))
            },
            "memory_mb": {
                "mean": float(np.mean(memory_values)),
                "peak": float(np.max(memory_values))
            }
        }
    
    def save_results(self, results: Dict, filepath: str):
        """Save benchmark results to JSON"""
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n[Benchmark] Results saved to {filepath}")
    
    def print_results(self, results: Dict):
        """Print human-readable results"""
        print("\n" + "="*80)
        print("VOICEBENCH RESULTS")
        print("CogniHuman Research Foundation")
        print("="*80)
        
        for category, metrics in results.items():
            if "error" in metrics:
                print(f"\n{category.upper()}: {metrics['error']}")
                continue
            
            print(f"\n{category.upper().replace('_', ' ')}:")
            print(f"  Tests: {metrics['successful']}/{metrics['total_tests']} successful")
            
            if metrics['successful'] > 0:
                print(f"  TTFA:")
                print(f"    Mean:   {metrics['ttfa']['mean']:.0f}ms")
                print(f"    Median: {metrics['ttfa']['median']:.0f}ms")
                print(f"    P95:    {metrics['ttfa']['p95']:.0f}ms")
                print(f"    P99:    {metrics['ttfa']['p99']:.0f}ms")
                print(f"    Range:  {metrics['ttfa']['min']:.0f}ms - {metrics['ttfa']['max']:.0f}ms")
                
                print(f"  WER:")
                print(f"    Mean:   {metrics['wer']['mean']:.3f}")
                print(f"    Median: {metrics['wer']['median']:.3f}")
                
                print(f"  Memory:")
                print(f"    Peak:   {metrics['memory_mb']['peak']:.1f}MB")
        
        print("\n" + "="*80 + "\n")
    
    def create_sample_test_set(self):
        """Create sample test cases for demonstration"""
        self.test_set_path.mkdir(parents=True, exist_ok=True)
        
        # Short queries (1-3 words)
        short_queries = [
            {
                "id": "short_001",
                "audio_path": "audio/what_time.wav",
                "ground_truth_text": "what time is it",
                "expected_response_type": "factual",
                "duration_sec": 1.2,
                "category": "short",
                "metadata": {"difficulty": "easy"}
            },
            {
                "id": "short_002",
                "audio_path": "audio/hello.wav",
                "ground_truth_text": "hello",
                "expected_response_type": "conversational",
                "duration_sec": 0.8,
                "category": "short",
                "metadata": {"difficulty": "easy"}
            },
            {
                "id": "short_003",
                "audio_path": "audio/thank_you.wav",
                "ground_truth_text": "thank you",
                "expected_response_type": "conversational",
                "duration_sec": 1.0,
                "category": "short",
                "metadata": {"difficulty": "easy"}
            }
        ]
        
        # Medium queries (5-10 words)
        medium_queries = [
            {
                "id": "medium_001",
                "audio_path": "audio/weather_query.wav",
                "ground_truth_text": "what is the weather like today",
                "expected_response_type": "factual",
                "duration_sec": 2.5,
                "category": "medium",
                "metadata": {"difficulty": "medium"}
            },
            {
                "id": "medium_002",
                "audio_path": "audio/how_are_you.wav",
                "ground_truth_text": "how are you doing today",
                "expected_response_type": "conversational",
                "duration_sec": 2.2,
                "category": "medium",
                "metadata": {"difficulty": "easy"}
            }
        ]
        
        # Long queries (15-30 words)
        long_queries = [
            {
                "id": "long_001",
                "audio_path": "audio/complex_question.wav",
                "ground_truth_text": "can you explain the difference between machine learning and deep learning in simple terms",
                "expected_response_type": "factual",
                "duration_sec": 5.5,
                "category": "long",
                "metadata": {"difficulty": "hard"}
            }
        ]
        
        # Save test sets
        test_sets = {
            "short_queries": short_queries,
            "medium_queries": medium_queries,
            "long_queries": long_queries
        }
        
        for category, cases in test_sets.items():
            filepath = self.test_set_path / f"{category}.json"
            with open(filepath, 'w') as f:
                json.dump(cases, f, indent=2)
            print(f"Created {filepath} with {len(cases)} test cases")
        
        # Create README
        readme_path = self.test_set_path / "README.md"
        with open(readme_path, 'w') as f:
            f.write("""# VoiceBench Test Sets

## Structure

Each test set is a JSON file containing test cases with:
- `id`: Unique identifier
- `audio_path`: Path to audio file (relative to test_sets/)
- `ground_truth_text`: Expected transcription
- `expected_response_type`: Type of response expected
- `duration_sec`: Audio duration
- `category`: Test category
- `metadata`: Additional information

## Categories

- **short_queries**: 1-3 words (simple commands, greetings)
- **medium_queries**: 5-10 words (typical questions)
- **long_queries**: 15-30 words (complex questions)
- **multi_turn**: Conversation sequences
- **interruptions**: Barge-in test cases

## Adding Test Cases

1. Record audio file (16kHz, mono, WAV format)
2. Place in `audio/` subdirectory
3. Add entry to appropriate JSON file
4. Include ground truth transcription

## Usage

```python
from research.benchmark_suite import VoiceBench

bench = VoiceBench()
results = bench.benchmark_system(voice_agent_fn)
bench.print_results(results)
```
""")
        print(f"Created {readme_path}")

# Convenience function
def create_sample_test_sets():
    """Create sample test sets"""
    bench = VoiceBench()
    bench.create_sample_test_set()

if __name__ == "__main__":
    create_sample_test_sets()
