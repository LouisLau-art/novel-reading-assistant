import os
from dataclasses import dataclass, field
from pathlib import Path


def _default_project_root() -> Path:
    return Path(__file__).resolve().parents[1]


@dataclass(slots=True)
class Settings:
    project_root: Path = field(default_factory=_default_project_root)
    data_dir: Path = field(default_factory=lambda: _default_project_root() / "data")
    llm_provider: str = "volcengine"
    llm_api_key: str = ""
    llm_model: str = ""  # 重量级模型：用于在线回答
    llm_model_fast: str = ""  # 轻量级模型：用于批量提取
    llm_base_url: str = "https://ark.cn-beijing.volces.com/api/v3"

    @classmethod
    def from_env(cls, env_file: Path | None = None) -> "Settings":
        settings = cls()
        dotenv_values = _load_dotenv(env_file or settings.project_root / ".env")
        settings.llm_provider = os.getenv(
            "NRA_LLM_PROVIDER",
            dotenv_values.get("NRA_LLM_PROVIDER", settings.llm_provider),
        )
        settings.llm_api_key = os.getenv(
            "ARK_API_KEY", dotenv_values.get("ARK_API_KEY", "")
        )
        settings.llm_model = os.getenv("ARK_MODEL", dotenv_values.get("ARK_MODEL", ""))
        settings.llm_model_fast = os.getenv(
            "ARK_MODEL_FAST", dotenv_values.get("ARK_MODEL_FAST", "")
        )
        settings.llm_base_url = os.getenv(
            "ARK_BASE_URL",
            dotenv_values.get("ARK_BASE_URL", settings.llm_base_url),
        )
        return settings


def _load_dotenv(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    env_path = Path(path)
    if not env_path.exists():
        return values

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip("\"'")
    return values
