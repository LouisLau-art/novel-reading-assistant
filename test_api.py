#!/usr/bin/env python3
"""Test script to verify Volcengine API is working correctly."""

import sys
from app.llm.volcengine import VolcengineChatClient


def main():
    api_key = "40ea6fdc-9dba-4d67-bb60-3637556b0449"
    model = "doubao-seed-code-preview-251028"
    base_url = "https://ark.cn-beijing.volces.com/api/v3"

    client = VolcengineChatClient(api_key=api_key, model=model, base_url=base_url)

    try:
        response = client.chat("你好，世界！")
        print("API调用成功！")
        print("响应内容：", response)
        return 0
    except Exception as e:
        print(f"API调用失败：{e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
