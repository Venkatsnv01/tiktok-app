# PDF to TikTok Content Generator 

This Streamlit application extracts text from PDF files, generates TikTok scripts using AI, converts text to speech, and creates TikTok-style videos with overlaid content.
Created for a bounty hackathon (re: https://x.com/the_jasonsamuel/status/1828082930813747579)

## Features

- PDF text extraction
- AI-powered (Claude) TikTok script generation
- Text-to-speech conversion
- Video creation with overlaid text and audio with CTA 

## Setup

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Create a `.env` file with your Anthropic API key: `ANTHROPIC_API_KEY=your_api_key_here`
4. Place video files in the `./videos` directory (for the video library)

## Usage

1. Run the app: `streamlit run main.py`
2. Upload a PDF file
3. Generate TikTok content
4. Edit the generated script 
5. Convert text to speech
6. Select or upload a video
7. Generate the final TikTok video
