"""
🚨 [ARCHIVE NOTICE]
이 코드는 Windows 전용 HWP 변환 모듈(win32com.client)을 사용하는 구버전 파이프라인입니다.
현재 운영 환경에서는 HWPX 업로드 기반으로 대체되었습니다.
"""
import redis
import requests


import json
import os

from app.services.downloader import download_hwp_from_edunet
from app.services.converter import convert_hwp_to_hwpx 
from app.services.parses import extract_blocks_from_hwpx

r = redis.StrictRedis(
    host=os.getenv("REDIS_HOST", "localhost"),  # 환경변수 REDIS_HOST 값 사용, 없으면 기본 localhost
    port=int(os.getenv("REDIS_PORT", 6379)),    # REDIS_PORT 값 사용, 없으면 기본 6379
    db=0,                                       # Redis DB 번호 (0번 DB 사용)
    decode_responses=True                       # Redis 응답을 바이트가 아닌 문자열(str)로 디코딩
)

# -------------------------------------------
# 큐 감시 및 작업 처리
# -------------------------------------------
def consume_parse_queue():
    """
    Redis 큐(parse:queue)에 쌓인 작업을 순서대로 처리한다.
    Spring 서버가 더 이상 FastAPI로 요청을 보내지 않고,
    Redis에 job을 push하면 워커가 바로 수행하는 구조.
    """
    queue_name = os.getenv("REDIS_QUEUE_NAME", "queue:material:admin")
    print(f"Worker 시작: queue={queue_name} 대기 중...")

    while True:
        try:
            # Redis에서 parse:queue의 데이터를 꺼내옴 (blocking)
            _, payload_json = r.brpop(queue_name)

            # JSON 문자열 → 파이썬 dict로 변환
            payload = json.loads(payload_json)
            job_no = payload.get("jobNo")
            url = payload.get("url")

            print(f"[작업 수신] jobNo={job_no}, url={url}")

            download_return_dict = download_hwp_from_edunet(url)  # HWP 파일 다운로드
            hwp_path = download_return_dict['path']  # 다운로드된 HWP 파일의 경로

             # HWP → HWPX 변환 + 텍스트 추출
            ext = os.path.splitext(hwp_path)[1]
            if ext == ".hwp":
                hwpx_path = convert_hwp_to_hwpx(hwp_path)  # HWP 파일을 HWPX로 변환
                blocks = extract_blocks_from_hwpx(hwpx_path) # HWPX 파일에서 텍스트 추출
            elif ext == ".hwpx":
                hwpx_path = hwp_path
                blocks = extract_blocks_from_hwpx(hwp_path)
            else:
                raise ValueError(f"지원하지 않는 확장자: {ext}")

            source_filename = os.path.basename(hwpx_path)  # HWPX 파일의 이름 추출

            blocks_string = json.dumps(blocks, ensure_ascii=False)  # blocks를 JSON 문자열로 변환
            # json.dumps()는 모든 문자열을 ASCII 문자로 이스케이프 처리하므로 ensure_ascii=False로 한글 그대로 출력되도록 설정 
            keywords_string = json.dumps( download_return_dict['keywords'], ensure_ascii=False)

            result = {
                "jobNo": job_no,
                "content": blocks_string,  # 추출된 블록 데이터
                "school": download_return_dict['school'],  # 학교 정보
                "grade": download_return_dict['grade'],  # 학년 정보
                "title": download_return_dict['title'],  # 제목 정보
                "keywords": keywords_string,  # 키워드 정보
                "sourceFilename": source_filename  # HWPX 파일의 이름
            }

            # -------------------------------------------
            # Spring 서버에 콜백 전송
            # -------------------------------------------
            callback_url = os.getenv(
                "SPRING_CALLBACK_URL_PARSE",
                "http://localhost:8080/api/worker/callback/materials/admin"
            )

            print(f"[작업 완료] jobNo={job_no} → 콜백 전송: {callback_url}")
            response = requests.post(callback_url, json=result, timeout=20)

            print(f"[콜백 응답] {response.status_code}: {response.text}")

        except Exception as e:
            # 예외 발생 시 에러 로그 출력 및 실패 콜백 전송
            error_message = str(e)
            print(f"[에러] jobNo={job_no} 처리 실패: {error_message}")

            fail_callback_url = os.getenv(
                "SPRING_CALLBACK_URL_MATERIAL_ADMIN_FAIL",
                "http://localhost:8080/api/worker/callback/materials/admin/fail"
            )
            try:
                res = requests.post(fail_callback_url, json={"jobNo": job_no, "error": error_message}, timeout=10)
                print(f"[실패 콜백 응답] {res.status_code}: {res.text}")
            except Exception as err:
                print(f"[경고] 실패 콜백 전송 중 오류 발생: {err}")


# -------------------------------------------
# 엔트리포인트
# -------------------------------------------
if __name__ == "__main__":
    consume_parse_queue()