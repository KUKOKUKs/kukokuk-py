from pydantic import BaseModel

# FastAPI에서 요청 본문을 처리하려면 Pydantic 모델을 정의하고, 이를 경로함수의 
# 매개변수로 지정하면 된다 
# Pydantic은 데이터 검증 라이브러리로, 입력데이터를 자동으로 검증하고 변환해준다 

class parseMaterialsRequest(BaseModel):
    file_url : str

