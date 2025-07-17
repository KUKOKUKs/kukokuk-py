# hwp -> hwpx 변환 (pywin32 활용) 
import os # 파일 경로와 폴더 탐색을 위해 사용
import win32com.client  # 파이썬으로 엑셀 뿐만 아니라 윈도우를 운영체제로 삼는 다른 모든 응용프로그램을 컨트롤할 수 있는 모
import pythoncom

from app.config import CONVERTED_HWPX_DIR  # 꼭 import 해야 함


# hwp파일을 hwpx로 변환하는 함수 
# :param hwp_path: 변환할 hwp 파일의 경로 (예: C:/downloads/sample.hwp)
# :return: 변환된 hwpx 파일의 경로
def convert_hwp_to_hwpx(hwp_path) -> str:
    pythoncom.CoInitialize() # COM 초기화 (필수)

    # 한글 프로그램을 파이썬에서 제어할 수 있도록 연결 (한글 객체 생성)
    hwp = win32com.client.Dispatch("HWPFrame.HwpObject")

    # 보안 모듈 등록 (이거 없으면 저장 시 오류 발생 가능)
    hwp.RegisterModule("FilePathCheckDLL", "FilePathCheckerModule")  # 보안팝업 자동클릭

    # 출력 파일 전체 경로 구성 (예: C:/downloads/hwp_files/sample.hwpx)
    output_path = os.path.join(CONVERTED_HWPX_DIR, os.path.basename(hwp_path).replace('.hwp', '.hwpx'))

    print(f"[변환 시작] {hwp_path}")  # 변환 시작 로그 출력

    # 한글 파일 열기
    hwp.Open(hwp_path, "", "HWP")  # (파일경로, 포맷, 문서형식)

    # 현재 열려있는 문서를 hwpx 형식으로 지정된 경로에 저장
    hwp.SaveAs(output_path,"HWPX", "") # (파일경로, 저장형식, Reserved)

    # 한글 종료 (닫지 않으면 계속 프로세스가 남아서 충돌 날 수 있음)
    hwp.Quit()
    pythoncom.CoUninitialize() # COM 해제 (필수)

    print(f"[변환 완료] {output_path}")  # 완료 로그 출력
    

    return output_path