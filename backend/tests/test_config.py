import pytest
from app.core.config import Settings
from pydantic import ValidationError


def test_settings_strip_application_text_fields() -> None:
    settings = Settings(
        app_name="  Dashboard API  ",
        app_version="  1.2.3  ",
        environment="  test  ",
        database_url="  sqlite:///./test.db  ",
        openrouter_model="  test/model  ",
        openrouter_base_url="  https://openrouter.ai/api/v1  ",
    )

    assert settings.app_name == "Dashboard API"
    assert settings.app_version == "1.2.3"
    assert settings.environment == "test"
    assert settings.database_url == "sqlite:///./test.db"
    assert settings.openrouter_model == "test/model"
    assert settings.openrouter_base_url == "https://openrouter.ai/api/v1"


@pytest.mark.parametrize(
    "field_name",
    ["app_name", "app_version", "environment", "database_url"],
)
def test_settings_reject_blank_application_text_fields(field_name: str) -> None:
    with pytest.raises(ValidationError):
        Settings(**{field_name: "   "})


@pytest.mark.parametrize(
    "field_name",
    ["openrouter_model", "openrouter_base_url"],
)
def test_settings_reject_blank_openrouter_text_fields(field_name: str) -> None:
    with pytest.raises(ValidationError):
        Settings(**{field_name: "   "})


@pytest.mark.parametrize("timeout_seconds", [0, -1])
def test_settings_reject_non_positive_openrouter_timeout(timeout_seconds: float) -> None:
    with pytest.raises(ValidationError):
        Settings(openrouter_timeout_seconds=timeout_seconds)
