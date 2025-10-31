# 🧠 Kukokuk Python Worker

국어국 AI 학습자료 전처리 파이프라인  
(Spring 서버와 Redis 기반 비동기 학습자료 파싱 워커)

---

## 🧩 개요
이 워커는 Spring 서버에서 Redis Queue로 전달된 학습자료를 비동기적으로 파싱하고,  
텍스트를 추출해 콜백 API로 전달하는 백엔드 워커 서비스입니다.

---

## 🚀 주요 역할

| 워커 | Redis Queue | 콜백 URL | 설명 |
|------|--------------|-----------|------|
| **Group Worker** | `queue:material:group` | `/api/worker/callback/materials` | 교사/그룹 업로드 자료 파싱 |
| **Admin Worker** | `queue:material:admin` | `/api/worker/callback/materials/admin` | 관리자 업로드 자료 파싱 |

---

## ⚙️ 빠른 실행

```bash
# Redis 실행
docker run -d -p 6379:6379 --name redis redis:7

# 그룹 워커 실행
docker run --rm -it --env-file env/group.env python-worker:latest

# 관리자 워커 실행
docker run --rm -it --env-file env/admin.env python-worker:latest
