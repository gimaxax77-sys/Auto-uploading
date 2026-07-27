# 완성된 영상을 YouTube에 올리는 도구
import os
import sys

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.force-ssl",  # 공개↔비공개 전환(videos.update)에 필요
    "https://www.googleapis.com/auth/yt-analytics.readonly",  # 노출수·클릭률·시청지속률 조회에 필요
]
CLIENT_SECRET = "client_secret.json"  # Google Cloud 에서 받은 파일
TOKEN = "token.json"  # 최초 인증 후 자동 생성. 다음부터는 로그인 안 함.


def get_service():
    """구글 인증을 처리하고 YouTube API 연결을 돌려줍니다."""
    creds = None
    if os.path.exists(TOKEN):
        creds = Credentials.from_authorized_user_file(TOKEN, SCOPES)

    # 저장된 인증이 없거나 만료됐으면 처리합니다.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CLIENT_SECRET):
                raise FileNotFoundError(
                    f"{CLIENT_SECRET} 가 없습니다. Google Cloud 에서 OAuth 클라이언트 "
                    "JSON 을 받아 이 폴더에 넣으십시오."
                )
            # 브라우저가 열리며 구글 로그인 창이 뜹니다(최초 1회, PC 필요).
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN, "w") as f:
            f.write(creds.to_json())

    return build("youtube", "v3", credentials=creds)


def upload(video_path: str, title: str, description: str = "", private: bool = True) -> str:
    """영상을 올리고 게시물 URL을 돌려줍니다. 기본은 비공개입니다."""
    body = {
        "snippet": {"title": title, "description": description, "categoryId": "22"},
        "status": {"privacyStatus": "private" if private else "public"},
    }
    media = MediaFileUpload(video_path, chunksize=-1, resumable=True)
    request = get_service().videos().insert(
        part="snippet,status", body=body, media_body=media
    )
    response = request.execute()
    return f"https://youtu.be/{response['id']}"


def set_privacy(video_id: str, private: bool = False) -> None:
    """이미 올린 영상의 공개 상태를 바꿉니다."""
    get_service().videos().update(
        part="status",
        body={"id": video_id, "status": {"privacyStatus": "private" if private else "public"}},
    ).execute()


def main() -> None:
    if len(sys.argv) < 3:
        print("사용법: python youtube.py 영상.mp4 \"제목\" [설명] [--public]")
        sys.exit(1)

    private = "--public" not in sys.argv
    desc = sys.argv[3] if len(sys.argv) > 3 and not sys.argv[3].startswith("--") else ""
    url = upload(sys.argv[1], sys.argv[2], desc, private)
    상태 = "공개" if not private else "비공개"
    print(f"업로드 완료({상태}): {url}")


if __name__ == "__main__":
    main()
