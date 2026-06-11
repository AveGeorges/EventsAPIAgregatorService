from urllib.parse import parse_qsl, urlencode, urljoin, urlparse, urlunparse


def normalize_base_url(url: str) -> str:
    """Нормализует base URL: без лишних слэшей в конце, с одним завершающим /."""
    return urljoin(url.rstrip("/") + "/", "")


def join_url(base: str, *parts: str, trailing_slash: bool = False) -> str:
    """Склеивает base URL и относительный path через urljoin."""
    path = "/".join(str(part).strip("/") for part in parts if part)
    if trailing_slash and path:
        path = f"{path}/"
    normalized_base = base if base.endswith("/") else f"{base}/"
    return urljoin(normalized_base, path)


def append_query(base_url: str, query: dict[str, str | int]) -> str:
    """Добавляет query-параметры к URL"""
    if not query:
        return base_url

    parsed = urlparse(base_url)
    merged = dict(parse_qsl(parsed.query, keep_blank_values=True))
    merged.update({key: str(value) for key, value in query.items()})
    return urlunparse(parsed._replace(query=urlencode(merged)))
