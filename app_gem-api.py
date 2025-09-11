import os
import google.generativeai as genai
import subprocess
import json
import re

# -----------------------------
# CONFIG
# -----------------------------
GENAI_API_KEY = "AIzaSyCAuuQRcB4VzOaIjlSCSySFcdju1jtA7bo"  # paste your Gemini API key
genai.configure(api_key=GENAI_API_KEY)
model = genai.GenerativeModel("models/gemini-2.5-pro")

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
# STEP 2: Transcribe Audio
# -----------------------------
def transcribe(audio_path):
    command = f"whisper {audio_path} --model tiny --output_format json"
    subprocess.run(command, shell=True)
    with open(audio_path.replace(".wav", ".json"), "r", encoding="utf-8") as f:
        transcript = json.load(f)
    return transcript["text"]


# -----------------------------
# STEP 3: Ask Gemini for Highlights
# -----------------------------
def get_highlights(transcript, model):
    prompt = (
        "Given the following transcript, extract 3 of the most interesting, engaging, or insightful moments. "
        "For each, return a JSON list of objects with keys: 'start', 'end', and 'text'. "
        'Format example: [{"start": "00:00:00", "end": "00:00:10", "text": "..."}, ...]\n'
        "Transcript:\n" + transcript
    )

    response = model.generate_content(prompt)
    raw = response.text
    print("Gemini raw response:", raw)

    try:
        cleaned = extract_json_from_gemini_response(raw)
        highlights = json.loads(cleaned)
        if not isinstance(highlights, list):
            raise ValueError("Not a list")
    except Exception as e:
        print("Failed to parse highlights as JSON:", e)
        highlights = []

    if not highlights:
        print(
            "No highlights found. Consider refining your prompt or checking the transcript."
        )
    else:
        print("Gemini Highlights:", highlights)

    return highlights


def extract_json_from_gemini_response(response_text):
    # Remove triple backticks and optional 'json' after them
    cleaned = re.sub(
        r"^```json\s*|^```\s*|```$", "", response_text.strip(), flags=re.MULTILINE
    )
    return cleaned


# -----------------------------
# STEP 4: Cut Video with FFmpeg
# -----------------------------
def cut_video_ffmpeg(video_path, highlights):
    shorts = []
    for i, h in enumerate(highlights):
        start, end = h["start"], h["end"]
        output_path = os.path.join(OUTPUT_DIR, f"short_{i+1}.mp4")
        command = (
            f'ffmpeg -i "{video_path}" -ss {start} -to {end} -c copy "{output_path}" -y'
        )
        subprocess.run(command, shell=True)
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
    highlights = get_highlights(transcript, model)
    print("Gemini Highlights:", highlights)

    print("▶ Cutting video with FFmpeg...")
    shorts = cut_video_ffmpeg(INPUT_VIDEO, highlights)

    print("✅ Shorts ready:", shorts)
