import streamlit as st
from core.router import ai_orchestrator
from utils.helpers import render_header

# Optional local voice dependencies with graceful fallback
try:
    import pyttsx3
except ImportError:
    pyttsx3 = None

try:
    import speech_recognition as sr
except ImportError:
    sr = None

def speak_text_locally(text: str):
    """Local offline Text-to-Speech using pyttsx3 or silent fallback."""
    if not pyttsx3:
        print("Local TTS Notice: pyttsx3 package not installed.")
        return
    try:
        engine = pyttsx3.init()
        engine.setProperty('rate', 165)
        engine.say(text[:300])  # Read first 300 chars for quick voice response
        engine.runAndWait()
    except Exception as e:
        print(f"Local TTS notice/fallback: {e}")

def render_voice_assistant(user_id: int, tenant_id: str):
    """Render Local Voice Assistant Module."""
    render_header("AI Voice Assistant (Local STT & TTS)")

    st.markdown("### 🎙️ Hands-Free AI Voice Assistant")
    st.info("Uses local speech recognition and text-to-speech. Type your question if local microphone transcription is unavailable.")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 🗣️ Speech Input")
        st.write("Click below to simulate or record voice query:")
        
        voice_query_input = st.text_input(
            "Transcribed Voice Input:",
            value="",
            placeholder="e.g. What are the key skills required for an AI Engineer in 2026?"
        )

        if st.button("🎤 Listen via Microphone (Local STT)", type="secondary"):
            if not sr:
                st.warning("⚠️ `SpeechRecognition` library is not installed. You can type your voice query in the input box above or run `pip install SpeechRecognition pyttsx3`.")
            else:
                try:
                    r = sr.Recognizer()
                    with sr.Microphone() as source:
                        st.info("Listening... Speak into your microphone now.")
                        audio = r.listen(source, timeout=5, phrase_time_limit=10)
                        transcription = r.recognize_sphinx(audio)
                        st.success(f"Recognized: \"{transcription}\"")
                        voice_query_input = transcription
                except Exception as e:
                    st.warning(f"Local microphone transcription is unavailable: {e}. You can type your question above.")

    with col2:
        st.markdown("#### 🔊 Audio Controls & Output Settings")
        enable_tts = st.checkbox("Enable Offline Voice Response (TTS)", value=True)
        speech_rate = st.slider("Speech Rate (Words/Min)", 100, 250, 160)

    if st.button("🚀 Process Voice Query", type="primary"):
        if not voice_query_input.strip():
            st.warning("Please provide a voice question or type text.")
        else:
            with st.spinner("Processing voice request through RAG & Ollama..."):
                response, sources, agent_name = ai_orchestrator.process_request(
                    query=voice_query_input,
                    user_id=user_id,
                    tenant_id=tenant_id
                )

                st.markdown(f"### 🤖 Response ({agent_name})")
                st.markdown(response)

                if enable_tts:
                    st.info("🔊 Playing local Text-to-Speech audio response...")
                    speak_text_locally(response)
