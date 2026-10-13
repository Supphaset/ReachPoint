# mypy: disable - error - code = "no-untyped-def,misc"
import os
import pathlib
from functools import lru_cache

from fastapi import FastAPI, File, Form, HTTPException, Response, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.staticfiles import StaticFiles
import google.auth
from google.api_core.client_options import ClientOptions
from google.api_core.exceptions import GoogleAPIError
from google.auth.exceptions import DefaultCredentialsError, GoogleAuthError
from google.cloud import speech_v2, texttospeech
from google.cloud.speech_v2.types import cloud_speech
from pydantic import BaseModel, Field

from agent.live_voice import router as live_voice_router

# Define the FastAPI app
app = FastAPI()
app.include_router(live_voice_router)

MAX_AUDIO_BYTES = 10 * 1024 * 1024
MAX_TTS_CHARACTERS = 5000
SPEECH_REGION = "us"


class SpeechRequest(BaseModel):
    """Text to synthesize as Thai speech."""

    text: str = Field(min_length=1, max_length=MAX_TTS_CHARACTERS)


@lru_cache(maxsize=1)
def get_speech_client() -> speech_v2.SpeechClient:
    """Create a Google Speech-to-Text client using Application Default Credentials."""
    return speech_v2.SpeechClient(
        client_options=ClientOptions(api_endpoint=f"{SPEECH_REGION}-speech.googleapis.com")
    )


@lru_cache(maxsize=1)
def get_speech_project_id() -> str:
    """Resolve the project for the regional V2 recognizer."""
    if project_id := os.environ.get("GOOGLE_CLOUD_PROJECT"):
        return project_id
    credentials, project_id = google.auth.default()
    project_id = project_id or credentials.quota_project_id
    if not project_id:
        raise DefaultCredentialsError("Set GOOGLE_CLOUD_PROJECT for Speech-to-Text V2.")
    return project_id


@lru_cache(maxsize=1)
def get_tts_client() -> texttospeech.TextToSpeechClient:
    """Create a Google Text-to-Speech client using Application Default Credentials."""
    return texttospeech.TextToSpeechClient()


def recognize_audio(audio: bytes):
    """Create the client and recognize audio outside the event loop."""
    request = cloud_speech.RecognizeRequest(
        recognizer=f"projects/{get_speech_project_id()}/locations/{SPEECH_REGION}/recognizers/_",
        config=cloud_speech.RecognitionConfig(
            auto_decoding_config=cloud_speech.AutoDetectDecodingConfig(),
            language_codes=["th-TH"],
            model="chirp_3",
        ),
        content=audio,
    )
    return get_speech_client().recognize(
        request=request,
        timeout=30,
    )


def synthesize_text(text: str):
    """Create the client and synthesize speech outside the event loop."""
    return get_tts_client().synthesize_speech(
        input=texttospeech.SynthesisInput(text=text),
        voice=texttospeech.VoiceSelectionParams(
            language_code="th-TH",
            name="th-TH-Chirp3-HD-Aoede",
        ),
        audio_config=texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
        ),
        timeout=30,
    )


@app.post("/voice/transcribe")
async def transcribe_voice(
    file: UploadFile = File(...),
    sample_rate_hertz: int = Form(16000, ge=8000, le=48000),
):
    """Transcribe one short Thai WAV, WebM/Opus, or Ogg/Opus recording."""
    content_type = (file.content_type or "").split(";")[0].lower()
    if content_type not in {"audio/webm", "audio/ogg", "audio/wav"}:
        raise HTTPException(status_code=415, detail="Use a WAV, WebM/Opus, or Ogg/Opus recording.")
    audio = await file.read(MAX_AUDIO_BYTES + 1)
    if not audio:
        raise HTTPException(status_code=400, detail="The recording is empty.")
    if len(audio) > MAX_AUDIO_BYTES:
        raise HTTPException(status_code=413, detail="The recording is too large. Please record a shorter message.")
    if content_type == "audio/wav" and len(audio) > sample_rate_hertz * 2 * 59 + 44:
        raise HTTPException(status_code=413, detail="The spoken turn is too long. Please keep each turn under one minute.")

    try:
        result = await run_in_threadpool(recognize_audio, audio)
    except DefaultCredentialsError as error:
        raise HTTPException(status_code=503, detail="ยังไม่ได้ตั้งค่า Google Cloud สำหรับบริการเสียงบนเซิร์ฟเวอร์") from error
    except (GoogleAPIError, GoogleAuthError) as error:
        raise HTTPException(status_code=502, detail="Google speech recognition is unavailable.") from error
    transcript = " ".join(
        alternative.transcript
        for item in result.results
        for alternative in item.alternatives[:1]
    ).strip()
    return {"text": transcript}


@app.post("/voice/synthesize")
async def synthesize_voice(request: SpeechRequest):
    """Synthesize assistant text using a Thai Google Cloud TTS voice."""
    try:
        response = await run_in_threadpool(synthesize_text, request.text)
    except DefaultCredentialsError as error:
        raise HTTPException(status_code=503, detail="ยังไม่ได้ตั้งค่า Google Cloud สำหรับบริการเสียงบนเซิร์ฟเวอร์") from error
    except (GoogleAPIError, GoogleAuthError) as error:
        raise HTTPException(status_code=502, detail="Google text-to-speech is unavailable.") from error
    return Response(content=response.audio_content, media_type="audio/mpeg")


def create_frontend_router(build_dir="../frontend/dist"):
    """Creates a router to serve the React frontend.

    Args:
        build_dir: Path to the React build directory relative to this file.

    Returns:
        A Starlette application serving the frontend.
    """
    build_path = pathlib.Path(__file__).parent.parent.parent / build_dir

    if not build_path.is_dir() or not (build_path / "index.html").is_file():
        print(
            f"WARN: Frontend build directory not found or incomplete at {build_path}. Serving frontend will likely fail."
        )
        # Return a dummy router if build isn't ready
        from starlette.routing import Route

        async def dummy_frontend(request):
            return Response(
                "Frontend not built. Run 'npm run build' in the frontend directory.",
                media_type="text/plain",
                status_code=503,
            )

        return Route("/{path:path}", endpoint=dummy_frontend)

    return StaticFiles(directory=build_path, html=True)


# Mount the frontend under /app to not conflict with the LangGraph API routes
app.mount(
    "/app",
    create_frontend_router(),
    name="frontend",
)
