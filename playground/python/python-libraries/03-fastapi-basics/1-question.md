# python/python-libraries/03 — FastAPI 기본 — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 스크립트 마지막 두 섹션의 출력 꼴 (예측)

```python
# 질문용 발췌 — 원본 스크립트의 끝부분
print("=== 자동 문서화 ===")
print("Swagger UI:  http://localhost:8000/docs")
print("ReDoc:       http://localhost:8000/redoc")
print("OpenAPI JSON: http://localhost:8000/openapi.json")

print()
print("=== 실행 방법 ===")
print("pip install fastapi uvicorn")
print("uvicorn main:app --reload --port 8000")
```

- 이 부분이 찍는 줄을 차례대로 적으면 어떻게 되나?
- 다른 섹션들과 달리 「=== 자동 문서화 ===」 바로 다음에 빈 줄이 없는 까닭은 무엇인가?

### 2. `/items?limit=12&q=1` 요청의 응답 (예측)

```python
# 질문용 발췌
@app.get("/items")
async def list_items(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=10, le=100),
    q: Optional[str] = Query(default=None, min_length=1, max_length=50)
):
    items = [{"id": i, "name": f"Item {i}"} for i in range(skip, skip + limit)]
    if q:
        items = [item for item in items if q.lower() in item["name"].lower()]
    return {"items": items, "total": len(items)}
```

- `GET /items?limit=12&q=1` 의 응답 JSON 은 무엇인가?
- 여기서 `total` 은 무엇을 센 수인가?

### 3. `ItemCreate` 에 두 가지 본문을 보내면 (예측)

```python
# 질문용 발췌
class ItemCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    price: float = Field(..., gt=0)
    description: Optional[str] = Field(None, max_length=500)
    tags: list[str] = Field(default_factory=list)
```

- 본문 `{"name": "펜", "price": 1.5}` 를 보내면 `item.description` 과 `item.tags` 는 각각 무엇인가?
- 본문 `{"name": "펜", "price": 0}` 을 보내면 핸들러 `create_item` 은 불리나?

### 4. 타입 힌트만 적었는데 검증 · 문서화가 되는 까닭 (왜)

- 파이썬은 타입 힌트를 실행 중에 검사하지 않는데, `get_user(user_id: int)` 에서 `/users/abc` 가 거부되는 까닭은 무엇인가?
- 같은 힌트가 `/docs` 문서에도 나타나는 까닭은 무엇인가?

### 5. `Path(...)` · `Field(...)` 의 `...` 이 필수를 뜻하는 까닭 (왜)

- `...` 은 파이썬에서 어떤 값이고, 왜 FastAPI 에서 「필수」 표시가 될 수 있나?

### 6. `skip` 과 `limit` 에 음수를 넣으면 (경계)

- 문제 2 의 `list_items` 에 `?limit=-3` 을 보내면 검사를 통과하나, 통과하면 응답 목록은 어떻게 되나?
- `?skip=-1` 은 어떻게 되나?

### 7. `response_model` 이 걸러 내는 범위 (경계)

- `response_model=ItemResponse` 인 POST 핸들러가 돌려준 `dict` 에 `ItemResponse` 에 없는 키 `"secret"` 이 섞여 있으면 응답에는 어떻게 나가나?

### 8. REST 메서드 · 데코레이터 · 상태 코드 (연결)

- 예제의 GET · POST · PUT · DELETE 네 데코레이터는 각각 자원에 어떤 일을 하는 자리이고, 그중 `status_code` 를 바꾼 둘은 왜 그 코드인가?

### 9. `dataclass` 와 `BaseModel` (연결)

- 정답 코드가 import 해 둔 `@dataclass` 로 `ItemCreate` 를 만들면 `price: float` 칸에 글자가 들어오는 것을 막을 수 있나?

## 실습

### 실습 1. FastAPI 앱의 뼈대를 섹션별로 출력하는 시연 스크립트

**만들 것** — FastAPI 앱의 핵심 코드(앱 생성 · 라우트 · Path · Query · Pydantic 모델 · POST/PUT/DELETE · 문서 주소 · 실행 방법)를 섹션 헤더와 함께 문자열로 출력하는 스크립트.

**준비물** — 파이썬 3 만 있으면 된다. 이 스크립트는 FastAPI 를 실제로 띄우지 않고 FastAPI 코드를 문자열로 찍어 보이는 흉내다. 출력한 코드를 실제로 띄워 보려면 `fastapi` 와 `uvicorn` 이 필요하다.

**요구 조건**

1단계 — 앱 생성
1. 「FastAPI 앱 기본 구조」 섹션에서 `FastAPI` 앱 `app` 을 `title="My API"` · `description="학습용 API"` · `version="1.0.0"` 으로 만드는 코드를 출력한다.

2단계 — 기본 라우트
2. `GET /` 가 `{"message": "Hello, FastAPI!"}` 를, `GET /health` 가 `{"status": "healthy"}` 를 돌려주는 `async` 핸들러 `root` · `health_check` 를 출력한다.

3단계 — Path 파라미터
3. `GET /users/{user_id}` 핸들러 `get_user` 가 `user_id` 를 `int` 로 받아 `{"user_id": …, "name": "User <id>"}` 를 돌려준다.
4. `GET /items/{item_id}` 핸들러 `get_item` 이 `Path` 로 `item_id` 를 필수 · `title="Item ID"` · 1 이상 10000 이하로 검사하고 `{"item_id": …}` 를 돌려준다.

4단계 — Query 파라미터
5. `GET /items` 핸들러 `list_items` 가 `skip`(기본 0, 0 이상) · `limit`(기본 10, 100 이하) · `q`(선택, 기본 `None`, 길이 1~50)를 `Query` 로 받는다.
6. `range(skip, skip + limit)` 로 `{"id": i, "name": "Item i"}` 목록을 만들고, `q` 가 있으면 대소문자를 무시하고 이름에 `q` 가 든 것만 남긴 뒤 `{"items": …, "total": 남은 개수}` 를 돌려준다.

5단계 — Pydantic 모델
7. 요청 모델 `ItemCreate` 를 출력한다 — `name`(필수, 길이 1~100) · `price`(필수, 0 초과) · `description`(선택, 최대 500) · `tags`(빠지면 새 빈 리스트).
8. 응답 모델 `ItemResponse` 를 출력한다 — `id` · `name` · `price` · `description` · `tags` · `created_at`(`datetime`) 필드와 `from_attributes = True` 설정.

6단계 — POST · PUT · DELETE
9. `POST /items` 핸들러 `create_item` 이 `response_model=ItemResponse` · `status_code=201` 로 등록되고, 받은 `item` 의 필드와 `id` 1 · `created_at` 현재 시각을 담은 `dict` 를 돌려준다.
10. `PUT /items/{item_id}` 핸들러 `update_item` 이 `item_id` 와 `item.model_dump()` 를 합친 `dict` 를 돌려준다.
11. `DELETE /items/{item_id}` 핸들러 `delete_item` 이 `status_code=204` 로 등록되고 `None` 을 돌려준다.

7단계 — 문서와 실행
12. 「자동 문서화」 섹션에서 Swagger UI · ReDoc · OpenAPI JSON 세 주소를 한 줄씩 출력한다.
13. 빈 줄 하나를 찍은 뒤 「실행 방법」 섹션에서 설치 명령과 `uvicorn` 실행 명령을 한 줄씩 출력한다.

**시작 코드**

```python
# [주요 라이브러리] FastAPI 기본 — 연습 파일
# FastAPI 앱 구조 시연 (실행: uvicorn main:app --reload)
from dataclasses import dataclass, field
from typing import Optional
import json

print("=== FastAPI 앱 기본 구조 ===")
print("""
from fastapi import FastAPI, Path, Query
from pydantic import BaseModel

# TODO: app = FastAPI(...) — title · description · version
""")

print("=== 기본 라우트 ===")
print("""
# TODO: GET / 핸들러 root

# TODO: GET /health 핸들러 health_check
""")

print("=== Path 파라미터 ===")
print("""
# TODO: GET /users/{user_id} 핸들러 get_user — user_id: int

# Path()로 상세 검증
# TODO: GET /items/{item_id} 핸들러 get_item — Path(필수, title, 범위)
""")

print("=== Query 파라미터 ===")
print("""
# /items?skip=0&limit=10&q=search
# TODO: GET /items 핸들러 list_items — skip · limit · q 를 Query 로
#       목록 만들기 → q 로 거르기 → {"items": ..., "total": ...}
""")

print("=== Pydantic 모델 (Request/Response) ===")
print("""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

# Request Body 모델
# TODO: class ItemCreate(BaseModel) — name · price · description · tags 와 Field 조건

# Response 모델
# TODO: class ItemResponse(BaseModel) — 여섯 필드 + from_attributes 설정
""")

print("=== POST 요청 처리 ===")
print("""
# TODO: POST /items — response_model · status_code, 핸들러 create_item

# TODO: PUT /items/{item_id} — 핸들러 update_item, model_dump 로 합치기

# TODO: DELETE /items/{item_id} — status_code, 핸들러 delete_item
""")

print("=== 자동 문서화 ===")
# TODO: Swagger UI · ReDoc · OpenAPI JSON 주소를 한 줄씩 출력

# TODO: 빈 줄 하나
print("=== 실행 방법 ===")
# TODO: 설치 명령과 uvicorn 실행 명령
```

**확인 방법** — `python fastapi-basics.py` 로 돌려 섹션 헤더 차례 · 빈 줄 위치 · 각 코드 조각이 요구 조건과 맞는지 본다. 더 나아가 출력된 코드를 `main.py` 로 모아 `uvicorn main:app --reload --port 8000` 으로 띄우고 `/docs` 에서 엔드포인트를 눌러 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
