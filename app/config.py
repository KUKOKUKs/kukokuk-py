import os

# 다운로드 디렉토리 설정
# 프로젝트 폴더가 어디에 있든 상관없이, 항상 이 파일 기준 두 단계 상위 디렉토리에 존재하는 downloads 폴더를 사용하도록 설정
"""
__file__ : 현재 파일의 경로 ex) 'C:\\pyserver\\app\\config.py'
os.path.abspath(__file__) : 절대 경로로 변환 
os.path.dirname() : 파일의 디렉토리 부분만 추출 ex) 'C:\\pyserver\\app'
    한 번 더 감싸서 한 단계 상위 디렉토리의 경로를 추출 ex) 'C:\\pyserver'
"""
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DOWNLOAD_DIR = os.path.join(BASE_DIR, "downloads") # 'C:\\pyserver\\downloads'

os.makedirs(DOWNLOAD_DIR, exist_ok=True)  # 다운로드 디렉토리가 없으면 생성

CONVERTED_HWPX_DIR = os.path.join(DOWNLOAD_DIR, "hwp_files")  # 변환된 HWPX 파일을 저장할 디렉토리