"""
Refactored Streamlit UI for speech-to-text recording and transcription.

This new version separates recording (client-side) from processing (server-side):
- Recording Page: Record audio locally and upload to API server
- Jobs Page: View ongoing and completed transcription jobs
- Transcript Page: View detailed results of completed transcriptions

The processing is now handled by a Flask API server with async queuing.
"""

import json
import os
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

import streamlit as st

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from requests.exceptions import ConnectionError

from src.audio import AudioCapture, categorize_devices
from src.client import APIClient

# Configuration
OUTPUT_DIR = "src/saved_audio"
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:5001")

# Page configuration
st.set_page_config(page_title="Speech-to-Text App", page_icon="🎙️", layout="wide", initial_sidebar_state="expanded")


def initialize_session_state():
    """Initialize session state variables."""
    if "current_page" not in st.session_state:
        st.session_state.current_page = "Recording"
    if "recording" not in st.session_state:
        st.session_state.recording = False
    if "stop_recording" not in st.session_state:
        st.session_state.stop_recording = False
    if "stop_recording_event" not in st.session_state:
        st.session_state.stop_recording_event = threading.Event()
    if "recording_start_time" not in st.session_state:
        st.session_state.recording_start_time = None
    if "recording_thread" not in st.session_state:
        st.session_state.recording_thread = None
    if "audio_files" not in st.session_state:
        st.session_state.audio_files = []
    if "api_client" not in st.session_state:
        st.session_state.api_client = APIClient(API_BASE_URL)
    if "selected_job_id" not in st.session_state:
        st.session_state.selected_job_id = None
    if "jobs_cache" not in st.session_state:
        st.session_state.jobs_cache = []
    if "jobs_last_refresh" not in st.session_state:
        st.session_state.jobs_last_refresh = None
    # Recording settings
    if "whisper_model" not in st.session_state:
        st.session_state.whisper_model = "base"
    if "enable_diarization" not in st.session_state:
        st.session_state.enable_diarization = True
    if "enable_summarization" not in st.session_state:
        st.session_state.enable_summarization = True


def check_api_connection() -> bool:
    """Check if the API server is accessible."""
    try:
        health = st.session_state.api_client.health_check()
        return health.get("status") == "healthy"
    except ConnectionError:
        return False


def get_default_microphone(devices):
    """Get the default microphone device."""
    categorized = categorize_devices(devices)

    for dev in categorized["input"]:
        if "microphone array" in dev["name"].lower():
            return dev

    if categorized["input"]:
        return categorized["input"][0]

    return None


def get_all_loopback_devices(devices):
    """Get all loopback devices for system audio capture."""
    categorized = categorize_devices(devices)
    return categorized["loopback"]


def recording_page():
    """Main recording interface."""
    st.title("🎙️ Audio Recording")

    # Check API connection
    if not check_api_connection():
        st.error(f"⚠️ Cannot connect to API server at {API_BASE_URL}. Make sure the Flask server is running.")
        st.info(
            "To start the server:\n"
            "```bash\n"
            "./start_server.sh\n"
            "# or: python3 -m src.server.app\n"
            "```\n\n"
            "The server uses Python's built-in Queue system - no external dependencies required!"
        )
        return

    # Audio device setup
    capture = AudioCapture(frames_per_buffer=1024)
    devices = capture.list_devices()

    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("Recording Controls")

        # Device information
        mic_device = get_default_microphone(devices)
        loopback_devices = get_all_loopback_devices(devices)

        if mic_device:
            st.success(f"🎙️ Microphone: {mic_device['name']}")
        else:
            st.error("❌ No microphone detected")
            return

        if loopback_devices:
            st.success(f"🔊 System Audio: {len(loopback_devices)} device(s) detected")
            with st.expander("View system audio devices"):
                for i, dev in enumerate(loopback_devices, 1):
                    st.text(f"{i}. {dev['name']}")
        else:
            st.warning("⚠️ No system audio devices found")

        # Recording controls
        if not st.session_state.recording:
            if st.button("🔴 Start Recording", type="primary", use_container_width=True):
                st.session_state.recording = True
                st.session_state.stop_recording = False
                st.session_state.recording_start_time = time.time()
                st.session_state.audio_files = []

                # Create a new stop event for this recording session
                stop_event = threading.Event()
                result_container = {"audio_files": []}

                # Store references in session state
                st.session_state.stop_recording_event = stop_event
                st.session_state.recording_result = result_container

                # Start recording thread
                def record_audio(stop_event_param, result_param):
                    devices_to_record = []
                    if mic_device:
                        devices_to_record.append(mic_device)
                    devices_to_record.extend(loopback_devices)

                    # Use the passed event - no session state access needed
                    try:
                        audio_files = capture.record_multiple_unlimited(
                            devices_to_record, lambda: stop_event_param.is_set()
                        )
                        # Store result in the container (thread-safe)
                        result_param["audio_files"] = audio_files
                    except Exception as e:
                        print(f"Recording error: {e}")
                        result_param["audio_files"] = []

                st.session_state.recording_thread = threading.Thread(
                    target=record_audio, args=(stop_event, result_container)
                )
                st.session_state.recording_thread.start()
                st.rerun()
        else:
            # Show recording status
            if st.session_state.recording_start_time:
                elapsed = time.time() - st.session_state.recording_start_time
                st.metric("Recording Time", f"{int(elapsed)}s")

            if st.button("⏹️ Stop Recording", type="secondary", use_container_width=True):
                st.session_state.stop_recording = True
                st.session_state.recording = False

                # Signal the recording thread to stop using the event
                if hasattr(st.session_state, "stop_recording_event"):
                    st.session_state.stop_recording_event.set()

                if st.session_state.recording_thread:
                    st.session_state.recording_thread.join(timeout=5.0)

                    # Transfer results from container to session state
                    if hasattr(st.session_state, "recording_result"):
                        result = st.session_state.recording_result
                        files = result.get("audio_files", [])
                        st.session_state.audio_files = files

                st.rerun()

        # Show recording status
        if st.session_state.recording:
            st.info("🔴 Recording in progress... Click 'Stop Recording' when finished.")
        elif st.session_state.audio_files and not st.session_state.recording:
            st.success("✅ Recording completed! You can now upload for processing.")

    with col2:
        st.subheader("Processing Settings")

        # Processing options
        st.session_state.whisper_model = st.selectbox(
            "Whisper Model",
            options=["tiny", "base", "small", "medium", "large"],
            index=["tiny", "base", "small", "medium", "large"].index(st.session_state.whisper_model),
            help="Larger models are more accurate but slower",
        )

        st.session_state.enable_diarization = st.checkbox(
            "Speaker Diarization",
            value=st.session_state.enable_diarization,
            help="Identify different speakers (requires HuggingFace token)",
        )

        st.session_state.enable_summarization = st.checkbox(
            "Generate Summary",
            value=st.session_state.enable_summarization,
            help="Create meeting summary (requires OpenAI API key)",
        )

    # Upload section
    if st.session_state.audio_files and not st.session_state.recording:
        st.markdown("---")
        st.subheader("Upload for Processing")

        # Show recorded files info
        valid_files = [f for f in st.session_state.audio_files if os.path.exists(f)]
        total_size = sum(os.path.getsize(f) for f in valid_files)
        total_size_mb = total_size / (1024 * 1024)

        st.info(f"📊 Recorded {len(valid_files)} audio file(s) - Total size: {total_size_mb:.1f} MB")

        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("� Show Saved Files", use_container_width=True):
                st.success(f"✅ {len(valid_files)} audio file(s) already saved")
                for file in valid_files:
                    st.text(f"📁 {os.path.basename(file)}")
                    st.caption(f"Full path: {file}")

        with col2:
            if st.button("🚀 Upload & Process", type="primary", use_container_width=True):
                try:
                    with st.spinner("Uploading audio file..."):
                        if not valid_files:
                            st.error("❌ No audio files to upload")
                            return

                        # Use the first file for processing (usually microphone)
                        main_audio_file = valid_files[0]

                        # Prepare processing options
                        options = {
                            "whisper_model": st.session_state.whisper_model,
                            "enable_diarization": st.session_state.enable_diarization,
                            "enable_summarization": st.session_state.enable_summarization,
                        }

                        # Upload to server
                        result = st.session_state.api_client.upload_audio_file(main_audio_file, options)

                        job_id = result["job_id"]
                        st.success(f"✅ Uploaded! Job ID: {job_id}")
                        st.info("📋 Check the 'Jobs' page to monitor progress.")

                        # Clear the recording
                        st.session_state.audio_files = []

                        # Switch to jobs page
                        time.sleep(2)
                        st.session_state.current_page = "Jobs"
                        st.rerun()

                except Exception as e:
                    st.error(f"❌ Upload failed: {e}")

        with col3:
            if st.button("🗑️ Clear Recording", use_container_width=True):
                st.session_state.audio_files = []
                st.rerun()


def jobs_page():
    """Jobs listing and monitoring interface."""
    st.title("📋 Transcription Jobs")

    # Check API connection
    if not check_api_connection():
        st.error(f"⚠️ Cannot connect to API server at {API_BASE_URL}")
        return

    # Refresh controls
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("🔄 Refresh", use_container_width=True):
            st.session_state.jobs_cache = []
            st.session_state.jobs_last_refresh = None
            st.rerun()

    with col2:
        auto_refresh = st.checkbox("Auto Refresh", value=False)

    with col3:
        status_filter = st.selectbox("Filter by Status", options=["All", "queued", "processing", "completed", "failed"])
        if status_filter == "All":
            status_filter = None

    # Fetch jobs (with caching)
    should_refresh = (
        not st.session_state.jobs_cache
        or not st.session_state.jobs_last_refresh
        or (datetime.now() - st.session_state.jobs_last_refresh).seconds > 30
    )

    if should_refresh or auto_refresh:
        try:
            with st.spinner("Loading jobs..."):
                jobs_data = st.session_state.api_client.list_jobs(status_filter=status_filter, limit=50)
                st.session_state.jobs_cache = jobs_data["jobs"]
                st.session_state.jobs_last_refresh = datetime.now()
        except Exception as e:
            st.error(f"❌ Failed to load jobs: {e}")
            return

    jobs = st.session_state.jobs_cache

    if not jobs:
        st.info("📭 No jobs found. Start by recording and uploading audio on the Recording page.")
        return

    # Jobs summary
    status_counts = {}
    for job in jobs:
        status = job.get("status", "unknown")
        status_counts[status] = status_counts.get(status, 0) + 1

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Jobs", len(jobs))
    with col2:
        st.metric("Completed", status_counts.get("completed", 0))
    with col3:
        st.metric("Processing", status_counts.get("processing", 0))
    with col4:
        st.metric("Queued", status_counts.get("queued", 0))

    # Jobs table
    st.subheader("Jobs List")

    for job in jobs:
        status = job.get("status", "unknown")

        # Status emoji
        status_emoji = {"queued": "⏳", "processing": "⚙️", "completed": "✅", "failed": "❌"}.get(status, "❓")

        # Create expandable job card
        with st.expander(
            f"{status_emoji} {job.get('original_filename', 'Unknown')} - {status.upper()}", expanded=False
        ):
            col1, col2 = st.columns(2)

            with col1:
                st.text(f"Job ID: {job.get('id', 'Unknown')}")
                st.text(f"Created: {job.get('created_at', 'Unknown')}")
                st.text(f"Status: {status}")

                if "file_size" in job:
                    file_size_mb = int(job["file_size"]) / (1024 * 1024)
                    st.text(f"File Size: {file_size_mb:.1f} MB")

                if status == "failed" and "error" in job:
                    st.error(f"Error: {job['error']}")

            with col2:
                button_col1, button_col2, button_col3 = st.columns(3)

                with button_col1:
                    if status == "completed":
                        if st.button("👁️ View", key=f"view_{job['id']}"):
                            st.session_state.selected_job_id = job["id"]
                            st.session_state.current_page = "Transcript"
                            st.rerun()

                with button_col2:
                    if status == "completed":
                        try:
                            # Get the result data for download
                            result_data = st.session_state.api_client.get_job_result(job["id"])
                            json_data = json.dumps(result_data, ensure_ascii=False, indent=2)

                            # Determine filename
                            original_filename = result_data.get("metadata", {}).get("original_filename", "transcript")
                            download_filename = f"{original_filename}_transcript.json"

                            st.download_button(
                                label="⬇️ Download",
                                data=json_data,
                                file_name=download_filename,
                                mime="application/json",
                                key=f"download_{job['id']}",
                            )
                        except Exception as e:
                            st.error(f"❌ Failed to prepare download: {e}")

                with button_col3:
                    if st.button("🗑️ Delete", key=f"delete_{job['id']}"):
                        try:
                            with st.spinner("Deleting..."):
                                st.session_state.api_client.delete_job(job["id"])
                                st.success("✅ Job deleted")
                                # Clear cache to refresh
                                st.session_state.jobs_cache = []
                                st.rerun()
                        except Exception as e:
                            st.error(f"❌ Delete failed: {e}")

    # Auto-refresh
    if auto_refresh:
        time.sleep(5)
        st.rerun()


def transcript_page():
    """Detailed transcript view."""
    st.title("📄 Transcript Details")

    if not st.session_state.selected_job_id:
        st.info("📭 No transcript selected. Go to the Jobs page and click 'View' on a completed job.")
        return

    # Check API connection
    if not check_api_connection():
        st.error(f"⚠️ Cannot connect to API server at {API_BASE_URL}")
        return

    job_id = st.session_state.selected_job_id

    # Fetch job result
    try:
        with st.spinner("Loading transcript..."):
            result = st.session_state.api_client.get_job_result(job_id)
    except Exception as e:
        st.error(f"❌ Failed to load transcript: {e}")
        return

    # Header with job info
    metadata = result.get("metadata", {})
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Job ID", job_id[:8] + "...")
    with col2:
        st.metric("File", metadata.get("original_filename", "Unknown"))
    with col3:
        if "processing_time" in metadata:
            processing_time = float(metadata["processing_time"])
            st.metric("Processing Time", f"{processing_time:.1f}s")

    # Navigation tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📝 Transcript", "👥 Segments", "📋 Summary", "ℹ️ Details"])

    with tab1:
        st.subheader("Full Transcript")
        transcript_text = result.get("transcript", "")

        if transcript_text:
            st.text_area("Transcript", transcript_text, height=400, label_visibility="collapsed")

            # Copy button
            if st.button("📋 Copy to Clipboard"):
                st.code(transcript_text, language=None)
                st.info("Select and copy the text above")
        else:
            st.info("No transcript available.")

    with tab2:
        st.subheader("Timestamped Segments")
        segments = result.get("segments", [])

        if segments:
            for i, segment in enumerate(segments):
                start = segment.get("start", 0)
                end = segment.get("end", 0)
                text = segment.get("text", "")
                speaker = segment.get("speaker")

                # Format timestamp
                start_time = f"{int(start // 60):02d}:{int(start % 60):02d}"
                end_time = f"{int(end // 60):02d}:{int(end % 60):02d}"

                # Speaker label
                speaker_label = f"[{speaker}]" if speaker else "[Unknown]"

                with st.container():
                    col1, col2 = st.columns([1, 4])
                    with col1:
                        st.text(f"{start_time} - {end_time}")
                        if speaker:
                            st.caption(speaker_label)
                    with col2:
                        st.text(text.strip())

                if i < len(segments) - 1:
                    st.divider()
        else:
            st.info("No segments available.")

    with tab3:
        st.subheader("Meeting Summary")
        summary = result.get("summary")

        if summary:
            st.markdown(summary)

            # Copy button for summary
            if st.button("📋 Copy Summary", key="copy_summary"):
                st.code(summary, language=None)
                st.info("Select and copy the summary above")
        else:
            st.info("No summary available. Make sure summarization was enabled during processing.")

    with tab4:
        st.subheader("Processing Details")

        # Job metadata
        st.json(metadata)

        # Processing metadata
        if "processing_metadata" in result:
            st.subheader("Processing Information")
            st.json(result["processing_metadata"])

    # Action buttons
    st.markdown("---")
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("⬅️ Back to Jobs", use_container_width=True):
            st.session_state.current_page = "Jobs"
            st.rerun()

    with col2:
        try:
            # Prepare download data
            json_data = json.dumps(result, ensure_ascii=False, indent=2)
            original_filename = result.get("metadata", {}).get("original_filename", "transcript")
            download_filename = f"{original_filename}_transcript.json"

            st.download_button(
                label="⬇️ Download JSON",
                data=json_data,
                file_name=download_filename,
                mime="application/json",
                use_container_width=True,
            )
        except Exception as e:
            st.error(f"❌ Failed to prepare download: {e}")

    with col3:
        if st.button("🗑️ Delete Job", use_container_width=True, type="secondary"):
            if st.button("⚠️ Confirm Delete", use_container_width=True):
                try:
                    with st.spinner("Deleting..."):
                        st.session_state.api_client.delete_job(job_id)
                        st.success("✅ Job deleted")
                        st.session_state.selected_job_id = None
                        st.session_state.current_page = "Jobs"
                        st.rerun()
                except Exception as e:
                    st.error(f"❌ Delete failed: {e}")


def main():
    """Main application entry point."""
    initialize_session_state()

    # Sidebar navigation
    with st.sidebar:
        st.title("🎙️ Speech-to-Text")

        # Page selection
        page = st.radio(
            "Navigation",
            options=["Recording", "Jobs", "Transcript"],
            index=["Recording", "Jobs", "Transcript"].index(st.session_state.current_page),
        )

        if page != st.session_state.current_page:
            st.session_state.current_page = page
            st.rerun()

        st.markdown("---")

        # API server status
        st.subheader("Server Status")
        if check_api_connection():
            st.success("🟢 API Server Connected")
        else:
            st.error("🔴 API Server Disconnected")

        st.caption(f"API URL: {API_BASE_URL}")

        # Settings
        st.markdown("---")
        st.subheader("Settings")

        # Allow changing API URL
        new_api_url = st.text_input("API Server URL", value=API_BASE_URL)
        if new_api_url != API_BASE_URL:
            st.session_state.api_client = APIClient(new_api_url)

        st.markdown("---")

    # Main content area
    if st.session_state.current_page == "Recording":
        recording_page()
    elif st.session_state.current_page == "Jobs":
        jobs_page()
    elif st.session_state.current_page == "Transcript":
        transcript_page()


if __name__ == "__main__":
    main()
