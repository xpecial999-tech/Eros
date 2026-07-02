import streamlit as st
import requests
import time
import os
from datetime import datetime
import base64

st.set_page_config(page_title="EroStory Animator", page_icon="🌹", layout="wide")
st.title("🌹 EroStory Animator")
st.markdown("**Turn your erotic stories into animated videos** using Grok Imagine Video via OpenRouter. Private & local-first feel.")

# Sidebar for API key
with st.sidebar:
    st.header("Settings")
    api_key = st.text_input("OpenRouter API Key", type="password", value=os.getenv("OPENROUTER_API_KEY", ""))
    model_video = st.selectbox("Video Model", ["x-ai/grok-imagine-video"], index=0)
    model_chat = st.selectbox("Chat Model (for scripting)", ["x-ai/grok-4"], index=0)
    st.info("Keep your API key private. Never share it.")

if not api_key:
    st.warning("Please enter your OpenRouter API Key in the sidebar.")
    st.stop()

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

# Main tabs
tab1, tab2, tab3 = st.tabs(["Story Input & Scenes", "References & Generation", "Final Assembly"])

with tab1:
    story = st.text_area("Paste your full erotic story here", height=300, placeholder="Once upon a time in a moonlit chamber...")
    
    if st.button("Analyze Story & Create Scenes", type="primary"):
        if not story:
            st.error("Please enter a story.")
        else:
            with st.spinner("Breaking story into scenes with Grok..."):
                payload = {
                    "model": model_chat,
                    "messages": [{
                        "role": "system",
                        "content": "You are an expert erotic storyteller. Break the story into 6-12 short vivid scenes suitable for 8-15 second video clips. For each scene output: scene_number, prompt (highly detailed cinematic video prompt with motion, camera, lighting, sensual details), characters_involved."
                    }, {
                        "role": "user",
                        "content": f"Story:\n{story}"
                    }]
                }
                try:
                    resp = requests.post("https://openrouter.ai/api/v1/chat/completions", json=payload, headers=headers)
                    resp.raise_for_status()
                    result = resp.json()
                    scenes_text = result['choices'][0]['message']['content']
                    st.session_state.scenes = scenes_text  # Store for later use
                    st.success("Scenes generated!")
                    st.text_area("Generated Scenes (edit as needed)", scenes_text, height=400)
                except Exception as e:
                    st.error(f"Error: {e}")

with tab2:
    st.header("Character References")
    uploaded_files = st.file_uploader("Upload reference images (faces, bodies, outfits, scenes)", accept_multiple_files=True, type=['png', 'jpg', 'jpeg'])
    
    references = []
    if uploaded_files:
        for file in uploaded_files:
            # In real deployment, you'd upload to a temp host or Supabase, but for simplicity we show base64 preview
            encoded = base64.b64encode(file.getvalue()).decode()
            references.append({"name": file.name, "data": encoded})
            st.image(file, width=150, caption=file.name)
    
    st.info("These will be used as references for character consistency in video generation.")

    if 'scenes' in st.session_state and st.button("Generate Video Clips for All Scenes"):
        # This is a placeholder loop - in production you'd parse scenes and call video API
        st.warning("Full multi-clip generation with polling would go here. For demo, we'll simulate one clip.")
        
        test_prompt = "A passionate embrace in a candlelit room, slow sensual movement, cinematic lighting, highly detailed, erotic atmosphere."
        
        with st.spinner("Generating video clip... (this can take 30-90 seconds)"):
            try:
                video_payload = {
                    "model": model_video,
                    "prompt": test_prompt,
                    # "reference_images": [...] would go here if supported
                }
                resp = requests.post("https://openrouter.ai/api/v1/videos", json=video_payload, headers=headers)
                resp.raise_for_status()
                job = resp.json()
                
                job_id = job.get("id")
                polling_url = job.get("polling_url")
                
                if polling_url:
                    for _ in range(30):  # Poll up to ~15 minutes
                        time.sleep(30)
                        poll_resp = requests.get(polling_url, headers=headers)
                        status = poll_resp.json()
                        if status.get("status") == "completed":
                            video_url = status.get("unsigned_urls", [None])[0]
                            if video_url:
                                st.success("Video ready!")
                                st.video(video_url)
                                st.download_button("Download Clip", requests.get(video_url).content, "clip.mp4", "video/mp4")
                            break
                        elif status.get("status") == "failed":
                            st.error("Generation failed")
                            break
            except Exception as e:
                st.error(f"Generation error: {str(e)}")

with tab3:
    st.header("Final Video Assembly")
    st.info("In a full version, clips would be stitched here using ffmpeg.")
    st.markdown("**Local ffmpeg command example** (run on your computer after downloading clips):")
    st.code("ffmpeg -f concat -safe 0 -i clips.txt -c copy final_video.mp4", language="bash")
    
    if st.button("Download All Clips as ZIP (demo)"):
        st.success("In real app this would package everything.")

st.caption("Built with Streamlit + OpenRouter Grok Imagine. For personal use. Respect model terms & local laws.")
