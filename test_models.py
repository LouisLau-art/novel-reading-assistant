#!/usr/bin/env python3
"""Test different Volcengine models to compare their performance."""

import sys
from app.llm.volcengine import VolcengineChatClient

API_KEY = "40ea6fdc-9dba-4d67-bb60-3637556b0449"
BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"

MODELS = [
    "doubao-seed-1-8-251228",
    "doubao-seed-code-preview-251028",
    "glm-4-7-251222",
    "kimi-k2-thinking-251104",
]

TEST_PROMPT = "用一句话介绍你自己"


def main():
    results = []

    for model in MODELS:
        print(f"\n{'=' * 60}")
        print(f"测试模型: {model}")
        print("=" * 60)

        client = VolcengineChatClient(api_key=API_KEY, model=model, base_url=BASE_URL)

        try:
            response = client.chat(TEST_PROMPT)
            print(f"响应: {response[:200]}...")
            results.append((model, "成功", response[:100]))
        except Exception as e:
            print(f"错误: {e}")
            results.append((model, f"失败: {e}", ""))

    print(f"\n\n{'=' * 60}")
    print("测试结果汇总")
    print("=" * 60)
    for model, status, response in results:
        print(f"- {model}: {status}")
        if response:
            print(f"  响应预览: {response}...")

    return 0


if __name__ == "__main__":
    sys.exit(main())
