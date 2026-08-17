"""OpenAI-compatible LLM client: per-step tier/reasoning (config.STEP_MODEL / MODEL_CAPS),
schema-forced JSON via a forced tool call with client-side validation + retries, backoff,
usage accounting with a per-repo token cap, one transcript per call, cassette record/replay.
Secrets (LLM_BASE_URL / LLM_API_KEY) are never logged or written to disk.
"""

from __future__ import annotations

import json
import os
import re
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import jsonschema

from pipeline.config import DEFAULT, MODEL_CAPS, Config, Tier
from pipeline.llm.cassette import Cassette, request_key

Mode = str  # "live" | "record" | "replay"
_FENCED_JSON = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL)


class LLMError(RuntimeError):
    pass


class TokenBudgetExceeded(LLMError):
    pass


class SchemaValidationError(LLMError):
    pass


@dataclass
class Usage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    reasoning_tokens: int = 0
    total_tokens: int = 0

    def add(self, other: Usage) -> None:
        self.prompt_tokens += other.prompt_tokens
        self.completion_tokens += other.completion_tokens
        self.reasoning_tokens += other.reasoning_tokens
        self.total_tokens += other.total_tokens


def _reasoning_extra_body(model: str, reasoning: str) -> dict[str, Any]:
    """Translate our normalized reasoning enum to the model's own knob."""
    caps = MODEL_CAPS.get(model)
    if not caps:
        return {}
    value = caps["map"][reasoning]
    param = caps["reasoning_param"]
    if param == "enable_thinking":  # Kimi: bool via chat_template_args
        return {"chat_template_args": {"enable_thinking": value}}
    return {param: value}  # DeepSeek / GLM: reasoning_effort string


def _resolve_secrets() -> tuple[str, str]:
    return os.environ.get("LLM_BASE_URL", ""), os.environ.get("LLM_API_KEY", "")


@dataclass
class LLMClient:
    config: Config = field(default_factory=lambda: DEFAULT)
    stage: str = "pipeline"
    mode: Mode = field(default_factory=lambda: os.environ.get("LLM_MODE", "live"))
    cassette_root: Path | None = None
    transcripts_dir: Path | None = None
    audit_dir: Path | None = None
    usage_by_stage: dict[str, Usage] = field(default_factory=dict)
    _client: Any = None

    def __post_init__(self) -> None:
        if self.cassette_root is None:
            self.cassette_root = Path(self.config.llm.cassette_dir)
        if self.transcripts_dir is None:
            self.transcripts_dir = Path("transcripts")

    # --- public API ---

    def chat(
        self,
        step: str,
        messages: list[dict],
        tools: list[dict] | None = None,
        tool_choice: Any = None,
        max_tokens: int | None = None,
    ) -> Any:
        """Single chat completion. Returns the SDK ChatCompletion object."""
        tier: Tier = self.config.step_model[step]
        model = self.config.model_for(step)
        reasoning = self.config.reasoning_for(step)
        if max_tokens is None:
            max_tokens = self.config.llm.max_tokens_for(tier)

        request: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": self.config.llm.temperature,
            "max_tokens": max_tokens,
            "extra_body": _reasoning_extra_body(model, reasoning),
        }
        if tools:
            request["tools"] = tools
        if tool_choice is not None:
            request["tool_choice"] = tool_choice

        completion = self._dispatch(step, request)
        self._account(step, completion)
        self._write_transcript(step, request, completion)
        return completion

    def complete_json(
        self,
        step: str,
        messages: list[dict],
        schema: dict,
        tool_name: str = "emit",
        max_tokens: int | None = None,
    ) -> dict:
        """Schema-forced JSON via a forced tool call; validation errors are fed back and
        retried up to ``llm.max_schema_retries``. Falls back to fenced JSON in text."""
        tools = [
            {
                "type": "function",
                "function": {
                    "name": tool_name,
                    "description": "Emit the result.",
                    "parameters": schema,
                },
            }
        ]
        tool_choice = {"type": "function", "function": {"name": tool_name}}
        convo = list(messages)
        last_error = ""
        for _ in range(self.config.llm.max_schema_retries + 1):
            completion = self.chat(
                step, convo, tools=tools, tool_choice=tool_choice, max_tokens=max_tokens
            )
            message = completion.choices[0].message
            payload = self._extract_json(message, tool_name)
            if payload is None:
                last_error = "no tool call or fenced JSON found in response"
            else:
                try:
                    jsonschema.validate(payload, schema)
                    return payload
                except jsonschema.ValidationError as exc:
                    last_error = f"schema validation failed: {exc.message}"
            convo = convo + [
                {"role": "assistant", "content": message.content or ""},
                {
                    "role": "user",
                    "content": (
                        f"Your previous output was invalid: {last_error}. "
                        f"Return only a valid {tool_name} call."
                    ),
                },
            ]
        raise SchemaValidationError(f"{step}: {last_error}")

    def write_usage(self) -> None:
        """Persist per-stage usage to output/<repo>/audit/llm_usage.json."""
        if self.audit_dir is None:
            return
        self.audit_dir.mkdir(parents=True, exist_ok=True)
        path = self.audit_dir / "llm_usage.json"
        # Steps from other stages' clients are kept; this client's steps replace their own.
        data = json.loads(path.read_text()) if path.is_file() else {}
        data.update({step: vars(usage) for step, usage in self.usage_by_stage.items()})
        total = Usage()
        for step, usage in data.items():
            if step != "_total":
                total.add(Usage(**usage))
        data["_total"] = vars(total)
        path.write_text(json.dumps(data, indent=2, sort_keys=True))

    # --- internals ---

    def _dispatch(self, step: str, request: dict) -> Any:
        from openai.types.chat import ChatCompletion

        cassette = Cassette(self.cassette_root, self.stage)
        key = request_key(request)
        if self.mode == "replay":
            stored = cassette.load(key)
            if stored is None:
                raise LLMError(f"no cassette for {self.stage}/{key} (step={step}); record first")
            return ChatCompletion.model_validate(stored)

        completion = self._call_api(request)
        if self.mode == "record":
            cassette.save(key, self._redact(request), completion.model_dump())
        return completion

    def _call_api(self, request: dict) -> Any:
        client = self._ensure_client()
        delay = self.config.llm.api_backoff_base_s
        last_exc: Exception | None = None
        for attempt in range(self.config.llm.api_max_retries):
            try:
                return client.chat.completions.create(
                    timeout=self.config.llm.request_timeout_s, **request
                )
            except Exception as exc:  # noqa: BLE001 - backoff on any transient API error
                last_exc = exc
                if attempt == self.config.llm.api_max_retries - 1:
                    break
                time.sleep(delay)
                delay *= 2
        raise LLMError(f"API call failed after retries: {last_exc}")

    def _ensure_client(self) -> Any:
        if self._client is None:
            from openai import OpenAI

            base, key = _resolve_secrets()
            if not base or not key:
                raise LLMError("LLM_BASE_URL / LLM_API_KEY not set")
            self._client = OpenAI(base_url=base, api_key=key)
        return self._client

    def _extract_json(self, message: Any, tool_name: str) -> dict | None:
        for call in message.tool_calls or []:
            if call.function.name == tool_name:
                try:
                    return json.loads(call.function.arguments)
                except json.JSONDecodeError:
                    return None
        if self.config.llm.accept_fenced_json_fallback and message.content:
            match = _FENCED_JSON.search(message.content)
            if match:
                try:
                    return json.loads(match.group(1))
                except json.JSONDecodeError:
                    return None
        return None

    def _account(self, step: str, completion: Any) -> None:
        raw = completion.usage
        details = getattr(raw, "completion_tokens_details", None)
        usage = Usage(
            prompt_tokens=raw.prompt_tokens or 0,
            completion_tokens=raw.completion_tokens or 0,
            reasoning_tokens=(getattr(details, "reasoning_tokens", 0) or 0) if details else 0,
            total_tokens=raw.total_tokens or 0,
        )
        self.usage_by_stage.setdefault(step, Usage()).add(usage)
        if self._total_usage().total_tokens > self.config.llm.max_tokens_per_repo:
            raise TokenBudgetExceeded(
                f"exceeded max_tokens_per_repo={self.config.llm.max_tokens_per_repo}"
            )

    def _total_usage(self) -> Usage:
        total = Usage()
        for usage in self.usage_by_stage.values():
            total.add(usage)
        return total

    def _write_transcript(self, step: str, request: dict, completion: Any) -> None:
        if self.transcripts_dir is None:
            return
        out = self.transcripts_dir / "pipeline" / self.stage
        out.mkdir(parents=True, exist_ok=True)
        call_id = uuid.uuid4().hex[:12]
        (out / f"{call_id}.json").write_text(
            json.dumps(
                {
                    "step": step,
                    "request": self._redact(request),
                    "response": completion.model_dump(),
                },
                indent=2,
                default=str,
            )
        )

    @staticmethod
    def _redact(request: dict) -> dict:
        return {k: v for k, v in request.items()}  # request never carries the key
