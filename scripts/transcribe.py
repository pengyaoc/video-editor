#!/usr/bin/env python3
"""Word-level transcription via faster-whisper. Auto-detects language."""

import argparse
import json
import os
import sys

# Bootstrap the venv before importing faster-whisper
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)
import setup_env
setup_env.activate()

from faster_whisper import WhisperModel


def transcribe(input_path, output_path, language=None, model_size="medium"):
    if not os.path.exists(input_path):
        print(f"Error: file not found: {input_path}")
        sys.exit(1)

    print(f"Loading Whisper model '{model_size}'...")
    model = WhisperModel(model_size, compute_type="int8")

    print(f"Transcribing: {input_path}")
    kwargs = {"word_timestamps": True}
    if language:
        kwargs["language"] = language

    segments, info = model.transcribe(input_path, **kwargs)

    words = []
    for segment in segments:
        for word in segment.words:
            words.append({
                "text": word.word.strip(),
                "start": round(word.start, 2),
                "end": round(word.end, 2),
            })

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(words, f, ensure_ascii=False, indent=2)

    detected = info.language if not language else language
    print(f"Saved {len(words)} words to {output_path} (language: {detected})")
    return words


def main():
    parser = argparse.ArgumentParser(description="Transcribe video/audio to word-level JSON")
    parser.add_argument("input", help="Video or audio file path")
    parser.add_argument("-o", "--output", default=None, help="Output JSON path (default: transcript.json)")
    parser.add_argument("--language", default=None, help="Force language (e.g. zh, en, es)")
    parser.add_argument("--model", default="medium", help="Whisper model size (default: medium)")

    args = parser.parse_args()
    output = args.output or "transcript.json"
    transcribe(args.input, output, language=args.language, model_size=args.model)


if __name__ == "__main__":
    main()
