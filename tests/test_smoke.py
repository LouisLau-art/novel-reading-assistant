from app.config import Settings


def test_settings_defaults():
    settings = Settings()
    assert settings.data_dir.name == "data"


def test_settings_can_read_volcengine_env(monkeypatch):
    monkeypatch.setenv("ARK_API_KEY", "test-key")
    monkeypatch.setenv("ARK_MODEL", "doubao-seed-1-8-251228")

    settings = Settings.from_env()

    assert settings.llm_provider == "volcengine"
    assert settings.llm_api_key == "test-key"
    assert settings.llm_model == "doubao-seed-1-8-251228"
    assert settings.llm_base_url == "https://ark.cn-beijing.volces.com/api/v3"
