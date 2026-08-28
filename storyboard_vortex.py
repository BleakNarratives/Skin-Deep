import streamlit as st
import json
import base64
import time
import io
import math
import struct
import wave
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from PIL import Image
from fpdf import FPDF

# Page Configuration
st.set_page_config(
    page_title="VORTEX Storyboard Studio",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Glassmorphic Dark UI Styling (EquiNex Aesthetic)
st.markdown("""
<style>
    /* Dark glassmorphism theme */
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #0f172a 100%);
        color: #f8fafc;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    .glass-card {
        background: rgba(30, 41, 59, 0.7);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
    }

    .shot-header {
        font-size: 1.25rem;
        font-weight: 700;
        color: #38bdf8;
        border-bottom: 1px solid rgba(56, 189, 248, 0.2);
        padding-bottom: 8px;
        margin-bottom: 16px;
    }

    /* Recording light indicator animation */
    @keyframes pulse-red {
        0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.7); }
        70% { transform: scale(1); box-shadow: 0 0 0 10px rgba(239, 68, 68, 0); }
        100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); }
    }

    .recording-indicator {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        background: rgba(239, 68, 68, 0.2);
        border: 1px solid #ef4444;
        color: #fca5a5;
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
    }

    .red-dot {
        width: 10px;
        height: 10px;
        background-color: #ef4444;
        border-radius: 50%;
        animation: pulse-red 1.5s infinite;
    }

    .prompt-box {
        background: rgba(15, 23, 42, 0.8);
        border: 1px solid #6366f1;
        border-radius: 8px;
        padding: 12px;
        font-family: 'Courier New', Courier, monospace;
        color: #a5b4fc;
        word-break: break-all;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Session State
if "storyboard_shots" not in st.session_state:
    st.session_state.storyboard_shots = [
        {
            "shot_number": 1,
            "title": "Lancy Attaches the MyoWare Sensors",
            "camera_angle": "Extreme Close-Up",
            "transition_fx": "Dissolve",
            "character": "Lancy",
            "lighting": "Neon Cyberpunk Blue & Amber Rim Light",
            "description": "Extreme macro close-up on Lancy's forearm skin as small biokinetic sensors light up, sending micro-pulses across the dermal interface.",
            "style_reference_url": "https://images.unsplash.com/photo-1518770660439-4636190af475",
            "audio_data": None,
            "audio_filename": None
        },
        {
            "shot_number": 2,
            "title": "Establishing the Obelisk Penthouse",
            "camera_angle": "Establishing Wide",
            "transition_fx": "Pan/Whip Zoom",
            "character": "Mike",
            "lighting": "Volumetric Fog & Dramatic Sunset",
            "description": "Wide panoramic shot showing the high-tech penthouse lab overlooking the rainy metropolitan skyline at dusk.",
            "style_reference_url": "https://images.unsplash.com/photo-1509198397868-475647b2a1e5",
            "audio_data": None,
            "audio_filename": None
        }
    ]

if "recording_active_shot" not in st.session_state:
    st.session_state.recording_active_shot = None


def generate_mock_audio_bytes(shot_number: int) -> tuple[str, str]:
    """Generates a synthetic voice note WAV binary string (base64) and filename."""
    sample_rate = 44100
    duration = 2.5  # seconds
    num_samples = int(sample_rate * duration)
    buf = io.BytesIO()

    with wave.open(buf, 'wb') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)

        # Audio tone synthesis with frequency sweep
        for i in range(num_samples):
            t = float(i) / sample_rate
            freq = 300 + 150 * math.sin(2 * math.pi * 2 * t)
            value = int(8000 * math.sin(2 * math.pi * freq * t) * (1 - (t / duration) ** 2))
            wav_file.writeframesraw(struct.pack('<h', max(-32768, min(32767, value))))

    b64_str = base64.b64encode(buf.getvalue()).decode('utf-8')
    filename = f"DirectorNote_Shot_{shot_number}_{int(time.time())}.wav"
    return b64_str, filename


def draw_camera_preset_visualizer(camera_angle: str):
    """Draws a 2D wireframe preview representing the camera angle preset on a matplotlib canvas."""
    fig, ax = plt.subplots(figsize=(6, 3.5), facecolor='#0f172a')
    ax.set_facecolor('#0f172a')

    # Outer frame
    frame = patches.Rectangle((0.05, 0.05), 0.9, 0.9, linewidth=1.5, edgecolor='#38bdf8', facecolor='none')
    ax.add_patch(frame)

    if camera_angle == "Extreme Close-Up":
        # Target macro reticle
        ax.plot([0.5, 0.5], [0.1, 0.9], color='#ef4444', linestyle='--', alpha=0.7)
        ax.plot([0.1, 0.9], [0.5, 0.5], color='#ef4444', linestyle='--', alpha=0.7)
        circle1 = patches.Circle((0.5, 0.5), 0.25, edgecolor='#ef4444', facecolor='none', linewidth=2)
        circle2 = patches.Circle((0.5, 0.5), 0.1, edgecolor='#f87171', facecolor='none', linewidth=1)
        ax.add_patch(circle1)
        ax.add_patch(circle2)
        ax.text(0.5, 0.82, "MACRO FOCUS - EXTREME CLOSE-UP", color='#f87171', fontsize=9, ha='center', weight='bold')

    elif camera_angle == "Low-Angle Tracker":
        # Perspective upward lines
        ax.plot([0.1, 0.5], [0.1, 0.85], color='#38bdf8', linewidth=2)
        ax.plot([0.9, 0.5], [0.1, 0.85], color='#38bdf8', linewidth=2)
        ax.plot([0.2, 0.8], [0.3, 0.3], color='#818cf8', linestyle=':')
        ax.plot([0.3, 0.7], [0.55, 0.55], color='#818cf8', linestyle=':')
        # Upward arrow
        ax.annotate('', xy=(0.5, 0.85), xytext=(0.5, 0.2),
                    arrowprops=dict(arrowstyle="->", color="#38bdf8", lw=3))
        ax.text(0.5, 0.92, "LOW-ANGLE TRACKER (TILT UP)", color='#38bdf8', fontsize=9, ha='center', weight='bold')

    elif camera_angle == "Establishing Wide":
        # Horizon line and wide perspective
        ax.axhline(0.4, color='#38bdf8', linestyle='-', linewidth=1.5)
        # Horizon grid
        for x in [0.1, 0.3, 0.5, 0.7, 0.9]:
            ax.plot([x, 0.5], [0.1, 0.4], color='#64748b', linestyle='--')
        ax.plot([0.2, 0.8], [0.75, 0.75], color='#a855f7', linewidth=2)
        ax.plot([0.2, 0.2], [0.65, 0.85], color='#a855f7', linewidth=2)
        ax.plot([0.8, 0.8], [0.65, 0.85], color='#a855f7', linewidth=2)
        ax.text(0.5, 0.82, "ESTABLISHING WIDE (PANORAMIC)", color='#a855f7', fontsize=9, ha='center', weight='bold')

    else:  # Rule of Thirds Grid
        # 3x3 Grid
        ax.axvline(0.33, color='#f59e0b', linestyle='--', linewidth=1.5)
        ax.axvline(0.66, color='#f59e0b', linestyle='--', linewidth=1.5)
        ax.axhline(0.33, color='#f59e0b', linestyle='--', linewidth=1.5)
        ax.axhline(0.66, color='#f59e0b', linestyle='--', linewidth=1.5)
        # Focal points
        for x in [0.33, 0.66]:
            for y in [0.33, 0.66]:
                node = patches.Circle((x, y), 0.03, color='#f59e0b')
                ax.add_patch(node)
        ax.text(0.5, 0.92, "RULE OF THIRDS GRID", color='#f59e0b', fontsize=9, ha='center', weight='bold')

    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')
    plt.tight_layout()
    return fig


def generate_midjourney_prompt(shot: dict) -> str:
    """Generates an optimized Midjourney v6 prompt from shot attributes."""
    prompt = f"Cinematic film still, {shot.get('camera_angle', 'Medium Shot')}, " \
             f"character {shot.get('character', 'Subject')}, {shot.get('description', '')}, " \
             f"{shot.get('lighting', 'dramatic lighting')}, shot on 35mm lens, ARRI Alexa Mini, " \
             f"photorealistic, highly detailed 8k --ar 16:9 --v 6.0"
    return prompt


def generate_dalle_prompt(shot: dict) -> str:
    """Generates an optimized DALL-E 3 prompt from shot attributes."""
    prompt = f"A realistic high-budget movie scene. {shot.get('camera_angle', 'Medium Shot')} composition. " \
             f"Featuring character {shot.get('character', 'Subject')}. {shot.get('description', '')}. " \
             f"Lighting style: {shot.get('lighting', 'dramatic cinematic lighting')}. Visual style: photorealistic 8k CGI frame pre-visualization."
    return prompt


# Header Section
st.title("🎬 VORTEX AI-Driven Storyboard & Shot-Planner")
st.markdown("*Director's Camera, Shot Deck & Audio Pre-Visualization Suite*")

# Sidebar Controls
with st.sidebar:
    st.header("⚙️ Timeline Management")

    if st.button("➕ Add New Shot", use_container_width=True):
        new_shot_num = len(st.session_state.storyboard_shots) + 1
        st.session_state.storyboard_shots.append({
            "shot_number": new_shot_num,
            "title": f"New Shot {new_shot_num}",
            "camera_angle": "Rule of Thirds Grid",
            "transition_fx": "Cut to Black",
            "character": "Lancy",
            "lighting": "High Contrast Studio Lighting",
            "description": "Enter scene action description here...",
            "style_reference_url": "",
            "audio_data": None,
            "audio_filename": None
        })
        st.rerun()

    st.markdown("---")
    st.subheader("💾 Export / Import Storyboard")

    # Save JSON
    json_data = json.dumps(st.session_state.storyboard_shots, indent=2)
    st.download_button(
        label="📥 Save Storyboard (.json)",
        data=json_data,
        file_name=f"vortex_storyboard_{int(time.time())}.json",
        mime="application/json",
        use_container_width=True
    )

    # Load JSON
    uploaded_json = st.file_uploader("📤 Load Storyboard (.json)", type=["json"], key="json_loader")
    if uploaded_json is not None:
        try:
            loaded_shots = json.load(uploaded_json)
            if isinstance(loaded_shots, list):
                st.session_state.storyboard_shots = loaded_shots
                st.success("Storyboard loaded successfully!")
                st.rerun()
        except Exception as e:
            st.error(f"Error parsing JSON: {e}")

    st.markdown("---")
    st.markdown("### 📊 Project Summary")
    st.info(f"Total Shots: **{len(st.session_state.storyboard_shots)}**")


# Main Timeline View
st.subheader("🎞️ Shot Timeline & Pre-Visualization Deck")

shots_to_delete = []

for idx, shot in enumerate(st.session_state.storyboard_shots):
    with st.container():
        st.markdown(f'<div class="glass-card">', unsafe_allow_html=True)
        col_edit, col_vis = st.columns([1.2, 1])

        with col_edit:
            st.markdown(f'<div class="shot-header">Shot #{shot["shot_number"]}: {shot["title"]}</div>', unsafe_allow_html=True)

            c1, c2 = st.columns(2)
            with c1:
                shot["title"] = st.text_input("Shot Title", shot["title"], key=f"title_{idx}")
                shot["camera_angle"] = st.selectbox(
                    "Camera Angle Preset",
                    ["Extreme Close-Up", "Low-Angle Tracker", "Establishing Wide", "Rule of Thirds Grid"],
                    index=["Extreme Close-Up", "Low-Angle Tracker", "Establishing Wide", "Rule of Thirds Grid"].index(shot.get("camera_angle", "Rule of Thirds Grid")),
                    key=f"cam_{idx}"
                )
                shot["character"] = st.text_input("Main Character / Subject", shot.get("character", "Lancy"), key=f"char_{idx}")

            with c2:
                shot["transition_fx"] = st.selectbox(
                    "Transition FX",
                    ["Dissolve", "Pan/Whip Zoom", "Cut to Black", "Haptic Static"],
                    index=["Dissolve", "Pan/Whip Zoom", "Cut to Black", "Haptic Static"].index(shot.get("transition_fx", "Cut to Black")),
                    key=f"trans_{idx}"
                )
                shot["lighting"] = st.text_input("Lighting Palette", shot.get("lighting", "Atmospheric Cyberpunk"), key=f"light_{idx}")
                shot["style_reference_url"] = st.text_input("Style Reference URL", shot.get("style_reference_url", ""), key=f"ref_{idx}")

            shot["description"] = st.text_area("Scene Description & Action", shot["description"], height=80, key=f"desc_{idx}")

        with col_vis:
            st.markdown("##### 📐 Camera Wireframe Pre-Vis")
            fig = draw_camera_preset_visualizer(shot["camera_angle"])
            st.pyplot(fig)
            plt.close(fig)

        # Director's Audio Notes Section
        st.markdown("---")
        st.markdown("#### 🎙️ Director's Audio Notes Lane")

        audio_col1, audio_col2 = st.columns([1.5, 1])

        with audio_col1:
            uploaded_audio = st.file_uploader(
                f"Upload Audio Note for Shot #{shot['shot_number']}",
                type=["mp3", "wav"],
                key=f"audio_upload_{idx}"
            )

            if uploaded_audio is not None:
                audio_bytes = uploaded_audio.read()
                shot["audio_data"] = base64.b64encode(audio_bytes).decode("utf-8")
                shot["audio_filename"] = uploaded_audio.name
                st.success(f"Attached audio: {uploaded_audio.name}")

            if shot.get("audio_data"):
                st.markdown(f"**Current Note:** `{shot.get('audio_filename', 'VoiceNote.wav')}`")
                decoded_audio = base64.b64decode(shot["audio_data"])
                st.audio(decoded_audio, format="audio/wav")

                if st.button("🗑️ Remove Audio Note", key=f"rm_audio_{idx}"):
                    shot["audio_data"] = None
                    shot["audio_filename"] = None
                    st.rerun()

        with audio_col2:
            st.markdown("**Simulated Audio Recorder**")

            # Check if this shot is simulating recording
            is_recording = (st.session_state.recording_active_shot == idx)

            if is_recording:
                st.markdown("""
                <div class="recording-indicator">
                    <div class="red-dot"></div>
                    RECORDING IN PROGRESS...
                </div>
                """, unsafe_allow_html=True)

                if st.button("⏹️ Stop Recording & Save Note", key=f"stop_rec_{idx}"):
                    b64_audio, filename = generate_mock_audio_bytes(shot["shot_number"])
                    shot["audio_data"] = b64_audio
                    shot["audio_filename"] = filename
                    st.session_state.recording_active_shot = None
                    st.success("Voice Note recorded and attached!")
                    st.rerun()
            else:
                if st.button("🔴 Start Recording Note", key=f"rec_{idx}"):
                    st.session_state.recording_active_shot = idx
                    st.rerun()

        # Delete Shot Button
        if st.button(f"🗑️ Delete Shot #{shot['shot_number']}", key=f"del_{idx}"):
            shots_to_delete.append(idx)

        st.markdown('</div>', unsafe_allow_html=True)

# Delete pending shots
if shots_to_delete:
    for delete_idx in sorted(shots_to_delete, reverse=True):
        st.session_state.storyboard_shots.pop(delete_idx)
    # Re-index remaining shot numbers
    for i, s in enumerate(st.session_state.storyboard_shots):
        s["shot_number"] = i + 1
    st.rerun()

# Prompt Generator Panel
st.markdown("---")
st.subheader("🎯 Midjourney v6 & DALL-E 3 Prompt Generator Panel")

selected_shot_num = st.selectbox(
    "Select Shot to Compile Prompt For",
    options=[s["shot_number"] for s in st.session_state.storyboard_shots],
    format_func=lambda x: f"Shot #{x}: {st.session_state.storyboard_shots[x-1]['title']}"
)

if selected_shot_num:
    target_shot = st.session_state.storyboard_shots[selected_shot_num - 1]

    col_mj, col_dalle = st.columns(2)

    with col_mj:
        st.markdown("##### 🚀 Midjourney v6.0 Prompt")
        mj_prompt = generate_midjourney_prompt(target_shot)
        st.code(mj_prompt, language="text")

    with col_dalle:
        st.markdown("##### 🎨 DALL-E 3 Prompt")
        dalle_prompt = generate_dalle_prompt(target_shot)
        st.code(dalle_prompt, language="text")
