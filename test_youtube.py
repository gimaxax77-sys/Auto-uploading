# 자격증명 파일이 없을 때 친절한 안내를 내는지 확인하는 자체 점검
import os
import tempfile

import youtube


def test_client_secret_없으면_안내_에러():
    # 인증 파일이 둘 다 없는 빈 폴더에서 실행합니다.
    with tempfile.TemporaryDirectory() as work:
        old = os.getcwd()
        os.chdir(work)
        try:
            youtube.get_service()
        except FileNotFoundError as e:
            assert "client_secret.json" in str(e)
        else:
            raise AssertionError("인증 파일이 없는데 FileNotFoundError 가 나지 않았습니다")
        finally:
            os.chdir(old)


if __name__ == "__main__":
    test_client_secret_없으면_안내_에러()
    print("통과")
