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
        "x-ai/grok-4", 
        "anthropic/claude-3.5-sonnet",
        "google/gemini-2.0-flash-exp"
    ], index=0)
    
    model_video = st.selectbox("Video Model", ["x-ai/grok-imagine-video"], index=0)
    
    st.info("💡 Use a strong chat model for better scene prompts.")

if not api_key:
    st.warning("Enter your OpenRouter API Key in the sidebar to continue.")
    st.stop()

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json",
    "HTTP-Referer": "https://your-app.streamlit.app",  # Optional but recommended
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
            with st.spinner("Analyzing story with Grok..."):
                try:
                    payload = {
                        "model": model_chat,
                        "messages": [
                            {
                                "role": "system",
                                "content": "You are an expert erotic video director. Break the given story into 8-12 short, visually rich scenes (8-15 seconds each). For each scene output in clear format: **Scene X:** [title] **Prompt:** [highly detailed cinematic prompt with camera, motion, lighting, sensual details] **References needed:** [what images would help]"
                            },
                            {
                                "role": "user",
                                "content": f"Story:\n{story}"
                            }
                        ]
                    }
                    
                    resp = requests.post("https://openrouter.ai/api/v1/chat/completions", 
                                       json=payload, headers=headers, timeout=60)
                    
                    if resp.status_code == 404:
                        st.error("404 Error: Check your model name or OpenRouter account status.")
                    resp.raise_for_status()
                    
                    result = resp.json()
                    scenes_text = result['choices'][0]['message']['content']
                    
                    st.session_state.scenes = scenes_text
                    st.success("✅ Scenes generated successfully!")
                    st.text_area("Generated Scenes (edit if needed)", scenes_text, height=500)
                    
                except requests.exceptions.HTTPError as e:
                    st.error(f"HTTP Error {resp.status_code}: {resp.text}")
                except Exception as e:
                    st.error(f"Error during analysis: {str(e)}")

with tab2:
    st.header("Character & Scene References")
    uploaded_files = st.file_uploader("Upload reference images (faces, outfits, bodies, settings)", 
                                    accept_multiple_files=True, type=['png', 'jpg', 'jpeg'])
    
    if uploaded_files:
        st.success(f"{len(uploaded_files)} reference images uploaded")
        for file in uploaded_files[:6]:  # Show preview
            st.image(file, width=120, caption=file.name)

    if 'scenes' in st.session_state and st.button("🎥 Generate Video Clips (Demo - First Scene)"):
        with st.spinner("Generating video clip... (this may take 30-90 seconds)"):
            try:
                test_prompt = "Sensual intimate scene in a moving car, beautiful woman in short dress with collar, aroused expression, cinematic lighting."
                
                video_payload = {
                    "model": model_video,
                    "prompt": test_prompt
                }
                
                resp = requests.post("https://openrouter.ai/api/v1/videos", 
                                   json=video_payload, headers=headers)
                resp.raise_for_status()
                job = resp.json()
                
                polling_url = job.get("polling_url")
                if polling_url:
                    for i in range(20):
                        time.sleep(25)
                        poll = requests.get(polling_url, headers=headers)
                        status = poll.json()
                        if status.get("status") == "completed":
                            video_url = status.get("unsigned_urls", [None])[0]
                            if video_url:
                                st.success("✅ Video generated!")
                                st.video(video_url)
                                st.download_button("⬇️ Download Clip", requests.get(video_url).content, 
                                                 f"clip_{datetime.now().strftime('%H%M')}.mp4", "video/mp4")
                            break
                        elif status.get("status") == "failed":
                            st.error("Generation failed")
                            break
                    else:
                        st.warning("Taking longer than expected...")
            except Exception as e:
                st.error(f"Video generation error: {str(e)}")

with tab3:
    st.header("Final Assembly")
    st.info("Download clips from above and use this ffmpeg command locally:")
    st.code("""ffmpeg -f concat -safe 0 -i mylist.txt -c copy final_erotic_video.mp4""", language="bash")
    st.caption("Create mylist.txt with all clip paths.")

st.caption("EroStory Animator • Streamlit + OpenRouter • For personal use only")
