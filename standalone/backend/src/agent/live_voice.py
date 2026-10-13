"""Bridge browser PCM audio to Gemini Live and the existing intake graph UI."""

import asyncio
import json
import os

import google.auth
from google.auth.transport.requests import Request
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from google import genai
from google.genai import types

router = APIRouter()

LIVE_MODEL = os.getenv("GEMINI_LIVE_MODEL", "gemini-3.8-live")
LIVE_LOCATION = os.getenv("GEMINI_LIVE_LOCATION", "us-central1")

TURN_TOOL = types.FunctionDeclaration(
    name="process_flood_turn",
    description="Send the user's exact spoken Thai words to the flood-intake graph and wait for its authoritative reply.",
    behavior="BLOCKING",
    parameters=types.Schema(
        type="OBJECT",
        properties={"spoken_text": types.Schema(type="STRING", description="The user's words, without paraphrasing")},
        required=["spoken_text"],
    ),
)

LIVE_CONFIG = types.LiveConnectConfig(
    response_modalities=["AUDIO"],
    system_instruction=(
        "You are the Thai-speaking voice interface for a flood assistance intake app. "
        "For every complete user utterance, call process_flood_turn with the user's exact words. "
        "Do not answer from your own knowledge or add facts. Wait for the tool response, "
        "then speak its reply in Thai faithfully, including any warning that no request was sent. "
        "Never claim to contact responders. If the tool fails, say the turn was not recorded and ask to repeat. "
        "Never call the tool more than twice consecutively without speaking."
    ),
    speech_config=types.SpeechConfig(
        voice_config=types.VoiceConfig(
            prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Aoede")
        )
    ),
    input_audio_transcription=types.AudioTranscriptionConfig(
        custom_vocabulary=["น้ำท่วม", "พิกัด", "จังหวัด", "อำเภอ", "1784", "1669"]
    ),
    tools=[types.Tool(function_declarations=[TURN_TOOL])],
)


async def _from_browser(websocket: WebSocket, session, audio_gate: dict[str, bool]) -> None:
    """Forward audio and graph tool results to the active Live session."""
    while True:
        event = await websocket.receive()
        if event["type"] == "websocket.disconnect":
            return
        if audio := event.get("bytes"):
            await session.send_realtime_input(
                audio=types.Blob(data=audio, mime_type="audio/pcm;rate=16000")
            )
            continue
        if not (raw := event.get("text")):
            continue
        data = json.loads(raw)
        if data.get("type") == "tool_result":
            audio_gate["open"] = True
            await session.send_tool_response(
                function_responses=types.FunctionResponse(
                    id=data["id"],
                    name="process_flood_turn",
                    response=data["result"],
                )
            )


async def _to_browser(websocket: WebSocket, session, audio_gate: dict[str, bool]) -> None:
    """Forward Live audio, transcripts, interruptions, and tool calls."""
    while True:
        async for message in session.receive():
            if message.data and audio_gate["open"]:
                await websocket.send_bytes(message.data)
            content = message.server_content
            if content:
                if content.input_transcription and content.input_transcription.text:
                    await websocket.send_json({"type": "transcript", "text": content.input_transcription.text})
                if content.interrupted:
                    audio_gate["open"] = False
                    await websocket.send_json({"type": "interrupted"})
                if content.turn_complete:
                    audio_gate["open"] = False
                    await websocket.send_json({"type": "turn_complete"})
            if message.tool_call:
                for call in message.tool_call.function_calls:
                    if call.name == "process_flood_turn":
                        await websocket.send_json({
                            "type": "tool_call",
                            "id": call.id,
                            "spoken_text": (call.args or {}).get("spoken_text", ""),
                        })
            if message.tool_call_cancellation:
                audio_gate["open"] = False
                await websocket.send_json({
                    "type": "tool_cancelled", "ids": message.tool_call_cancellation.ids
                })


@router.websocket("/voice/live")
async def live_voice(websocket: WebSocket) -> None:
    """Keep Gemini credentials on the server while relaying live audio."""
    await websocket.accept()
    try:
        credentials, detected_project = await asyncio.to_thread(
            google.auth.default, scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )
        if not credentials.valid:
            await asyncio.to_thread(credentials.refresh, Request())
        project = os.getenv("GOOGLE_CLOUD_PROJECT") or detected_project or credentials.quota_project_id
        if not project:
            raise RuntimeError("GOOGLE_CLOUD_PROJECT is required for Gemini Live.")
        client = await asyncio.to_thread(
            genai.Client, enterprise=True, credentials=credentials,
            project=project, location=LIVE_LOCATION,
        )
        async with client.aio.live.connect(model=LIVE_MODEL, config=LIVE_CONFIG) as session:
            await websocket.send_json({"type": "ready"})
            audio_gate = {"open": False}
            browser_task = asyncio.create_task(_from_browser(websocket, session, audio_gate))
            model_task = asyncio.create_task(_to_browser(websocket, session, audio_gate))
            done, pending = await asyncio.wait(
                {browser_task, model_task}, return_when=asyncio.FIRST_COMPLETED
            )
            for task in pending:
                task.cancel()
            await asyncio.gather(*pending, return_exceptions=True)
            for task in done:
                task.result()
    except WebSocketDisconnect:
        pass
    except Exception:
        try:
            await websocket.send_json({"type": "error", "message": "Gemini Live is unavailable. Please restart voice mode."})
            await websocket.close(code=1011)
        except RuntimeError:
            pass
