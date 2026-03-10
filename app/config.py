from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class Settings:
    project_root: Path = Path("/root/novel-reading-assistant")
    data_dir: Path = field(default_factory=lambda: Path("/root/novel-reading-assistant/data"))
