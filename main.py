# 주제를 받아 AI로 글을 쓰고 X(트위터)에 올리는 도구
import os
import sys

import anthropic
import tweepy
from dotenv import load_dotenv

load_dotenv()

LIMIT = 280


def write_post(topic: str) -> str:
    """주제를 받아 X에 올릴 글을 생성합니다."""
    client = anthropic.Anthropic()
    response = client.messages.create(
        model="claude-opus-4-8",
        max_tokens=1000,
        system=(
            f"너는 SNS 게시글을 쓴다. 한국어로, {LIMIT}자 이내로 쓴다. "
            "해시태그는 최대 3개. 설명이나 인사말 없이 게시글 본문만 출력한다."
        ),
        messages=[{"role": "user", "content": topic}],
    )
    text = next(b.text for b in response.content if b.type == "text").strip()
    if len(text) > LIMIT:
        raise ValueError(f"생성된 글이 {len(text)}자로 {LIMIT}자를 넘습니다: {text}")
    return text


def post_to_x(text: str) -> str:
    """글을 X에 올리고 게시물 URL을 돌려줍니다."""
    client = tweepy.Client(
        consumer_key=os.environ["X_API_KEY"],
        consumer_secret=os.environ["X_API_SECRET"],
        access_token=os.environ["X_ACCESS_TOKEN"],
        access_token_secret=os.environ["X_ACCESS_TOKEN_SECRET"],
    )
    result = client.create_tweet(text=text)
    return f"https://x.com/i/status/{result.data['id']}"


def main() -> None:
    if len(sys.argv) < 2:
        print("사용법: python main.py \"주제\" [--post]")
        sys.exit(1)

    topic = sys.argv[1]
    text = write_post(topic)
    print(text)

    # 기본은 미리보기만. 실제 게시는 --post 를 붙여야 합니다.
    if "--post" in sys.argv:
        print(f"\n게시 완료: {post_to_x(text)}")
    else:
        print("\n(미리보기입니다. 실제로 올리려면 --post 를 붙이세요.)")


if __name__ == "__main__":
    main()
