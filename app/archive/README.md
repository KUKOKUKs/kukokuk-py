


---

## 🗂️ **`/archive/README.md` (기존 코드 기록용)**

```markdown
# 🗃️ Kukokuk Python Worker Archive

이 폴더에는 과거 버전의 Kukokuk 파이썬 워커 코드가 보관되어 있습니다.

---

## 🔁 Legacy 구조 개요

| 항목 | 설명 |
|------|------|
| 프레임워크 | FastAPI 기반 서버 |
| 처리 방식 | Spring → FastAPI 직접 호출 (Queue 미사용) |
| 주요 기능 | Edunet URL 다운로드 + `.hwp → .hwpx` 변환 |
| 환경 제약 | Windows 전용 (win32com.client 의존) |

---

## 📦 주요 파일
| 파일 | 역할 |
|------|------|
| `worker_material_admin_old.py` | Edunet URL 파서 |
| `worker_material_group_old.py` | 그룹 학습자료용 워커 |
| `converter.py` | win32com 기반 HWP 변환 |
| `README.md` | 아카이브 코드 설명 |

---

## 📚 보관 이유
- 과거 Edunet 기반 수집 로직 참고용  
- HWP 변환 모듈(`win32com.client`) 재활용 가능성  
- 윈도우 환경에서 로컬 분석 시 활용 가능  

현재 운영 버전은 `/app/worker_material_unified.py` 기준으로 유지됩니다.

---

# 📄 HWP Parser API

에듀넷 링크에서 HWP 파일을 자동으로 다운로드 받아, HWPX로 변환한 후 내부 텍스트를 JSON 형태로 파싱해주는 FastAPI 기반의 파이썬 서버입니다.  
이 서버는 학습자료 수집 및 자동화 파이프라인의 일부로 사용되며, Spring 서버와 연동됩니다.

---

## ✅ 주요 기능

- 에듀넷 링크로부터 HWP 파일 다운로드
- HWP → HWPX 포맷 자동 변환 (한글 오토메이션 사용)
- HWPX 내부 텍스트 블록(JSON) 추출
- 제목, 학년, 학교, 키워드 등 메타데이터 파싱
- JSON 형태로 Spring 서버에 응답

---

## 🛠️ 기술 스택

- Python 3.9+
- FastAPI
- Uvicorn
- pywin32 (한글 오토메이션)
- xml.etree.ElementTree (HWPX 파싱)
- requests, BeautifulSoup (에듀넷 웹 파싱)

---

## 🚀 실행 방법

### 1. 가상환경 생성 및 패키지 설치

```bash
conda create -n hwp_env python=3.9
conda activate hwp_env

pip install -r requirements.txt
```

### 2. 보안 모듈 등록 (한글 자동화용, Windows 전용)
한글 자동화를 위해 보안모듈 DLL 등록이 필요합니다.

####📍 등록 방법
보안모듈(Automation) 폴더의 .dll 파일 경로를 확인하세요.

Windows 명령 프롬프트를 관리자 권한으로 열고 다음 명령어를 실행합니다:

```bash
regsvr32 "C:\경로\HncShellExt2.dll"
```
등록이 성공하면 "DllRegisterServer 성공" 메시지가 표시됩니다.

⚠️ 이 작업은 사용자 PC마다 한 번씩 필요합니다. 자동화된 테스트나 GitHub 액션에서는 사용할 수 없습니다.

### 3。 서버 실행하기 
```bash
 uvicorn app.main:app --reload       
```

## 📡 API 명세
POST /edunet/parse-materials
에듀넷 링크를 전달하면 학습자료를 파싱해 JSON 형태로 반환합니다.

### ✅ Request Body 예시 
```json
{
  "url": "https://www.edunet.net/…"
}
```

### ✅ Response 예시
```json
{
  "status": 200,
  "message": "HWP 파일을 성공적으로 파싱했습니다.",
  "data": {
    "content": "[{\"type\":\"title\",\"content\":\"1. 환경\"}, …]",
    "school": "중",
    "grade": "2",
    "title": "환경보호에 대해 알아보자",
    "keywords": "[\"환경\", \"지속가능\"]",
    "sourceFilename": "환경보호.hwpx"
  }
}
```
## 🔒 주의사항
- 이 서버는 Windows 환경에서만 동작합니다 (HWP 자동화 COM 객체 때문).

- HWP 2020 이상 버전이 설치되어 있어야 작동합니다.

- HWP 파일은 반드시 한글 프로그램이 설치된 PC에서만 변환 가능하며, Linux/macOS에서는 동작하지 않습니다.

## 📦 추후 개선 계획
- Docker 환경 지원은 한글 오토메이션 제약으로 어려움이 있음 (보안모듈 COM 객체 윈도우 전용)

- 향후 HWP 대신 HWPX 소스만 제공받는 구조로 개선 고려
