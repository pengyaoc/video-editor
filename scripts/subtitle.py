#!/usr/bin/env python3
"""Burn subtitles into video from word-level transcript."""

import argparse
import json
import os
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(__file__))
import setup_env
setup_env.activate()


def format_srt_time(seconds):
    """Convert seconds to SRT time format: HH:MM:SS,mmm"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def group_words(words, max_chars=18, pause_break=0.3):
    """Group words into subtitle lines based on character count and pauses."""
    lines = []
    current_words = []
    current_chars = 0

    for i, w in enumerate(words):
        word_len = len(w["text"])

        # Check if adding this word would exceed max_chars
        would_exceed = (current_chars + word_len + (1 if current_words else 0)) > max_chars

        # Check if there's a long pause before this word
        has_pause = (i > 0 and w["start"] - words[i - 1]["end"] > pause_break)

        if current_words and (would_exceed or has_pause):
            lines.append({
                "text": " ".join(ww["text"] for ww in current_words),
                "start": current_words[0]["start"],
                "end": current_words[-1]["end"],
            })
            current_words = []
            current_chars = 0

        current_words.append(w)
        current_chars += word_len + (1 if len(current_words) > 1 else 0)

    if current_words:
        lines.append({
            "text": " ".join(ww["text"] for ww in current_words),
            "start": current_words[0]["start"],
            "end": current_words[-1]["end"],
        })

    return lines


def generate_srt(lines):
    """Generate SRT content from grouped lines."""
    srt_parts = []
    for i, line in enumerate(lines, 1):
        start = format_srt_time(line["start"])
        end = format_srt_time(line["end"])
        srt_parts.append(f"{i}\n{start} --> {end}\n{line['text']}\n")
    return "\n".join(srt_parts)


def find_ffmpeg():
    """Return the path to an ffmpeg binary that supports the subtitles filter."""
    candidates = [
        "/opt/homebrew/opt/ffmpeg-full/bin/ffmpeg",
        "ffmpeg",
    ]
    for ffmpeg_bin in candidates:
        result = subprocess.run(
            [ffmpeg_bin, "-filters"],
            capture_output=True, text=True
        )
        if "subtitles" in result.stdout:
            return ffmpeg_bin
    # Fall back to plain ffmpeg even if it lacks the filter (will error at runtime)
    return "ffmpeg"


def burn_subtitles(input_path, output_path, transcript_path=None,
                   language=None, model="medium",
                   max_chars=18, position="bottom",
                   font_size=48, font_color="white"):
    if not os.path.exists(input_path):
        print(f"Error: file not found: {input_path}")
        sys.exit(1)

    # Step 1: Get transcript
    tmp_transcript = None
    if transcript_path:
        with open(transcript_path, "r", encoding="utf-8") as f:
            words = json.load(f)
        print(f"Loaded {len(words)} words from {transcript_path}")
    else:
        from transcribe import transcribe as do_transcribe
        tmp_fd, tmp_transcript = tempfile.mkstemp(suffix=".json")
        os.close(tmp_fd)
        words = do_transcribe(input_path, tmp_transcript,
                              language=language, model_size=model)

    if not words:
        print("Error: transcript is empty — no words found.")
        sys.exit(1)

    # Step 2: Group words into subtitle lines
    lines = group_words(words, max_chars=max_chars)
    print(f"Generated {len(lines)} subtitle lines from {len(words)} words")

    # Step 3: Generate SRT file
    srt_content = generate_srt(lines)
    tmp_fd, srt_path = tempfile.mkstemp(suffix=".srt")
    os.close(tmp_fd)
    with open(srt_path, "w", encoding="utf-8") as f:
        f.write(srt_content)

    # Step 4: Build FFmpeg command
    # Position: bottom = Alignment=2 (center-bottom), top = Alignment=6 (center-top)
    alignment = 2 if position == "bottom" else 6
    margin_v = 30

    # Escape special characters in srt_path for FFmpeg filter
    escaped_srt = srt_path.replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'")

    style = f"FontSize={font_size},PrimaryColour=&H00FFFFFF,Alignment={alignment},MarginV={margin_v}"
    if font_color != "white":
        # Convert common color names to ASS BGR hex
        color_map = {
            "yellow": "&H0000FFFF",
            "red": "&H000000FF",
            "green": "&H0000FF00",
            "blue": "&H00FF0000",
            "black": "&H00000000",
        }
        if font_color in color_map:
            style = style.replace("&H00FFFFFF", color_map[font_color])

    ffmpeg_bin = find_ffmpeg()
    cmd = [
        ffmpeg_bin, "-y",
        "-i", input_path,
        "-vf", f"subtitles={escaped_srt}:force_style='{style}'",
        "-c:v", "libx264", "-preset", "fast", "-crf", "18",
        "-c:a", "aac", "-b:a", "192k",
        output_path,
    ]

    print("Burning subtitles...")
    result = subprocess.run(cmd, capture_output=True, text=True)

    # Clean up temp files
    os.remove(srt_path)
    if tmp_transcript and os.path.exists(tmp_transcript):
        os.remove(tmp_transcript)

    if result.returncode == 0:
        print(f"Done! Output: {output_path}")
    else:
        print(f"FFmpeg error: {result.stderr[-500:]}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Burn subtitles into video")
    parser.add_argument("input", help="Video file path")
    parser.add_argument("-o", "--output", default=None, help="Output path (default: <input>_sub.mp4)")
    parser.add_argument("--transcript", default=None, help="Reuse existing transcript JSON")
    parser.add_argument("--language", default=None, help="Force language for transcription")
    parser.add_argument("--model", default="medium", help="Whisper model size (default: medium)")
    parser.add_argument("--max-chars", type=int, default=18, help="Max chars per subtitle line (default: 18)")
    parser.add_argument("--position", choices=["bottom", "top"], default="bottom",
                        help="Subtitle position (default: bottom)")
    parser.add_argument("--font-size", type=int, default=48, help="Font size (default: 48)")
    parser.add_argument("--font-color", default="white", help="Font color (default: white)")

    args = parser.parse_args()

    if args.output:
        output = args.output
    else:
        base, ext = os.path.splitext(args.input)
        output = f"{base}_sub.mp4"

    burn_subtitles(
        args.input, output,
        transcript_path=args.transcript,
        language=args.language, model=args.model,
        max_chars=args.max_chars, position=args.position,
        font_size=args.font_size, font_color=args.font_color,
    )


if __name__ == "__main__":
    main()
