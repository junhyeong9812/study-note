# python/python-libraries/03 — FastAPI 기본 — 정리 (힌트)

> 출처 — study-site 항목 `python/fastapi-basics`(항목 데이터 `data/python/libraries.json`) · 정답 코드 study-practice `python/python-libraries/reference/fastapi-basics.py`\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).\
> 실행 — 원본 예제를 `Python 3.12.3` 에서 2회 돌렸다.

## 한눈에 — 쉽게 말하면

**FastAPI 는 「주문서 양식이 붙은 식당 창구」다.**
손님(클라이언트)은 정해진 창구(주소)에 주문서(요청)를 낸다.
창구마다 양식이 붙어 있고, 검수 직원이 양식대로 썼는지 먼저 본다.
칸을 비우거나 숫자 칸에 글자를 쓰면 주방(함수)까지 가지 못하고 바로 돌려보내진다.
통과한 주문만 요리사가 받아 요리(응답)를 내고, 요리는 정해진 그릇(응답 모델)에 담겨 나간다.
식당 입구의 메뉴판(문서)은 양식을 보고 저절로 만들어진다.
FastAPI 도 똑같은 구조다.

| 비유 | 실체 |
|---|---|
| 창구 | 엔드포인트(`@app.get("/items")` 처럼 메서드 + 경로) |
| 주문서 양식의 칸 | 함수 인자의 타입 힌트 · `Path` · `Query` · Pydantic 모델 |
| 검수 직원 | FastAPI 와 Pydantic 의 자동 검증 |
| 요리사 | 핸들러 함수 |
| 그릇 | `response_model` |
| 메뉴판 | 자동 문서(`/docs` · `/redoc` · `/openapi.json`) |

```text
요청 ──▶ [주소 맞추기] ──▶ [양식 검사] ──통과──▶ 핸들러 ──▶ [응답 모델로 담기] ──▶ JSON
                              │
                              └─실패──▶ 오류 응답 (핸들러는 불리지 않음)
```

## 이 주제가 답하려는 질문

1. 함수 하나를 어떻게 「`GET /items` 가 오면 부를 함수」로 등록하나?
2. 주소 안의 값 · 물음표 뒤의 값 · 본문 JSON 을 어떻게 함수 인자로 받고, 어떻게 검사하나?
3. 필수 값과 선택 값은 어떻게 가르나?
4. 응답은 어떻게 걸러지고 JSON 이 되며, 문서는 어디서 생기나?

## 동작 방식

### (1) 앱 만들기와 라우트 등록

**언제 쓰나** — API 를 처음 세울 때, 주소마다 처리할 함수를 붙일 때.

```text
app = FastAPI(title="My API", ...)      앱 하나 = 라우트 목록 하나
@app.get("/health")                      "GET /health" 를 이 함수에 묶음
async def health_check():
    return {"status": "healthy"}  ──▶  dict 를 JSON 으로 바꿔 응답
```

- `FastAPI()` 가 앱 객체를 만들고, 넘긴 `title` · `description` · `version` 은 문서에 그대로 실린다.
- `@app.get(경로)` 데코레이터가 「이 메서드 + 이 경로가 오면 이 함수를 부른다」를 앱에 적어 둔다.
- 핸들러는 `async def` 든 보통 `def` 든 된다.
- 핸들러가 돌려준 `dict` 는 FastAPI 가 JSON 으로 바꿔 보낸다.

> **엔드포인트** — 「HTTP 메서드 + 경로」 한 쌍과 그것을 처리하는 함수.\
> 예: `GET /health` → `health_check()`.

> **데코레이터** — 함수 정의 위에 `@이름` 으로 붙여 그 함수를 감싸거나 어딘가에 등록하는 문법.\
> 예: `@app.get("/")`.

### (2) Path 파라미터 — 주소 안의 값

**언제 쓰나** — 「몇 번 사용자」처럼 자원 하나를 가리킬 때.

```text
@app.get("/users/{user_id}")
async def get_user(user_id: int)

GET /users/42   ──▶ {user_id} 칸에 "42" ──▶ 타입 힌트 int ──▶ 42 로 바꿔 인자에 넣음
GET /users/abc  ──▶ "abc" 는 int 가 아님  ──▶ 오류 응답, 핸들러 안 불림
```

- 경로의 `{user_id}` 는 이름이 같은 함수 인자 `user_id` 와 짝지어진다.
- 주소에서 온 값은 글자지만, 타입 힌트 `int` 를 보고 정수로 바꾸고 검사한다.
- 더 자세히 검사하려면 `Path()` 를 기본값 자리에 둔다.
  `Path(..., title="Item ID", ge=1, le=10000)` 은 「필수, 문서 제목은 Item ID, 1 이상 10000 이하」다.
- `ge` 는 「이상(≥)」, `le` 는 「이하(≤)」다.

### (3) Query 파라미터 — 물음표 뒤의 값

**언제 쓰나** — 목록을 몇 개 건너뛰고 몇 개 볼지, 무엇으로 거를지처럼 「덧붙이는 조건」을 받을 때.

```text
GET /items?skip=3&limit=4&q=1
            │       │       │
            ▼       ▼       ▼
     skip=3     limit=4    q="1"     (경로에 없는 인자 → 쿼리에서 찾음)
     ge=0 검사  le=100 검사  길이 1~50 검사
```

- 경로의 `{…}` 에 없는 단순 타입 인자는 쿼리스트링에서 찾는다.
- `Query(default=0, ge=0)` 처럼 기본값이 있으면 빠져도 되는 **선택** 값이 된다.
- `Query(default=None, ...)` 이면 빠졌을 때 `None` 이 들어오고, 타입을 `Optional[str]` 로 적는다.
- `min_length` · `max_length` 는 문자열 길이를, `ge` · `le` 는 숫자 범위를 검사한다.
- 예제의 `list_items` 는 `range(skip, skip + limit)` 로 `{"id": i, "name": f"Item {i}"}` 목록을 먼저 만들고, `q` 가 있으면 이름에 `q` 가 (대소문자 무시로) 들어간 것만 남긴다.
- `total` 은 **거르고 남은 목록의 길이**다.

> **쿼리스트링** — 주소 끝 `?` 뒤에 `이름=값` 을 `&` 로 이은 부분.\
> 예: `?skip=0&limit=10`.

### (4) 요청 본문 — Pydantic 모델

**언제 쓰나** — 새 자원을 만들거나 고칠 때처럼 여러 필드를 JSON 으로 한꺼번에 받을 때.

```text
class ItemCreate(BaseModel):            본문 JSON
    name: str  = Field(..., min_length=1)   {"name": "펜", "price": 1.5}
    price: float = Field(..., gt=0)                │
    description: Optional[str] = Field(None)       ▼
    tags: list[str] = Field(default_factory=list)  검사 + 빈 칸 채우기
                                                   │
async def create_item(item: ItemCreate)  ◀─────────┘  item.name, item.price … 로 꺼냄
```

- `BaseModel` 을 상속한 클래스를 인자 타입으로 적으면 그 인자는 요청 본문 JSON 에서 온다.
- `Field(...)` 는 필수, `Field(None)` 은 선택(빠지면 `None`)이다.
- `Field(default_factory=list)` 는 빠졌을 때 요청마다 새 빈 리스트를 넣는다.
- `gt=0` 은 「0 보다 큼」이라 `0` 은 통과하지 못한다.
- 핸들러가 받는 `item` 은 이미 검사를 통과한 모델 객체다.
- 파이썬 자체는 타입 힌트를 실행 중에 검사하지 않는다.
  `@dataclass` 로 만든 클래스에 `price: float` 이라고 적어도 글자를 넣으면 그대로 들어간다.
  검사는 Pydantic 이 힌트를 읽어서 하는 일이다.

> **Pydantic 모델** — `BaseModel` 을 상속해 필드와 타입을 적은 클래스. 만들 때 값을 검사한다.\
> 예: `class ItemCreate(BaseModel): name: str`.

### (5) 응답 — `response_model` · `status_code` · `model_dump()`

**언제 쓰나** — 응답 꼴을 고정하고, 생성 · 삭제에 맞는 상태 코드를 줄 때.

```text
@app.post("/items", response_model=ItemResponse, status_code=201)
핸들러가 dict 반환 ──▶ ItemResponse 필드만 남김(나머지 버림) ──▶ JSON ──▶ 201
```

- `response_model` 을 주면 돌려준 값을 그 모델의 필드로 걸러 직렬화한다.
  모델에 없는 키는 응답에서 빠진다.
- `status_code` 는 성공했을 때의 응답 코드를 바꾼다 — 생성은 `201`, 본문 없이 끝나는 삭제는 `204`.
- `item.model_dump()` 는 모델을 `dict` 로 바꾸는 Pydantic v2 메서드다(v1 의 `.dict()` 는 낡은 방식).
  `{"item_id": item_id, **item.model_dump()}` 는 경로 값과 본문 필드를 한 `dict` 로 합친다.
- `ItemResponse` 안의 `class Config: from_attributes = True` 는 ORM 객체처럼 속성으로 값을 가진 객체에서도 모델을 만들게 하는 설정이다(예전 이름 `orm_mode`).

> **직렬화** — 파이썬 객체를 JSON 같은 전송용 글자로 바꾸는 일.\
> 예: `{"status": "healthy"}` → `'{"status":"healthy"}'`.

### (6) 자동 문서와 실행

**언제 쓰나** — 만든 API 를 확인하고 남에게 보일 때.

```text
타입 힌트 · Path · Query · 모델 ──▶ OpenAPI 스펙 ──▶ /openapi.json (원본 JSON)
                                                  ├▶ /docs   (Swagger UI, 눌러서 시도)
                                                  └▶ /redoc  (ReDoc, 읽기용)
```

- 같은 타입 정보가 검사 · 직렬화 · 문서 세 군데에 쓰인다.
- 실행은 `pip install fastapi uvicorn` 으로 설치한 뒤 `uvicorn main:app --reload --port 8000` 이다.
  `main:app` 은 「`main.py` 안의 `app` 객체」, `--reload` 는 코드가 바뀌면 다시 띄우는 개발용 옵션이다.

> **OpenAPI** — HTTP API 의 경로 · 인자 · 응답 꼴을 적는 표준 문서 형식.\
> 예: `/openapi.json`.

## 문법 — 형태와 규칙

```python
from typing import Optional
from fastapi import FastAPI, Path, Query
from pydantic import BaseModel, Field

app = FastAPI(title="Demo")

class Memo(BaseModel):
    text: str = Field(..., min_length=1)

@app.get("/memos/{memo_id}")
async def read(memo_id: int = Path(..., ge=1),
               full: bool = Query(default=False)):
    return {"id": memo_id, "full": full}

@app.post("/memos", status_code=201)
async def make(memo: Memo):
    return memo.model_dump()
```

- `@app.get` · `@app.post` · `@app.put` · `@app.delete` 가 메서드별 등록이다.
- 경로의 `{이름}` ↔ 같은 이름의 인자(Path), 그 밖의 단순 타입 인자 ↔ 쿼리(Query), `BaseModel` 타입 인자 ↔ 본문.
- 기본값이 있으면 선택, `...` 이면 필수.
- 검사 옵션: 숫자 `ge` · `le` · `gt`, 문자열 `min_length` · `max_length`.
- 예제 스크립트 자체는 FastAPI 를 띄우지 않고 위 코드들을 **문자열로 출력하는 시연**이다.
  `print("""` 바로 뒤에서 줄을 바꾸고 `"""` 앞에서 줄을 바꾸므로, 출력은 헤더 다음에 빈 줄 하나, 코드 끝에 빈 줄 하나가 생긴다.
  한 줄짜리 `print("...")` 는 빈 줄을 만들지 않고, 인자 없는 `print()` 는 빈 줄 하나를 찍는다.

## 어디서 틀리나

### 1. 타입 힌트가 곧 규칙이다
FastAPI 는 타입 힌트로 검증 · 직렬화 · 문서화를 한꺼번에 한다.
힌트를 빼거나 틀리게 적으면 세 가지가 모두 틀어진다.

### 2. 기본값 하나로 필수와 선택이 갈린다
`Path` · `Query` · `Field` 에 기본값을 주면 선택, `...` 을 주면 필수다.
`Optional[str]` 만 적고 기본값을 안 주면 「None 을 허용」할 뿐 「빠져도 된다」는 뜻이 아니다.

### 3. 검사는 적은 것만 한다
`limit` 에는 `le=100` 만 있고 하한이 없다.
그래서 `limit=-3` 은 통과하고, `range(skip, skip - 3)` 은 비어 빈 목록이 나온다.
반면 `skip` 은 `ge=0` 이라 음수가 거부된다.

### 4. `total` 은 전체 개수가 아니다
`list_items` 는 `skip`~`skip+limit` 으로 먼저 자른 뒤에 `q` 로 거른다.
그래서 `total` 은 「이 쪽 안에서 걸러진 개수」이고, 전체 자료 중 몇 개가 맞는지는 알 수 없다.

### 5. `response_model` 은 걸러 낸다
돌려준 `dict` 에 모델에 없는 키가 있으면 응답에서 사라진다.
비밀번호 같은 필드를 숨기는 데 쓸 수 있지만, 「분명 넣었는데 안 보인다」의 원인도 된다.

### 6. `.dict()` 대신 `model_dump()`
원본 주석대로 Pydantic v2 에서는 `model_dump()` 를 쓰고 `.dict()` 는 낡은 방식이다.

### 7. `class Config` 는 v2 방식이 맞나
원본은 `class Config: from_attributes = True` 에 「Pydantic v2」 주석을 달았다.
의심스러운 까닭: v2 에서 설정 이름 `from_attributes` 는 맞지만, 설정을 담는 방식으로 `model_config = ConfigDict(...)` 를 권하고 `class Config` 는 낡은 꼴로 남겨 둔 것으로 알려져 있다(확인 필요).

### 8. `--reload` 는 개발용이다
파일 변화를 지켜보다 다시 띄우는 옵션이라 운영 서버에서 켜 두지 않는다.

### 9. `Optional[X]` 와 `X | None`
원본 주석대로 파이썬 3.10 이후에는 `X | None` 꼴을 권한다.
뜻은 같다.

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| 타입 힌트는 실행 중에 검사되지 않는다 | 파이썬 언어 — 힌트는 붙어 있을 뿐 강제되지 않는다 |
| `...` 은 `Ellipsis` 라는 값이다 | 파이썬 언어 |
| `...` 이 「필수」를 뜻한다 | FastAPI · Pydantic 의 약속 — 언어 뜻이 아니다 |
| 타입 힌트로 검증 · 직렬화 · 문서화한다 | FastAPI · Pydantic 라이브러리 |
| `model_dump()` · `from_attributes` | Pydantic v2 — v1 에서는 이름이 다르다 |
| `/docs` · `/redoc` · `/openapi.json` 주소 | FastAPI 의 기본 설정 |
| `--reload` 로 자동 재시작 | uvicorn |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 자원 하나를 가리킴 | Path 파라미터 `/items/{item_id}` | 쿼리 `?id=` 로만 받기 |
| 목록의 쪽 나누기 · 거르기 | Query 파라미터 | 본문 모델 |
| 여러 필드를 한꺼번에 받기 | Pydantic 모델 본문 | 쿼리 인자 수십 개 |
| 응답 꼴 고정 · 필드 숨기기 | `response_model` | 핸들러에서 손으로 키 지우기 |
| 생성 · 삭제 응답 | `status_code=201` · `204` | 언제나 기본 코드 |
| 값 범위 검사 | `ge` · `le` · `gt` · `min_length` | 핸들러 안 `if` 로 직접 검사 |

## 핵심 문장

1. **타입 힌트 하나가 검증 · 직렬화 · 문서 셋을 만든다.**
2. **값이 어디서 오나는 인자의 모양이 정한다** — 경로 `{…}` 면 Path, 단순 타입이면 Query, `BaseModel` 이면 본문.
3. **기본값이 있으면 선택, `...` 이면 필수다.**
4. **검사는 적은 조건만 한다** — 하한을 안 적으면 음수도 통과한다.
5. **`response_model` 은 응답을 모델 필드로 걸러 낸다.**

## 관련 자료

- [fastapi-advanced](../04-fastapi-advanced/2-summary.md)
- [data-validation](../../python-patterns/20-data-validation/2-summary.md)
- 원본: study-site 항목 데이터 `data/python/libraries.json` 의 `fastapi-basics`

## 용어 풀이

- **엔드포인트** — HTTP 메서드 + 경로와 그것을 처리하는 함수.
- **라우트(라우팅)** — 들어온 요청을 맞는 핸들러로 보내는 규칙.
- **핸들러** — 요청을 받아 응답을 돌려주는 함수.
- **데코레이터** — `@이름` 으로 함수 위에 붙여 함수를 감싸거나 등록하는 문법.
- **Path 파라미터** — 주소 경로 안 `{이름}` 자리의 값.
- **Query 파라미터** — 주소 `?` 뒤 `이름=값` 꼴의 값.
- **쿼리스트링** — 주소 `?` 뒤의 부분 전체.
- **요청 본문** — 요청에 실려 오는 데이터(여기서는 JSON).
- **Pydantic 모델** — `BaseModel` 을 상속해 필드 · 타입을 적고, 만들 때 값을 검사하는 클래스.
- **`Field`** — 모델 필드의 기본값 · 검사 조건을 적는 함수.
- **`Ellipsis`(`...`)** — 파이썬의 특수 값. FastAPI · Pydantic 에서는 「필수」 표시로 쓴다.
- **`response_model`** — 응답을 걸러 직렬화할 기준 모델.
- **직렬화** — 객체를 JSON 같은 전송용 형태로 바꾸는 일.
- **상태 코드** — 응답의 결과를 나타내는 숫자(201 생성, 204 본문 없음).
- **REST** — 자원을 주소로, 할 일을 HTTP 메서드(GET · POST · PUT · DELETE)로 나타내는 API 설계 방식.
- **OpenAPI** — API 의 꼴을 적는 표준 문서 형식.
- **Swagger UI · ReDoc** — OpenAPI 스펙을 보여 주는 화면(시도용 · 읽기용).
- **uvicorn** — FastAPI 앱을 띄우는 ASGI 서버.
- **`@dataclass`** — 필드 목록으로 `__init__` 등을 만들어 주는 표준 데코레이터. 값을 검사하지 않는다.

## 더 들어가면

- 검증에 실패하면 FastAPI 는 기본으로 상태 코드 422 와 어느 필드가 왜 틀렸는지 담은 JSON 을 돌려준다(확인 필요).
- `@app.post` 등에 `status_code` 를 안 주면 기본은 200 이다(확인 필요).
- 응답 코드가 204 일 때 핸들러가 `None` 을 돌려주면 본문을 비워 보내는지는 FastAPI 버전에 따라 다를 수 있다(확인 필요).
- `response_model` 의 필수 필드가 돌려준 값에 빠지면 서버 쪽 검증 오류가 난다(확인 필요).
- 클래스 본문의 `list[str]` 꼴 힌트는 파이썬 3.9 이상에서 쓸 수 있다(확인 필요).
- 요즘 FastAPI 는 `Annotated[int, Query(ge=0)] = 0` 꼴을 권한다(확인 필요).
- `def` 핸들러는 스레드 풀에서, `async def` 핸들러는 이벤트 루프에서 돈다 — `async def` 안에서 막히는 호출을 하면 다른 요청이 멈춘다(확인 필요).
- 표준 `json.dumps` 는 `datetime` 을 바로 직렬화하지 못하지만, FastAPI 는 자체 변환으로 처리한다(확인 필요).
