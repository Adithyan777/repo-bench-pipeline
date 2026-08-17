"""LLM client: reasoning translation, schema-forced JSON + retry, usage, replay."""

from __future__ import annotations

from pathlib import Path

import pytest

from pipeline.config import Config
from pipeline.llm.client import (
    LLMClient,
    TokenBudgetExceeded,
    _reasoning_extra_body,
)

SMALL_STEP = "p1.pin.import_to_pypi"  # deepseek, reasoning low
BIG_STEP = "p1.docker.repair_agent"  # kimi, thinking on
SCHEMA = {"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]}


def make_completion(content=None, tool_calls=None, reasoning_tokens=0, tokens=10):
    from openai.types.chat import ChatCompletion

    message: dict = {"role": "assistant", "content": content}
    if tool_calls:
        message["tool_calls"] = [
            {"id": f"call_{i}", "type": "function", "function": {"name": n, "arguments": a}}
            for i, (n, a) in enumerate(tool_calls)
        ]
    return ChatCompletion.model_validate(
        {
            "id": "cmpl-test",
            "object": "chat.completion",
            "created": 0,
            "model": "test-model",
            "choices": [{"index": 0, "message": message, "finish_reason": "stop"}],
            "usage": {
                "prompt_tokens": tokens,
                "completion_tokens": tokens,
                "total_tokens": 2 * tokens,
                "completion_tokens_details": {"reasoning_tokens": reasoning_tokens},
            },
        }
    )


# --- reasoning translation per model (the known facts) ---


def test_reasoning_translation_deepseek() -> None:
    body = _reasoning_extra_body("deepseek-ai/DeepSeek-V4-Flash-0731", "low")
    assert body == {"reasoning_effort": "low"}


def test_reasoning_translation_kimi_on_off() -> None:
    on = _reasoning_extra_body("moonshotai/Kimi-K2.6", "high")
    off = _reasoning_extra_body("moonshotai/Kimi-K2.6", "off")
    assert on == {"chat_template_args": {"enable_thinking": True}}
    assert off == {"chat_template_args": {"enable_thinking": False}}


def test_reasoning_translation_glm_clamps_low_to_high() -> None:
    body = _reasoning_extra_body("zai-org/GLM-5.2", "low")
    assert body == {"reasoning_effort": "high"}  # GLM rejects "low"


# --- JSON extraction ---


def _client(tmp_path: Path, mode="live") -> LLMClient:
    return LLMClient(
        stage="unit_test",
        mode=mode,
        transcripts_dir=tmp_path / "transcripts",
        audit_dir=tmp_path / "audit",
    )


def test_extract_json_from_tool_call(tmp_path: Path) -> None:
    c = _client(tmp_path)
    msg = make_completion(tool_calls=[("emit", '{"name": "x"}')]).choices[0].message
    assert c._extract_json(msg, "emit") == {"name": "x"}


def test_extract_json_fenced_fallback(tmp_path: Path) -> None:
    c = _client(tmp_path)
    msg = make_completion(content='here:\n```json\n{"name": "y"}\n```').choices[0].message
    assert c._extract_json(msg, "emit") == {"name": "y"}


def test_extract_json_invalid_returns_none(tmp_path: Path) -> None:
    c = _client(tmp_path)
    msg = make_completion(tool_calls=[("emit", "{not json")]).choices[0].message
    assert c._extract_json(msg, "emit") is None


# --- schema retry loop (endpoint substituted at the _call_api seam) ---


def test_schema_retry_recovers(tmp_path: Path) -> None:
    c = _client(tmp_path)
    seq = iter(
        [
            make_completion(tool_calls=[("emit", "{}")]),  # missing required -> invalid
            make_completion(tool_calls=[("emit", '{"name": "ok"}')]),  # valid
        ]
    )
    calls = {"n": 0}

    def fake(request):
        calls["n"] += 1
        return next(seq)

    c._call_api = fake  # substitute the endpoint only
    result = c.complete_json(SMALL_STEP, [{"role": "user", "content": "go"}], SCHEMA)
    assert result == {"name": "ok"}
    assert calls["n"] == 2


# --- usage accounting incl. reasoning tokens ---


def test_usage_accounting_records_reasoning_tokens(tmp_path: Path) -> None:
    c = _client(tmp_path)
    c._account(BIG_STEP, make_completion(reasoning_tokens=7, tokens=10))
    usage = c.usage_by_stage[BIG_STEP]
    assert usage.reasoning_tokens == 7
    assert usage.total_tokens == 20
    c.write_usage()
    import json

    data = json.loads((tmp_path / "audit" / "llm_usage.json").read_text())
    assert data["_total"]["reasoning_tokens"] == 7


def test_token_budget_cap(tmp_path: Path) -> None:
    cfg = Config()
    cfg.llm.max_tokens_per_repo = 5
    c = LLMClient(config=cfg, stage="unit_test", transcripts_dir=tmp_path / "t")
    with pytest.raises(TokenBudgetExceeded):
        c._account(SMALL_STEP, make_completion(tokens=10))


# --- cassette replay (activates once recorded against the real endpoint) ---


def _has_cassettes(stage: str) -> bool:
    d = Path("tests/cassettes") / stage
    return d.is_dir() and any(d.glob("*.json"))


@pytest.mark.skipif(not _has_cassettes("llm_smoke"), reason="llm_smoke cassettes not recorded yet")
def test_complete_json_replay(tmp_path: Path) -> None:
    from tests import _smoke

    c = LLMClient(stage=_smoke.JSON_STAGE, mode="replay", transcripts_dir=tmp_path / "t")
    result = _smoke.run_smoke_json(c)
    assert result["answer"] == 42
