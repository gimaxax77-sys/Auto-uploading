# 글자 수 가드가 실제로 동작하는지 확인하는 자체 점검
import types
from unittest.mock import patch

import main


def fake_response(text):
    block = types.SimpleNamespace(type="text", text=text)
    return types.SimpleNamespace(content=[block])


def test_길이_초과하면_에러():
    with patch("anthropic.Anthropic") as client:
        client.return_value.messages.create.return_value = fake_response("가" * 300)
        try:
            main.write_post("아무 주제")
        except ValueError as e:
            assert "300자" in str(e)
        else:
            raise AssertionError("길이 초과인데 에러가 나지 않았습니다")


def test_정상_길이는_통과():
    with patch("anthropic.Anthropic") as client:
        client.return_value.messages.create.return_value = fake_response("  안녕하세요  ")
        assert main.write_post("아무 주제") == "안녕하세요"


if __name__ == "__main__":
    test_길이_초과하면_에러()
    test_정상_길이는_통과()
    print("통과")
