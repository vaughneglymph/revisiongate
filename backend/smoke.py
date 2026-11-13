"""Run a real Vertex AI preflight and print its redacted result."""
import json

from dotenv import load_dotenv

from .vertex import API_VERSION, ROOT, VertexClient, VertexError, utc_now


def main() -> int:
    load_dotenv(ROOT / ".env", override=False)
    client = VertexClient()
    try:
        report = {"result": "passed", **client.smoke()}
    except VertexError as exc:
        report = {
            "result": "blocked" if exc.stage in ("configuration", "authentication") else "failed",
            "timestamp": utc_now(), "stage": exc.stage, "code": exc.code, "message": exc.message,
            "provider": client.provider, "api_version": API_VERSION,
        }
    finally:
        client.close()
    print(json.dumps(report, indent=2))
    return 0 if report["result"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
