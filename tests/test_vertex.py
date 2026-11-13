"""Wire and ADC tests run locally. Only the live script measures Vertex AI output."""
from datetime import datetime, timedelta, timezone
import json

from google.auth.credentials import Credentials
from google.auth.exceptions import RefreshError
import httpx
import pytest

from backend import vertex


def completion(text, model=None, finish="STOP"):
    return httpx.Response(200, json={"modelVersion": model or vertex.MODEL_ID, "candidates": [{
        "finishReason": finish, "content": {"parts": [{"thought": True, "text": "internal"}, {"text": text}]},
    }]})


class TestCredentials(Credentials):
    __test__ = False

    def __init__(self):
        super().__init__()
        self.refresh_count = 0
        self.fail = False

    def refresh(self, request):
        self.refresh_count += 1
        assert isinstance(request, vertex._AuthRequest)
        if self.fail:
            raise RefreshError("upstream-private-raw-token")
        self.token = "synthetic-access-token"
        self.expiry = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(hours=1)


class Peer:
    def __init__(self, results, **config):
        self.results = iter(results)
        self.calls = []
        self.creds = TestCredentials()
        self.vertex = vertex.VertexClient(http_client=httpx.Client(transport=httpx.MockTransport(self.send)),
            credentials=self.creds, project=config.pop("project", "synthetic-test"), **config)

    def send(self, req):
        self.calls.append(json.loads(req.content))
        assert req.url.scheme == "https" and req.url.host.endswith("aiplatform.googleapis.com")
        assert req.url.path.endswith("/publishers/google/models/" + self.vertex.model_id + ":generateContent")
        assert req.headers["authorization"] == "Bearer synthetic-access-token"
        result = next(self.results)
        if isinstance(result, Exception):
            raise result
        return result


@pytest.fixture(autouse=True)
def defaults(monkeypatch):
    monkeypatch.setenv("VERTEX_MODEL_ID", vertex.MODEL_ID)
    monkeypatch.setenv("GOOGLE_CLOUD_LOCATION", "global")


def test_adc_cache_and_near_expiry_refresh_plus_prompt_boundaries():
    peer = Peer([completion('{"status":"ok"}'), completion('{"reply":"extraction"}'), completion('{"reply":"draft"}')])
    packet = json.loads((vertex.ROOT / "fixtures/04_injection.json").read_text())
    assert peer.vertex.smoke() == peer.vertex.smoke()
    result, proof = peer.vertex.extract(packet, lambda _: None)
    assert result == {"reply": "extraction"} and peer.creds.refresh_count == 1
    assert proof["model_version"] == vertex.MODEL_ID and proof["response_format"] == "json_schema"
    assert proof["latency_ms"] >= 0 and proof["timestamp"] and proof["api_version"] == "v1"
    assert "synthetic-test" not in json.dumps(proof) and peer.creds.token not in json.dumps(proof)
    peer.creds.expiry = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(seconds=30)
    f = {"finding_id": "revision_conflict", "kind": "conflict", "field": "revision", "evidence_refs": ["RFQ:L004"],
         "policy_refs": [], "values": {"RFQ": "C", "DRAWING": "B"}}
    peer.vertex.draft(packet["packet_id"], [{**f, "unused": "PRIVATE"}], lambda _: None)
    assert peer.creds.refresh_count == 2
    extract, draft = peer.calls[1:]
    assert "IGNORE ALL PRIOR" not in extract["systemInstruction"]["parts"][0]["text"]
    assert extract["systemInstruction"]["parts"][0]["text"].startswith(vertex.EXTRACT_PROMPT)
    assert draft["systemInstruction"]["parts"][0]["text"].startswith(vertex.DRAFT_PROMPT)
    assert json.loads(extract["contents"][0]["parts"][0]["text"]) == packet
    lengths = json.loads(extract["contents"][0]["parts"][1]["text"].split(": ", 1)[1])
    assert lengths["DRAWING"]["L003"] == len("Drawing revision: B.")
    assert json.loads(draft["contents"][0]["parts"][0]["text"]) == {
        "packet_id": packet["packet_id"], "validated_findings": [f]}
    assert "PRIVATE" not in json.dumps(draft) and "IGNORE ALL PRIOR" not in json.dumps(draft)
    for request in peer.calls:
        cfg = request["generationConfig"]
        assert cfg["responseMimeType"] == "application/json" and cfg["responseJsonSchema"]["type"] == "object"
        assert cfg["temperature"] <= .2 and "tools" not in request


@pytest.mark.parametrize("bad", ["malformed", '{"a":1,"a":2}', '{"test":NaN}', "[]"])
def test_one_schema_repair_only(bad):
    peer = Peer([completion('{"status":"ok"}'), completion(bad), completion(bad)])
    with pytest.raises(vertex.VertexError) as error:
        peer.vertex.extract({"sources": []}, lambda _: None)
    assert error.value.code == "invalid_model_output" and len(peer.calls) == 3


def test_validation_retry_uses_only_trusted_feedback():
    peer = Peer([completion('{"status":"ok"}'), completion('{"x":"raw-input"}'), completion('{"x":0}')])

    def validate(obj):
        if obj["x"] != 0:
            raise ValueError("raw-exception")

    value, proof = peer.vertex.extract({"sources": []}, validate)
    assert value["x"] == 0 and proof["repair_attempted"] and proof["attempts"] == 2
    assert "raw-input" not in json.dumps(peer.calls) and "raw-exception" not in json.dumps(peer.calls)


@pytest.mark.parametrize(("reply", "code"), [
    (httpx.ReadTimeout("secret"), "vertex_timeout"),
    (httpx.Response(403, text="secret"), "vertex_access_denied"),
    (httpx.Response(404, text="secret"), "vertex_model_unavailable"),
    (httpx.Response(429, text="secret"), "vertex_rate_limited"),
    (httpx.Response(500, text="secret"), "vertex_service_error"),
    (completion('{}', model="unexpected"), "vertex_model_mismatch"),
    (completion('{}', finish="MAX_TOKENS"), "vertex_incomplete"),
    (httpx.Response(200, text="secret"), "vertex_protocol_error"),
])
def test_safe_transport_errors(reply, code):
    peer = Peer([reply])
    with pytest.raises(vertex.VertexError) as error:
        peer.vertex.smoke()
    assert error.value.code == code and error.value.stage == "smoke" and len(peer.calls) == 1
    assert "secret" not in str(error.value)


def test_expired_adc_reports_action_and_redacts_upstream_text():
    peer = Peer([])
    peer.creds.fail = True
    with pytest.raises(vertex.VertexError) as error:
        peer.vertex.smoke()
    assert error.value.code == "vertex_reauth_required" and error.value.stage == "authentication"
    assert "gcloud auth application-default login" in str(error.value) and "raw-token" not in str(error.value)
    assert not peer.calls


@pytest.mark.parametrize("config", [{"location": "https://elsewhere.example"}, {"model_id": "../../bad"},
                                   {"project": "../other"}, {"location": "us-central1@elsewhere.example"}])
def test_invalid_configuration_rejected_before_credentials_sent(config):
    peer = Peer([], **config)
    with pytest.raises(vertex.VertexError) as error:
        peer.vertex.smoke()
    assert error.value.stage == "configuration" and not peer.calls and peer.creds.refresh_count == 0


def test_retry_reloads_adc_after_local_login(monkeypatch):
    expired, current = TestCredentials(), TestCredentials()
    expired.fail = True
    credentials = iter([(expired, "expired-project"), (current, "current-project")])
    monkeypatch.delenv("GOOGLE_CLOUD_PROJECT", raising=False)
    monkeypatch.setattr(vertex.google.auth, "default", lambda **_: next(credentials))

    def send(req):
        assert "/projects/current-project/" in req.url.path
        assert req.headers["authorization"] == "Bearer synthetic-access-token"
        return completion('{"status":"ok"}')

    client = vertex.VertexClient(http_client=httpx.Client(transport=httpx.MockTransport(send)))
    with pytest.raises(vertex.VertexError, match="application-default login"):
        client.smoke()
    assert client.smoke()["attempts"] == 1
    assert expired.refresh_count == current.refresh_count == 1
    client.close()
