# 생성한 글을 X(트위터)에 올리는 도구
import os
import sys

import tweepy
from dotenv import load_dotenv

from generate import write_post

load_dotenv()


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

    text = write_post(sys.argv[1], "x")
    print(text)

    # 기본은 미리보기만. 실제 게시는 --post 를 붙여야 합니다.
    if "--post" in sys.argv:
        print(f"\n게시 완료: {post_to_x(text)}")
    else:
        print("\n(미리보기입니다. 실제로 올리려면 --post 를 붙이세요.)")


if __name__ == "__main__":
    main()
