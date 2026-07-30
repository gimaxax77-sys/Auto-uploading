# 주제를 받아 플랫폼에 맞는 게시글과 영상 대본을 생성하는 도구
import json
import sys

import anthropic
from dotenv import load_dotenv

load_dotenv()

# 플랫폼별 규칙. 새 플랫폼은 여기에 한 줄 추가하면 됩니다.
PLATFORMS = {
    "x": {"limit": 280, "hashtags": 3},
    "threads": {"limit": 500, "hashtags": 5},
}

TONE = "친근하고 담백한 한국어"


def write_post(topic: str, platform: str = "x") -> str:
    """주제를 받아 해당 플랫폼에 올릴 글을 생성합니다."""
    if platform not in PLATFORMS:
        raise ValueError(f"모르는 플랫폼입니다: {platform} (가능: {', '.join(PLATFORMS)})")

    rule = PLATFORMS[platform]
    client = anthropic.Anthropic()
    response = client.messages.create(
        model="claude-opus-4-8",
        max_tokens=1000,
        system=(
            f"너는 SNS 게시글을 쓴다. {TONE}로, {rule['limit']}자 이내로 쓴다. "
            f"해시태그는 최대 {rule['hashtags']}개. "
            "설명이나 인사말 없이 게시글 본문만 출력한다."
        ),
        messages=[{"role": "user", "content": topic}],
    )
    text = next(b.text for b in response.content if b.type == "text").strip()

    if len(text) > rule["limit"]:
        raise ValueError(
            f"생성된 글이 {len(text)}자로 {platform} 한도 {rule['limit']}자를 넘습니다: {text}"
        )
    return text


def write_script(topic: str, scenes: int = 5) -> list[dict]:
    """주제를 받아 장면별 내레이션과 이미지 검색어를 생성합니다."""
    client = anthropic.Anthropic()
    response = client.messages.create(
        model="claude-opus-4-8",
        max_tokens=2000,
        system=(
            f"너는 짧은 영상 대본을 쓴다. {TONE}로 정확히 {scenes}개 장면을 만든다. "
            "narration 은 소리내어 읽었을 때 5~10초인 한국어 한두 문장. "
            "image_query 는 그 장면에 어울리는 사진을 스톡 사이트에서 찾을 영어 검색어 2~3단어."
        ),
        messages=[{"role": "user", "content": topic}],
        output_config={
            "format": {
                "type": "json_schema",
                "schema": {
                    "type": "object",
                    "properties": {
                        "scenes": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "narration": {"type": "string"},
                                    "image_query": {"type": "string"},
                                },
                                "required": ["narration", "image_query"],
                                "additionalProperties": False,
                            },
                        }
                    },
                    "required": ["scenes"],
                    "additionalProperties": False,
                },
            }
        },
    )
    text = next(b.text for b in response.content if b.type == "text")
    return json.loads(text)["scenes"]


def main() -> None:
    if len(sys.argv) < 2:
        print(f"사용법: python generate.py \"주제\" [플랫폼]  (가능: {', '.join(PLATFORMS)})")
        sys.exit(1)

    platform = sys.argv[2] if len(sys.argv) > 2 else "x"
    text = write_post(sys.argv[1], platform)
    print(text)
    print(f"\n[{platform} / {len(text)}자 / 한도 {PLATFORMS[platform]['limit']}자]")


if __name__ == "__main__":
    main()
