# python/python-libraries/03 — FastAPI 기본 — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 한 줄짜리 `print` 는 빈 줄을 만들지 않고, `print()` 만 빈 줄 하나를 만든다

**출력**

```text
=== 자동 문서화 ===
Swagger UI:  http://localhost:8000/docs
ReDoc:       http://localhost:8000/redoc
OpenAPI JSON: http://localhost:8000/openapi.json

=== 실행 방법 ===
pip install fastapi uvicorn
uvicorn main:app --reload --port 8000
```

**왜 그런가**
앞 섹션들은 `print("""` 바로 뒤에서 줄을 바꾸는 여러 줄 문자열을 찍으므로, 문자열이 줄바꿈으로 시작해 헤더 다음에 빈 줄이 생긴다.
「자동 문서화」 섹션은 한 줄짜리 문자열을 `print` 로 하나씩 찍으므로 사이에 빈 줄이 없다.
`OpenAPI JSON` 줄과 「실행 방법」 사이의 빈 줄 하나는 인자 없는 `print()` 가 만든 것이다.
근거: 2-summary 「문법 — 형태와 규칙」의 마지막 불릿.

### 2. 걸러진 세 개 — `total` 은 3

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
{"items": [{"id": 1, "name": "Item 1"}, {"id": 10, "name": "Item 10"}, {"id": 11, "name": "Item 11"}], "total": 3}
```

- `skip` 은 빠졌으므로 기본값 0, `limit=12` 는 100 이하라 통과, `q="1"` 은 길이 1 이라 통과한다.
- `range(0, 12)` 로 `Item 0` ~ `Item 11` 열두 개를 만든다.
- 이름에 `"1"` 이 들어간 것은 `Item 1` · `Item 10` · `Item 11` 셋이다.

**왜 그런가**
목록을 먼저 자르고 그 안에서 거르므로 `total` 은 「이 쪽 안에서 걸러지고 남은 개수」다.
전체 자료에서 `q` 에 맞는 개수가 아니다.
근거: 2-summary 「동작 방식 (3)」 · 「어디서 틀리나 4」.

### 3. 빠진 선택 칸은 기본값으로, `price=0` 은 검사에서 막힌다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

- 첫 본문: `item.description` 은 `None`, `item.tags` 는 빈 리스트 `[]` 다.
- 둘째 본문: `price` 가 `gt=0`(0 보다 큼)을 어기므로 검사에서 거부되고, `create_item` 은 불리지 않는다.

**왜 그런가**
`Field(None)` 은 선택이라 빠지면 `None` 이 들어가고, `Field(default_factory=list)` 는 빠지면 새 빈 리스트를 넣는다.
`gt` 는 「이상」이 아니라 「초과」라 0 은 통과하지 못하며, 검사를 통과한 값만 핸들러에 들어간다.
근거: 2-summary 「동작 방식 (4)」.

### 4. 힌트를 읽어 쓰는 쪽이 FastAPI · Pydantic 이라서

파이썬은 힌트를 붙여 둘 뿐 검사하지 않는다.
FastAPI 가 핸들러의 인자 힌트를 읽어, 주소에서 온 글자 `"abc"` 를 `int` 로 바꾸려다 실패하면 오류 응답을 내고 핸들러를 부르지 않는다.
같은 힌트 · `Path` · `Query` · 모델 정보로 OpenAPI 스펙을 만들고, `/docs` 는 그 스펙을 보여 주는 화면이라 문서에도 나타난다.
즉 타입 정보 하나가 검증 · 직렬화 · 문서 세 군데에 쓰인다.
근거: 2-summary 「동작 방식 (2) · (6)」 · 「구현 세부사항 대 언어 보장」 표 첫 줄.

### 5. `...` 은 `Ellipsis` 라는 평범한 값이고, 「필수」는 라이브러리의 약속이다

`...` 은 파이썬 언어의 특수 값 `Ellipsis` 다.
기본값 자리에 놓을 수 있는 값이면서 실제 데이터로는 거의 쓰이지 않으므로, FastAPI · Pydantic 은 「기본값 대신 `...` 이 오면 기본값이 없다 = 반드시 보내야 한다」로 약속해 쓴다.
그래서 기본값을 주면 선택, `...` 을 주면 필수가 된다.
근거: 2-summary 「문법 — 형태와 규칙」 · 「구현 세부사항 대 언어 보장」 표 2~3 줄.

### 6. `limit=-3` 은 통과해 빈 목록, `skip=-1` 은 거부

- `limit` 에는 `le=100` 만 있어 하한이 없으므로 -3 은 검사를 통과한다.
  `range(0, -3)` 은 비어 `{"items": [], "total": 0}` 이 된다.
- `skip` 은 `ge=0` 이라 -1 은 검사에서 거부되고 핸들러가 불리지 않는다.

검사는 적은 조건만 하므로, 하한이 필요하면 `ge` 를 직접 적어야 한다.
근거: 2-summary 「어디서 틀리나 3」.

### 7. 모델에 없는 키는 응답에서 빠진다

`response_model` 을 주면 돌려준 값을 그 모델의 필드로 걸러 직렬화한다.
`"secret"` 은 `ItemResponse` 필드가 아니므로 응답 JSON 에 나가지 않는다.
이 성질로 민감한 필드를 숨길 수 있지만, 넣었는데 안 보이는 원인이 되기도 한다.
근거: 2-summary 「동작 방식 (5)」 · 「어디서 틀리나 5」.

### 8. 조회 · 생성 · 수정 · 삭제 — 생성은 201, 삭제는 204

| 데코레이터 | 자원에 하는 일 | 상태 코드 |
|---|---|---|
| `@app.get` | 조회 (`/items`, `/items/{item_id}`) | 바꾸지 않음 |
| `@app.post` | 생성 (`/items`) | `201` — 새로 만들어졌다 |
| `@app.put` | 수정 (`/items/{item_id}`) | 바꾸지 않음 |
| `@app.delete` | 삭제 (`/items/{item_id}`) | `204` — 본문 없이 끝났다 |

REST 는 자원을 주소로, 할 일을 HTTP 메서드로 나타내고, FastAPI 는 메서드마다 데코레이터를 둔다.
`status_code` 로 성공 응답 코드를 그 일의 뜻에 맞게 바꾼 것이다.
근거: 2-summary 「동작 방식 (5)」 · 「용어 풀이」의 REST.

### 9. 막을 수 없다 — `dataclass` 는 검사하지 않는다

`@dataclass` 는 필드 목록으로 생성자 등을 만들어 줄 뿐, 타입 힌트를 실행 중에 검사하지 않는다.
그래서 `price: float` 에 글자를 넣어도 그대로 들어간다.
값을 검사하는 것은 `BaseModel` 을 상속한 Pydantic 모델이 힌트를 읽어 하는 일이다.
정답 코드가 `dataclass` 를 「시뮬레이션용」으로 import 만 해 두고 실제로는 Pydantic 코드를 문자열로 보여 주는 것도 이 차이 때문이다.
근거: 2-summary 「동작 방식 (4)」 마지막 불릿 · 「구현 세부사항 대 언어 보장」 표 첫 줄.

## 실습 정답

### 실습 1. FastAPI 앱의 뼈대를 섹션별로 출력하는 시연 스크립트

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. 앱 생성 | 첫 `print("""…""")` 안 `app = FastAPI(title=…, description=…, version=…)` |
| 2. 기본 라우트 | `@app.get("/")` `root` · `@app.get("/health")` `health_check` |
| 3. `/users/{user_id}` | `get_user(user_id: int)` |
| 4. `/items/{item_id}` 범위 검사 | `get_item` 의 `Path(..., title="Item ID", ge=1, le=10000)` |
| 5. Query 세 인자 | `list_items` 의 `Query(default=0, ge=0)` · `Query(default=10, le=100)` · `Query(default=None, min_length=1, max_length=50)` |
| 6. 목록 · 거르기 · total | `range(skip, skip + limit)` 목록, `if q:` 거르기, `{"items": items, "total": len(items)}` |
| 7. 요청 모델 | `class ItemCreate(BaseModel)` 와 네 `Field(...)` |
| 8. 응답 모델 | `class ItemResponse(BaseModel)` 와 `class Config: from_attributes = True` |
| 9. POST | `@app.post("/items", response_model=ItemResponse, status_code=201)` `create_item` |
| 10. PUT | `update_item` 의 `{"item_id": item_id, **item.model_dump()}` |
| 11. DELETE | `@app.delete("/items/{item_id}", status_code=204)` `delete_item` → `return None` |
| 12. 문서 주소 | `print("Swagger UI: …")` · `print("ReDoc: …")` · `print("OpenAPI JSON: …")` |
| 13. 빈 줄 · 실행 방법 | `print()` 뒤 `print("pip install fastapi uvicorn")` · `print("uvicorn main:app --reload --port 8000")` |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`python/python-libraries/reference/fastapi-basics.py`

```python
# [주요 라이브러리] FastAPI 기본
# 설명: FastAPI 앱 생성, @app.get/post, Path/Query 파라미터, Pydantic 모델
# 팁: FastAPI는 타입 힌트를 기반으로 자동 검증, 직렬화, 문서화를 수행한다. Path/Query에 기본값을 설정하면 선택적 파라미터, ...을 설정하면 필수 파라미터가 된다. response_model을 설정하면 응답 데이터가 자동으로 필터링/직렬화된다.

# FastAPI 앱 구조 시연 (실행: uvicorn main:app --reload)
# 데이터클래스 데코레이터와 field 헬퍼(시뮬레이션 용도로만 import)
from dataclasses import dataclass, field
# Optional 타입은 None 허용을 표시(파이썬 3.10 이후엔 X | None 권장)
from typing import Optional
# json 모듈은 직렬화 시뮬레이션용
import json

# === Pydantic 모델 시뮬레이션 (실제로는 from pydantic import BaseModel) ===
# 실제 FastAPI 코드와 동일한 구조를 보여주되, 실행 가능하도록 구성

# 섹션 헤더 출력: FastAPI 앱 인스턴스 생성
print("=== FastAPI 앱 기본 구조 ===")
# FastAPI() 생성자에 title/description/version을 주면 OpenAPI 문서에 그대로 반영
print("""
from fastapi import FastAPI, Path, Query
from pydantic import BaseModel

app = FastAPI(
    title="My API",
    description="학습용 API",
    version="1.0.0"
)
""")

# 섹션 헤더 출력: 가장 단순한 GET 라우트
print("=== 기본 라우트 ===")
# @app.get("/")로 루트 핸들러 등록. async/일반 함수 모두 가능
# 반환 dict은 자동으로 JSON 직렬화됨
print("""
@app.get("/")
async def root():
    return {"message": "Hello, FastAPI!"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
""")

# 섹션 헤더 출력: URL 경로 변수(Path 파라미터)
print("=== Path 파라미터 ===")
# {user_id}는 함수 인자로 매핑되며 타입 힌트로 자동 검증/변환
# Path()의 ...은 Ellipsis로 "필수"를 의미. ge/le는 숫자 범위 검증
print("""
@app.get("/users/{user_id}")
async def get_user(user_id: int):  # 자동 타입 검증
    return {"user_id": user_id, "name": f"User {user_id}"}

# Path()로 상세 검증
@app.get("/items/{item_id}")
async def get_item(
    item_id: int = Path(
        ...,              # 필수
        title="Item ID",
        ge=1,             # >= 1
        le=10000          # <= 10000
    )
):
    return {"item_id": item_id}
""")

# 섹션 헤더 출력: 쿼리스트링(Query 파라미터)
print("=== Query 파라미터 ===")
# Query()의 default가 None이면 Optional, 값이 있으면 기본값
# min_length/max_length는 문자열 검증, ge/le는 숫자 검증
print("""
# /items?skip=0&limit=10&q=search
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
""")

# 섹션 헤더 출력: Pydantic으로 요청/응답 스키마 정의
print("=== Pydantic 모델 (Request/Response) ===")
# BaseModel 상속 클래스가 요청 본문/응답 스키마가 됨
# Field(...)로 필수, Field(None)으로 선택, default_factory=list로 빈 리스트 기본값
# Pydantic v2: from_attributes=True가 ORM 모드(예전 orm_mode 대체)
print("""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

# Request Body 모델
class ItemCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    price: float = Field(..., gt=0)
    description: Optional[str] = Field(None, max_length=500)
    tags: list[str] = Field(default_factory=list)

# Response 모델
class ItemResponse(BaseModel):
    id: int
    name: str
    price: float
    description: Optional[str]
    tags: list[str]
    created_at: datetime

    class Config:
        from_attributes = True  # ORM 모드 (Pydantic v2)
""")

# 섹션 헤더 출력: POST/PUT/DELETE 처리
print("=== POST 요청 처리 ===")
# response_model을 지정하면 응답이 해당 스키마로 필터링되어(불필요 필드 제거) 직렬화됨
# status_code로 기본 응답 코드 변경(생성=201, 삭제 후 본문 없음=204)
# item.model_dump()는 Pydantic v2 직렬화 메서드(.dict()는 v1 deprecated)
print("""
@app.post("/items", response_model=ItemResponse, status_code=201)
async def create_item(item: ItemCreate):
    # item은 자동으로 검증된 Pydantic 모델 인스턴스
    new_item = {
        "id": 1,
        "name": item.name,
        "price": item.price,
        "description": item.description,
        "tags": item.tags,
        "created_at": datetime.now()
    }
    return new_item

@app.put("/items/{item_id}")
async def update_item(item_id: int, item: ItemCreate):
    return {"item_id": item_id, **item.model_dump()}

@app.delete("/items/{item_id}", status_code=204)
async def delete_item(item_id: int):
    return None  # 204 No Content
""")

# 섹션 헤더 출력: 자동 생성되는 문서 URL 안내
print("=== 자동 문서화 ===")
# Swagger UI: 시도 가능한 인터랙티브 UI
print("Swagger UI:  http://localhost:8000/docs")
# ReDoc: 읽기 좋은 정적 문서
print("ReDoc:       http://localhost:8000/redoc")
# 원시 OpenAPI 스펙(JSON)
print("OpenAPI JSON: http://localhost:8000/openapi.json")

# 빈 줄 출력으로 섹션 분리
print()
# 섹션 헤더 출력: 실행 방법 안내
print("=== 실행 방법 ===")
# 필수 패키지 설치 안내
print("pip install fastapi uvicorn")
# uvicorn ASGI 서버로 앱 실행. --reload는 개발용 자동 재시작
print("uvicorn main:app --reload --port 8000")
```

**실행 결과** — 원본 예제(`component`)를 실제로 돌린 출력이다. 환경 `Python 3.12.3` · 2026-11-28 · exit 0 · 두 번 돌려 출력이 같았다.

````text
$ python3 -I example.py
=== FastAPI 앱 기본 구조 ===

from fastapi import FastAPI, Path, Query
from pydantic import BaseModel

app = FastAPI(
    title="My API",
    description="학습용 API",
    version="1.0.0"
)

=== 기본 라우트 ===

@app.get("/")
async def root():
    return {"message": "Hello, FastAPI!"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

=== Path 파라미터 ===

@app.get("/users/{user_id}")
async def get_user(user_id: int):  # 자동 타입 검증
    return {"user_id": user_id, "name": f"User {user_id}"}

# Path()로 상세 검증
@app.get("/items/{item_id}")
async def get_item(
    item_id: int = Path(
        ...,              # 필수
        title="Item ID",
        ge=1,             # >= 1
        le=10000          # <= 10000
    )
):
    return {"item_id": item_id}

=== Query 파라미터 ===

# /items?skip=0&limit=10&q=search
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

=== Pydantic 모델 (Request/Response) ===

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

# Request Body 모델
class ItemCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    price: float = Field(..., gt=0)
    description: Optional[str] = Field(None, max_length=500)
    tags: list[str] = Field(default_factory=list)

# Response 모델
class ItemResponse(BaseModel):
    id: int
    name: str
    price: float
    description: Optional[str]
    tags: list[str]
    created_at: datetime

    class Config:
        from_attributes = True  # ORM 모드 (Pydantic v2)

=== POST 요청 처리 ===

@app.post("/items", response_model=ItemResponse, status_code=201)
async def create_item(item: ItemCreate):
    # item은 자동으로 검증된 Pydantic 모델 인스턴스
    new_item = {
        "id": 1,
        "name": item.name,
        "price": item.price,
        "description": item.description,
        "tags": item.tags,
        "created_at": datetime.now()
    }
    return new_item

@app.put("/items/{item_id}")
async def update_item(item_id: int, item: ItemCreate):
    return {"item_id": item_id, **item.model_dump()}

@app.delete("/items/{item_id}", status_code=204)
async def delete_item(item_id: int):
    return None  # 204 No Content

=== 자동 문서화 ===
Swagger UI:  http://localhost:8000/docs
ReDoc:       http://localhost:8000/redoc
OpenAPI JSON: http://localhost:8000/openapi.json

=== 실행 방법 ===
pip install fastapi uvicorn
uvicorn main:app --reload --port 8000
````

**풀이 요점**
- 스크립트는 FastAPI 를 띄우지 않고 코드를 문자열로 보여 주는 시연이라, 파이썬만으로 돌아간다.
- 값이 어디서 오는지는 인자 모양이 정한다 — `{item_id}` 는 Path, `skip` · `limit` · `q` 는 Query, `item: ItemCreate` 는 본문.
- 필수와 선택은 `...` 과 기본값으로 가른다 — `Path(...)` · `Field(...)` 는 필수, `Field(None)` · `Query(default=None)` 은 선택.
- `response_model` 은 응답을 걸러 직렬화하고, `status_code` 는 생성 201 · 삭제 204 로 뜻을 맞춘다.
- `class Config` 를 v2 방식이라 적은 원본 주석은 의심스럽다 — 2-summary 「어디서 틀리나 7」 참고.
- `import json` 과 `dataclass` · `field` 는 import 만 되고 쓰이지 않는다 (원본에 근거 없음 — 추론).

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 원본 예제를 `Python 3.12.3` 에서 2회 돌렸다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
