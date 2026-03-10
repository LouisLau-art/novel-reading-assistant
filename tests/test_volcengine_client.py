import json

from app.llm.volcengine import VolcengineChatClient


def test_volcengine_client_posts_openai_compatible_chat_request(monkeypatch):
    captured: dict[str, object] = {}

    class FakeResponse:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self) -> bytes:
            return json.dumps(
                {
                    "choices": [
                        {
                            "message": {
                                "content": "这是火山模型的回答。"
                            }
                        }
                    ]
                }
            ).encode("utf-8")

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["headers"] = dict(request.header_items())
        captured["body"] = json.loads(request.data.decode("utf-8"))
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

    client = VolcengineChatClient(
        api_key="test-key",
        model="doubao-seed-1-8-251228",
        base_url="https://ark.cn-beijing.volces.com/api/v3",
    )
    answer = client.chat("请解释韩冈是谁。")

    assert answer == "这是火山模型的回答。"
    assert captured["url"] == "https://ark.cn-beijing.volces.com/api/v3/chat/completions"
    assert captured["headers"]["Authorization"] == "Bearer test-key"
    assert captured["body"]["model"] == "doubao-seed-1-8-251228"
    assert captured["body"]["messages"][0]["role"] == "user"
