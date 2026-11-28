# python/python-project-structures/01 — FastAPI CRUD 전체 — 정리 (힌트)

> 출처 — study-site 항목 `python/crud-fastapi`(항목 데이터 `data/python/project-structures.json`) · 정답 코드 study-practice `python/python-project-structures/reference/crud-fastapi.py`\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).\
> 실행 — 실행하지 않음 — 외부 라이브러리 `fastapi` 가 있어야 도는 예제다 — 그것 없이 만들어 실행하지 않았다.

## 한눈에 — 쉽게 말하면

**FastAPI CRUD 앱은 「주문 창구가 있는 작은 창고」다.**
손님은 정해진 주문서(스키마)를 내야 하고, 창구 직원(라우터)은 주문서가 바르게 쓰였는지 먼저 본다.
그다음 창고 선반(저장소)에서 물건(모델)을 꺼내거나 넣는다.
돌려줄 때는 정해진 영수증 양식(응답 스키마)에 맞춰 적는다.
물건이 없거나 이미 있으면 정해진 거절 쪽지(예외)를 건넨다.
FastAPI CRUD 코드도 똑같은 구조다.

| 비유 | 실체 |
|---|---|
| 주문서 양식 | 입력 스키마 `TodoCreate` · `TodoUpdate` |
| 창구 직원 | 라우터 함수 `create_todo` · `list_todos` · … |
| 창고 선반 | 인메모리 저장소 `db: dict[int, TodoItem]` |
| 선반 위 물건 | 모델 `TodoItem` |
| 영수증 양식 | 응답 스키마 `TodoResponse` + `response_model` |
| 거절 쪽지 | `NotFoundError`(404) · `DuplicateError`(409) |
| 번호표 기계 | `next_id()` 와 `id_counter` |

```text
  요청 ──▶ [입력 스키마로 검증] ──▶ [라우터 함수] ──▶ [db 저장소]
                 │ 틀림                    │ 없음/중복         │
                 ▼                         ▼                   ▼
            자동 오류 응답          예외(404/409) 응답   to_dict() ──▶ [response_model 로 거름] ──▶ 응답
```

## 이 주제가 답하려는 질문

1. 모델 · 스키마 · 저장소 · 라우터 · 예외를 어떻게 나눠 한 파일에 CRUD API 를 세우나?
2. 요청이 들어와 응답이 나갈 때까지 각 층은 무엇을 검사하고 무엇을 돌려주나?
3. 목록 조회의 필터 · 페이지네이션과 부분 수정(PATCH)은 어떤 규칙으로 동작하나?
4. 「없음」 · 「중복」 같은 도메인 오류를 어떻게 일관된 HTTP 응답으로 바꾸나?

## 동작 방식

이 항목의 코드는 FastAPI 로 할 일(Todo) 목록을 만들고, 읽고, 고치고, 지우는 API 한 벌이다.
DB 대신 모듈 전역 `dict` 를 저장소로 쓴다.

> **CRUD** — Create(생성) · Read(조회) · Update(수정) · Delete(삭제)의 네 가지 기본 데이터 조작.\
> 예: `POST /todos` 가 Create, `DELETE /todos/{todo_id}` 가 Delete 다.

### (1) 네 층으로 나누기 — 모델 · 스키마 · 저장소 · 라우터

**언제 쓰나** — API 하나라도 「저장되는 꼴」과 「주고받는 꼴」을 갈라 두고 싶을 때 쓴다.
그래야 저장소를 DB 로 바꿔도 요청 · 응답 꼴은 그대로 둘 수 있다.

```text
코드                                         하는 일
class TodoItem: ...                      →  모델: 저장되는 실체(id·title·done·두 시각)
class TodoCreate(BaseModel): ...         →  입력 스키마: 생성 요청 본문의 꼴
class TodoUpdate(BaseModel): ...         →  입력 스키마: 수정 요청 본문의 꼴
class TodoResponse(BaseModel): ...       →  응답 스키마: 나가는 응답의 꼴
db: dict[int, TodoItem] = {}             →  저장소: id → TodoItem
@app.post("/todos", ...) def ...         →  라우터: 요청을 받아 저장소를 다룬다
```

- `TodoItem` 은 Pydantic 모델이 아닌 평범한 클래스다 — 원본 주석이 말하는 「모델/스키마 분리」다.
- `TodoItem.to_dict()` 는 응답 스키마에 넣기 쉽게 속성을 `dict` 로 모은다.
- 저장소와 `id_counter` 는 학습용 모듈 전역 값이다 — 원본 주석대로 실무에서는 DB Repository 로 바꾼다.
- `app = FastAPI(title="Todo API", version="1.0.0")` 의 메타데이터는 OpenAPI 문서에 보인다.

> **스키마** — 주고받는 데이터의 필드 이름 · 타입 · 제약을 적은 클래스. 여기서는 Pydantic `BaseModel` 을 상속한다.\
> 예: `TodoCreate` 는 「`title` 은 1~200자 문자열」이라는 규칙을 담는다.

### (2) 생성 — `POST /todos`

**언제 쓰나** — 새 자원을 만들고, 만든 결과를 201 상태 코드와 함께 돌려줄 때.

```text
요청 본문 {"title": "장보기"}
   │
   ▼ ① TodoCreate 로 검증 (title 필수, 1~200자)
   ▼ ② any(t.title == body.title ...) → 같은 제목이 있으면 raise DuplicateError → 409
   ▼ ③ TodoItem(id=next_id(), title=...) → id_counter 1 증가
   ▼ ④ db[item.id] = item
   ▼ ⑤ return item.to_dict()
   ▼ ⑥ response_model=TodoResponse 로 응답 꼴 맞춤, status_code=201
응답 {"id": 1, "title": "장보기", "done": false, "created_at": ..., "updated_at": ...}
```

- ① 본문 검증은 FastAPI 가 함수 실행 **전에** 한다 — 규칙을 어긴 요청은 함수 몸체에 닿지 않는다.
- ② 중복 검사는 저장된 모든 항목의 `title` 을 훑는다.
- ③ `next_id()` 는 `global id_counter` 로 전역 카운터를 1 올리고 그 값을 돌려준다.
- ⑤ 함수는 `dict` 를 돌려주지만 ⑥ 에서 `TodoResponse` 꼴로 검증 · 정리되어 나간다.
- `done` 은 `TodoItem` 생성자의 기본값 `False` 로 시작한다.

> **`response_model`** — 라우트 데코레이터에 주는 「응답의 꼴」. 반환값을 이 스키마로 검증하고 문서에도 적는다.\
> 예: `@app.post("/todos", response_model=TodoResponse)`.

### (3) 목록 조회 — `GET /todos` (필터 + 페이지네이션)

**언제 쓰나** — 많은 항목을 조건으로 거르고, 한 번에 정해진 수만큼 나눠 보낼 때.

```text
GET /todos?done=true&skip=1&limit=2
   │
   ▼ ① 쿼리 검증: done 은 bool 또는 없음, skip ≥ 0, 1 ≤ limit ≤ 100
   ▼ ② items = list(db.values())          (넣은 차례대로)
   ▼ ③ done 이 None 이 아니면 done 이 같은 것만 남김
   ▼ ④ items[skip : skip + limit]          (거른 뒤에 자른다)
   ▼ ⑤ 각각 to_dict() → list[TodoResponse] 로 응답
```

- 함수 인자 중 경로에 없는 것(`done` · `skip` · `limit`)은 쿼리 파라미터가 된다.
- `Query(0, ge=0)` 은 「기본값 0, 0 이상」, `Query(20, ge=1, le=100)` 은 「기본값 20, 1 이상 100 이하」다.
- 제약을 어긴 쿼리는 (1)처럼 함수 실행 전에 거절된다.
- 필터를 **먼저** 하고 슬라이스를 **나중에** 한다 — `skip` 은 「거른 결과」에서 건너뛸 개수다.
- `done` 을 주지 않으면 `None` 이라 필터가 걸리지 않고 전부 대상이 된다.

> **페이지네이션** — 결과를 일정 크기로 잘라 나눠 주는 것.\
> 예: `skip=20&limit=20` 은 21번째부터 20개.

### (4) 단건 조회 · 삭제 — `GET` · `DELETE /todos/{todo_id}`

**언제 쓰나** — 경로에 든 id 로 자원 하나를 집어 돌려주거나 지울 때.

```text
GET /todos/7                         DELETE /todos/7
   │ todo_id: int 로 변환               │
   ▼ 7 not in db?                      ▼ 7 not in db?
   ├─ 예 → raise NotFoundError → 404   ├─ 예 → raise NotFoundError → 404
   └─ 아니오 → db[7].to_dict()          └─ 아니오 → del db[7] → 204, 본문 없음
```

- `{todo_id}` 는 경로 파라미터이고, 함수 인자 `todo_id: int` 로 정수 변환된다.
- 팁의 `Path` 는 경로 파라미터에 `Query` 처럼 제약을 거는 도구다 — 이 코드에는 쓰이지 않았다.
- 삭제는 `status_code=204`(No Content)이고 함수가 아무것도 돌려주지 않는다.
- 지운 id 는 다시 쓰이지 않는다 — `id_counter` 는 줄지 않으니 다음 생성은 계속 다음 번호를 받는다.

### (5) 부분 수정 — `PATCH /todos/{todo_id}`

**언제 쓰나** — 자원 전체가 아니라 보낸 필드만 바꾸고 싶을 때.

```text
PATCH /todos/1  {"done": true}
   │
   ▼ ① TodoUpdate 검증: title 도 done 도 Optional (기본 None)
   ▼ ② 1 not in db → NotFoundError(404)
   ▼ ③ body.title is not None ?  → 아니오 → title 그대로
   ▼ ④ body.done  is not None ?  → 예     → done = True
   ▼ ⑤ updated_at = datetime.now()   (created_at 은 손대지 않음)
   ▼ ⑥ to_dict() → TodoResponse
```

- `TodoUpdate` 의 모든 필드가 `Optional` 이라 빈 본문 `{}` 도 검증을 통과한다 — 이때도 ⑤ 는 실행되어 `updated_at` 만 바뀐다.
- 「보내지 않은 필드」와 「`null` 을 보낸 필드」는 둘 다 `None` 이라 이 코드에서는 구별되지 않는다.
- `title` 을 보낼 때는 생성과 같은 1~200자 제약이 걸린다.
- 수정 경로에는 제목 중복 검사가 **없다**.

> **PATCH 시멘틱** — 요청에 담긴 필드만 바꾸고 나머지는 그대로 두는 부분 수정 규칙.\
> 예: `{"done": true}` 만 보내면 `title` 은 바뀌지 않는다.

### (6) 도메인 예외 — `HTTPException` 을 상속한 클래스

**언제 쓰나** — 「없음」 · 「중복」 같은 업무상 실패를 라우터마다 같은 모양으로 알리고 싶을 때.

```text
raise NotFoundError("Todo", 7)
   │ __init__ 이 super().__init__(status_code=404, detail="Todo #7 not found")
   ▼
FastAPI 가 HTTPException 을 잡음
   ▼
상태 404, 본문 {"detail": "Todo #7 not found"}
```

- `NotFoundError` 는 자원 이름과 id 를 받아 404 와 메시지를 만든다.
- `DuplicateError` 는 제목을 받아 409 Conflict 와 `"Todo '<제목>' already exists"` 를 만든다.
- 상태 코드와 메시지 꼴이 클래스 한 곳에 모이므로 라우터에는 `raise NotFoundError("Todo", todo_id)` 한 줄만 남는다.
- 둘 다 `HTTPException` 의 자식이라 따로 예외 처리기를 등록하지 않아도 FastAPI 기본 처리로 응답이 된다.
- 원본 절 제목은 「앱 및 에러 핸들러」지만 `@app.exception_handler` 같은 등록 코드는 없다.

> **`HTTPException`** — FastAPI 가 잡아 상태 코드와 `detail` 로 HTTP 오류 응답을 만드는 예외 클래스.\
> 예: `raise HTTPException(status_code=404, detail="없음")`.

## 문법 — 형태와 규칙

```python
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

app = FastAPI(title="Mini", version="0.1.0")
store: dict[int, str] = {}

class NoteIn(BaseModel):
    text: str = Field(..., min_length=1, max_length=50)   # ... = 필수

@app.post("/notes", status_code=201)
def add(body: NoteIn):                                    # 본문 → 스키마
    store[len(store) + 1] = body.text
    return {"id": len(store)}

@app.get("/notes/{nid}")
def one(nid: int, upper: bool = Query(False)):           # 경로 + 쿼리
    if nid not in store:
        raise HTTPException(status_code=404, detail="no note")
    return {"text": store[nid].upper() if upper else store[nid]}
```

- `@app.post` · `@app.get` · `@app.patch` · `@app.delete` 로 HTTP 메서드와 경로를 함수에 묶는다.
- 인자 타입이 `BaseModel` 자식이면 요청 본문, 경로의 `{이름}` 과 같으면 경로 파라미터, 나머지는 쿼리 파라미터다.
- `Field(...)` 의 `...`(Ellipsis)는 「필수 필드」, `Field(None, ...)` 은 「기본값 `None` 인 선택 필드」다.
- `Field` 의 `min_length` · `max_length` 는 문자열 길이, `examples` 는 OpenAPI 문서에 보일 예시다.
- `Query(기본값, ge=..., le=...)` 는 쿼리 파라미터의 기본값과 하한 · 상한을 건다. 경로 파라미터는 `Path` 로 같은 일을 한다.
- `response_model=스키마` 는 응답의 꼴을, `status_code=` 는 성공 상태 코드를 정한다.
- 목록 응답은 `response_model=list[TodoResponse]` 처럼 리스트 타입으로 적는다.
- `from __future__ import annotations` 는 타입 주석의 평가를 미룬다(원본 주석: 「자기참조 타입 평가 지연」).
- 직접 실행하면 `uvicorn.run(app, host="0.0.0.0", port=8000)` 으로 ASGI 서버를 띄우고, 자동 문서는 `/docs` 에 있다.

## 어디서 틀리나

### 1. 스키마가 검증과 문서를 「자동」으로 준다는 것을 잊고 손으로 다시 검사한다
팁대로 Pydantic 스키마와 `Query` 제약은 함수 실행 전에 검증하고 OpenAPI 문서에도 적힌다.
함수 안에서 `if len(body.title) == 0` 을 또 쓰는 것은 중복이다.
반대로 스키마에 없는 규칙(제목 중복 등)은 함수에서 직접 검사해야 한다.

### 2. `response_model` 을 빼먹는다
팁대로 `response_model` 은 응답 형태를 명시한다.
빼면 함수가 돌려준 값이 그대로 나가고 문서에도 응답 꼴이 적히지 않는다.
이 코드는 `dict` 를 돌려주므로, 응답 꼴을 고정하는 일은 `response_model` 이 맡는다.

### 3. 페이지네이션 파라미터에 제약을 걸지 않는다
팁대로 `Query` 로 제약을 건다.
`skip` 이 음수거나 `limit` 이 아주 크면 엉뚱한 슬라이스나 거대한 응답이 나온다.
이 코드는 `skip ≥ 0`, `1 ≤ limit ≤ 100` 으로 막는다.

### 4. 필터와 슬라이스의 차례를 거꾸로 생각한다
`list_todos` 는 거른 **뒤에** 자른다.
`skip` 은 전체가 아니라 거른 결과에서 건너뛰는 개수다.

### 5. PATCH 는 제목 중복을 막지 않는다
생성은 `DuplicateError` 로 같은 제목을 막지만 `update_todo` 에는 그 검사가 없다.
그래서 PATCH 로 이미 있는 제목으로 바꿀 수 있다 — 규칙이 경로마다 다르다.

### 6. PATCH 로 값을 「비울」 수 없다
`is not None` 으로 「보냈나」를 판단하므로 `{"title": null}` 은 「안 보냄」과 같다.
게다가 `title` 은 `TodoResponse` 에서 `str` 이라 비울 수도 없다.
「보내지 않음」과 「`null` 을 보냄」을 구별해야 하는 API 라면 이 방식으로는 모자란다.

### 7. 커스텀 예외로 일관성을 얻는다 — 그러나 `ErrorResponse` 는 연결되어 있지 않다
팁대로 커스텀 예외 클래스는 도메인 오류를 한 꼴로 표현해 처리를 일관되게 한다.
원본 주석은 `ErrorResponse` 를 「일관된 에러 형식 정의」라 한다.
→ 의심: 이 스키마는 어느 라우트의 `response_model` 에도, 어느 예외 처리기에도 쓰이지 않는다.
실제 오류 본문은 `HTTPException` 기본 꼴인 `{"detail": ...}` 이고 `error_code` 는 들어가지 않는다.
`error_code` 까지 내보내려면 예외 처리기를 따로 등록해야 한다.

### 8. 인메모리 저장소의 한계
`db` 와 `id_counter` 는 프로세스 메모리에 있어 서버를 다시 띄우면 사라진다.
서버 프로세스를 여럿 띄우면 저마다 다른 `db` 를 가진다.
원본 주석대로 실무에서는 DB Repository 로 바꾸고, 서버는 gunicorn + uvicorn worker 조합으로 띄운다.

### 9. 지운 id 가 다시 쓰인다고 생각한다
`next_id()` 는 카운터를 올리기만 한다.
1, 2 를 만들고 2 를 지운 뒤 만들면 3 이다.

### 10. `created_at` 과 `updated_at` 이 처음에 똑같다고 단정한다
생성자에서 `datetime.now()` 를 두 번 따로 부른다.
두 호출 사이에 시간이 흐르면 값이 조금 다를 수 있다.

### 11. `host="0.0.0.0"` 과 출력 주소
출력문은 `http://localhost:8000/docs` 를 알리지만 서버는 `0.0.0.0`, 곧 모든 네트워크 인터페이스에서 받는다.
같은 망의 다른 기기에서도 닿을 수 있다는 뜻이다.

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| `list(db.values())` 가 넣은 차례대로 나온다 | Python 언어(`dict` 의 삽입 순서 보존) |
| 본문 · 쿼리 검증이 함수 실행 전에 일어나고 실패하면 자동 오류 응답이 나간다 | FastAPI + Pydantic 의 동작 — 언어가 아니다 |
| `HTTPException` 을 던지면 `{"detail": ...}` 본문과 상태 코드가 나간다 | FastAPI 기본 예외 처리 |
| `response_model` 이 반환값을 검증 · 정리한다 | FastAPI 의 동작 |
| `Field(...)` 의 `...` 이 「필수」다 | Pydantic 의 규약 |
| 서버를 다시 띄우면 데이터가 사라진다 | 이 코드의 설계(인메모리) — 어느 쪽 보장도 아니다 |
| `created_at == updated_at` (생성 직후) | 아무도 보장하지 않는다 — `now()` 를 두 번 부른다 |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 요청 본문 규칙 검사 | Pydantic 스키마 + `Field` 제약 | 함수 안 손 검사 반복 |
| 응답 꼴 고정 · 문서화 | `response_model=` | 모델 객체를 그대로 반환하고 꼴을 운에 맡기기 |
| 쿼리 · 경로 값의 범위 제한 | `Query(...)` · `Path(...)` | 제약 없는 `int` |
| 생성과 수정의 필드 규칙이 다름 | `TodoCreate` · `TodoUpdate` 분리 | 한 스키마로 둘 다 받기 |
| 「없음」 · 「중복」 같은 업무 오류 | `HTTPException` 을 상속한 예외 클래스 | 라우터마다 다른 상태 코드 · 메시지 손으로 쓰기 |
| 학습 · 프로토타입 | 전역 `dict` 저장소 | 여러 프로세스 운영 서버 |
| 운영 | DB Repository · gunicorn + uvicorn worker | 전역 `dict` · `uvicorn.run` 개발 서버 |

## 핵심 문장

1. **층을 나눈다** — 저장되는 꼴(모델)과 주고받는 꼴(입력 · 응답 스키마)을 가르고, 라우터는 그 사이를 잇는다.
2. **검증은 함수 앞에서 끝난다** — 스키마 · `Field` · `Query` 를 어긴 요청은 라우터 몸체에 닿지 않는다.
3. **`response_model` 이 응답의 꼴을 정한다** — 함수가 `dict` 를 돌려줘도 스키마대로 나간다.
4. **목록은 거른 뒤 자르고, PATCH 는 `None` 이 아닌 필드만 바꾼다.**
5. **도메인 오류는 `HTTPException` 자식 클래스로** — 상태 코드와 메시지가 한 곳에 모여 일관된다.

## 관련 자료

- `service-layer` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- `middleware-chain` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- [config-management](../../python-patterns/11-config-management/2-summary.md)
- 원본: study-site 항목 데이터 `data/python/project-structures.json` 의 `crud-fastapi`

## 용어 풀이

- **CRUD** — 생성 · 조회 · 수정 · 삭제의 네 가지 기본 데이터 조작.
- **REST API** — 자원을 URL 로, 조작을 HTTP 메서드(POST · GET · PATCH · DELETE)로 나타내는 API 꼴.
- **FastAPI** — 타입 주석과 Pydantic 으로 검증 · 문서를 자동으로 붙이는 Python 웹 프레임워크.
- **Pydantic** — 타입 주석으로 데이터 검증 클래스를 만드는 라이브러리. `BaseModel` 을 상속한다.
- **스키마** — 주고받는 데이터의 필드 · 타입 · 제약을 적은 클래스.
- **모델(도메인 엔티티)** — 저장되는 실체를 나타내는 클래스. 여기서는 `TodoItem`.
- **라우터(라우트 함수)** — HTTP 메서드 + 경로에 묶인 함수.
- **`response_model`** — 응답의 꼴을 정하고 검증 · 문서화하는 데코레이터 인자.
- **`Field`** — Pydantic 필드에 기본값 · 제약 · 예시를 붙이는 함수.
- **`Query` / `Path`** — 쿼리 / 경로 파라미터에 기본값 · 제약을 붙이는 FastAPI 함수.
- **쿼리 파라미터** — URL 의 `?` 뒤에 오는 `이름=값`.
- **경로 파라미터** — URL 경로 속 `{todo_id}` 같은 자리의 값.
- **페이지네이션** — 결과를 `skip` · `limit` 으로 잘라 나눠 주는 것.
- **PATCH 시멘틱** — 보낸 필드만 바꾸는 부분 수정 규칙.
- **`HTTPException`** — FastAPI 가 HTTP 오류 응답으로 바꾸는 예외.
- **409 Conflict** — 요청이 현재 상태와 충돌(여기서는 제목 중복)했다는 상태 코드.
- **204 No Content** — 성공했지만 응답 본문이 없다는 상태 코드.
- **OpenAPI 문서** — API 의 경로 · 스키마를 적은 명세. FastAPI 는 `/docs` 에서 보여 준다.
- **ASGI 서버** — Python 비동기 웹 앱을 돌리는 서버 규격. `uvicorn` 이 그 구현이다.
- **인메모리 저장소** — 프로세스 메모리의 자료구조에 데이터를 두는 저장 방식.

## 더 들어가면

- FastAPI 의 요청 검증 실패 기본 응답은 상태 코드 422 와 오류 위치 목록이다 (확인 필요).
- `def`(동기) 라우트 함수는 스레드풀에서 돌아 여러 요청이 동시에 전역 `db` · `id_counter` 를 건드릴 수 있다 — 잠금이 없어 경쟁 조건 여지가 있다 (확인 필요).
- 「보내지 않음」과 「`null`」을 구별하려면 Pydantic v2 의 `model_dump(exclude_unset=True)` 로 실제로 보낸 필드만 꺼내는 방식이 흔히 쓰인다 (확인 필요).
- `ErrorResponse` 를 실제 오류 본문으로 쓰려면 `@app.exception_handler(HTTPException)` 처리기에서 `JSONResponse` 로 `detail` · `error_code` 를 내보내고, 라우트의 `responses=` 인자로 문서에 적는 방법이 있다 (확인 필요).
- `from __future__ import annotations` 를 쓰면 FastAPI 는 문자열이 된 주석을 모듈 전역에서 다시 풀어 읽는다 — 함수 안에서 정의한 스키마는 찾지 못할 수 있다 (확인 필요).
- 204 응답에는 본문이 없어야 하므로 삭제 함수가 값을 돌려주지 않는 편이 맞다 (확인 필요).
- 생성 응답에 `Location` 헤더로 새 자원 주소를 붙이는 것도 REST 관례다 (확인 필요).
