---
name: subtitle
description: Burn subtitles into video from word-level transcript. Supports Chinese and English. Use when the user wants to add subtitles, captions, or text overlay synced to speech.
---

# Subtitle

Burn word-timed subtitles into video.

## Usage

```bash
python3 scripts/subtitle.py <input>
python3 scripts/subtitle.py <input> --transcript transcript.json
python3 scripts/subtitle.py <input> -o subtitled.mp4
python3 scripts/subtitle.py <input> --max-chars 20 --font-size 48
```

## Flags

| Flag | Default | Description |
|------|---------|-------------|
| `input` | (required) | Video file path |
| `-o, --output` | `<input>_sub.mp4` | Output video path |
| `--transcript` | (none) | Reuse existing transcript JSON (skips transcription) |
| `--language` | auto-detect | Force language for transcription |
| `--model` | `medium` | Whisper model size |
| `--max-chars` | `18` | Max characters per subtitle line |
| `--position` | `bottom` | Subtitle position: `bottom` or `top` |
| `--font-size` | `48` | Font size in pixels |
| `--font-color` | `white` | Text color (white, yellow, red, green, blue, black) |

## How Word Grouping Works

Words are accumulated into a subtitle line until either:
- The character count exceeds `--max-chars`, or
- There's a pause > 0.3s between words

This keeps subtitles readable and naturally aligned with speech rhythm. The default `--max-chars 18` works for both Chinese and English.

## Tips

- Pass `--transcript` if you already ran `transcribe` or `removefiller`
- Use `--font-size 64` for mobile-friendly videos
- Use `--position top` if the speaker is at the bottom of frame
