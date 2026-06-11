from app.core.url_utils import append_query, join_url, normalize_base_url


def test_normalize_base_url_adds_trailing_slash():
    assert normalize_base_url("http://provider.test") == "http://provider.test/"
    assert normalize_base_url("http://provider.test/") == "http://provider.test/"


def test_join_url_builds_provider_paths():
    base = "http://provider.test/"
    assert join_url(base, "api", "events", trailing_slash=True) == "http://provider.test/api/events/"
    event_id = "550e8400-e29b-41d4-a716-446655440000"
    seats_url = join_url(base, "api", "events", event_id, "seats", trailing_slash=True)
    assert seats_url == f"http://provider.test/api/events/{event_id}/seats/"


def test_append_query_builds_pagination_url():
    base = "http://test/api/events"
    url = append_query(base, {"page": 2, "page_size": 20, "date_from": "2026-06-06"})
    assert url == "http://test/api/events?page=2&page_size=20&date_from=2026-06-06"


def test_append_query_merges_with_existing_query_params():
    base = "http://test/api/events?page=1&page_size=20"
    url = append_query(base, {"page": 2, "date_from": "2026-06-06"})

    assert url == "http://test/api/events?page=2&page_size=20&date_from=2026-06-06"
