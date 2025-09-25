# AI Content Creator Helper – Long Video to Shorts

## Overview

This project automates the process of converting long videos into **short, engaging clips** (e.g., YouTube Shorts, Instagram Reels, TikTok).  
It uses the **Gemini API** for AI-based content analysis, summarization, and caption generation, along with **FFmpeg** for video processing.

## Setup

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd "Ai Content Creator Helper - Log video to shorts"
   ```

2. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**

   - Copy the `.env` file and add your Gemini API key:

   ```bash
   GEMINI_API_KEY=your_actual_gemini_api_key_here
   ```

   - Get your API key from [Google AI Studio](https://makersuite.google.com/app/apikey)

4. **Install FFmpeg**
   - Download and install FFmpeg from [https://ffmpeg.org/download.html](https://ffmpeg.org/download.html)
   - Make sure it's added to your system PATH

## Features

- Extracts highlights from long-form video.
- Uses **Gemini API** for intelligent scene analysis & summarization.
- Generates engaging captions automatically.
- Adds background music (optional).
- Outputs vertical video format optimized for Shorts/Reels/TikTok.
- Lightweight: only uses FFmpeg + Gemini API (no heavy libraries).

## Tech Stack

- **Python**
- **Gemini API** (AI analysis + captions)
- **FFmpeg** (video trimming & formatting)

## Workflow

1. **Input Video** → Provide a long video.
2. **Scene Detection** → Split video into smaller segments.
3. **AI Processing (Gemini)** →
   - Analyze transcript/visuals
   - Pick best highlight moments
   - Generate captions & hooks
4. **Video Processing (FFmpeg)** →
   - Trim & reformat video
   - Overlay captions
   - Add background audio (if needed)
5. **Output** → Short-form video, ready for posting.

## Potential Use Cases

1. Content creators converting podcasts, lectures, vlogs → Shorts/Reels

2. Startups repurposing webinars → Marketing snippets

3. Teachers summarizing lectures → Quick revision shorts

## Future Improvements

1. Face detection to focus on speaker.

2. Direct upload to YouTube Shorts API.

3. More advanced caption styling.
