from agent.config import settings


def test_settings_load_defaults():
    assert settings.log_level == "INFO"


def test_api_key_is_loaded_from_env():
    assert settings.anthropic_api_key != ""
