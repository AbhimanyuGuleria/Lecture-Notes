import streamlit as st
import os
from google import genai
from google.genai import types

# Set page configuration
st.set_page_config(
    page_title="Lecture Voice-to-Notes Generator",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 1rem 0;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .upload-section {
        border: 2px dashed #ccc;
        border-radius: 10px;
        padding: 2rem;
        text-align: center;
        margin: 1rem 0;
    }
    .success-message {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# --- 1. CONCEPT & UI SETUP ---
st.markdown('<div class="main-header"><h1>🎙️ Lecture Voice-to-Notes Generator</h1></div>', unsafe_allow_html=True)
st.write("Transform your lecture audio files into comprehensive study materials with AI-powered transcription and note generation!")

# Sidebar for API key and settings
with st.sidebar:
    st.header("⚙️ Configuration")
    gemini_api_key = st.text_input("Enter your Gemini API Key:", type="password", help="Get your API key from Google AI Studio")
    st.markdown("📚 [Get API key from Google AI Studio](https://aistudio.google.com/app/apikey)")

    # Additional settings
    st.subheader("📝 Generation Settings")
    include_timestamps = st.checkbox("Include timestamps (if available)", value=False)
    quiz_difficulty = st.selectbox("Quiz difficulty level", ["Easy", "Medium", "Hard"], index=1)
    num_questions = st.slider("Number of quiz questions", 3, 10, 5)

# File upload section
st.markdown('<div class="upload-section">', unsafe_allow_html=True)
st.subheader("📁 Upload Audio File")
uploaded_file = st.file_uploader(
    "Choose your lecture audio file",
    type=["mp3", "mp4", "mpeg", "mpga", "m4a", "wav", "webm", "aac"],
    help="Supported formats: MP3, WAV, M4A, AAC, WEBM, and more"
)

if uploaded_file:
    st.success(f"✅ File uploaded: {uploaded_file.name} ({uploaded_file.size/1024/1024:.2f} MB)")
st.markdown('</div>', unsafe_allow_html=True)

# Information section
with st.expander("ℹ️ How it works"):
    st.write("""
    1. **Upload** your lecture audio file (various formats supported)
    2. **Transcribe** using Google's advanced Gemini AI
    3. **Generate** structured study materials including:
       - Complete transcript
       - Summary and key points
       - Interactive quiz questions
       - Study recommendations
    """)

# --- 2. MAIN PROCESSING LOGIC ---
if gemini_api_key and uploaded_file is not None:
    # Initialize Gemini client
    try:
        gemini_client = genai.Client(api_key=gemini_api_key)

        # Create tabs for organized output
        tab1, tab2, tab3, tab4 = st.tabs(["📜 Transcript", "📝 Summary", "🔍 Key Points", "🧠 Quiz"])

        # STEP 1: Transcribe the audio file
        with st.spinner("🔄 Transcribing audio... Please wait, this may take a few minutes depending on file size"):
            try:
                # Read the audio file content
                audio_bytes = uploaded_file.read()

                # Determine MIME type based on file extension
                file_extension = uploaded_file.name.split('.')[-1].lower()
                mime_type_map = {
                    'mp3': 'audio/mp3',
                    'mpeg': 'audio/mpeg',
                    'mpga': 'audio/mpeg',
                    'mp4': 'audio/mp4',
                    'm4a': 'audio/mp4',
                    'wav': 'audio/wav',
                    'webm': 'audio/webm',
                    'aac': 'audio/aac'
                }

                mime_type = mime_type_map.get(file_extension, 'audio/mpeg')

                # Enhanced transcription prompt
                transcription_prompt = """Please transcribe this audio file accurately. 
                Provide the complete transcript with proper punctuation, paragraph breaks, 
                and speaker identification if multiple speakers are present."""

                if include_timestamps:
                    transcription_prompt += " Include timestamps where possible."

                # Use Gemini to transcribe the audio
                transcription_response = gemini_client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=[
                        transcription_prompt,
                        types.Part.from_bytes(
                            data=audio_bytes,
                            mime_type=mime_type
                        )
                    ]
                )

                transcript_text = transcription_response.text.strip()

                # Display transcript in first tab
                with tab1:
                    if transcript_text:
                        st.subheader("📜 Full Transcript")
                        st.text_area("Transcript", transcript_text, height=400)

                        # Download transcript
                        st.download_button(
                            label="📥 Download Transcript",
                            data=transcript_text,
                            file_name=f"transcript_{uploaded_file.name}.txt",
                            mime="text/plain"
                        )
                    else:
                        st.error("No transcript generated. Please try again.")

            except Exception as e:
                st.error(f"❌ Error during transcription: {str(e)}")
                transcript_text = ""

        # STEP 2: Generate study materials if transcription was successful
        if transcript_text:
            with st.spinner("🧠 Generating study materials... Almost done!"):
                try:
                    # Enhanced prompt for better study materials
                    study_prompt = f"""You are an expert educational assistant. Based on the following lecture transcript, 
                    please generate comprehensive study materials:

                    1. **SUMMARY**: Write a concise 3-4 sentence summary of the main topic and key concepts.

                    2. **KEY POINTS**: Create a bullet-point list of the most important concepts, facts, and ideas. 
                       Organize them logically and use clear, educational language.

                    3. **QUIZ**: Create {num_questions} {quiz_difficulty.lower()}-level multiple-choice questions to test understanding. 
                       For each question:
                       - Provide 4 answer options (A, B, C, D)
                       - Clearly indicate the correct answer
                       - Include a brief explanation for why the answer is correct

                    Transcript:
                    ---
                    {transcript_text}

                    Please format your response with clear headers and organize the content for easy reading."""

                    # Generate study materials
                    response = gemini_client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=study_prompt
                    )

                    generated_content = response.text

                    # Parse and display the generated content in appropriate tabs
                    # This is a simple parsing - you might want to make it more sophisticated
                    sections = generated_content.split("**")

                    with tab2:
                        st.subheader("📝 Lecture Summary")
                        # Extract summary section
                        for i, section in enumerate(sections):
                            if "SUMMARY" in section.upper():
                                if i + 1 < len(sections):
                                    summary_text = sections[i + 1].strip()
                                    st.write(summary_text)
                                    break
                        else:
                            # Fallback: show first part of generated content
                            st.write(generated_content[:500] + "..." if len(generated_content) > 500 else generated_content)

                    with tab3:
                        st.subheader("🔍 Key Points")
                        # Extract key points section
                        for i, section in enumerate(sections):
                            if "KEY POINTS" in section.upper():
                                if i + 1 < len(sections):
                                    key_points = sections[i + 1].strip()
                                    st.write(key_points)
                                    break
                        else:
                            st.write("Key points extracted from the lecture content.")

                    with tab4:
                        st.subheader("🧠 Knowledge Quiz")
                        # Extract quiz section
                        for i, section in enumerate(sections):
                            if "QUIZ" in section.upper():
                                if i + 1 < len(sections):
                                    quiz_text = sections[i + 1].strip()
                                    st.write(quiz_text)
                                    break
                        else:
                            st.write("Quiz questions based on the lecture content.")

                    # Download all study materials
                    st.subheader("📚 Download Study Materials")
                    col1, col2 = st.columns(2)

                    with col1:
                        st.download_button(
                            label="📥 Download Complete Notes",
                            data=f"LECTURE NOTES\n\n{generated_content}",
                            file_name=f"study_notes_{uploaded_file.name}.txt",
                            mime="text/plain"
                        )

                    with col2:
                        # Create a formatted study guide
                        study_guide = f"""
# Study Guide: {uploaded_file.name}

## Transcript
{transcript_text}

## Generated Study Materials
{generated_content}

---
Generated by Lecture Voice-to-Notes Generator
"""
                        st.download_button(
                            label="📋 Download Study Guide",
                            data=study_guide,
                            file_name=f"complete_study_guide_{uploaded_file.name}.md",
                            mime="text/markdown"
                        )

                except Exception as e:
                    st.error(f"❌ Error during note generation: {str(e)}")

    except Exception as e:
        st.error(f"❌ Error initializing Gemini client: {str(e)}")
        st.info("Please check your API key and try again.")

else:
    # Welcome message and instructions
    if not gemini_api_key:
        st.warning("🔑 Please enter your Gemini API key in the sidebar to get started.")
    if not uploaded_file:
        st.warning("📁 Please upload an audio file to begin processing.")

    # Show demo information
    st.info("""
    ### 🚀 Get Started:
    1. Get your free API key from [Google AI Studio](https://aistudio.google.com/app/apikey)
    2. Enter the API key in the sidebar
    3. Upload your lecture audio file
    4. Let AI generate your study materials!

    ### ✨ Features:
    - **Multi-format support**: MP3, WAV, M4A, AAC, and more
    - **Smart transcription**: Accurate speech-to-text conversion
    - **Structured notes**: Summary, key points, and quizzes
    - **Customizable**: Adjust quiz difficulty and question count
    - **Export options**: Download transcripts and study guides
    """)

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666;'>
    Built with ❤️ using Streamlit and Google Gemini AI<br>
    Perfect for students, educators, and lifelong learners
    </div>
    """, 
    unsafe_allow_html=True
)
