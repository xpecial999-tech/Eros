import streamlit as st
import requests
import time
import os
import base64
from datetime import datetime

st.set_page_config(page_title="EroStory Animator", page_icon="🌹", layout="wide")
st.title("🌹 EroStory Animator")
st.markdown("**Turn erotic stories into animated videos** with Grok Imagine Video via OpenRouter")

# Sidebar
with st.sidebar:
    st.header("Settings")
    api_key = st.text_input("OpenRouter API Key", type="password", value=os.getenv("OPENROUTER_API_KEY", ""))
    
    model_chat = st.selectbox("Chat Model (Scene Breakdown)", [
        "x-ai/grok-4.3",           # Recommended
        "anthropic/claude-3.5-sonnet",
        "google/gemini-2.0-flash-exp"
    ], index=0)
    
    model_video = st.selectbox("Video Model", ["x-ai/grok-imagine-video"], index=0)
    
    st.info("💡 Grok 4.3 is the current recommended model.")

if not api_key:
    st.warning("Enter your OpenRouter API Key in the sidebar.")
    st.stop()

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json",
    "HTTP-Referer": "https://erostory.streamlit.app",
    "X-Title": "EroStory Animator"
}

tab1, tab2, tab3 = st.tabs(["📖 Story & Scenes", "🖼️ References & Generation", "🎬 Assembly"])

with tab1:
    story = st.text_area("Paste your full erotic story here", height=400, 
                        placeholder="Write or paste your story...")

    if st.button("🔍 Analyze Story & Create Scenes", type="primary"):
        if not story.strip():
            st.error("Please enter a story.")
        else:
            with st.spinner("Analyzing with Grok 4.3..."):
                try:
                    payload = {
                        "model": model_chat,
                        "messages": [
                            {
                                "role": "system",
                                "content": "You are an expert erotic video director. Break the story into 8-12 short, visually rich scenes (8-15 seconds each). For each scene output clearly: **Scene X:** [short title] **Prompt:** [detailed cinematic prompt with motion, camera angles, lighting, sensual details] **References:** [suggested image types]"
                            },
                            {
                                "role": "user",
                                "content": f"Story:\n{story}"
                            }
                        ]
                    }
                    
                    resp = requests.post("https://openrouter.ai/api/v1/chat/completions", 
                                       json=payload, headers=headers, timeout=90)
                    resp.raise_for_status()
                    
                    result = resp.json()
                    scenes_text = result['choices'][0]['message']['content']
                    
                    st.session_state.scenes = scenes_text
                    st.success("✅ Scenes created successfully!")
                    st.text_area("Generated Scenes (you can edit them)", scenes_text, height=500)
                    
                except Exception as e:
                    st.error(f"Error: {str(e)}")
                    if "404" in str(e):
                        st.error("Model not found. Try switching chat model in sidebar.")

with tab2:
    st.header("Character References")
    uploaded = st.file_uploader("Upload images (Bunni, outfits, settings, etc.)", 
                              accept_multiple_files=True, type=['png','jpg','jpeg'])
    if uploaded:
        st.success(f"{len(uploaded)} images ready")
        for f in uploaded[:5]:
            st.image(f, width=140, caption=f.name)

    if 'scenes' in st.session_state and st.button("🎥 Generate Sample Video Clip"):
        with st.spinner("Calling Grok Imagine Video..."):
            try:
                sample_prompt = "Beautiful young woman in short dress and collar in a moving luxury car, sensual and submissive expression, cinematic lighting."
                payload = {"model": model_video, "prompt": sample_prompt}
                
                resp = requests.post("https://openrouter.ai/api/v1/videos", json=payload, headers=headers)
                resp.raise_for_status()
                job = resp.json()
                
                polling_url = job.get("polling_url")
                if polling_url:
                    for _ in range(25):
                        time.sleep(25)
                        status_resp = requests.get(polling_url, headers=headers)
                        status = status_resp.json()
                        if status.get("status") == "completed":
                            video_url = status.get("unsigned_urls", [None])[0]
                            if video_url:
                                st.success("Video ready!")
                                st.video(video_url)
                                st.download_button("Download", requests.get(video_url).content, "clip.mp4", "video/mp4")
                            break
            except Exception as e:
                st.error(f"Video error: {str(e)}")

with tab3:
    st.header("Final Assembly")
    st.info("Download your clips and stitch them locally with ffmpeg:")
    st.code("ffmpeg -f concat -safe 0 -i clips.txt -c copy final_video.mp4", language="bash")

st.caption("EroStory Animator • Personal use only")
