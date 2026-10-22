from __future__ import annotations

import json
import logging
import unittest
import urllib.error
from typing import Any, Dict, Optional
from unittest.mock import MagicMock, patch

from ml.llm.client import (
    OllamaClient,
    _QUANT_CACHE,
    _WARM_MODELS,
    get_model_quantization,
    get_ollama_version,
)


class TestOllamaClient(unittest.TestCase):
    def setUp(self) -> None:
        _QUANT_CACHE.clear()
        _WARM_MODELS.clear()

    def _create_mock_response(self, data: dict) -> MagicMock:
        resp = MagicMock()
        resp.read.return_value = json.dumps(data).encode("utf-8")
        resp.__enter__.return_value = resp
        resp.__exit__.return_value = None
        return resp

    def _make_mock_urlopen(
        self,
        chat_data: Optional[Dict[str, Any]] = None,
        show_data: Optional[Dict[str, Any]] = None,
    ):
        default_chat = {
            "model": "qwen2.5:7b-instruct",
            "message": {"role": "assistant", "content": "Test completion response"},
            "prompt_eval_count": 123,
            "eval_count": 45,
        }
        default_show = {
            "details": {"quantization_level": "Q4_K_M"},
        }
        active_chat = chat_data if chat_data is not None else default_chat
        active_show = show_data if show_data is not None else default_show

        def fake_urlopen(req: Any, timeout: float = 120.0) -> MagicMock:
            url = req.full_url if hasattr(req, "full_url") else str(req)
            resp = MagicMock()
            resp.__enter__.return_value = resp
            resp.__exit__.return_value = None
            if "/api/show" in url:
                resp.read.return_value = json.dumps(active_show).encode("utf-8")
            elif "/api/chat" in url:
                resp.read.return_value = json.dumps(active_chat).encode("utf-8")
            elif "/api/version" in url:
                resp.read.return_value = json.dumps({"version": "0.40.6"}).encode("utf-8")
            else:
                resp.read.return_value = b"{}"
            return resp

        return fake_urlopen

    @patch("urllib.request.urlopen")
    def test_tokens_and_latency_come_from_response(self, mock_urlopen: MagicMock) -> None:
        mock_urlopen.side_effect = self._make_mock_urlopen(
            chat_data={
                "model": "qwen2.5:7b-instruct",
                "message": {"role": "assistant", "content": "Test completion response"},
                "prompt_eval_count": 123,
                "eval_count": 45,
            }
        )

        client = OllamaClient(url="http://localhost:11434", model="qwen2.5:7b-instruct")
        result = client.complete(system="System test", user="User test")

        self.assertEqual(result.prompt_tokens, 123)
        self.assertEqual(result.completion_tokens, 45)
        self.assertIsInstance(result.latency_ms, float)
        self.assertGreater(result.latency_ms, 0.0)

    @patch("urllib.request.urlopen")
    def test_quantization_read_from_api_show(self, mock_urlopen: MagicMock) -> None:
        mock_urlopen.side_effect = self._make_mock_urlopen(
            show_data={"details": {"quantization_level": "Q4_K_M"}}
        )

        client = OllamaClient()
        result = client.complete(system="System", user="User")
        self.assertEqual(result.quantization, "Q4_K_M")

    @patch("urllib.request.urlopen")
    def test_quantization_missing_yields_none_and_logs_warning(self, mock_urlopen: MagicMock) -> None:
        mock_urlopen.side_effect = self._make_mock_urlopen(
            show_data={"details": {}}
        )

        client = OllamaClient()
        with self.assertLogs(level="WARNING") as log_capture:
            result = client.complete(system="System", user="User")
            self.assertIsNone(result.quantization)

        self.assertTrue(
            any("Quantization level missing" in record.getMessage() for record in log_capture.records)
        )

    @patch("urllib.request.urlopen")
    def test_warm_run_flag(self, mock_urlopen: MagicMock) -> None:
        mock_urlopen.side_effect = self._make_mock_urlopen()

        client = OllamaClient()
        result1 = client.complete(system="System", user="Call 1")
        self.assertFalse(result1.warm_run)

        result2 = client.complete(system="System", user="Call 2")
        self.assertTrue(result2.warm_run)

    @patch("urllib.request.urlopen")
    def test_missing_token_count_raises(self, mock_urlopen: MagicMock) -> None:
        mock_urlopen.side_effect = self._make_mock_urlopen(
            chat_data={
                "model": "qwen2.5:7b-instruct",
                "message": {"role": "assistant", "content": "Incomplete token telemetry"},
                "eval_count": 45,
            }
        )

        client = OllamaClient()
        with self.assertRaises(RuntimeError) as ctx:
            client.complete(system="System", user="User")
        self.assertIn("prompt_eval_count", str(ctx.exception))

    @patch("urllib.request.urlopen")
    def test_empty_text_raises(self, mock_urlopen: MagicMock) -> None:
        mock_urlopen.side_effect = self._make_mock_urlopen(
            chat_data={
                "model": "qwen2.5:7b-instruct",
                "message": {"role": "assistant", "content": ""},
                "prompt_eval_count": 10,
                "eval_count": 0,
            }
        )

        client = OllamaClient()
        with self.assertRaises(RuntimeError) as ctx:
            client.complete(system="System", user="User")
        self.assertIn("Empty or missing content", str(ctx.exception))

    @patch("urllib.request.urlopen")
    def test_unreachable_raises_clear_message(self, mock_urlopen: MagicMock) -> None:
        mock_urlopen.side_effect = urllib.error.URLError(ConnectionRefusedError("Connection refused"))

        client = OllamaClient(url="http://localhost:11434")
        with self.assertRaises(RuntimeError) as ctx:
            client.complete(system="System", user="User")
        self.assertIn("ollama serve", str(ctx.exception))

    @patch("urllib.request.urlopen")
    def test_no_api_key_in_request(self, mock_urlopen: MagicMock) -> None:
        recorded_requests = []

        def recording_urlopen(req: Any, timeout: float = 120.0) -> MagicMock:
            recorded_requests.append(req)
            return self._make_mock_urlopen()(req, timeout)

        mock_urlopen.side_effect = recording_urlopen

        client = OllamaClient()
        client.complete(system="System", user="User")

        for req in recorded_requests:
            if hasattr(req, "data") and req.data:
                body = json.loads(req.data.decode("utf-8"))
                self.assertNotIn("api_key", body)
                self.assertNotIn("apikey", body)
            self.assertNotIn("Authorization", req.headers)
            self.assertNotIn("authorization", req.headers)

    @patch("urllib.request.urlopen")
    def test_cost_is_zero(self, mock_urlopen: MagicMock) -> None:
        mock_urlopen.side_effect = self._make_mock_urlopen()

        client = OllamaClient()
        result = client.complete(system="System", user="User")
        self.assertEqual(result.cost_usd, 0.0)

    @patch("urllib.request.urlopen")
    def test_env_config(self, mock_urlopen: MagicMock) -> None:
        recorded_chat_body = {}

        def record_urlopen(req: Any, timeout: float = 120.0) -> MagicMock:
            url = req.full_url if hasattr(req, "full_url") else str(req)
            if "/api/chat" in url:
                recorded_chat_body.update(json.loads(req.data.decode("utf-8")))
            return self._make_mock_urlopen()(req, timeout)

        mock_urlopen.side_effect = record_urlopen

        with patch.dict("os.environ", {"OLLAMA_MODEL": "custom-test-model:latest"}):
            client = OllamaClient()
            client.complete(system="System", user="User")
            self.assertEqual(recorded_chat_body["model"], "custom-test-model:latest")


if __name__ == "__main__":
    unittest.main()
