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
    """
    그룹용 / 관리자용 통합 워커 (HWPX 전용)
    --------------------------------------
    환경변수로 구분:
      - REDIS_QUEUE_NAME        : Redis 큐 이름 (예: queue:material:group / queue:material:admin)
      - SPRING_CALLBACK_URL     : 성공 콜백 URL
      - SPRING_FAIL_CALLBACK_URL: 실패 콜백 URL
      - WORKER_TYPE             : "GROUP" 또는 "ADMIN"
    --------------------------------------
    StudyMaterialJobPayload 구조:
        {
          "jobId": "admin:material:123",
          "fileUrl": "...",
          "groupNo": 12,
          "difficulty": 2,
          "dailyStudyMaterialNo": 33,
          "school": "서울초등학교",
          "grade": 3
        }
    """

    queue_name = os.getenv("REDIS_QUEUE_NAME", "parse:queue:group")
    callback_url = os.getenv("SPRING_CALLBACK_URL", "http://localhost:8080/api/worker/callback/materials") #/admin 붙이면 어드민 콜백 
    worker_type = os.getenv("WORKER_TYPE", "GROUP").upper()

    # fail콜백은 추후 구현 
    fail_callback_url = os.getenv("SPRING_FAIL_CALLBACK_URL", "http://localhost:8080/api/worker/callback/materials/fail")
    
    print(f"🚀 Worker 시작 ({worker_type} 모드) | queue={queue_name}")

    while True:
        # Redis에서 "queue:material:group" 큐에 작업이 들어올 때까지 대기 (blocking)
        # brpop는 ("키이름", "꺼낸값") 튜플 반환. 키이름은 사용하지 않으므로 _로 무시 
        _, payload_json = r.brpop(queue_name) 

        # JSON 문자열을 파이썬 dict로 변환
        payload = json.loads(payload_json)

        # payload 안에 들어있는 작업 데이터 꺼내기
        job_id = payload.get("jobId") # 작업 식별자
        file_url = payload.get("fileUrl") # 다운로드할 파일 경로(URL)
        group_no = payload.get("groupNo") # 그룹 ID (교사/학생 그룹 구분용)
        difficulty = payload.get("difficulty") # 난이도 정보
        material_no = payload.get("dailyStudyMaterialNo")  # 학습 자료 번호
        school = payload.get("school")
        grade = payload.get("grade")

        print(f"[작업 수신] jobId={job_id}, file={file_url}")

        # 1. 파일 다운로드 
        local_path = download_from_object_storage(file_url, material_no)
        
        # 2. 확장자 검사 (HWPX만 허용)
        ext = os.path.splitext(local_path)[1].lower()
        if ext != ".hwpx":
            raise ValueError(f"❌ 지원하지 않는 확장자: {ext}. 현재 워커는 .hwpx 파일만 처리합니다.")

        # 3. HWPX 파일 파싱
        blocks = extract_blocks_from_hwpx(local_path)

        # 콜백으로 보낼 결과 데이터 구성
        result = {
            "jobId": job_id,             # 작업 ID
            "dailyStudyMaterialNo": material_no,   # 학습자료 ID
            "groupNo": group_no,
            "difficulty": difficulty,    # 난이도
            "content": json.dumps(blocks, ensure_ascii=False),  # ✅ 배열 → 문자열
            "school": school,
            "grade": grade
        }

        # Spring 서버로 HTTP POST 요청 보내기 (결과 전달)
        print(f"[작업 완료] callback_url={callback_url} jobId={job_id} → 콜백 전송")
        response = requests.post(callback_url, json=result)
        print(f"[콜백 응답] {response.status_code} {response.text}")

if __name__ == "__main__":
    consume_queue()