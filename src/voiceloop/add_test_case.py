#!/usr/bin/env python3
"""
Helper script to add new test cases to VoiceBench
Usage: python add_test_case.py
"""

import json
import os
from pathlib import Path

def add_test_case():
    """Interactive script to add a new test case"""
    
    print("\n" + "="*70)
    print("ADD NEW TEST CASE TO VOICEBENCH")
    print("="*70)
    
    # Get test case details
    print("\nTest Case Details:")
    test_id = input("Test ID (e.g., short_004): ").strip()
    audio_filename = input("Audio filename (e.g., what_time.wav): ").strip()
    ground_truth = input("Ground truth text: ").strip().lower()
    
    print("\nCategory:")
    print("  1. short (1-3 seconds)")
    print("  2. medium (3-5 seconds)")
    print("  3. long (5-10 seconds)")
    category_choice = input("Choose category (1-3): ").strip()
    
    category_map = {"1": "short", "2": "medium", "3": "long"}
    category = category_map.get(category_choice, "short")
    
    print("\nResponse Type:")
    print("  1. factual (questions with factual answers)")
    print("  2. conversational (greetings, thanks, etc.)")
    print("  3. command (instructions, requests)")
    response_choice = input("Choose response type (1-3): ").strip()
    
    response_map = {"1": "factual", "2": "conversational", "3": "command"}
    response_type = response_map.get(response_choice, "conversational")
    
    duration = float(input("Duration in seconds (e.g., 1.5): ").strip())
    
    print("\nDifficulty:")
    print("  1. easy")
    print("  2. medium")
    print("  3. hard")
    difficulty_choice = input("Choose difficulty (1-3): ").strip()
    
    difficulty_map = {"1": "easy", "2": "medium", "3": "hard"}
    difficulty = difficulty_map.get(difficulty_choice, "easy")
    
    # Create test case object
    test_case = {
        "id": test_id,
        "audio_path": f"audio/{audio_filename}",
        "ground_truth_text": ground_truth,
        "expected_response_type": response_type,
        "duration_sec": duration,
        "category": category,
        "metadata": {
            "difficulty": difficulty
        }
    }
    
    # Determine which JSON file to update
    json_file = f"test_sets/{category}_queries.json"
    
    # Load existing test cases
    if os.path.exists(json_file):
        with open(json_file, 'r') as f:
            test_cases = json.load(f)
    else:
        test_cases = []
    
    # Add new test case
    test_cases.append(test_case)
    
    # Save updated test cases
    with open(json_file, 'w') as f:
        json.dump(test_cases, f, indent=2)
    
    print("\n" + "="*70)
    print(f"✅ Test case added to {json_file}")
    print("="*70)
    print("\nTest Case:")
    print(json.dumps(test_case, indent=2))
    print("\n⚠️  Don't forget to place the audio file at:")
    print(f"   research/test_sets/audio/{audio_filename}")
    print("="*70 + "\n")

if __name__ == "__main__":
    add_test_case()
