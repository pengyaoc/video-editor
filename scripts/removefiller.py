#!/usr/bin/env python3
"""Remove filler words and long pauses from video."""

import argparse
import json
import os
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(__file__))
import setup_env
setup_env.activate()

FILLER_WORDS_ZH = {
    "嗯", "啊", "呃", "额", "哦", "唔", "那个", "就是", "然后",
    "嗯嗯", "这个", "就是说", "对",
}

FILLER_WORDS_EN = {
    "um", "uh", "like", "you know", "so", "well", "er",
}


def detect_language(words):
    """If >30% of words contain CJK characters, return 'zh'; otherwise 'en'."""
    cjk_count = 0
    for w in words:
        if any('一' <= c <= '鿿' for c in w["text"]):
            cjk_count += 1
    return "zh" if len(words) > 0 and cjk_count / len(words) > 0.3 else "en"


def get_video_duration(input_path):
    """Get video duration in seconds via ffprobe."""
    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", input_path],
        capture_output=True, text=True,
    )
    try:
        return float(result.stdout.strip())
    except ValueError:
        return None


def remove_fillers(input_path, output_path, transcript_path=None,
                   language=None, model="medium",
                   pause_threshold=0.25, keep_padding=0.05,
                   max_word_duration=0.8):
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

    # Step 2: Detect language and pick filler list
    lang = detect_language(words)
    fillers = FILLER_WORDS_ZH if lang == "zh" else FILLER_WORDS_EN
    print(f"Detected language: {lang}")

    # Step 3: Remove filler words
    filtered = []
    removed_fillers = []
    for w in words:
        if w["text"].lower().strip() in fillers:
            removed_fillers.append(w)
        else:
            filtered.append(w)

    if removed_fillers:
        print(f"Removing {len(removed_fillers)} filler words:")
        for filler in removed_fillers:
            print(f"  '{filler['text']}' at {filler['start']:.2f}s - {filler['end']:.2f}s")

    words = filtered

    # Step 4: Trim suspiciously long single words
    trimmed_count = 0
    result = []
    for w in words:
        dur = w["end"] - w["start"]
        if dur > max_word_duration and len(w["text"]) <= 2:
            new_end = w["start"] + 0.4
            print(f"  Trimming '{w['text']}' from {dur:.2f}s to 0.40s")
            result.append({**w, "end": new_end})
            trimmed_count += 1
        else:
            result.append(w)
    words = result

    # Step 5: Build speech segments
    segments = []
    seg_start = words[0]["start"]

    for i in range(1, len(words)):
        gap = words[i]["start"] - words[i - 1]["end"]
        if gap > pause_threshold:
            segments.append((
                max(0, seg_start - keep_padding),
                words[i - 1]["end"] + keep_padding,
            ))
            seg_start = words[i]["start"]

    segments.append((
        max(0, seg_start - keep_padding),
        words[-1]["end"] + keep_padding,
    ))

    # Step 6: Calculate stats
    original_duration = get_video_duration(input_path)
    total_kept = sum(end - start for start, end in segments)
    total_cut = (original_duration - total_kept) if original_duration else None

    print(f"\nFound {len(segments)} speech segments from {len(words)} words")
    if original_duration:
        print(f"Original duration: {original_duration:.1f}s")
        print(f"Total cut: {total_cut:.1f}s")
        print(f"Output duration: ~{total_kept:.1f}s")

    # Step 7: Build FFmpeg filter_complex and run
    filter_parts = []
    for i, (start, end) in enumerate(segments):
        filter_parts.append(
            f"[0:v]trim=start={start}:end={end},setpts=PTS-STARTPTS[v{i}];"
            f"[0:a]atrim=start={start}:end={end},asetpts=PTS-STARTPTS[a{i}];"
        )

    concat_inputs = "".join(f"[v{i}][a{i}]" for i in range(len(segments)))
    filter_parts.append(f"{concat_inputs}concat=n={len(segments)}:v=1:a=1[outv][outa]")
    filter_complex = "".join(filter_parts)

    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-filter_complex", filter_complex,
        "-map", "[outv]", "-map", "[outa]",
        "-c:v", "libx264", "-preset", "fast", "-crf", "18",
        "-c:a", "aac", "-b:a", "192k",
        output_path,
    ]

    print("\nRunning FFmpeg...")
    result = subprocess.run(cmd, capture_output=True, text=True)

    # Clean up temp transcript
    if tmp_transcript and os.path.exists(tmp_transcript):
        os.remove(tmp_transcript)

    if result.returncode == 0:
        print(f"Done! Output: {output_path}")
        print(f"\nSummary:")
        print(f"  Fillers removed: {len(removed_fillers)}")
        print(f"  Words trimmed: {trimmed_count}")
        if total_cut:
            print(f"  Time saved: {total_cut:.1f}s")
    else:
        print(f"FFmpeg error: {result.stderr[-500:]}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Remove filler words and pauses from video")
    parser.add_argument("input", help="Video file path")
    parser.add_argument("-o", "--output", default=None, help="Output path (default: <input>_cut.mp4)")
    parser.add_argument("--transcript", default=None, help="Reuse existing transcript JSON")
    parser.add_argument("--language", default=None, help="Force language for transcription")
    parser.add_argument("--model", default="medium", help="Whisper model size (default: medium)")
    parser.add_argument("--pause-threshold", type=float, default=0.25,
                        help="Cut gaps longer than this (seconds, default: 0.25)")
    parser.add_argument("--keep-padding", type=float, default=0.05,
                        help="Silence to keep at boundaries (seconds, default: 0.05)")
    parser.add_argument("--max-word-duration", type=float, default=0.8,
                        help="Trim single words longer than this (seconds, default: 0.8)")

    args = parser.parse_args()

    if args.output:
        output = args.output
    else:
        base, ext = os.path.splitext(args.input)
        output = f"{base}_cut.mp4"

    remove_fillers(
        args.input, output,
        transcript_path=args.transcript,
        language=args.language, model=args.model,
        pause_threshold=args.pause_threshold,
        keep_padding=args.keep_padding,
        max_word_duration=args.max_word_duration,
    )


if __name__ == "__main__":
    main()
