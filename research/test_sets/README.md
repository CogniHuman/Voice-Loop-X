# VoiceBench Test Sets

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
