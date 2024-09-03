import streamlit as st
import fitz
from langchain_anthropic import ChatAnthropic
from dotenv import load_dotenv
import asyncio
import edge_tts
import moviepy.editor as mp  
import os
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import tempfile
import subprocess

# List to store extracted content from each page
objList = []

def extract_text_from_pdf(uploaded_file):
    # Open the uploaded PDF file
    pdf_document = fitz.open(stream=uploaded_file.read(), filetype="pdf")
    text = ""
    count = 0
    # Iterate through each page in the PDF
    for page_number in range(len(pdf_document)):
        count += 1        
        obj = {} 
        page = pdf_document.load_page(page_number)
        content = page.get_text()
        obj["pageNo"] = count
        obj["content"] = content
        obj["contentLength"] = len(content) if content else 0
        text += content if content else ""
        objList.append(obj)
    return text

def show_content():
    # Display the extracted content from each page
    for i in range(len(objList)):
        st.write("Page:", objList[i]["pageNo"])
        st.write("Content Length:", objList[i]["contentLength"])
        st.write("Content:", objList[i]["content"]) 

def generate_tiktok_content(extracted_text):
    # Load environment variables
    load_dotenv()
    anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")

    # Initialize Claude API with the specified model and API key
    claude = ChatAnthropic(model="claude-3-sonnet-20240229", api_key=anthropic_api_key)

    # Define the prompt to generate viral TikTok content
    prompt = f"Generate a viral TikTok script from the following content with a CTA and hook, no emojis, no need to give instructions, readable in less than 30 seconds: {extracted_text}"

    # Call the Claude API to generate TikTok content
    response = claude.invoke(input=[{"role": "user", "content": prompt}], max_tokens=3000)
    tiktok_script = response.content

    return tiktok_script

async def convert_text_to_speech(text, voice_model):
    # Convert the given text to speech using the specified voice model
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_file:
        communicate = edge_tts.Communicate(text, voice_model)
        await communicate.save(temp_file.name)
        return temp_file.name

def overlay_content_on_video(video_path, script_text, audio_path, output_path):
    # Create a temporary file for the video if it's an UploadedFile
    if hasattr(video_path, 'read'):
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_video:
            temp_video.write(video_path.read())
            video_path = temp_video.name

    video = mp.VideoFileClip(video_path)
    audio = mp.AudioFileClip(audio_path)

    # Loop the video to match audio duration
    looped_video = video.loop(duration=audio.duration)

    # Split the script into words
    script_words = script_text.split()
    word_durations = audio.duration / len(script_words)  # Simple even split, adjust if needed

    # Create a function to generate text images
    def create_text_image(word, video_size):
        font_size = 80
        font = ImageFont.truetype("arial.ttf", font_size)
        text_color = (255, 255, 255)  # White color for text

        # Create a transparent image
        img = Image.new("RGBA", video_size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Calculate text position (centered horizontally, near the middle bottom vertically)
        text_bbox = font.getbbox(word)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        x_position = (video_size[0] - text_width) // 2
        y_position = int(video_size[1] * 0.7)  # Position text near the middle bottom

        # Draw text onto the image
        draw.text((x_position, y_position), word, font=font, fill=text_color)

        return np.array(img)

    # Generate text clips for each word with timing
    clips = [looped_video]

    for i, word in enumerate(script_words):
        word_img = create_text_image(word, looped_video.size)
        text_clip = (mp.ImageClip(word_img, duration=word_durations)
                     .set_start(i * word_durations)
                     .set_position(('center', 'center')))
        clips.append(text_clip)

    # Combine all clips together
    final_video = mp.CompositeVideoClip(clips).set_audio(audio)

    # Write the final video to a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_video:
        try:
            final_video.write_videofile(temp_video.name, codec="libx264", audio_codec="aac")
        except subprocess.CalledProcessError as e:
            st.error(f"Error during video creation: {str(e)}")
        finally:
            # Ensure all resources are properly closed
            final_video.close()
            for clip in clips:
                if hasattr(clip, 'close'):
                    clip.close()
            looped_video.close()
            video.close()
            audio.close()
        
        return temp_video.name

# Define the main function
def main():
    
    st.title("PDF Text Extraction and TikTok Content Generation")
    
    # Step 1: Upload a PDF
    uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")
    if uploaded_file is not None:
        st.write("File uploaded successfully!")  
        
        # Step 2: Extract and Display Content
        with st.spinner('Extracting text...'):
            extracted_text = extract_text_from_pdf(uploaded_file)
            show_content()
            
            st.subheader("Extracted Text Operations")
            
            # Step 3: Generate TikTok Content
            if st.button("Generate TikTok Content"):
                with st.spinner('Generating TikTok content...'):
                    tiktok_script = generate_tiktok_content(extracted_text)
                    st.session_state['audio_content'] = tiktok_script

            # Step 4: Edit and Convert to Audio
            if 'audio_content' in st.session_state:
                st.text_area("Edit the generated TikTok content below:", st.session_state['audio_content'], key='audio_content')
                voice_model = st.selectbox(
                    "Choose a Voice Model",
                    [
                        "en-US-AriaNeural", "en-US-GuyNeural", "en-US-JennyNeural",
                        "en-GB-RyanNeural", "en-AU-NatashaNeural", "en-IN-NeerjaNeural"
                    ],
                    key='voice_model'
                )
                if st.button("Convert to Audio"):
                    with st.spinner('Converting text to audio...'):
                        audio_file = asyncio.run(convert_text_to_speech(st.session_state['audio_content'], st.session_state['voice_model']))
                        
                        with open(audio_file, "rb") as f:
                            audio_bytes = f.read()
                            st.download_button(label="Download TikTok Audio", data=audio_bytes, file_name="tiktok_audio.mp3", mime="audio/mpeg")
                            st.audio(audio_bytes, format="audio/mp3")
                        
                        # Store the audio file path in session state
                        st.session_state['audio_file_path'] = audio_file

            # Step 5: Select or Upload a Video
            st.subheader("Select or Upload a Video")
            
            # Get list of video files in the /videos directory
            video_files = [f for f in os.listdir('./videos') if f.endswith(('.mp4', '.mov', '.avi'))]
            
            video_source = st.radio("Choose video source:", ["Internal Storage", "Upload"])
            
            if video_source == "Internal Storage":
                if video_files:
                    selected_video = st.selectbox("Select a video:", video_files)
                    video_path = os.path.join('./videos', selected_video)
                else:
                    st.warning("No video files found in the /videos directory.")
                    video_path = None
            else:
                uploaded_video = st.file_uploader("Upload a video", type=["mp4", "mov", "avi"])
                if uploaded_video:
                    # Save the uploaded video to a temporary file
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_video:
                        temp_video.write(uploaded_video.read())
                        video_path = temp_video.name
                else:
                    video_path = None
            
            if video_path and 'audio_content' in st.session_state and 'audio_file_path' in st.session_state:
                if isinstance(video_path, str):
                    st.video(video_path)
                else:
                    st.video(video_path.read())

                # Step 6: Generate Final Video with Overlays
                if st.button("Generate Final TikTok Video"):
                    output_video_path = "final_tiktok_video.mp4"
                    with st.spinner('Generating final video...'):
                        try:
                            final_video_path = overlay_content_on_video(video_path, st.session_state['audio_content'], st.session_state['audio_file_path'], output_video_path)
                            st.success("Final video created successfully!")
                            with open(final_video_path, "rb") as video_file:
                                video_bytes = video_file.read()
                                st.download_button(label="Download TikTok Video", data=video_bytes, file_name=output_video_path, mime="video/mp4")
                                st.video(video_bytes)
                        except Exception as e:
                            st.error(f"An error occurred during video generation: {str(e)}")

# Run the main function when the script is executed
if __name__ == "__main__":
    main()
