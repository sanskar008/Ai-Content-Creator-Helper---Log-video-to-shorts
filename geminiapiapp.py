import os
import google.generativeai as genai
import subprocess
from moviepy.editor import VideoFileClip
import json

# -----------------------------
# CONFIG
# -----------------------------
GENAI_API_KEY = (
    "AIzaSyBzqXhSxpRElacXbYbiOxGab1wXMSn9UVc"  # paste your Gemini API key here
)
genai.configure(api_key=GENAI_API_KEY)

INPUT_VIDEO = "sample2.mp4"
OUTPUT_DIR = "shorts"
os.makedirs(OUTPUT_DIR, exist_ok=True)


# -----------------------------
# STEP 1: Extract Audio
# -----------------------------
def extract_audio(video_path, audio_path="audio.wav"):
    command = (
        f"ffmpeg -i {video_path} -vn -acodec pcm_s16le -ar 16000 -ac 1 {audio_path} -y"
    )
    subprocess.run(command, shell=True)
    return audio_path


# -----------------------------
# STEP 2: Transcribe Audio (using Whisper via OpenAI CLI for lightness)
# -----------------------------
def transcribe(audio_path):
    # Whisper tiny model (small size) via CLI
    command = f"whisper {audio_path} --model tiny --output_format json"
    subprocess.run(command, shell=True)
    with open(audio_path.replace(".wav", ".json"), "r", encoding="utf-8") as f:
        transcript = json.load(f)
    return transcript["text"]


# -----------------------------
# STEP 3: Ask Gemini for Highlights
# -----------------------------
def get_highlights(transcript_text):
    prompt = f"""
    I have this video transcript:

    {transcript_text[:5000]}

    Please give me 2-3 of the most engaging short moments (30–60 seconds each).
    Reply strictly in JSON format like this:

    [
      {{"start": 30, "end": 90, "reason": "funny moment"}},
      {{"start": 120, "end": 160, "reason": "educational tip"}}
    ]
    """
    response = genai.GenerativeModel("gemini-1.5-flash").generate_content(prompt)
    try:
        highlights = json.loads(response.text)
    except:
        highlights = []
    return highlights


# -----------------------------
# STEP 4: Cut Video
# -----------------------------
def cut_video(video_path, highlights):
    clip = VideoFileClip(video_path)
    shorts = []
    for i, h in enumerate(highlights):
        start, end = h["start"], h["end"]
        subclip = clip.subclip(start, end)
        output_path = os.path.join(OUTPUT_DIR, f"short_{i+1}.mp4")
        subclip.write_videofile(output_path, codec="libx264")
        shorts.append(output_path)
    return shorts


# -----------------------------
# MAIN PIPELINE
# -----------------------------
if __name__ == "__main__":
    print("▶ Extracting audio...")
    audio = extract_audio(INPUT_VIDEO)

    print("▶ Transcribing...")
    transcript = transcribe(audio)

    print("▶ Asking Gemini for highlights...")
    highlights = get_highlights(transcript)
    print("Gemini Highlights:", highlights)

    print("▶ Cutting video...")
    shorts = cut_video(INPUT_VIDEO, highlights)

    print("✅ Shorts ready:", shorts)
