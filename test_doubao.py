#!/usr/bin/env python3
"""简单测试doubao-seed-1.6-lite-251015模型"""

from app.llm.model_pool import create_model_pool_from_env


def main():
    print("正在初始化模型池...")
    pool = create_model_pool_from_env()
    print(f"模型池初始化完成，共 {len(pool.models)} 个模型可用")

    print("\n尝试调用doubao-seed-1.6-lite-251015模型...")
    try:
        response = pool.chat("你好，请简短介绍一下你自己")
        print(f"\n✅ 调用成功！响应：")
        print(response)
    except Exception as e:
        print(f"\n❌ 调用失败：")
        print(str(e))


if __name__ == "__main__":
    main()
