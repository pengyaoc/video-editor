---
name: removefiller
description: Remove filler words (嗯, 啊, um, uh, like) and long pauses from video. Supports Chinese and English with auto-detection. Use when the user wants to clean up a video, remove fillers, cut dead air, or do a rough cut.
---

# Remove Filler

Remove filler words and long pauses from video, producing a clean rough cut.

## Usage

```bash
python3 scripts/removefiller.py <input>
python3 scripts/removefiller.py <input> -o clean.mp4
python3 scripts/removefiller.py <input> --transcript transcript.json
python3 scripts/removefiller.py <input> --pause-threshold 0.3
```

## Flags

| Flag | Default | Description |
|------|---------|-------------|
| `input` | (required) | Video file path |
| `-o, --output` | `<input>_cut.mp4` | Output video path |
| `--transcript` | (none) | Reuse existing transcript JSON (skips transcription) |
| `--language` | auto-detect | Force language for transcription |
| `--model` | `medium` | Whisper model size |
| `--pause-threshold` | `0.25` | Cut gaps longer than this (seconds) |
| `--keep-padding` | `0.05` | Silence kept at cut boundaries |
| `--max-word-duration` | `0.8` | Trim single words longer than this |

## What It Does

1. Transcribes the video (or loads existing transcript)
2. Auto-detects language (Chinese vs English)
3. Removes filler words (Chinese: 嗯, 啊, 呃, 额, 然后, 这个, etc. English: um, uh, like, etc.)
4. Trims suspiciously long single words (hidden fillers merged by Whisper)
5. Cuts silence gaps longer than the threshold
6. Outputs clean video via FFmpeg

## Tips

- Pass `--transcript` if you already have a transcript to skip re-transcription
- Lower `--pause-threshold` (e.g. 0.15) for more aggressive cutting
- Raise `--pause-threshold` (e.g. 0.5) to keep natural pauses for emphasis
