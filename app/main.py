#FastAPI의 엔트리포인트 

from fastapi import FastAPI

from app.models.schema import parseMaterialsRequest
from app.services.downloader import download_hwp_from_edunet
from app.services.converter import convert_hwp_to_hwpx 
from app.services.parses import extract_blocks_from_hwpx

app = FastAPI()

"""
에듀넷 URL을 받아 해당 파일을 파싱하는 엔드포인트
:param item: parseMaterialsRequest 모델 인스턴스
:return: 성공 메시지
"""
@app.post('/edunet/parse-materials')
def parse_materials(item: parseMaterialsRequest):
    file_url = item.file_url
    hwp_path = download_hwp_from_edunet(file_url)  # HWP 파일 다운로드
    hwpx_path = convert_hwp_to_hwpx(hwp_path)  # HWP 파일을 HWPX로 변환
    blocks = extract_blocks_from_hwpx(hwpx_path)  # HWPX 파일에서 텍스트 추출
    
    return {
        "message": "HWP 파일을 성공적으로 파싱했습니다.",
        "blocks": blocks  # 추출된 텍스트와 표의 리스트 반환
    }
