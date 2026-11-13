"""Server-only adapter for Google's Vertex AI v1 generateContent REST endpoint."""
from __future__ import annotations

import json
import os
import re
import threading
import time
from datetime import datetime, timezone

import google.auth
import httpx
import requests
from google.auth.exceptions import GoogleAuthError, RefreshError
from google.auth.transport.requests import Request

from .domain import DRAFT_SCHEMA, EXTRACTION_SCHEMA, ROOT

API_VERSION = "v1"
MODEL_ID = "gemini-3.5-flash"
SCOPES = ["https://www.googleapis.com/auth/cloud-platform"]
EXTRACT_PROMPT = (ROOT / "prompts/extract.txt").read_text(encoding="utf-8")
DRAFT_PROMPT = (ROOT / "prompts/draft.txt").read_text(encoding="utf-8")
SMOKE_SCHEMA = {
    "type": "object", "properties": {"status": {"type": "string", "enum": ["ok"]}},
    "required": ["status"], "additionalProperties": False,
}


def utc_now():
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


class VertexError(Exception):
    """Safe to display. Never put a credential, project ID or upstream body here."""

    def __init__(self, code, message, status_code, stage):
        super().__init__(message)
        self.code, self.message, self.status_code, self.stage = code, message, status_code, stage


def _no_duplicates(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON key")
        result[key] = value
    return result


def _reject_number(_value):
    raise ValueError("Nonstandard JSON number")


def _vertex_schema(node):
    """Compile the repo's schema to Vertex's generation subset. Validate the full schema locally."""
    # See GenerationConfig.responseJsonSchema. Unsupported contract keywords such
    # as conditional evidence bounds still apply in the server-side validator.
    result = {k: node[k] for k in ("type", "enum", "minimum", "maximum", "required", "$ref",
              "additionalProperties", "minItems", "maxItems") if k in node}
    if "const" in node and isinstance(node["const"], str):
        result["enum"] = [node["const"]]
    if isinstance(result.get("type"), list):
        result["anyOf"] = [{"type": t} for t in result.pop("type")]
    if "items" in node:
        result["items"] = _vertex_schema(node["items"])
    for key in ("properties", "$defs"):
        if key in node:
            result[key] = {name: _vertex_schema(sub) for name, sub in node[key].items()}
    return result


class _AuthRequest(Request):
    def __call__(self, *args, timeout=10, **kwargs):
        # google-auth may pass its own long discovery/refresh deadline.
        return super().__call__(*args, timeout=min(timeout or 10, 10), **kwargs)


class VertexClient:
    provider = "Google Cloud Vertex AI"

    def __init__(self, http_client=None, credentials=None, project=None, *, model_id=None, location=None):
        self.model_id = model_id or os.getenv("VERTEX_MODEL_ID") or MODEL_ID
        self.location = location or os.getenv("GOOGLE_CLOUD_LOCATION") or "global"
        self._configured_project = project or os.getenv("GOOGLE_CLOUD_PROJECT")
        self._project = self._configured_project
        self._uses_adc = credentials is None
        self._credentials = credentials
        self._auth = _AuthRequest()
        self._http = http_client if http_client is not None else httpx.Client()
        self._token_lock, self._smoke_lock = threading.Lock(), threading.Lock()
        self._preflight = None

    def close(self):
        self._http.close()
        self._auth.session.close()

    def _authorized_request(self):
        with self._token_lock:
            if not re.fullmatch(r"gemini-[a-z0-9][a-z0-9.-]{0,75}", self.model_id) or not re.fullmatch(
                r"(?:global|[a-z]{2,20}(?:-[a-z0-9]{1,20}){0,2})", self.location
            ):
                raise VertexError("vertex_configuration_invalid", "Check the backend model and location.", 503, "configuration")
            try:
                if self._credentials is None:
                    self._credentials, discovered = google.auth.default(scopes=SCOPES, request=self._auth)
                    self._project = self._project or discovered
                if not re.fullmatch(r"[A-Za-z0-9][a-zA-Z0-9-]{0,62}", self._project or ""):
                    raise VertexError("vertex_not_configured", "Set the backend Google Cloud project and retry.", 503, "configuration")
                host = "aiplatform.googleapis.com" if self.location == "global" else f"{self.location}-aiplatform.googleapis.com"
                url = (f"https://{host}/{API_VERSION}/projects/{self._project}/locations/{self.location}"
                       f"/publishers/google/models/{self.model_id}:generateContent")
                # before_request reuses the credential's token and refreshes it near
                # expiration, also applying a quota-project header when configured.
                headers = {}
                self._credentials.before_request(self._auth, "POST", url, headers)
                return url, headers
            except RefreshError:
                # A local login replaces the ADC file. Re-discover it on the
                # next explicit retry; keep caller-injected credentials intact.
                if self._uses_adc:
                    self._credentials = None
                    self._project = self._configured_project
                raise VertexError("vertex_reauth_required",
                                  "Refresh server credentials. For local ADC, run gcloud auth application-default login and retry.",
                                  503, "authentication") from None
            except (GoogleAuthError, requests.RequestException, OSError, ValueError):
                raise VertexError("vertex_auth_failed", "Configure server-side Google application default credentials and retry.",
                                  503, "authentication") from None

    def _chat(self, stage, body):
        url, headers = self._authorized_request()
        try:
            response = self._http.post(url, headers=headers, json=body, timeout=httpx.Timeout(75, connect=10), follow_redirects=False)
        except httpx.TimeoutException:
            raise VertexError("vertex_timeout", "Vertex AI timed out. Retry this packet.", 504, stage) from None
        except httpx.HTTPError:
            raise VertexError("vertex_unreachable", "Could not reach Vertex AI. Retry this packet.", 503, stage) from None
        if response.status_code in (401, 403):
            raise VertexError("vertex_access_denied", "Check Vertex AI API access, billing, and the backend principal's permissions.", 503, stage)
        if response.status_code in (408, 504):
            raise VertexError("vertex_timeout", "Vertex AI timed out. Retry this packet.", 504, stage)
        if response.status_code == 429:
            raise VertexError("vertex_rate_limited", "Vertex AI is rate limiting requests. Retry shortly.", 503, stage)
        if response.status_code == 404:
            raise VertexError("vertex_model_unavailable", "Check the Vertex model and serving location configured on the server.", 503, stage)
        if not response.is_success:
            raise VertexError("vertex_service_error", f"Vertex AI returned HTTP {response.status_code}. Check server configuration and retry.", 502, stage)
        try:
            if len(response.content) > 512_000:
                raise ValueError
            data = response.json()
            result = data["candidates"][0]
            if result.get("finishReason") != "STOP":
                raise VertexError("vertex_incomplete", "Vertex AI returned an incomplete completion. Retry this packet.", 502, stage)
            parts = [p for p in result["content"]["parts"] if not p.get("thought")]
            if not parts or any(not isinstance(p.get("text"), str) or "functionCall" in p for p in parts):
                raise ValueError
            model = data.get("modelVersion")
            if not isinstance(model, str) or not re.fullmatch(r"[a-zA-Z0-9_.-]{1,120}", model):
                raise ValueError
            if model != self.model_id and not model.startswith(self.model_id + "-"):
                raise VertexError("vertex_model_mismatch", "Vertex AI returned an unexpected model version.", 502, stage)
            return "".join(p["text"] for p in parts), model
        except (ValueError, KeyError, AttributeError, TypeError, IndexError, RecursionError):
            raise VertexError("vertex_protocol_error", "Vertex AI returned an unreadable response. Retry this packet.", 502, stage) from None

    def _generate(self, stage, prompt, data, schema, validate, max_tokens):
        contents = [{"text": json.dumps(data, ensure_ascii=False, separators=(",", ":"))}]
        if stage == "extract":
            lengths = {}
            for source in data["sources"]:
                lines = [line.split(" | ", 1) for line in source["text"].split("\n")]
                lengths[source["source_id"]] = {identifier: len(body) for identifier, body in lines}
            contents.append({"text": "Line-body lengths in Unicode code points: " + json.dumps(lengths)})
            prompt += ("\nPrefer quoting the whole supporting line body for context. Use char_start 0 "
                       "and its supplied line-body length for char_end when doing so.")
        settings = {"temperature": 0.1, "candidateCount": 1, "maxOutputTokens": max_tokens,
                    "responseMimeType": "application/json", "responseJsonSchema": _vertex_schema(schema)}
        if self.model_id.startswith("gemini-3.5-flash"):
            settings["thinkingConfig"] = {"thinkingLevel": "MINIMAL"}
        body = {"systemInstruction": {"parts": [{"text": prompt}]},
                "contents": [{"role": "user", "parts": contents}], "generationConfig": settings}
        started, stamp = time.monotonic(), utc_now()
        for attempt in (1, 2):
            raw, model_version = self._chat(stage, body)
            try:
                obj = json.loads(raw, object_pairs_hook=_no_duplicates, parse_constant=_reject_number)
                if not isinstance(obj, dict):
                    raise ValueError("Expected an object")
                validate(obj)
            except (ValueError, RecursionError):
                if attempt == 2:
                    raise VertexError("invalid_model_output", "The response failed validation after one repair. Review the sources and retry.",
                                      502, stage) from None
                hint = {
                    "extract": "Recheck ownership, all values, and the exact whole-line quotations and lengths.",
                    "draft": "Include every finding exactly once, preserve competing values and copy reference lists exactly.",
                    "smoke": 'Return exactly {"status":"ok"}.',
                }[stage]
                body["systemInstruction"]["parts"][0]["text"] = prompt + "\nThe prior response failed validation. " + hint
                continue
            return obj, {
                "stage": stage, "mode": "live", "provider": self.provider, "model_id": self.model_id, "model_version": model_version,
                "location": self.location, "region": self.location, "api_version": API_VERSION, "timestamp": stamp,
                "latency_ms": round((time.monotonic() - started) * 1000), "response_format": "json_schema",
                "attempts": attempt, "repair_attempted": attempt > 1,
            }

    def smoke(self):
        with self._smoke_lock:
            if self._preflight is None:
                def validate(obj):
                    if obj != {"status": "ok"}:
                        raise ValueError("Unexpected smoke result")

                _, self._preflight = self._generate("smoke", "Return the requested JSON object only.",
                    {"request": 'Return {"status":"ok"}.'}, SMOKE_SCHEMA, validate, 512)
            return self._preflight.copy()

    def extract(self, packet, validate):
        self.smoke()
        return self._generate("extract", EXTRACT_PROMPT, packet, EXTRACTION_SCHEMA, validate, 8192)

    def draft(self, packet_id, validated_findings, validate):
        self.smoke()
        keys = ("finding_id", "kind", "field", "values", "evidence_refs", "policy_refs")
        data = {"packet_id": packet_id, "validated_findings": [{key: f[key] for key in keys} for f in validated_findings]}
        return self._generate("draft", DRAFT_PROMPT, data, DRAFT_SCHEMA, validate, 4096)
