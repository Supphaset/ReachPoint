"""Short caller intake, shared by chat and voice, without live model calls."""

import unittest
import os
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from api.intake import conversation, live_voice
from api.intake.facts import FloodCase, LOCATION_QUESTION, OPTIONAL_QUESTIONS, next_question, render_summary


ESSENTIALS = {"location": "Synthetic building", "type": "food", "phone_number": "0000000000"}


class ConciseIntakeTests(unittest.IsolatedAsyncioTestCase):
    async def test_stream_starts_before_extraction_and_reports_failure(self):
        from fastapi import HTTPException, Request
        from api import main
        session = conversation.Conversation(id="synthetic-stream-failure")
        request = Request({"type": "http", "headers": [(b"accept", b"text/event-stream")]})
        with patch.object(conversation, "enabled", return_value=True), patch.object(conversation, "get", return_value=session), \
                patch.object(conversation, "turn", new=AsyncMock(side_effect=HTTPException(503, "Please retry"))) as turn:
            response = await main.call_turn(session.id, main.CallTurn(text="Synthetic request", turnId="one"), request)
            stream = response.body_iterator
            self.assertIn("event: status", await anext(stream))
            turn.assert_not_awaited()
            error = await anext(stream)
            self.assertIn("event: error", error)
            self.assertIn("Please retry", error)
            with self.assertRaises(StopAsyncIteration):
                await anext(stream)

    async def test_four_short_prompts_then_summary_for_chat_and_voice(self):
        for channel in ("chat", "voice"):
            with self.subTest(channel=channel):
                session = conversation.Conversation(id="synthetic-short-" + channel)
                cases = [FloodCase(location=ESSENTIALS["location"]),
                         FloodCase(location=ESSENTIALS["location"], type="food"),
                         FloodCase(**ESSENTIALS), FloodCase(**ESSENTIALS)]
                with patch.object(conversation, "save"), patch.object(conversation, "_extract", side_effect=cases), \
                        patch.object(conversation, "_search", new=AsyncMock(return_value={"status": "unavailable", "query": ESSENTIALS["location"]})):
                    self.assertTrue(session.messages[-1]["text"].endswith(LOCATION_QUESTION))
                    for index, words in enumerate(("Synthetic building", "อาหาร", "0000000000")):
                        result = await conversation.turn(session, words, str(index), channel=channel)
                        self.assertFalse(result["canConfirm"])
                        self.assertLess(len(result["messages"][-1]["text"]), 120)
                    self.assertIn(result["messages"][-1]["text"], OPTIONAL_QUESTIONS.values())
                    self.assertTrue(result["canSkipDetails"])
                    # Reconnect while the optional prompt is pending; it must still be asked only once.
                    session = conversation.Conversation.restore(session.record())
                    result = await conversation.turn(session, "ข้าม", "skip", channel=channel)
                    self.assertTrue(result["canConfirm"])
                    self.assertFalse(result["canSkipDetails"])
                    self.assertEqual(result["messages"][-1]["text"], result["summary"])
                    self.assertEqual(session.case.unavailable_fields, ["people_details", "situation_details", "water_level"])
                    self.assertIsNone(session.case.n_children)
                    self.assertEqual(session.channel, channel)
                    duplicate = await conversation.turn(session, "ข้าม", "skip", channel=channel)
                    self.assertEqual(duplicate, result)

    async def test_one_optional_answer_is_enough_and_corrections_do_not_restart_questions(self):
        session = conversation.Conversation(id="synthetic-optional")
        partial = FloodCase(**ESSENTIALS, people_details="Synthetic adult with one child")
        with patch.object(conversation, "save"), patch.object(conversation, "_search", new=AsyncMock(return_value={"status": "unavailable", "query": ESSENTIALS["location"]})), \
                patch.object(conversation, "_extract", side_effect=[FloodCase(**ESSENTIALS), partial, FloodCase(**ESSENTIALS)]):
            await conversation.turn(session, "Synthetic location, food, 0000000000", "first")
            result = await conversation.turn(session, "Synthetic adult with one child", "people")
            self.assertTrue(result["canConfirm"])
            self.assertIsNone(session.case.situation_details)
            self.assertIn("situation_details", session.case.unavailable_fields)
            session = conversation.Conversation.restore(session.record())
            result = await conversation.turn(session, "แก้ไข ไม่ทราบรายละเอียดผู้ประสบภัย", "correction")
            self.assertTrue(result["canConfirm"])
            # Corrections never restart the optional questionnaire, including after a reconnect.
            self.assertIn("people_details", session.case.unavailable_fields)
            self.assertIn("situation_details", session.case.unavailable_fields)

    async def test_complete_five_fields_need_no_followups_or_maps_lookup(self):
        session = conversation.Conversation(id="synthetic-one-turn")
        case = FloodCase(**{**ESSENTIALS, "location": "https://www.google.com/maps?q=0,0"},
                         people_details="Synthetic family", situation_details="Need food upstairs", water_level="Knee height")
        with patch.object(conversation, "save"), patch.object(conversation, "_extract", return_value=case), \
                patch.object(conversation, "_search", new=AsyncMock()) as search:
            result = await conversation.turn(session, "Synthetic complete request", "one", channel="voice")
        self.assertTrue(result["canConfirm"])
        self.assertEqual(result["messages"][-1]["text"], result["summary"])
        self.assertIsNone(case.coordinates)
        search.assert_not_called()

    async def test_urgent_callers_skip_optional_prompts_and_keep_danger(self):
        session = conversation.Conversation(id="synthetic-urgent")
        case = FloodCase(**ESSENTIALS, immediate_danger=True, emergency_detail="Synthetic urgent danger")
        with patch.object(conversation, "save"), patch.object(conversation, "_extract", return_value=case), \
                patch.object(conversation, "_search", new=AsyncMock(return_value={"status": "unavailable"})):
            result = await conversation.turn(session, "Synthetic urgent request", "urgent", channel="voice")
        self.assertTrue(result["canConfirm"])
        self.assertIn("Synthetic urgent danger", result["summary"])
        self.assertIn("1669", result["messages"][-1]["text"])
        for field in ESSENTIALS:
            incomplete = case.model_copy(update={field: None, "unavailable_fields": [field]})
            self.assertIsNotNone(next_question(incomplete))

    async def test_location_candidates_still_require_caller_choice(self):
        session = conversation.Conversation(id="synthetic-candidates")
        case = FloodCase(**ESSENTIALS, people_details="Synthetic family", situation_details="Need food", water_level="Knee height")
        lookup = {"status": "candidates", "query": ESSENTIALS["location"], "candidates": [{"id": "synthetic", "label": "Synthetic place"}]}
        with patch.object(conversation, "save"), patch.object(conversation, "_extract", return_value=case), \
                patch.object(conversation, "_search", new=AsyncMock(return_value=lookup)):
            result = await conversation.turn(session, "Synthetic complete request", "one")
            self.assertFalse(result["canConfirm"])
            result = await conversation.choose_location(session, lookup["query"], "reject", None)
        self.assertTrue(result["canConfirm"])
        self.assertIsNone(session.case.coordinates)

    async def test_voice_opening_question_is_audible_but_unrequested_followups_are_blocked(self):
        class EndOfStream(Exception):
            pass

        def message(data, complete=False):
            return SimpleNamespace(data=data, tool_call=None, tool_call_cancellation=None,
                                   server_content=SimpleNamespace(input_transcription=None, interrupted=False, turn_complete=complete))

        async def receive():
            yield message(b"opening question")
            yield message(None, complete=True)
            yield message(b"unrequested extra question")
            raise EndOfStream

        live = SimpleNamespace(receive=receive)
        websocket = SimpleNamespace(send_bytes=AsyncMock(), send_json=AsyncMock())
        with self.assertRaises(EndOfStream):
            await live_voice._to_browser(websocket, live, conversation.Conversation(id="synthetic-greeting"))
        websocket.send_bytes.assert_awaited_once_with(b"opening question")


class ConciseSummaryTests(unittest.TestCase):
    def test_optional_prompt_explicitly_asks_missing_water_level(self):
        self.assertIn("น้ำสูงถึงไหน", next_question(FloodCase(**ESSENTIALS)))
        self.assertIn("น้ำสูงถึงไหน", next_question(FloodCase(**ESSENTIALS, people_details="Synthetic adult", situation_details="Waiting upstairs")))

    def test_chat_accepts_streaming_without_breaking_json_clients(self):
        from fastapi.testclient import TestClient
        from api import main
        session = conversation.Conversation(id="synthetic-stream")
        snapshot = session.snapshot()
        snapshot["messages"] = [*snapshot["messages"], {"role": "assistant", "text": "ตอนนี้น้ำสูงถึงไหนคะ?"}]
        with patch.object(conversation, "enabled", return_value=True), patch.object(conversation, "get", return_value=session), \
                patch.object(conversation, "turn", new=AsyncMock(return_value=snapshot)):
            client = TestClient(main.app)
            body = {"text": "Synthetic request", "turnId": "stream-once"}
            response = client.post('/api/callers/sessions/synthetic-stream/turn', json=body, headers={"Accept": "text/event-stream"})
            self.assertTrue(response.headers["content-type"].startswith("text/event-stream"))
            self.assertIn("event: status", response.text)
            self.assertIn("event: delta", response.text)
            self.assertIn("event: snapshot", response.text)
            response = client.post('/api/callers/sessions/synthetic-stream/turn', json=body)
            self.assertEqual(response.json(), snapshot)

    def test_conversation_switch_preserves_background_ai_setting(self):
        from api import main
        with patch.object(main, "USE_AI", False), patch.object(conversation, "configured", return_value=True), \
                patch.dict(os.environ, {"REACHPOINT_CONVERSATION": "on", "REACHPOINT_VOICE": "on"}):
            self.assertEqual(main.call_config(), {"chat": True, "voice": True})
            self.assertFalse(main.USE_AI)
        with patch.object(main, "USE_AI", True), patch.dict(os.environ, {"REACHPOINT_CONVERSATION": "off"}):
            self.assertEqual(main.call_config(), {"chat": False, "voice": False})

    def test_summary_omits_unknown_extra_fields_and_keeps_volunteered_information(self):
        case = FloodCase(**ESSENTIALS, n_children=0, water_level="Knee height", emergency_detail="Synthetic danger")
        summary = render_summary(case)
        self.assertIn("เด็ก: 0 คน", summary)
        self.assertIn("Knee height", summary)
        self.assertIn("Synthetic danger", summary)
        self.assertNotIn("ผู้สูงอายุ:", summary)
        self.assertNotIn("พิกัด:", summary)
        self.assertIn("ยืนยันส่งคำขอ", summary)
        self.assertIn("ยังไม่มีทีมยืนยัน", summary)


if __name__ == "__main__":
    unittest.main()
