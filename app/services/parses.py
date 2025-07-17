import zipfile  # .hwpx 파일은 zip 구조이므로 압축 해제를 위해 사용
from lxml import etree as ET # XML 파싱을 위한 모듈

# HWPX 내부 XML 네임스페이스 정의
ns = {
    'hp': 'http://www.hancom.co.kr/hwpml/2011/paragraph'
}

# hwpx에서 텍스트/표를 추출하는 함수 
# :param hwpx_path: hwpx 파일의 경로
# :return: 추출된 텍스트와 표의 리스트 (dict 형태로 저장되므로 json으로 변환 가능)
def extract_blocks_from_hwpx(hwpx_path) -> list:
    blocks = []

    # 1. .hwpx 파일을 zip처럼 열기 
    with zipfile.ZipFile(hwpx_path, 'r') as zipf: #'r'은 읽기모드 
        # 2. 본문 내용이 들어있는 Contents 폴더 내의 section0.xml 읽기
        with zipf.open('Contents/section0.xml') as section_file:
            tree = ET.parse(section_file) # XML을 파싱 
            print(tree)
            root = tree.getroot() # 최상위 루트 엘리먼트 가져오기 

            # 텍스트 추출에서 제외해야할 문단인지 판단하는 함수 
            def should_skip_paragraph(elem):
                # 표 안에 들어 있는 경우-> 이미 표로 추출되므로 중복 추출 방지 
                for parent in elem.iterancestors():  # iterancestors는 상위노드를 거슬러 올라감 
                    if parent.tag == f"{{{ns['hp']}}}tbl":
                        return True
            
                for child in elem.iter():
                     # 자식 중에 표를 포함한 경우 (P태그가 표를 감싼 경우)
                    if child.tag == f"{{{ns['hp']}}}tbl":
                        return True
                    # 자식 중에 P태그가 또 존재하는 경우 (껍데기 태그이므로 추출 제외) 
                    elif child.tag == f"{{{ns['hp']}}}p" and child != elem:
                        return True
                        
                return False  # 위 조건에 모두 해당 안 되면 사용 가능한 문단

            # 제목 문단인지 판단하는 함수 
            # <hp:p> 안에 첫번째 <hp:run>이 이미지고 두번째 <hp:run>이 텍스트면 제목 문단으로 판단 
            def guess_paragraph_type_by_image(elem):
                runs = list(elem.findall(f"./{{{ns['hp']}}}run")) # <hp:run> 태그 추출 (findall은 iter과 다르게 직계 자식만 탐색) 
                if not runs or len(runs) < 2: # <hp:run>이 없거나 1개뿐이면, paragraph로 처리 
                    return "paragraph"  # 텍스트만 있거나 한 줄짜리
            
                # 첫 run에 이미지 포함 + 두 번째 run에 텍스트 있으면 title로 추정
                has_image = runs[0].find(f"./{{{ns['hp']}}}pic") is not None # 첫 run에 <hp:pic>가 있는지 확인
                has_text_after = runs[1].find(f"./{{{ns['hp']}}}t") is not None # 두번째 run에 <hp:t>가 있는지 확인 
            
                if has_image and has_text_after:
                    return "title"
                
                return "paragraph"

            # 3. 문서 안에 있는 모든 요소(태그)를 반복하며 순회
            for elem in root.iter():
                """
                elem.tag가 반환하는 문자열은 "{http://www.hancom.co.kr/hwpml/2011/paragraph}p" 형식 
                """
                # 1. 표 추출 
                if elem.tag == f"{{{ns['hp']}}}tbl": # <hp:tbl> 표 태그면 
                    table = []
                    for row in elem.iter(f"{{{ns['hp']}}}tr"): # <ht:tr> 하나의 행 태그 
                        row_data = []
                        for cell in row.iter(f"{{{ns['hp']}}}tc"): # <ht:tc> 하나의 셀 태그 
                            cell_text = ""
                            for t in cell.iter(f"{{{ns['hp']}}}t"): # <hp:t> 텍스트 태그 추출해서 
                                cell_text += t.text or ""
                            row_data.append(cell_text.strip()) # 하나의 행에 저장 예 : ['촉감 표현', '끈적거리고']
                        table.append(row_data) # 한 행을 table 리스트에 저장 
                    blocks.append({"type": "table", "content": table})
                #  2. 텍스트 단락 추출
                # <hp:p> 태그를 찾아서 그 내부의 <hp:t>를 찾아 추출 
                elif elem.tag == f"{{{ns['hp']}}}p" and not should_skip_paragraph(elem): # <hp:p> 태그이고, 표내부의 태그가 아니면
                    paragraph_text = ""
                    for t in elem.iter(f"{{{ns['hp']}}}t"): # <hp:t> 텍스트 태그 추출
                        paragraph_text += t.text or ""
                        paragraph_text += " "
                    if paragraph_text.strip():  # 공백 제외하고 내용이 있으면 
                        block_type = guess_paragraph_type_by_image(elem) # 문단의 타입을 결정 (paragraph, title)
                        # 만약 문단의 타입이 title이면, 스타일 정보까지 저장 
                        # 이유 -> 제목이 두줄이상일 경우 첫줄만 제목으로 인식됨
                        # 제목 뒤에 나오는 문단이 제목 문단과 스타일이 같으면, 제목으로 인식되도록 구현 
                        if block_type == "title":
                            title_style = None
                            # p 안에서 t를 감싼 r태그를 찾는다
                            # <hp:run charPrIDRef="26"><hp:t>이야기를 읽고</hp:t></hp:run> 형식으로 스타일이 저장되어 있기 때문 
                            for run in elem.iter(f"{{{ns['hp']}}}run"):
                                for trun in run.iter(f"{{{ns['hp']}}}t"): ### 수정 해보자 
                                    title_style = run.attrib
                            # 타입이 title일때, block에 스타일정보도 함께 저장 
                            blocks.append({
                                "type": block_type, 
                                "content": paragraph_text.strip(),
                                "title_style" : title_style
                            })
                        # 만약 문단의 타입이 paragraph면
                        elif block_type == "paragraph":
                            # 앞문단이 title이면, 스타일을 비교해서 같으면 제목으로 취급 
                            if blocks and blocks[-1]["type"] == "title":
                                curr_style = None
                                prev_style = blocks[-1]["title_style"] or {}
                                # p 안에서 t를 감싼 run태그를 찾아 현재 문단의 스타일 저장 
                                for run in elem.iter(f"{{{ns['hp']}}}run"):
                                    for trun in run.iter(f"{{{ns['hp']}}}t"): ### 수정 해보자 
                                        curr_style = run.attrib
                                # 현재 문단의 스타일이 앞 제목 문단의 스타일과 같으면
                                if curr_style and "charPrIDRef" in curr_style and "charPrIDRef" in prev_style:
                                    if curr_style["charPrIDRef"] == prev_style["charPrIDRef"]:
                                        # 앞 제목문단의 content에 텍스트 추가 
                                        blocks[-1]["content"] = blocks[-1]["content"] + " " + paragraph_text.strip()
                                    else:
                                         blocks.append({"type": block_type, "content": paragraph_text.strip()})
                            else : 
                                blocks.append({"type": block_type, "content": paragraph_text.strip()})
    return blocks