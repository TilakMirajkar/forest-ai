from forest_ai.core.config import Settings


def test_settings_read_from_environment(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("ACCESS_TOKEN_EXPIRE_MINUTES", "45")

    settings = Settings()

    assert settings.environment == "test"
    assert settings.access_token_expire_minutes == 45

def test_settings_have_safe_defaults(monkeypatch):
    monkeypatch.delenv("ENVIRONMENT", raising=False)

    settings = Settings(_env_file=None)

    assert settings.environment == "development"