---
name: transcribe
description: Transcribe video or audio to word-level JSON with timestamps. Supports Chinese, English, and auto-detection. Use when the user wants to transcribe a video, generate a transcript, get word timestamps, or create captions input.
---

# Transcribe

Generate word-level transcripts from video or audio files using faster-whisper (local, no API key).

## Usage

```bash
python3 scripts/transcribe.py <input>
python3 scripts/transcribe.py <input> -o transcript.json
python3 scripts/transcribe.py <input> --language zh
python3 scripts/transcribe.py <input> --model medium
```

## Flags

| Flag | Default | Description |
|------|---------|-------------|
| `input` | (required) | Video or audio file path |
| `-o, --output` | `transcript.json` | Output JSON path |
| `--language` | auto-detect | Force language (`zh`, `en`, `es`, etc.) |
| `--model` | `medium` | Whisper model: `tiny`, `base`, `small`, `medium`, `large-v3` |

## Output Format

Flat JSON array of word objects:

```json
[
  { "text": "Hello", "start": 0.0, "end": 0.5 },
  { "text": "world", "start": 0.6, "end": 1.2 }
]
```

## Notes

- First run creates a venv at `~/.cache/video-editor/venv/` and downloads the Whisper model (~1.5GB for medium)
- Subsequent runs are fast (venv and model are cached)
- `medium` is the default — reliable for Chinese word boundaries. Use `small` for faster results on English-only audio
- The transcript output is consumed by `removefiller` and `subtitle` skills
