import time
import httpx

TARGETS = {
    "ok": "http://demo:9000/ok",
    "error": "http://demo:9000/error",
    "slow": "http://demo:9000/slow",
    "invalid": "http://demo:9000/invalid",
}

def inspect_target(mode, client):
    started = time.monotonic()
    status = None
    error = ""
    try:
        with client.stream("GET", TARGETS[mode]) as response:
            status = response.status_code
            if status != 200:
                error = f"http_{status}"
            else:
                body = bytearray()
                for chunk in response.iter_bytes():
                    body.extend(chunk)
                    if len(body) > 65536:
                        raise ValueError("body_too_large")
                payload = httpx.Response(200, content=bytes(body)).json()
                if not isinstance(payload, dict) or payload.get("status") != "ok":
                    error = "invalid_contract"
    except httpx.TimeoutException:
        error = "timeout"
    except httpx.RequestError:
        error = "network_error"
    except (ValueError, UnicodeError):
        error = "invalid_json_or_size"

    return {
        "ok": not error,
        "status_code": status,
        "latency_ms": int((time.monotonic() - started) * 1000),
        "error": error,
    }