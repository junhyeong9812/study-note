# python/python-project-structures/01 — FastAPI CRUD 전체 — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. id 4 하나 — 거른 뒤에 자른다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
응답 목록에는 id 4 인 항목 하나만 들어 있다.

**왜 그런가**
- `list(db.values())` 는 넣은 차례대로 `[1, 2, 3, 4, 5]` 다.
- `done=true` 필터로 `[2, 4, 5]` 가 남는다.
- `items[1 : 2]` 는 거른 결과의 두 번째 하나, 곧 id 4 다.
- `skip` 은 전체가 아니라 거른 결과에서 건너뛴다 — 2-summary 「동작 방식 (3)」, 「어디서 틀리나 4」.

### 2. 409 와 `Todo '장보기' already exists`

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
두 번째 응답은 상태 409, 본문 `{"detail": "Todo '장보기' already exists"}` 다.

**왜 그런가**
- 첫 요청으로 `db` 에 `"장보기"` 가 들어간다.
- 두 번째 요청의 `any(t.title == body.title ...)` 가 참이라 `DuplicateError("장보기")` 가 던져진다.
- `DuplicateError` 는 `status_code=409` 와 그 `detail` 을 부모 `HTTPException` 에 넘기고, FastAPI 가 그것을 응답으로 바꾼다 — 2-summary 「동작 방식 (2)」 ②, 「동작 방식 (6)」.

### 3. 3 — 지운 id 는 다시 쓰이지 않는다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
마지막 응답의 `id` 는 3 이다.

**왜 그런가**
- `"a"` 가 1, `"b"` 가 2 를 받으며 `id_counter` 는 2 가 된다.
- `DELETE` 는 `db` 에서 2 를 지울 뿐 카운터는 건드리지 않는다.
- `next_id()` 는 카운터를 1 올려 3 을 돌려준다 — 2-summary 「동작 방식 (4)」, 「어디서 틀리나 9」.

### 4. `done` 과 `updated_at` 만 바뀐다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
`done` 은 `True` 로, `updated_at` 은 요청 시각으로 바뀐다. `title` 과 `created_at` 은 그대로다.

**왜 그런가**
- 보내지 않은 `title` 은 `TodoUpdate` 의 기본값 `None` 이라 `if body.title is not None` 을 건너뛴다.
- `done` 은 `True` 라 갱신된다.
- `updated_at = datetime.now()` 는 조건 없이 실행되고, `created_at` 은 어디서도 다시 대입하지 않는다 — 2-summary 「동작 방식 (5)」.

### 5. 생성 요청과 응답은 담는 필드도, 정하는 쪽도 다르기 때문이다

생성 요청에서 손님이 정하는 것은 제목뿐이다.
`id` 와 두 시각은 서버가 만든다.
한 클래스로 합치면 클라이언트가 `id` 나 시각을 보낼 수 있는 꼴이 되거나, 응답에 꼭 있어야 할 필드를 선택으로 두어야 한다.
나눠 두면 입력은 `TodoCreate` 로 좁게 검증하고, 응답은 `response_model=TodoResponse` 로 꼴을 고정한다.
같은 까닭으로 수정은 전부 선택 필드인 `TodoUpdate` 를 따로 둔다.
근거: 2-summary 「동작 방식 (1)」 · 「동작 방식 (2)」 · 「언제 쓰고 언제 안 쓰나」.

### 6. 상태 코드와 메시지 꼴이 한 곳에 모여 일관되고 라우터가 짧아진다

`NotFoundError` 가 404 와 `"<자원> #<id> not found"` 꼴을 정해 두므로 세 라우터(`get` · `patch` · `delete`)가 모두 같은 응답을 낸다.
라우터에는 `raise NotFoundError("Todo", todo_id)` 한 줄만 남아 도메인 뜻(「없다」)이 그대로 읽힌다.
`HTTPException` 의 자식이라 따로 처리기 없이도 FastAPI 가 응답으로 바꾼다.
근거: 2-summary 「동작 방식 (6)」, 「어디서 틀리나 7」(원본 팁).

### 7. 실행되지 않는다 — `Query` 제약에서 먼저 거절된다

`limit` 은 `Query(20, ge=1, le=100)` 으로 100 이하만 허용한다.
500 은 이 제약을 어기므로 FastAPI 가 함수 호출 전에 검증 오류 응답을 돌려준다.
근거: 2-summary 「동작 방식 (3)」, 「동작 방식 (2)」 ①, 「어디서 틀리나 3」.

### 8. 둘 다 막히지 않는다 — 중복은 통과하고, `null` 은 「안 보냄」으로 처리된다

- `update_todo` 에는 제목 중복 검사가 없어 409 가 나오지 않고 제목이 그대로 바뀐다.
- `{"title": null}` 은 `body.title is None` 이라 `title` 이 바뀌지 않는다 — 「보내지 않음」과 구별되지 않는다.
- 이 요청도 성공으로 처리되어 `updated_at` 만 바뀐 응답이 나온다.

근거: 2-summary 「동작 방식 (5)」, 「어디서 틀리나 5」 · 「어디서 틀리나 6」.

### 9. 스키마와 라우트 계약은 그대로, 저장소 접근이 바뀐다

입력 · 응답 스키마(`TodoCreate` · `TodoUpdate` · `TodoResponse`)와 경로 · 상태 코드 · 예외 클래스는 바깥과의 약속이라 그대로 둔다.
바뀌는 것은 `db` · `next_id()` 를 쓰던 자리 — 라우터 몸체의 `db.values()` · `db[...]` · `del db[...]` 가 Repository 호출로 바뀐다.
`TodoItem` 은 원본 주석대로 「DB ORM 모델 대신」 둔 것이라 ORM 모델로 바뀐다.
모델과 스키마를 갈라 둔 덕에 응답 꼴은 저장 방식과 따로 지켜진다.
근거: 2-summary 「동작 방식 (1)」, 「어디서 틀리나 8」. (Repository 의 구체 꼴은 원본에 근거 없음 — 추론)

### 10. 들어가지 않는다 — `ErrorResponse` 는 정의만 되어 있다

`ErrorResponse` 는 어느 라우트의 `response_model` 에도, 어느 예외 처리기에도 쓰이지 않는다.
`NotFoundError` 는 `HTTPException` 기본 처리로 나가므로 본문은 `{"detail": "Todo #7 not found"}` 꼴이고 `error_code` 는 없다.
원본 주석의 「일관된 에러 형식 정의」는 실제 응답과 이어지지 않은 선언이다.
`error_code` 까지 내려면 예외 처리기를 따로 등록해야 한다.
근거: 2-summary 「어디서 틀리나 7」, 「동작 방식 (6)」.

## 실습 정답

### 실습 1. 인메모리 Todo CRUD API 세우기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. 모델과 `to_dict()` | `class TodoItem` 의 `__init__` · `to_dict` |
| 2. 생성 스키마 | `TodoCreate.title = Field(..., min_length=1, max_length=200, examples=["장보기"])` |
| 3. 수정 스키마 | `TodoUpdate` 의 `title: Optional[str] = Field(None, ...)` · `done: Optional[bool] = None` |
| 4. 응답 스키마 | `class TodoResponse` |
| 5. 오류 스키마 | `class ErrorResponse` |
| 6. 저장소 · id | `db` · `id_counter` · `next_id()` 의 `global id_counter` |
| 7. 앱 | `app = FastAPI(title="Todo API", version="1.0.0")` |
| 8. 404 예외 | `class NotFoundError(HTTPException)` |
| 9. 409 예외 | `class DuplicateError(HTTPException)` |
| 10. 생성 | `@app.post("/todos", response_model=TodoResponse, status_code=201)` `create_todo` |
| 11. 목록 | `@app.get("/todos", response_model=list[TodoResponse])` `list_todos` 의 `Query(0, ge=0)` · `Query(20, ge=1, le=100)` · 슬라이스 |
| 12. 단건 | `@app.get("/todos/{todo_id}")` `get_todo` |
| 13. 부분 수정 | `@app.patch("/todos/{todo_id}")` `update_todo` 의 `is not None` 검사 · `updated_at` 갱신 |
| 14. 삭제 | `@app.delete("/todos/{todo_id}", status_code=204)` `delete_todo` |
| 15. 실행 | `if __name__ == "__main__":` 의 `print` · `uvicorn.run(app, host="0.0.0.0", port=8000)` |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`python/python-project-structures/reference/crud-fastapi.py`

```python
# [실무 프로젝트 구조] FastAPI CRUD 전체
# 설명: FastAPI로 모델, 스키마, 라우터, 에러 처리를 포함한 완전한 CRUD API 구현
# 팁: FastAPI는 Pydantic 스키마로 자동 검증과 문서화를 제공한다. response_model로 응답 형태를 명시하고, Query/Path로 파라미터 제약을 건다. 커스텀 예외 클래스로 도메인 에러를 표현하면 에러 처리가 일관된다.

"""FastAPI CRUD 전체: 모델 -> 스키마 -> 라우터 -> 에러 처리"""
# 자기참조 타입 평가 지연
from __future__ import annotations
# 생성/수정 시각용 표준 datetime
from datetime import datetime
# 선택 필드 표기
from typing import Optional
# FastAPI 본체와 HTTP 예외/쿼리 파라미터 검증 도구
from fastapi import FastAPI, HTTPException, Query
# Pydantic 모델 베이스와 필드 메타데이터
from pydantic import BaseModel, Field

# === 모델 (DB 대신 인메모리) ===
# 도메인 엔티티 - DB ORM 모델 대신 단순 클래스로 구현 (관심사: 모델/스키마 분리)
class TodoItem:
    # 식별자/내용/상태/타임스탬프 초기화
    def __init__(self, id: int, title: str, done: bool = False):
        self.id = id
        self.title = title
        self.done = done
        self.created_at = datetime.now()
        self.updated_at = datetime.now()

    # 응답 직렬화용 dict 변환 - Pydantic 모델로 매핑하기 쉽게
    def to_dict(self) -> dict:
        return {
            "id": self.id, "title": self.title,
            "done": self.done, "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

# === 스키마 ===
# 입력 스키마 - 생성 시 요청 본문 검증
class TodoCreate(BaseModel):
    # ... 필수, min/max 길이 제약, OpenAPI 예시 자동 생성
    title: str = Field(..., min_length=1, max_length=200, examples=["장보기"])

# 부분 수정용 스키마 - 모든 필드가 Optional (PATCH 시멘틱)
class TodoUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    done: Optional[bool] = None

# 응답 스키마 - response_model로 지정해서 응답 형태 고정
class TodoResponse(BaseModel):
    id: int
    title: str
    done: bool
    created_at: datetime
    updated_at: datetime

# 에러 응답 스키마 - 일관된 에러 형식 정의
class ErrorResponse(BaseModel):
    detail: str
    error_code: str

# === 인메모리 저장소 ===
# 모듈 전역 dict - 학습용. 실무에선 DB Repository로 교체
db: dict[int, TodoItem] = {}
# ID 시퀀스 - 모듈 전역 카운터
id_counter = 0

# 다음 ID 생성 - global로 카운터 변경
def next_id() -> int:
    global id_counter
    id_counter += 1
    return id_counter

# === 앱 및 에러 핸들러 ===
# FastAPI 앱 인스턴스 - 메타데이터는 OpenAPI 문서에 노출
app = FastAPI(title="Todo API", version="1.0.0")

# 도메인 의미를 가진 HTTPException 서브클래스 - 라우터 코드를 깔끔하게
class NotFoundError(HTTPException):
    def __init__(self, resource: str, resource_id: int):
        # 부모 HTTPException에 상태/메시지 위임
        super().__init__(
            status_code=404,
            detail=f"{resource} #{resource_id} not found",
        )

# 중복 충돌 예외 - 409 Conflict
class DuplicateError(HTTPException):
    def __init__(self, title: str):
        super().__init__(status_code=409, detail=f"Todo '{title}' already exists")

# === CRUD 라우터 ===
# POST /todos - 새 Todo 생성. response_model로 응답 검증/문서화 동시 처리
@app.post("/todos", response_model=TodoResponse, status_code=201)
def create_todo(body: TodoCreate):
    # 동일 title 중복 검사
    if any(t.title == body.title for t in db.values()):
        raise DuplicateError(body.title)
    item = TodoItem(id=next_id(), title=body.title)
    db[item.id] = item
    return item.to_dict()

# GET /todos - 목록 조회 + 필터 + 페이지네이션
@app.get("/todos", response_model=list[TodoResponse])
def list_todos(
    # done 쿼리 파라미터로 필터
    done: Optional[bool] = None,
    # Query(...)로 제약 조건 지정 (음수 방지, 페이지 크기 1~100)
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    items = list(db.values())
    # done 필터 적용
    if done is not None:
        items = [i for i in items if i.done == done]
    # 슬라이싱으로 페이지네이션
    return [i.to_dict() for i in items[skip : skip + limit]]

# GET /todos/{id} - 단건 조회
@app.get("/todos/{todo_id}", response_model=TodoResponse)
def get_todo(todo_id: int):
    if todo_id not in db:
        raise NotFoundError("Todo", todo_id)
    return db[todo_id].to_dict()

# PATCH /todos/{id} - 부분 수정. None인 필드는 변경 안 함
@app.patch("/todos/{todo_id}", response_model=TodoResponse)
def update_todo(todo_id: int, body: TodoUpdate):
    if todo_id not in db:
        raise NotFoundError("Todo", todo_id)
    item = db[todo_id]
    # 제공된 필드만 갱신 - PATCH 시멘틱 보장
    if body.title is not None:
        item.title = body.title
    if body.done is not None:
        item.done = body.done
    # 수정 시각 갱신
    item.updated_at = datetime.now()
    return item.to_dict()

# DELETE /todos/{id} - 204 No Content
@app.delete("/todos/{todo_id}", status_code=204)
def delete_todo(todo_id: int):
    if todo_id not in db:
        raise NotFoundError("Todo", todo_id)
    del db[todo_id]

# === 실행 확인 ===
# 모듈 직접 실행 시 ASGI 서버 기동
if __name__ == "__main__":
    # 개발 서버 - 실무에선 gunicorn + uvicorn worker 조합
    import uvicorn
    print("Todo API 시작: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

**실행 결과** — 실행하지 않음 — 외부 라이브러리 `fastapi` 가 있어야 도는 예제다 — 그것 없이 만들어 실행하지 않았다.

**풀이 요점**
- 검증 규칙은 스키마의 `Field` 와 `Query` 에 두고, 스키마로 표현할 수 없는 제목 중복만 함수에서 검사한다.
- 반환은 `to_dict()` 의 `dict` 지만 `response_model` 이 응답 꼴을 고정한다.
- 목록은 `done` 필터를 먼저, `[skip : skip + limit]` 슬라이스를 나중에 적용한다.
- PATCH 는 `None` 이 아닌 필드만 바꾸고 `updated_at` 은 늘 갱신한다 — 중복 검사는 하지 않는다.
- 세 단건 경로의 「없음」은 모두 `NotFoundError` 한 클래스로 같은 404 꼴을 낸다.
- `ErrorResponse` 는 만들어 두지만 어디에도 연결하지 않는다 — 원본 그대로다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — 외부 라이브러리 `fastapi` 가 있어야 도는 예제다 — 그것 없이 만들어 실행하지 않았다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
