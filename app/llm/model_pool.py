from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import List
from urllib import request

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class ModelConfig:
    name: str
    api_key: str
    base_url: str
    model: str
    provider: str
    priority: int = 1
    enabled: bool = True


@dataclass(slots=True)
class ModelPool:
    models: List[ModelConfig] = field(default_factory=list)
    timeout: int = 30

    def add_model(self, config: ModelConfig) -> None:
        self.models.append(config)
        self.models.sort(key=lambda x: -x.priority)

    def add_from_env(self, env_vars: dict[str, str]) -> None:
        # 0. Zhipu GLM-4-Flash: 200 req/s (优先，免费高并发，解决当前限流问题)
        if env_vars.get("ZHIPU_API_KEY"):
            self.add_model(
                ModelConfig(
                    name="zhipu-glm-4-flash",
                    api_key=env_vars["ZHIPU_API_KEY"],
                    base_url="https://open.bigmodel.cn/api/paas/v4",
                    model="glm-4-flash",
                    provider="zhipu",
                    priority=110,
                )
            )
            self.add_model(
                ModelConfig(
                    name="zhipu-glm-4-flashx",
                    api_key=env_vars["ZHIPU_API_KEY"],
                    base_url="https://open.bigmodel.cn/api/paas/v4",
                    model="glm-4-flashx-250414",
                    provider="zhipu",
                    priority=109,
                )
            )

        # 1. Doubao Seed 2.0 Lite: 备用付费模型
        if env_vars.get("ARK_API_KEY"):
            self.add_model(
                ModelConfig(
                    name="doubao-seed-2-0-lite-260215",
                    api_key=env_vars["ARK_API_KEY"],
                    base_url=env_vars.get(
                        "ARK_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3"
                    ),
                    model="doubao-seed-2-0-lite-260215",
                    provider="volcengine",
                    priority=108,
                )
            )
            # 2. Doubao Seed 2.0 Mini: 备用模型
            self.add_model(
                ModelConfig(
                    name="doubao-seed-2-0-mini-260215",
                    api_key=env_vars["ARK_API_KEY"],
                    base_url=env_vars.get(
                        "ARK_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3"
                    ),
                    model="doubao-seed-2-0-mini-260215",
                    provider="volcengine",
                    priority=107,
                )
            )
            # 3. Doubao Seed 1.6 Lite: 备用模型
            self.add_model(
                ModelConfig(
                    name="doubao-seed-1-6-lite-251015",
                    api_key=env_vars["ARK_API_KEY"],
                    base_url=env_vars.get(
                        "ARK_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3"
                    ),
                    model="doubao-seed-1-6-lite-251015",
                    provider="volcengine",
                    priority=106,
                )
            )
            # 1. Doubao Seed 2.0 Mini: 高并发备用模型
            self.add_model(
                ModelConfig(
                    name="doubao-seed-2-0-mini-260215",
                    api_key=env_vars["ARK_API_KEY"],
                    base_url=env_vars.get(
                        "ARK_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3"
                    ),
                    model="doubao-seed-2-0-mini-260215",
                    provider="volcengine",
                    priority=109,
                )
            )
            # 2. Doubao Seed 1.6 Lite: 备用模型
            self.add_model(
                ModelConfig(
                    name="doubao-seed-1-6-lite-251015",
                    api_key=env_vars["ARK_API_KEY"],
                    base_url=env_vars.get(
                        "ARK_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3"
                    ),
                    model="doubao-seed-1-6-lite-251015",
                    provider="volcengine",
                    priority=108,
                )
            )
            # 1. Doubao Seed 2.0 Lite: 高可用备用模型
            self.add_model(
                ModelConfig(
                    name="doubao-seed-2-0-lite-260215",
                    api_key=env_vars["ARK_API_KEY"],
                    base_url=env_vars.get(
                        "ARK_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3"
                    ),
                    model="doubao-seed-2-0-lite-260215",
                    provider="volcengine",
                    priority=109,
                )
            )
            # 2. Doubao Seed 2.0 Mini: 高并发备用模型
            self.add_model(
                ModelConfig(
                    name="doubao-seed-2-0-mini-260215",
                    api_key=env_vars["ARK_API_KEY"],
                    base_url=env_vars.get(
                        "ARK_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3"
                    ),
                    model="doubao-seed-2-0-mini-260215",
                    provider="volcengine",
                    priority=108,
                )
            )

        # 1. Zhipu GLM-4-Flash: 200 req/s (优先)
        if env_vars.get("ZHIPU_API_KEY"):
            self.add_model(
                ModelConfig(
                    name="zhipu-glm-4-flash",
                    api_key=env_vars["ZHIPU_API_KEY"],
                    base_url="https://open.bigmodel.cn/api/paas/v4",
                    model="glm-4-flash",
                    provider="zhipu",
                    priority=100,
                )
            )
            self.add_model(
                ModelConfig(
                    name="zhipu-glm-4-flashx",
                    api_key=env_vars["ZHIPU_API_KEY"],
                    base_url="https://open.bigmodel.cn/api/paas/v4",
                    model="glm-4-flashx-250414",
                    provider="zhipu",
                    priority=90,
                )
            )

        # 2. Gemini Advanced Models
        if env_vars.get("GEMINI_API_KEY"):
            self.add_model(
                ModelConfig(
                    name="gemini-3.1-flash-lite",
                    api_key=env_vars["GEMINI_API_KEY"],
                    base_url="https://generativelanguage.googleapis.com/v1beta",
                    model="gemini-3.1-flash-lite-preview",
                    provider="gemini",
                    priority=95,
                )
            )
            self.add_model(
                ModelConfig(
                    name="gemini-3-flash",
                    api_key=env_vars["GEMINI_API_KEY"],
                    base_url="https://generativelanguage.googleapis.com/v1beta",
                    model="gemini-3-flash-preview",
                    provider="gemini",
                    priority=94,
                )
            )

        # 3. Groq Llama 3.3
        if env_vars.get("GROQ_API_KEY"):
            self.add_model(
                ModelConfig(
                    name="groq-llama-3.3",
                    api_key=env_vars["GROQ_API_KEY"],
                    base_url="https://api.groq.com/openai/v1",
                    model="llama-3.3-70b-versatile",
                    provider="groq",
                    priority=85,
                )
            )

        # 4. SiliconFlow Qwen3-32B
        if env_vars.get("SILICONFLOW_API_KEY"):
            self.add_model(
                ModelConfig(
                    name="siliconflow-qwen3-32b",
                    api_key=env_vars["SILICONFLOW_API_KEY"],
                    base_url="https://api.siliconflow.cn/v1",
                    model="Qwen/Qwen3-32B",
                    provider="siliconflow",
                    priority=80,
                )
            )

        # 5. Mistral Experiment (Free access to all models)
        if env_vars.get("MISTRAL_API_KEY"):
            self.add_model(
                ModelConfig(
                    name="mistral-large",
                    api_key=env_vars["MISTRAL_API_KEY"],
                    base_url="https://api.mistral.ai/v1",
                    model="mistral-large-latest",
                    provider="mistral",
                    priority=75,
                )
            )
            self.add_model(
                ModelConfig(
                    name="mistral-codestral",
                    api_key=env_vars["MISTRAL_API_KEY"],
                    base_url="https://api.mistral.ai/v1",
                    model="codestral-latest",
                    provider="mistral",
                    priority=74,
                )
            )

        # 6. Cerebras
        if env_vars.get("CEREBRAS_API_KEY"):
            self.add_model(
                ModelConfig(
                    name="cerebras-llama-3.3",
                    api_key=env_vars["CEREBRAS_API_KEY"],
                    base_url="https://api.cerebras.ai/v1",
                    model="llama-3.3-70b",
                    provider="cerebras",
                    priority=70,
                )
            )

        # 7. ModelScope
        if env_vars.get("MODELSCOPE_API_KEY"):
            self.add_model(
                ModelConfig(
                    name="modelscope-qwen3-32b",
                    api_key=env_vars["MODELSCOPE_API_KEY"],
                    base_url="https://api.modelscope.cn/v1",
                    model="Qwen/Qwen3-32B",
                    provider="modelscope",
                    priority=60,
                )
            )
            self.add_model(
                ModelConfig(
                    name="modelscope-deepseek-v3",
                    api_key=env_vars["MODELSCOPE_API_KEY"],
                    base_url="https://api.modelscope.cn/v1",
                    model="deepseek-ai/DeepSeek-V3.2",
                    provider="modelscope",
                    priority=59,
                )
            )

        # 8. OpenRouter
        if env_vars.get("OPENROUTER_API_KEY"):
            self.add_model(
                ModelConfig(
                    name="openrouter-qwen",
                    api_key=env_vars["OPENROUTER_API_KEY"],
                    base_url="https://openrouter.ai/api/v1",
                    model="qwen/qwen-2.5-7b-instruct",
                    provider="openrouter",
                    priority=50,
                )
            )

        # 9. Cloudflare
        if env_vars.get("CLOUDFLARE_API_KEY"):
            self.add_model(
                ModelConfig(
                    name="cloudflare-llama",
                    api_key=env_vars["CLOUDFLARE_API_KEY"],
                    base_url="https://api.cloudflare.com/client/v4/accounts",
                    model="@cf/meta/llama-3.1-8b-instruct",
                    provider="cloudflare",
                    priority=40,
                )
            )

    def chat(self, prompt: str) -> str:
        for model_config in self.models:
            if not model_config.enabled:
                continue

            try:
                response = self._chat_with_model(model_config, prompt)
                logger.info(
                    f"Success with {model_config.name} ({model_config.provider})"
                )
                return response
            except Exception as e:
                logger.warning(f"Failed with {model_config.name}: {e}")
                continue

        raise RuntimeError("All models in the pool failed")

    def _chat_with_model(self, config: ModelConfig, prompt: str) -> str:
        if config.provider == "volcengine":
            return self._chat_volcengine(config, prompt)
        elif config.provider == "gemini":
            return self._chat_gemini(config, prompt)
        elif config.provider == "cloudflare":
            return self._chat_cloudflare(config, prompt)
        elif config.provider in [
            "groq",
            "siliconflow",
            "zhipu",
            "mistral",
            "openrouter",
            "cerebras",
            "modelscope",
        ]:
            return self._chat_openai_compatible(config, prompt)
        else:
            raise ValueError(f"Unsupported provider: {config.provider}")

    def _chat_volcengine(self, config: ModelConfig, prompt: str) -> str:
        payload = {
            "model": config.model,
            "messages": [{"role": "user", "content": prompt}],
        }
        return self._make_request(config, payload)

    def _chat_gemini(self, config: ModelConfig, prompt: str) -> str:
        url = f"{config.base_url.rstrip('/')}/models/{config.model}:generateContent"
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        body = json.dumps(payload).encode("utf-8")
        req = request.Request(
            url=url,
            data=body,
            headers={
                "x-goog-api-key": config.api_key,
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with request.urlopen(req, timeout=self.timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
        return str(data["candidates"][0]["content"]["parts"][0]["text"])

    def _chat_cloudflare(self, config: ModelConfig, prompt: str) -> str:
        url = f"{config.base_url}/ai/run/{config.model}"
        payload = {"messages": [{"role": "user", "content": prompt}]}
        body = json.dumps(payload).encode("utf-8")
        req = request.Request(
            url=url,
            data=body,
            headers={
                "Authorization": f"Bearer {config.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with request.urlopen(req, timeout=self.timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
        return str(data["result"]["response"])

    def _chat_openai_compatible(self, config: ModelConfig, prompt: str) -> str:
        payload = {
            "model": config.model,
            "messages": [{"role": "user", "content": prompt}],
        }
        return self._make_request(config, payload)

    def _make_request(self, config: ModelConfig, payload: dict) -> str:
        body = json.dumps(payload).encode("utf-8")
        req = request.Request(
            url=f"{config.base_url.rstrip('/')}/chat/completions",
            data=body,
            headers={
                "Authorization": f"Bearer {config.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with request.urlopen(req, timeout=self.timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
        return str(data["choices"][0]["message"]["content"])


def create_model_pool_from_env() -> ModelPool:
    import os
    from pathlib import Path

    env_vars = {}
    env_file = Path(".env")
    if env_file.exists():
        for raw_line in env_file.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            env_vars[key.strip()] = value.strip().strip("\"'")

    for key in [
        "ARK_API_KEY",
        "ARK_MODEL",
        "ARK_BASE_URL",
        "GEMINI_API_KEY",
        "GROQ_API_KEY",
        "SILICONFLOW_API_KEY",
        "ZHIPU_API_KEY",
        "MISTRAL_API_KEY",
        "OPENROUTER_API_KEY",
        "CEREBRAS_API_KEY",
        "CLOUDFLARE_API_KEY",
        "MODELSCOPE_API_KEY",
    ]:
        if key in os.environ:
            env_vars[key] = os.environ[key]

    pool = ModelPool()
    pool.add_from_env(env_vars)
    return pool
