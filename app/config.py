import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class Settings:
    project_root: Path = Path("/root/novel-reading-assistant")
    data_dir: Path = field(default_factory=lambda: Path("/root/novel-reading-assistant/data"))
    llm_provider: str = "volcengine"
    llm_api_key: str = ""
    llm_model: str = ""
    llm_base_url: str = "https://ark.cn-beijing.volces.com/api/v3"

    @classmethod
    def from_env(cls) -> "Settings":
        settings = cls()
        settings.llm_provider = os.getenv("NRA_LLM_PROVIDER", settings.llm_provider)
        settings.llm_api_key = os.getenv("ARK_API_KEY", "")
        settings.llm_model = os.getenv("ARK_MODEL", "")
        settings.llm_base_url = os.getenv("ARK_BASE_URL", settings.llm_base_url)
        return settings
