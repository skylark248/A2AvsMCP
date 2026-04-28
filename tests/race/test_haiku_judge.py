"""HaikuJudge determinism + cache_control + missing-key handling (RACE-05, D-42).

All tests mock anthropic.Anthropic — NO real API calls.
"""
from __future__ import annotations

import os
import unittest
from unittest.mock import MagicMock, patch

from a2a_vs_mcp.race.judges.haiku import HAIKU_MODEL, HaikuJudge, JudgeVerdict
from a2a_vs_mcp.trace import TraceRecorder


def _fake_anthropic_response(text: str = "R1: YES\nRATIONALE: ok") -> MagicMock:
    """Build a fake Message-shaped response object."""
    rsp = MagicMock()
    block = MagicMock()
    block.text = text
    rsp.content = [block]
    rsp.usage = MagicMock(input_tokens=100, output_tokens=20)
    return rsp


class TestHaikuJudgeDeterminism(unittest.TestCase):
    """Anthropic call kwargs locked: temperature=0, model=claude-haiku-4-5,
    cache_control=ephemeral on system prompt."""

    def test_temperature_zero_passed_to_create(self) -> None:
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-fake-test-key"}):
            with patch("a2a_vs_mcp.race.judges.haiku.anthropic.Anthropic") as mock_cls:
                client = mock_cls.return_value
                client.messages.create.return_value = _fake_anthropic_response()
                judge = HaikuJudge()
                judge.judge(rubric_system_prompt="r", artifact_user_prompt="a")
                kwargs = client.messages.create.call_args.kwargs
        self.assertEqual(kwargs["temperature"], 0.0)

    def test_haiku_model_id_pinned(self) -> None:
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-fake"}):
            with patch("a2a_vs_mcp.race.judges.haiku.anthropic.Anthropic") as mock_cls:
                client = mock_cls.return_value
                client.messages.create.return_value = _fake_anthropic_response()
                judge = HaikuJudge()
                judge.judge(rubric_system_prompt="r", artifact_user_prompt="a")
                kwargs = client.messages.create.call_args.kwargs
        self.assertEqual(kwargs["model"], "claude-haiku-4-5")
        self.assertEqual(HAIKU_MODEL, "claude-haiku-4-5")

    def test_cache_control_ephemeral_on_system_prompt(self) -> None:
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-fake"}):
            with patch("a2a_vs_mcp.race.judges.haiku.anthropic.Anthropic") as mock_cls:
                client = mock_cls.return_value
                client.messages.create.return_value = _fake_anthropic_response()
                judge = HaikuJudge()
                judge.judge(rubric_system_prompt="rubric", artifact_user_prompt="a")
                kwargs = client.messages.create.call_args.kwargs
        system = kwargs["system"]
        self.assertEqual(system[0]["cache_control"], {"type": "ephemeral"})


class TestHaikuJudgeKeyHandling(unittest.TestCase):
    """ANTHROPIC_API_KEY missing -> RuntimeError; key value never leaked."""

    def test_missing_api_key_raises_runtime_error(self) -> None:
        # Strip the key from env, then instantiate.
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(RuntimeError) as cm:
                HaikuJudge()
        # Message must NOT echo the (absent) key value, and must mention the var name.
        self.assertIn("ANTHROPIC_API_KEY", str(cm.exception))

    def test_api_key_value_never_appears_in_exception(self) -> None:
        """If the key is present but malformed downstream, the key value must
        not surface in any user-visible exception arg."""
        sentinel = "sk-test-sentinel-1234567890abcdef"
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": sentinel}):
            with patch("a2a_vs_mcp.race.judges.haiku.anthropic.Anthropic") as mock_cls:
                client = mock_cls.return_value
                client.messages.create.side_effect = RuntimeError("upstream error")
                judge = HaikuJudge()
                with self.assertRaises(RuntimeError) as cm:
                    judge.judge(rubric_system_prompt="r", artifact_user_prompt="a")
        self.assertNotIn(sentinel, str(cm.exception))


class TestHaikuJudgeRecorderEvent(unittest.TestCase):
    """judge() records an llm_call event with role='judge' on the recorder."""

    def test_judge_emits_llm_call_event(self) -> None:
        rec = TraceRecorder(mode="pure_mcp", runtime="mock", task_id="summarize_repo")
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-fake"}):
            with patch("a2a_vs_mcp.race.judges.haiku.anthropic.Anthropic") as mock_cls:
                client = mock_cls.return_value
                client.messages.create.return_value = _fake_anthropic_response()
                judge = HaikuJudge(recorder=rec)
                v = judge.judge(rubric_system_prompt="r", artifact_user_prompt="a")
        self.assertIsInstance(v, JudgeVerdict)
        llm_calls = [e for e in rec.events if e.get("event_type") == "llm_call" and e.get("role") == "judge"]
        self.assertEqual(len(llm_calls), 1)
        self.assertEqual(llm_calls[0]["model"], "claude-haiku-4-5")
        self.assertEqual(llm_calls[0]["tokens_in"], 100)
        self.assertEqual(llm_calls[0]["tokens_out"], 20)


if __name__ == "__main__":
    unittest.main()
