import httpx


def _extract_error_message(response: httpx.Response) -> str:
    content_type = response.headers.get("content-type", "")
    if "application/json" in content_type:
        try:
            payload = response.json()
        except ValueError:
            return response.text or f"HTTP {response.status_code}"
        if isinstance(payload, dict):
            detail = payload.get("detail")
            if isinstance(detail, str):
                return detail
            if isinstance(detail, dict):
                return str(detail.get("message") or detail)
        return str(payload)

    text = response.text.strip()
    if text:
        return text[:500]
    return f"HTTP {response.status_code}"
