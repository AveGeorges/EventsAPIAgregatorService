from unittest.mock import patch

from app.core.glitchtip import init_glitchtip


@patch("app.core.glitchtip.sentry_sdk.init")
@patch("app.core.glitchtip.settings")
def test_init_glitchtip_skips_when_dsn_missing(mock_settings, mock_sentry_init):
    mock_settings.glitchtip_dsn = ""

    init_glitchtip()

    mock_sentry_init.assert_not_called()


@patch("app.core.glitchtip.sentry_sdk.init")
@patch("app.core.glitchtip.settings")
def test_init_glitchtip_initializes_sentry_when_dsn_set(mock_settings, mock_sentry_init):
    mock_settings.glitchtip_dsn = "https://example.com/1"

    init_glitchtip()

    mock_sentry_init.assert_called_once()
    assert mock_sentry_init.call_args.kwargs["dsn"] == "https://example.com/1"


@patch("app.main.init_glitchtip")
def test_create_app_initializes_glitchtip(mock_init_glitchtip):
    from app.main import create_app

    create_app()

    mock_init_glitchtip.assert_called_once()
