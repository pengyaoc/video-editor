# video-editor

Video editing tools — transcription, filler removal, subtitles. Works with Chinese and English audio.

## Installation

```bash
npx skills add <your-github>/video-editor
```

Or clone and use directly:

```bash
git clone https://github.com/<your-github>/video-editor.git
```

## Prerequisites

- **Python 3.8+** — `python3 --version`
- **FFmpeg** — `brew install ffmpeg` (macOS) or `apt install ffmpeg` (Linux)
- **~1.5GB disk** — for Whisper model (downloaded on first run)

No manual `pip install` needed. Dependencies are installed automatically into `~/.cache/video-editor/venv/` on first run.

## Tools

### transcribe

Generate word-level transcripts from video/audio files.

```bash
python3 scripts/transcribe.py video.mov
python3 scripts/transcribe.py video.mov -o transcript.json
python3 scripts/transcribe.py video.mov --language zh
python3 scripts/transcribe.py video.mov --model medium
```

### removefiller

Remove filler words (嗯, 啊, um, uh, like...) and long pauses from video.

```bash
python3 scripts/removefiller.py video.mov
python3 scripts/removefiller.py video.mov -o clean.mp4
python3 scripts/removefiller.py video.mov --transcript transcript.json
python3 scripts/removefiller.py video.mov --pause-threshold 0.3
```

### subtitle

Burn subtitles into video from transcript.

```bash
python3 scripts/subtitle.py video.mov
python3 scripts/subtitle.py video.mov --transcript transcript.json
python3 scripts/subtitle.py video.mov --max-chars 20 --font-size 48
```

## How It Works

1. On first run, creates a Python virtual environment at `~/.cache/video-editor/venv/` and installs `faster-whisper`
2. Whisper model weights are cached at `~/.cache/huggingface/` (~1.5GB for `medium`)
3. Subsequent runs reuse both — startup is near-instant
