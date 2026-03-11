#!/usr/bin/env python3
"""Test the model pool functionality."""

from app.llm.model_pool import create_model_pool_from_env


def main():
    pool = create_model_pool_from_env()
    print(f"Loaded {len(pool.models)} models:")
    for i, m in enumerate(pool.models, 1):
        print(f"  {i}. {m.name} ({m.provider}) priority={m.priority}")

    print("\nTesting simple chat...")
    try:
        response = pool.chat("你好，你是哪个AI模型？请用中文回答。")
        print(f"Response: {response[:200]}...")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
