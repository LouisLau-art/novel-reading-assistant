from app.api.cli import build_request


def test_build_request_keeps_question_and_progress():
    req = build_request("玉昆是谁", chapter_idx=120)
    assert req["question"] == "玉昆是谁"
    assert req["chapter_idx"] == 120
