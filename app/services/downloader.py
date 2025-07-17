# hwp 다운호드 후 경로 반환 
# selenium의 webdriver를 사용하기 위한 import
from selenium import webdriver
from selenium.webdriver.common.by import By

# selenium으로 키를 조작하기 위한 import
from selenium.webdriver.common.keys import Keys

# 페이지 로딩을 기다리는데에 사용할 time 모듈 import
import time
import os

from app.config import DOWNLOAD_DIR

# 에듀넷 url 페이지에서 HWP 파일을 다운로드하는 함수
# :param file_url: 에듀넷에서 HWP를 제공하는 페이지의 URL
# :return: 다운로드된 HWP 파일의 경로
def download_hwp_from_edunet(file_url: str) -> str:

    # Chrome 옵션에서 다운로드 경로 설정 
    options = webdriver.ChromeOptions()
    options.add_experimental_option("prefs", {
        "download.default_directory" : DOWNLOAD_DIR
    })
    options.add_argument("headless")  # 브라우저를 실제로 띄우지 않고 백그라운드에서 실행

    # 크롬드라이버 실행
    driver = webdriver.Chrome(options = options) 

    #크롬 드라이버에 url 주소 넣고 실행
    driver.get(file_url)

    # 페이지가 완전히 로딩되도록 3초동안 기다림
    time.sleep(3)

    # pdf 엘리먼트 찾기
    hwp_element = driver.find_element(By.CSS_SELECTOR, '.add_btn_view .btn_hwp+a')

    # PDF 다운로드 전 downloads 폴더의 파일 목록 저장
    before = set(os.listdir(DOWNLOAD_DIR))

    # 클릭해서 pdf 다운로드하기
    hwp_element.click()

    # 다운로드가 완료될 때까지 기다린 후, 새로 다운로드된 hwp 파일의 경로를 반환
    path = wait_for_new_hwp(DOWNLOAD_DIR, before)

    return path

# hwp 파일이 다운로드될 때까지 기다렸다가, 새로 다운로드된 hwp 파일의 경로를 반환하는 함수
# :param download_dir: 다운로드 디렉토리 경로
# :param before_files: 다운로드 전의 파일 목록
# :param timeout: 최대 대기 시간 (초)
# :return: 새로 다운로드된 hwp 파일의 경로
def wait_for_new_hwp(download_dir, before_files, timeout=15) -> str:
    """
    기존 파일 목록과 비교하여, 새롭게 생긴 hwp 파일을 반환한다.
    """
    for _ in range(timeout): # 1초간격으로 최대 timeout번까지 시도 
        after_files = set(os.listdir(download_dir))
        new_files = after_files - before_files
        # new_files에서 hwp로 끝나는 파일만 새 리스트에 담는다 
        new_pdfs = [f for f in new_files if f.lower().endswith('.hwp')]

        if new_pdfs:
            # 다운로드 경로 + 파일명 합쳐서 전체 경로 반환
            return os.path.join(download_dir, new_pdfs[0])
        time.sleep(1)
     # 15초내에 파일이 안생기면 에러 발생 
    raise TimeoutError("hwp 다운로드가 완료되지 않았습니다.")