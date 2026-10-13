"""Gemini Live voice transport for an existing ReachPoint call session.

Runs on Vertex AI (`gemini-3.8-live`, GA in us-central1; it is not offered in Singapore or global) with the
service's own identity, or with the Gemini API key on the key route (api/ai/gemini.py). The model speaks the
caller's language, Thai or English, and may switch when they do. Confirmation needs the caller to say the exact
phrase, checked on the server: "ยืนยันส่งคำขอ" or "confirm and send".
"""

from __future__ import annotations

import asyncio
import os
from uuid import uuid4

import re

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from google import genai
from google.genai import types

from api.ai import gemini
from api.intake import conversation

CONFIRM_PHRASES = ("ยืนยันส่งคำขอ", "confirm and send")


def is_confirm(spoken: str) -> bool:
    said = re.sub(r"[^\w\s\u0e00-\u0e7f]", "", spoken or "").strip().casefold()
    return re.sub(r"\s+", " ", said) in CONFIRM_PHRASES

router = APIRouter()
LIVE_MODEL = os.getenv("GEMINI_LIVE_MODEL", "gemini-3.8-live")
LIVE_LOCATION = os.getenv("GEMINI_LIVE_LOCATION", "us-central1")

TURN_TOOL = types.FunctionDeclaration(
    name="process_flood_turn", behavior="BLOCKING",
    description="Record the caller's exact spoken words in the ReachPoint intake session and get the authoritative reply.",
    parameters=types.Schema(type="OBJECT", properties={"spoken_text": types.Schema(type="STRING")}, required=["spoken_text"]),
)
CONFIRM_TOOL = types.FunctionDeclaration(
    name="confirm_flood_request", behavior="BLOCKING",
    description="Only when the caller explicitly says the exact phrase ยืนยันส่งคำขอ (Thai) or 'confirm and send' (English) after hearing the summary, save the request for human coordinator review.",
    parameters=types.Schema(type="OBJECT", properties={"spoken_text": types.Schema(type="STRING")}, required=["spoken_text"]),
)
LIVE_CONFIG = types.LiveConnectConfig(
    response_modalities=["AUDIO"],
    system_instruction=(
        "You are the voice interface for ReachPoint flood intake in Hat Yai. Speak the caller's language: Thai or "
        "English, switching if they switch. For every complete caller utterance, call process_flood_turn with their "
        "exact words. Read its reply faithfully; never add facts. Once the tool reply contains a review summary, read "
        "it aloud and tell the caller to say exactly ยืนยันส่งคำขอ (or, in English, 'confirm and send') if correct, or "
        "speak corrections. Only for that exact spoken phrase, call confirm_flood_request "
        "instead of process_flood_turn. Wait for each tool response. Never claim a team is assigned or arriving. "
        "If a tool fails, say the turn was not recorded and ask them to repeat."
    ),
    speech_config=types.SpeechConfig(voice_config=types.VoiceConfig(
        prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Aoede"))),
    input_audio_transcription=types.AudioTranscriptionConfig(
        custom_vocabulary=["น้ำท่วม", "พิกัด", "จังหวัด", "อำเภอ", "หาดใหญ่", "ยืนยันส่งคำขอ", "confirm and send", "1669", "1784"]),
    tools=[types.Tool(function_declarations=[TURN_TOOL, CONFIRM_TOOL])],
)


async def _from_browser(websocket: WebSocket, live) -> None:
    while True:
        event = await websocket.receive()
        if event["type"] == "websocket.disconnect":
            return
        if audio := event.get("bytes"):
            await live.send_realtime_input(audio=types.Blob(data=audio, mime_type="audio/pcm;rate=16000"))


async def _to_browser(websocket: WebSocket, live, session: conversation.Conversation) -> None:
    audio_open = False
    while True:
        async for message in live.receive():
            if message.data and audio_open:
                await websocket.send_bytes(message.data)
            content = message.server_content
            if content:
                if content.input_transcription and content.input_transcription.text:
                    await websocket.send_json({"type": "transcript", "text": content.input_transcription.text})
                if content.interrupted:
                    audio_open = False
                    await websocket.send_json({"type": "interrupted"})
                if content.turn_complete:
                    audio_open = False
                    await websocket.send_json({"type": "turn_complete"})
            if message.tool_call:
                audio_open = False
                for call in message.tool_call.function_calls:
                    spoken = str((call.args or {}).get("spoken_text") or "").strip()
                    try:
                        if call.name == "confirm_flood_request":
                            if not is_confirm(spoken):
                                raise HTTPException(409, "กรุณาพูดว่า ยืนยันส่งคำขอ หลังฟังสรุปค่ะ / Please say 'confirm and send' after the summary.")
                            from api.main import submit_call_session
                            snapshot = await submit_call_session(session, f"CALL-{uuid4().hex}")
                            reply = ("บันทึกคำขอแล้วค่ะ ผู้ประสานงานจะตรวจสอบ ยังไม่มีทีมยืนยัน กรุณาเปิดลิงก์สถานะบนหน้าจอค่ะ" if session.lang == "th" else
                                     "Your request is saved. A coordinator will review it; no team is confirmed yet. Open the status link on screen.")
                        elif call.name == "process_flood_turn":
                            snapshot = await conversation.turn(session, spoken, uuid4().hex)
                            reply = snapshot["messages"][-1]["text"]
                        else:
                            raise HTTPException(422, "Unknown voice action")
                        await websocket.send_json({"type": "snapshot", "value": snapshot})
                        result = {"status": "ok", "reply": reply}
                    except HTTPException as exc:
                        result = {"status": "error", "reply": str(exc.detail)}
                    await live.send_tool_response(function_responses=types.FunctionResponse(
                        id=call.id, name=call.name, response=result))
                    audio_open = True
            if message.tool_call_cancellation:
                audio_open = False
                await websocket.send_json({"type": "interrupted"})


def _live_client() -> genai.Client:
    if gemini.use_vertex():
        credentials, project = gemini._credentials()
        if not project:
            raise RuntimeError("GOOGLE_CLOUD_PROJECT is required for Gemini Live.")
        return genai.Client(vertexai=True, credentials=credentials, project=project, location=LIVE_LOCATION)
    return genai.Client(api_key=gemini.api_key())


@router.websocket("/api/call/sessions/{session_id}/live")
async def live_voice(websocket: WebSocket, session_id: str) -> None:
    await websocket.accept()
    try:
        if os.environ.get("REACHPOINT_AI", "on") == "off" or os.environ.get("REACHPOINT_VOICE", "off") != "on":
            raise RuntimeError("Voice mode is disabled on this server.")
        session = conversation.get(session_id)
        session.channel = "voice"
        client = await asyncio.to_thread(_live_client)
        async with client.aio.live.connect(model=LIVE_MODEL, config=LIVE_CONFIG) as live:
            await websocket.send_json({"type": "ready"})
            browser_task = asyncio.create_task(_from_browser(websocket, live))
            model_task = asyncio.create_task(_to_browser(websocket, live, session))
            done, pending = await asyncio.wait({browser_task, model_task}, timeout=600,
                                               return_when=asyncio.FIRST_COMPLETED)
            for task in pending:
                task.cancel()
            await asyncio.gather(*pending, return_exceptions=True)
            for task in done:
                task.result()
            if not done:
                await websocket.send_json({"type": "error", "message": "Voice session ended after ten minutes. You can reconnect."})
    except WebSocketDisconnect:
        pass
    except Exception:
        try:
            await websocket.send_json({"type": "error", "message": "Gemini Live is unavailable. Check voice setup and try again."})
            await websocket.close(code=1011)
        except RuntimeError:
            pass
