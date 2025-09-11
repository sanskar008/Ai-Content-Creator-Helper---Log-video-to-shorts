#!/usr/bin/env python3
"""
shorts_pipeline_full.py
Usage:
  python shorts_pipeline_full.py --url "https://youtu.be/VIDEOID" --outdir demo_out --num_clips 3
  or
  python shorts_pipeline_full.py --input /path/to/local.mp4 --outdir demo_out --num_clips 3

What it does:
 - downloads video (if --url)
 - transcribes with Whisper (model: tiny/base/small/medium)
 - builds candidate windows and scores them
 - selects top non-overlapping highlights
 - cuts clips with ffmpeg (fast copy)
 - creates SRTs and burns subtitles (re-encode lightly)
 - outputs final clips and JSON summary
"""
import argparse, subprocess, json, shutil
from pathlib import Path
import whisper
import nltk
from nltk.corpus import stopwords
from collections import Counter
import math
import os
import sys
import tempfile
import nltk

nltk.download("punkt_tab")

# --------- NLTK setup (first-run) ----------
nltk.download("punkt", quiet=True)
nltk.download("stopwords", quiet=True)
STOP = set(stopwords.words("english"))


# --------- Helper funcs ----------
def run(cmd, check=True):
    print("RUN:", " ".join(cmd))
    res = subprocess.run(cmd, check=check)
    return res


def seconds_to_srt_timestamp(t):
    # t in seconds (float) -> "HH:MM:SS,mmm"
    h = int(t // 3600)
    m = int((t % 3600) // 60)
    s = int(t % 60)
    ms = int((t - int(t)) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def srt_block(idx, start, end, text):
    return f"{idx}\n{seconds_to_srt_timestamp(start)} --> {seconds_to_srt_timestamp(end)}\n{text.strip()}\n\n"


# --------- pipeline steps ----------
def download_video(url, outdir: Path):
    outdir.mkdir(parents=True, exist_ok=True)
    out = outdir / "input.%(ext)s"
    # use yt-dlp to grab best mp4 if possible
    run(["yt-dlp", "-f", "bestvideo[ext=mp4]+bestaudio/best", url, "-o", str(out)])
    # yt-dlp will write a file like input.mp4
    # find first mp4 in outdir
    for f in outdir.iterdir():
        if f.suffix.lower() in [".mp4", ".mkv", ".webm", ".mov"]:
            return str(f)
    raise FileNotFoundError("Downloaded file not found in " + str(outdir))


def transcribe_with_whisper(input_path, model="small", verbose=False):
    print("Loading Whisper model:", model)
    m = whisper.load_model(model)
    print("Transcribing... (this can take some time depending on model & CPU/GPU)")
    result = m.transcribe(input_path, verbose=verbose)
    segments = result.get("segments", [])
    print(f"Transcription produced {len(segments)} segments")
    return segments


def build_candidates(segments, target_len=40, min_len=20, max_len=60):
    candidates = []
    n = len(segments)
    for i in range(n):
        start = segments[i]["start"]
        end = segments[i]["end"]
        text_parts = [segments[i]["text"]]
        j = i + 1
        while (end - start) < target_len and j < n and (end - start) < max_len:
            end = segments[j]["end"]
            text_parts.append(segments[j]["text"])
            j += 1
        if (end - start) >= min_len:
            candidates.append(
                {"start": start, "end": end, "text": " ".join(text_parts)}
            )
    print(f"Built {len(candidates)} candidate windows")
    return candidates


# simple scoring heuristic
POWER_WORDS = set(
    [
        "amazing",
        "incredible",
        "surprising",
        "shocking",
        "wow",
        "unbelievable",
        "insane",
        "funny",
        "joke",
        "laugh",
        "emotional",
        "tear",
        "tip",
        "hack",
        "secret",
        "change",
        "best",
        "mistake",
        "fail",
        "win",
        "winning",
        "reveal",
        "revealed",
        "wow",
    ]
)


def score_text(text):
    words = [w.lower() for w in nltk.word_tokenize(text) if w.isalpha()]
    word_count = len(words)
    power_hits = sum(1 for w in words if w in POWER_WORDS)
    exclaims = text.count("!") + text.count("…") + text.count("?")
    key_words = [w for w in words if w not in STOP]
    uniq = len(set(key_words))
    score = power_hits * 6 + exclaims * 2 + uniq * 0.4 + min(word_count, 60) * 0.08
    return score


def select_top_non_overlapping(candidates, top_k=3, min_gap=3.0):
    for c in candidates:
        c["score"] = score_text(c["text"])
    candidates.sort(key=lambda x: x["score"], reverse=True)
    selected = []
    for c in candidates:
        if len(selected) >= top_k:
            break
        overlap = False
        for s in selected:
            if not (c["end"] + min_gap < s["start"] or c["start"] - min_gap > s["end"]):
                overlap = True
                break
        if not overlap:
            selected.append(c)
    selected.sort(key=lambda x: x["start"])
    print(f"Selected {len(selected)} highlights")
    return selected


def cut_clip_copy(input_file, start, end, out_file):
    # use -ss before -i for faster seek when copying
    run(
        [
            "ffmpeg",
            "-y",
            "-ss",
            str(start),
            "-to",
            str(end),
            "-i",
            input_file,
            "-c",
            "copy",
            out_file,
        ]
    )


def build_srt_for_clip(clip_start, clip_end, segments):
    srt = ""
    idx = 1
    for seg in segments:
        seg_start = seg["start"]
        seg_end = seg["end"]
        if seg_end < clip_start or seg_start > clip_end:
            continue
        rel_start = max(0.0, seg_start - clip_start)
        rel_end = max(0.0, min(seg_end, clip_end) - clip_start)
        srt += srt_block(idx, rel_start, rel_end, seg["text"])
        idx += 1
    return srt


def save_file(path, text):
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def generate_title_and_hashtags(text):
    words = [w.lower() for w in nltk.word_tokenize(text) if w.isalpha()]
    words = [w for w in words if w not in STOP]
    c = Counter(words)
    top = [w for w, _ in c.most_common(4)]
    title = " ".join(top).title() or "Short Clip"
    hashtags = " ".join("#" + w for w in top[:3]) if top else "#shorts"
    return title, hashtags


def concat_clips_list(file_list_path, output_path):
    # ffmpeg concat (works when all clips have same codecs/enc)
    run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(file_list_path),
            "-c",
            "copy",
            str(output_path),
        ]
    )


# --------- Main ----------
def main():
    p = argparse.ArgumentParser()
    p.add_argument("--url", type=str, default=None)
    p.add_argument("--input", type=str, default=None)
    p.add_argument("--outdir", type=str, default="output")
    p.add_argument("--num_clips", type=int, default=3)
    p.add_argument(
        "--whisper_model",
        type=str,
        default="small",
        help="tiny|base|small|medium|large",
    )
    p.add_argument("--target_len", type=int, default=40)
    p.add_argument("--min_len", type=int, default=20)
    args = p.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    # 1) download or check input
    if args.url:
        print("Downloading video...")
        input_file = download_video(args.url, outdir=outdir)
    elif args.input:
        input_file = args.input
        if not Path(input_file).exists():
            print("Input file does not exist:", input_file)
            sys.exit(1)
    else:
        print("Provide --url or --input")
        sys.exit(1)

    print("Input file:", input_file)

    # 2) transcribe
    segments = transcribe_with_whisper(input_file, model=args.whisper_model)

    # 3) build candidate windows
    candidates = build_candidates(
        segments,
        target_len=args.target_len,
        min_len=args.min_len,
        max_len=args.target_len + 20,
    )

    # 4) select top K
    picks = select_top_non_overlapping(candidates, top_k=args.num_clips)

    # 5) cut, create srt, burn subtitles
    results = []
    clip_files_for_concat = []
    for idx, pck in enumerate(picks, start=1):
        start = pck["start"]
        end = pck["end"]
        raw_clip = outdir / f"clip_{idx}_raw.mp4"
        final_clip = outdir / f"clip_{idx}_final.mp4"

        print(f"Cutting clip {idx}: {start:.2f} -> {end:.2f}")
        cut_clip_copy(input_file, start, end, str(raw_clip))

        # SRT using segments overlapping the clip
        clip_srt = build_srt_for_clip(start, end, segments)
        srt_path = outdir / f"clip_{idx}.srt"
        save_file(srt_path, clip_srt)

        # Burn subtitles (re-encode lightly for subtitle burn)
        # On Windows, if path contains spaces, ffmpeg subtitles filter may need escaping. Use -i + -filter_complex instead if problems appear.
        run(
            [
                "ffmpeg",
                "-y",
                "-i",
                str(raw_clip),
                "-vf",
                f"subtitles={str(srt_path)}",
                "-c:v",
                "libx264",
                "-preset",
                "veryfast",
                "-c:a",
                "aac",
                str(final_clip),
            ]
        )

        title, hashtags = generate_title_and_hashtags(pck["text"])
        results.append(
            {
                "clip": str(final_clip),
                "start": start,
                "end": end,
                "title": title,
                "hashtags": hashtags,
                "score": pck.get("score", None),
            }
        )
        clip_files_for_concat.append(final_clip)

    # Create a short compilation file for demo (optional)
    if clip_files_for_concat:
        filelist = outdir / "concat_list.txt"
        with open(filelist, "w", encoding="utf-8") as f:
            for c in clip_files_for_concat:
                f.write(f"file '{str(c)}'\n")
        compilation = outdir / "shorts_compilation.mp4"
        concat_clips_list(filelist, compilation)

    # Dump JSON summary
    summary_path = outdir / "clips_summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print("\nDone. Results:")
    print(json.dumps(results, indent=2))
    print("Output folder:", outdir.resolve())


if __name__ == "__main__":
    main()
