import redis
import json
import requests
import os
from app.services.downloader import download_from_object_storage
from app.services.converter import convert_hwp_to_hwpx 
from app.services.parses import extract_blocks_from_hwpx

r = redis.StrictRedis(
    host=os.getenv("REDIS_HOST", "localhost"),  # 환경변수 REDIS_HOST 값 사용, 없으면 기본 localhost
    port=int(os.getenv("REDIS_PORT", 6379)),    # REDIS_PORT 값 사용, 없으면 기본 6379
    db=0,                                       # Redis DB 번호 (0번 DB 사용)
    decode_responses=True                       # Redis 응답을 바이트가 아닌 문자열(str)로 디코딩
)

def consume_queue():
    queue_name = os.getenv("REDIS_QUEUE_NAME", "parse:queue:group")
    print(f"Worker 시작: queue={queue_name} 대기 중...")

    while True:
        # Redis에서 "queue:material:group" 큐에 작업이 들어올 때까지 대기 (blocking)
        # brpop는 ("키이름", "꺼낸값") 튜플 반환. 키이름은 사용하지 않으므로 _로 무시 
        _, payload_json = r.brpop(queue_name) 

        # JSON 문자열을 파이썬 dict로 변환
        payload = json.loads(payload_json)

        # payload 안에 들어있는 작업 데이터 꺼내기
        job_id = payload["jobId"]                 # 작업 식별자
        file_url = payload["fileUrl"]             # 다운로드할 파일 경로(URL)
        group_no = payload["groupNo"]             # 그룹 ID (교사/학생 그룹 구분용)
        difficulty = payload["difficulty"]        # 난이도 정보
        material_no = payload["dailyStudyMaterialNo"]  # 학습 자료 번호

        print(f"[작업 수신] jobId={job_id}, file={file_url}")

        # 1. 파일 다운로드 
        local_path = download_from_object_storage(file_url, material_no)

        # 2. HWP면, HWPX로 변환 및 텍스트 추출 
        ext = os.path.splitext(local_path)[1]
        if ext == ".hwp":
            hwpx_path = convert_hwp_to_hwpx(local_path)
            blocks = extract_blocks_from_hwpx(hwpx_path)
        elif ext == ".hwpx":
            blocks = extract_blocks_from_hwpx(local_path)
        else:
            print(f"[에러] 지원하지 않는 확장자: {ext}")
            continue

        # Spring 서버 콜백 URL (환경변수에서 읽고 없으면 기본값 사용)
        callback_url = os.getenv("SPRING_CALLBACK_URL", "http://localhost:8080/api/worker/callback/materials")

        # 콜백으로 보낼 결과 데이터 구성
        result = {
            "jobId": job_id,             # 작업 ID
            "groupNo": group_no,
            "dailyStudyMaterialNo": material_no,   # 학습자료 ID
            "difficulty": difficulty,    # 난이도
            "content": json.dumps(blocks, ensure_ascii=False)  # ✅ 배열 → 문자열
        }

        # Spring 서버로 HTTP POST 요청 보내기 (결과 전달)
        print(f"[작업 완료] callback_url={callback_url} jobId={job_id} → 콜백 전송")
        response = requests.post(callback_url, json=result)
        print(f"[콜백 응답] {response.status_code} {response.text}")

if __name__ == "__main__":
    consume_queue()