import pytest
from app.core.config import Settings
from pydantic import ValidationError


def test_settings_strip_application_text_fields() -> None:
    settings = Settings(
        app_name="  Dashboard API  ",
        app_version="  1.2.3  ",
        environment="  test  ",
        database_url="  sqlite:///./test.db  ",
    )

    assert settings.app_name == "Dashboard API"
    assert settings.app_version == "1.2.3"
    assert settings.environment == "test"
    assert settings.database_url == "sqlite:///./test.db"


@pytest.mark.parametrize(
    "field_name",
    ["app_name", "app_version", "environment", "database_url"],
)
def test_settings_reject_blank_application_text_fields(field_name: str) -> None:
    with pytest.raises(ValidationError):
        Settings(**{field_name: "   "})
