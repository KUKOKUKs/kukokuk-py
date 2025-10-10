# hwp 다운호드 후 경로 반환 
# selenium의 webdriver를 사용하기 위한 import
import re
from selenium import webdriver
from selenium.webdriver.common.by import By

# selenium으로 키를 조작하기 위한 import
from selenium.webdriver.common.keys import Keys

# 페이지 로딩을 기다리는데에 사용할 time 모듈 import
import time
import os

import requests

from config import DOWNLOAD_DIR

# 에듀넷 url 페이지에서 HWP 파일을 다운로드하는 함수
# :param file_url: 에듀넷에서 HWP를 제공하는 페이지의 URL
# :return: 응답을 반환할때 필요한 정보를 담은 dict 
# {"path": path, "school": school, "grade": grade, "title": title, "keywords": keywords }
def download_hwp_from_edunet(file_url: str) -> dict:

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
    # school 정보 추출
    school = driver.find_element(By.CSS_SELECTOR, '.filter_container .flex_between .tab_filter_container button.active').text
    if (school == "초등학교") : school = "초등" # 초로 통일
    elif (school == "중학교") : school = "중등" # 중으로 통일
    # 선택된 grade 정보 추출 - radio 버튼에서 선택된 값 가져오기
    grade_radio = driver.find_element(By.CSS_SELECTOR, "input[type='radio'][name='searchContsClsfId']:checked")
    # 선택된 radio의 id를 이용해 이 radio에 연결된 label 엘리먼트를 찾아서 텍스트 저장
    grade_radio_id = grade_radio.get_attribute("id")
    grade_all = driver.find_element(By.CSS_SELECTOR, f"label[for='{grade_radio_id}']").text
    # 정규표현식으로 grade에서 숫자만 추출
    grade = int(re.findall(r'\d+', grade_all)[0])  # 숫자만 추출 (리스트 형태로 반환되므로 [0]으로 첫번째 요소 선택)
    # 학습자료의 제목 추출
    title = driver.find_element(By.CSS_SELECTOR, '.title_txt strong').text
    # 학습자료의 키워드 추출
    keyword_elements = driver.find_elements(By.CSS_SELECTOR, '.board_view_desc dd a')
    keywords = [element.text for element in keyword_elements]
    

    print("school : " + school)  # 현재 선택된 학교 이름 출력
    print("grade : " + str(grade))  # 현재 선택된 학년 출력
    print("title : " + title)  # 현재 선택된 학습자료 제목 출력
    print("keywords : " + ", ".join(keywords))  # 현재 선택된 학습자료 키워드 출력

    # PDF 다운로드 전 downloads 폴더의 파일 목록 저장
    before = set(os.listdir(DOWNLOAD_DIR))

    # 클릭해서 pdf 다운로드하기
    hwp_element.click()

    # 다운로드가 완료될 때까지 기다린 후, 새로 다운로드된 hwp 파일의 경로를 반환
    path = wait_for_new_hwp(DOWNLOAD_DIR, before)

    # 보통 파이썬에선 간단한 DTO는 dict로 처리
    return {
        "path": path,  # 다운로드된 HWP 파일의 경로
        "school": school,
        "grade": grade,
        "title": title,
        "keywords": keywords
    }

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


# 교사의 그룹 자료 업로드에서, NHN Object Storage(S3)에 저장된 파일을 가져오는 메소드 
def download_from_object_storage(file_url, material_no):
    """
    NHN Object Storage에서 파일 다운로드
    파일 확장자는 URL에서 추출해서 유지함 (hwp, hwpx 구분)
    """

     # file_url에서 확장자 추출 (.hwp or .hwpx) - 파일 경로(또는 URL)를 이름과 확장자로 분리
    ext = os.path.splitext(file_url)[1]  # ".hwp" 또는 ".hwpx" 반환
    
     # ✅ 안전한 로컬 경로 (Windows에서도 작동) - \pyserver\downloads
    download_dir = os.path.join(os.getcwd(), "downloads")
    os.makedirs(download_dir, exist_ok=True)  # 폴더 없으면 생성

     # 로컬 경로 (material_n 기반 + 확장자 그대로)
    local_path = os.path.join(download_dir, f"{material_no}{ext}")

    # 파일 다운로드
    response = requests.get(file_url, stream=True)  # 스트리밍 다운로드
    response.raise_for_status()  # 실패 시 예외 발생

    with open(local_path, "wb") as f:  # local_path 경로에 파일을 '쓰기 모드(wb: write binary)'로 열기
        for chunk in response.iter_content(chunk_size=8192):  # 응답(response)을 8192바이트 단위로 스트리밍 읽기
            f.write(chunk) # 읽어온 chunk(조각)를 파일에 바로 기록
            
    return local_path # 다 쓴 후 최종 저장된 파일 경로 반환