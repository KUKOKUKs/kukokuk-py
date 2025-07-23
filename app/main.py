#FastAPI의 엔트리포인트 

import json
import os
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
def parse_materials(item: parseMaterialsRequest): # parseMaterialsRequest 모델을 사용하여 요청 본문을 받음
    url = item.url
    download_return_dict = download_hwp_from_edunet(url)  # HWP 파일 다운로드
    hwp_path = download_return_dict['path']  # 다운로드된 HWP 파일의 경로
    hwpx_path = convert_hwp_to_hwpx(hwp_path)  # HWP 파일을 HWPX로 변환
    blocks = extract_blocks_from_hwpx(hwpx_path)  # HWPX 파일에서 텍스트 추출

    source_filename = os.path.basename(hwpx_path)  # HWPX 파일의 이름 추출

    blocks_string = json.dumps(blocks, ensure_ascii=False)  # blocks를 JSON 문자열로 변환
    # json.dumps()는 모든 문자열을 ASCII 문자로 이스케이프 처리하므로 ensure_ascii=False로 한글 그대로 출력되도록 설정 
    keywords_string = json.dumps( download_return_dict['keywords'], ensure_ascii=False)
    
    return {
        "status" : 200,
        "message": "HWP 파일을 성공적으로 파싱했습니다.",
        "data" : {
            "content": blocks_string,  # 추출된 블록 데이터
            "school": download_return_dict['school'],  # 학교 정보
            "grade": download_return_dict['grade'],  # 학년 정보
            "title": download_return_dict['title'],  # 제목 정보
            "keywords": keywords_string,  # 키워드 정보
            "sourceFilename": source_filename  # HWPX 파일의 이름
        }
    }
