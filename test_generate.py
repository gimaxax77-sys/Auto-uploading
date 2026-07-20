# 글자 수 가드와 플랫폼 설정이 실제로 동작하는지 확인하는 자체 점검
import types
from unittest.mock import patch

import generate


def fake_response(text):
    block = types.SimpleNamespace(type="text", text=text)
    return types.SimpleNamespace(content=[block])


def test_길이_초과하면_에러():
    with patch("anthropic.Anthropic") as client:
        client.return_value.messages.create.return_value = fake_response("가" * 300)
        try:
            generate.write_post("아무 주제", "x")
        except ValueError as e:
            assert "300자" in str(e) and "280자" in str(e)
        else:
            raise AssertionError("길이 초과인데 에러가 나지 않았습니다")


def test_플랫폼마다_한도가_다름():
    # x에서는 초과인 300자가 threads(500자)에서는 통과해야 합니다.
    with patch("anthropic.Anthropic") as client:
        client.return_value.messages.create.return_value = fake_response("가" * 300)
        assert len(generate.write_post("아무 주제", "threads")) == 300


def test_정상_길이는_통과():
    with patch("anthropic.Anthropic") as client:
        client.return_value.messages.create.return_value = fake_response("  안녕하세요  ")
        assert generate.write_post("아무 주제", "x") == "안녕하세요"


def test_모르는_플랫폼은_에러():
    try:
        generate.write_post("아무 주제", "없는곳")
    except ValueError as e:
        assert "없는곳" in str(e)
    else:
        raise AssertionError("모르는 플랫폼인데 에러가 나지 않았습니다")


if __name__ == "__main__":
    test_길이_초과하면_에러()
    test_플랫폼마다_한도가_다름()
    test_정상_길이는_통과()
    test_모르는_플랫폼은_에러()
    print("통과")
