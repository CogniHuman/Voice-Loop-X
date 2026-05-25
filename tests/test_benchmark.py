#!/usr/bin/env python3
"""
Test script for VoiceBench benchmark suite
Simulates voice agent and validates benchmarking functionality

To run:  python tests/test_benchmark.py
"""

import sys
import tempfile
from pathlib import Path

# Ensure src/ is on path
sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

import time
import numpy as np
from voiceloop.benchmark_suite import VoiceBench

def mock_voice_agent(audio: np.ndarray) -> dict:
    """
    Mock voice agent for testing
    Simulates processing with realistic delays
    """
    # Simulate processing time based on audio length
    audio_duration = len(audio) / 16000  # Assuming 16kHz
    
    # Simulate VAD + transcription + LLM + TTS
    processing_time = 0.5 + (audio_duration * 0.3)  # Base + proportional
    time.sleep(processing_time)
    
    # Generate mock transcription based on audio length
    if audio_duration < 1.5:
        transcription = "hello"
    elif audio_duration < 3.0:
        transcription = "what is the weather like today"
    else:
        transcription = "can you explain the difference between machine learning and deep learning"
    
    # Generate mock response
    response = f"I heard you say: {transcription}"
    
    return {
        "transcription": transcription,
        "response": response,
        "success": True
    }

def test_benchmark_suite():
    """Test the benchmark suite"""
    print("="*60)
    print("VOICEBENCH TEST")
    print("="*60 + "\n")
    
    # Initialize benchmark
    print("Initializing VoiceBench...")
    source_data_dir = Path(__file__).parents[1] / "data" / "test_cases"
    temp_data_dir = Path(tempfile.mkdtemp(prefix="voicebench_mock_"))
    bench = VoiceBench(str(source_data_dir))
    
    # Check test cases loaded
    total_cases = sum(len(cases) for cases in bench.test_cases.values())
    print(f"Loaded {total_cases} test cases")
    
    for category, cases in bench.test_cases.items():
        if cases:
            print(f"  - {category}: {len(cases)} cases")
    
    print("\nNote: This test uses mock audio (sine waves) since actual audio files")
    print("are not included. In production, use real audio recordings.\n")
    
    # Create mock audio files for testing
    print("Creating mock audio files...")
    test_audio_dir = temp_data_dir / "audio"
    test_audio_dir.mkdir(exist_ok=True)
    
    # Generate simple sine wave audio for each test case
    import wave
    for category, cases in bench.test_cases.items():
        for case in cases:
            audio_path = temp_data_dir / case.audio_path
            audio_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Generate sine wave (440Hz, duration from test case)
            sample_rate = 16000
            duration = case.duration_sec
            t = np.linspace(0, duration, int(sample_rate * duration))
            audio = np.sin(2 * np.pi * 440 * t) * 0.3  # 440Hz sine wave
            audio_int16 = (audio * 32767).astype(np.int16)
            
            # Save as WAV
            with wave.open(str(audio_path), 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(sample_rate)
                wf.writeframes(audio_int16.tobytes())
    
    print(f"Mock audio files created in {temp_data_dir}\n")

    # Repoint the benchmark instance at the temporary synthetic-audio tree so
    # this test never mutates the real research dataset.
    bench = VoiceBench(str(source_data_dir))
    bench.test_set_path = temp_data_dir
    
    # Run benchmark
    print("Running benchmark with mock voice agent...")
    print("(This will take a few seconds)\n")
    
    results = bench.benchmark_system(
        voice_agent_fn=mock_voice_agent,
        verbose=True
    )
    
    # Print results
    bench.print_results(results)
    
    # Save results
    bench.save_results(results, "test_benchmark_results.json")
    
    # Validate results
    print("\nValidating results...")
    validation_passed = True
    
    for category, metrics in results.items():
        if "error" in metrics:
            print(f"  {category}: SKIPPED (no test cases)")
            continue
        
        # Check that we have results
        if metrics['successful'] == 0:
            print(f"  {category}: FAILED (no successful tests)")
            validation_passed = False
        else:
            # Check TTFA is reasonable (should be > 0 and < 10000ms)
            if 0 < metrics['ttfa']['mean'] < 10000:
                print(f"  {category}: OK (TTFA: {metrics['ttfa']['mean']:.0f}ms)")
            else:
                print(f"  {category}: FAILED (unreasonable TTFA)")
                validation_passed = False
    
    print("\n" + "="*60)
    if validation_passed:
        print("Test completed successfully!")
        print("Check test_benchmark_results.json for detailed results")
    else:
        print("Test completed with errors")
    print("="*60 + "\n")
    
    return validation_passed

if __name__ == "__main__":
    success = test_benchmark_suite()
    exit(0 if success else 1)
