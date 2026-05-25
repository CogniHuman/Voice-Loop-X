#!/usr/bin/env python3
"""
Test script for latency profiler
Simulates voice agent pipeline stages

To run:  python tests/test_profiler.py
"""

import sys
from pathlib import Path

# Ensure src/ is on path
sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

import time
import numpy as np
from voiceloop.latency_profiler import profiler

def simulate_pipeline():
    """Simulate a voice agent pipeline"""
    print("Simulating voice agent pipeline...\n")
    
    # Simulate 5 utterances
    for i in range(5):
        print(f"Utterance {i+1}/5")
        profiler.increment_utterance()
        
        # VAD detection (fast)
        profiler.start_stage("vad_detection")
        time.sleep(0.003)  # 3ms
        profiler.end_stage("vad_detection")
        
        # Buffer accumulation (silence detection)
        profiler.start_stage("buffer_accumulation")
        time.sleep(0.7)  # 700ms
        profiler.end_stage("buffer_accumulation")
        
        # Smart Turn
        profiler.start_stage("smart_turn")
        time.sleep(0.045)  # 45ms
        profiler.end_stage("smart_turn")
        
        # Transcription
        profiler.start_stage("transcription")
        time.sleep(0.25)  # 250ms
        profiler.end_stage("transcription")
        
        # LLM first token (bottleneck)
        profiler.start_stage("llm_first_token")
        vad_end = time.monotonic()
        time.sleep(0.5)  # 500ms
        profiler.end_stage("llm_first_token")
        
        # LLM full generation
        profiler.start_stage("llm_full_generation")
        time.sleep(1.5)  # 1500ms
        profiler.end_stage("llm_full_generation")
        
        # TTS first chunk
        profiler.start_stage("tts_first_chunk")
        time.sleep(0.07)  # 70ms
        profiler.end_stage("tts_first_chunk")
        
        # TTS full synthesis
        profiler.start_stage("tts_full_synthesis")
        time.sleep(0.4)  # 400ms
        audio_start = time.monotonic()
        profiler.end_stage("tts_full_synthesis")
        
        # Record TTFA
        profiler.record_ttfa(vad_end, audio_start)
        
        # AEC processing (many calls)
        for _ in range(10):
            profiler.start_stage("aec_processing")
            time.sleep(0.002)  # 2ms
            profiler.end_stage("aec_processing")
        
        print(f"  Completed\n")

if __name__ == "__main__":
    print("="*60)
    print("LATENCY PROFILER TEST")
    print("="*60 + "\n")
    
    # Enable profiler
    profiler.enable()
    
    # Run simulation
    simulate_pipeline()
    
    # Print report
    profiler.print_report()
    
    # Save report
    profiler.save_report("test_profile_report.json")
    
    print("\nTest completed successfully!")
    print("Check test_profile_report.json for detailed results")
