import pytest
from unittest import mock
from google.genai import errors as genai_errors
from rag_assistant.generation import llm_client
from rag_assistant.generation.llm_client import LLMError, _call_with_fallback


def _api_error(code: int) -> genai_errors.APIError:
    # minimal APIError with just the code and message we check in _call_with_fallback
    err = genai_errors.APIError(code, {"message": f"error {code}"}, None)
    return err


def test_fallback_called_on_429() -> None:
    # primary raises 429 → wrapper retries with FALLBACK_MODEL_NAME
    primary_error = _api_error(429)
    fallback_response = mock.MagicMock()
    calls = []

    def fn(model_name: str):
        calls.append(model_name)
        if model_name == llm_client.MODEL_NAME:
            raise primary_error
        return fallback_response

    result = _call_with_fallback(fn)
    assert result is fallback_response
    assert calls == [llm_client.MODEL_NAME, llm_client.FALLBACK_MODEL_NAME]


def test_fallback_called_on_404() -> None:
    # primary raises 404 (model not found) → same swap as 429
    primary_error = _api_error(404)
    fallback_response = mock.MagicMock()
    calls = []

    def fn(model_name: str):
        calls.append(model_name)
        if model_name == llm_client.MODEL_NAME:
            raise primary_error
        return fallback_response

    result = _call_with_fallback(fn)
    assert result is fallback_response
    assert calls == [llm_client.MODEL_NAME, llm_client.FALLBACK_MODEL_NAME]


def test_non_swap_error_raises_immediately() -> None:
    # 500 is not in (429, 404) — no fallback, raise LLMError straight away
    calls = []

    def fn(model_name: str):
        calls.append(model_name)
        raise _api_error(500)

    with pytest.raises(LLMError, match="Primary model error 500"):
        _call_with_fallback(fn)

    assert calls == [llm_client.MODEL_NAME]  # fallback never tried


def test_fallback_also_fails_raises_llmerror() -> None:
    # primary 429 → fallback also raises → LLMError from fallback
    def fn(model_name: str):
        raise _api_error(429) if model_name == llm_client.MODEL_NAME else _api_error(503)

    with pytest.raises(LLMError, match="Fallback model error 503"):
        _call_with_fallback(fn)


def test_no_fallback_configured_raises_on_429() -> None:
    # FALLBACK_MODEL_NAME patched to None → 429 raises immediately with helpful message
    def fn(model_name: str):
        raise _api_error(429)

    with mock.patch.object(llm_client, "FALLBACK_MODEL_NAME", None):
        with pytest.raises(LLMError, match="no fallback model is configured"):
            _call_with_fallback(fn)
