from app.config import Settings


def test_settings_defaults():
    settings = Settings()
    assert settings.data_dir.name == "data"
