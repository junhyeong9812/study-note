# python/python-project-structures/01 — FastAPI CRUD 전체 — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. `done` 필터와 `skip` · `limit` 을 함께 주면 (예측)

```python
# 질문용 발췌 — db 에 id 1~5 가 이 차례로 들어 있고, done 이 True 인 것은 2, 4, 5 다
items = list(db.values())
if done is not None:
    items = [i for i in items if i.done == done]
return [i.to_dict() for i in items[skip : skip + limit]]
```

- `GET /todos?done=true&skip=1&limit=1` 의 응답에는 어느 id 가 들어 있나?

### 2. 같은 제목으로 두 번 POST 하면 (예측)
- 빈 저장소에 `{"title": "장보기"}` 를 두 번 `POST /todos` 하면 두 번째 응답의 상태 코드와 `detail` 은 무엇인가?

### 3. 지우고 새로 만들면 받는 id (예측)

```python
# 질문용 발췌 — 서버를 막 띄운 빈 상태에서 차례로 요청한다
# POST   /todos   {"title": "a"}
# POST   /todos   {"title": "b"}
# DELETE /todos/2
# POST   /todos   {"title": "c"}
```

- 마지막 `POST` 응답의 `id` 는 몇인가?

### 4. `done` 만 담아 PATCH 하면 (예측)
- `PATCH /todos/1` 에 `{"done": true}` 만 보내면 `title` · `done` · `created_at` · `updated_at` 가운데 바뀌는 것은 어느 것인가?

### 5. 입력 스키마와 응답 스키마를 따로 두는 까닭 (왜)
- `TodoCreate` 에는 `title` 하나뿐이고 `TodoResponse` 에는 `id` · 시각까지 있는데, 왜 한 클래스로 합치지 않았나?

### 6. `HTTPException` 을 상속한 예외 클래스를 만든 까닭 (왜)
- 라우터에서 `raise HTTPException(404, ...)` 을 바로 쓰지 않고 `NotFoundError` 를 만든 이로움은 무엇인가?

### 7. `limit=500` 을 보내면 (경계)
- `GET /todos?limit=500` 요청에서 `list_todos` 함수 몸체는 실행되나?

### 8. PATCH 로 막을 수 있는 것과 없는 것 (경계)
- `PATCH` 로 `title` 을 이미 다른 항목이 쓰는 제목으로 바꾸려 하면 409 가 나오나?
- `{"title": null}` 을 보내 제목을 지우려 하면 어떻게 되나?

### 9. 저장소를 실제 DB 로 바꿀 때 (연결)
- 전역 `db` dict 를 DB Repository 로 바꾸면 스키마 · 라우터 · 모델 가운데 어느 층이 그대로 남고 어느 층이 바뀌나?

### 10. `ErrorResponse` 스키마와 실제 오류 응답 (연결)
- `ErrorResponse` 에는 `error_code` 가 있는데, `NotFoundError` 가 났을 때 실제 응답 본문에도 `error_code` 가 들어가나?

## 실습

### 실습 1. 인메모리 Todo CRUD API 세우기

**만들 것** — FastAPI 로 Todo 를 만들고 · 목록/단건 조회하고 · 부분 수정하고 · 지우는 API 를 한 파일에 세운다. 저장소는 전역 `dict` 다.

**준비물** — `fastapi` · `pydantic` · `uvicorn` 패키지가 필요하다(`pip install fastapi uvicorn`).

**요구 조건**

1단계 — 모델과 스키마
1. `TodoItem` 클래스는 `id` · `title` · `done`(기본 `False`) · `created_at` · `updated_at`(둘 다 생성 시각)을 갖고, `to_dict()` 로 다섯 속성을 담은 `dict` 를 돌려준다.
2. `TodoCreate` 는 필수 문자열 `title`(1~200자, 문서 예시 `"장보기"`)을 받는다.
3. `TodoUpdate` 는 선택 필드 `title`(주면 1~200자)과 선택 필드 `done` 을 받는다.
4. `TodoResponse` 는 `id` · `title` · `done` · `created_at` · `updated_at` 다섯 필드다.
5. `ErrorResponse` 는 `detail` · `error_code` 두 문자열 필드다.

2단계 — 저장소와 앱 · 예외
6. 전역 `db: dict[int, TodoItem]` 과 전역 카운터를 두고, `next_id()` 가 카운터를 1 올려 돌려준다.
7. 앱은 제목 `"Todo API"`, 버전 `"1.0.0"` 으로 만든다.
8. `NotFoundError(resource, resource_id)` 는 404 와 `"<resource> #<id> not found"` 를 내는 `HTTPException` 자식이다.
9. `DuplicateError(title)` 는 409 와 `"Todo '<title>' already exists"` 를 내는 `HTTPException` 자식이다.

3단계 — 라우터
10. `POST /todos` — 같은 제목이 있으면 `DuplicateError`, 없으면 새 id 로 저장하고 `TodoResponse` 꼴 · 201 로 돌려준다.
11. `GET /todos` — 선택 쿼리 `done` 으로 거르고, `skip`(기본 0, 0 이상) · `limit`(기본 20, 1~100)로 거른 결과를 잘라 `TodoResponse` 목록으로 돌려준다.
12. `GET /todos/{todo_id}` — 없으면 `NotFoundError`, 있으면 그 항목.
13. `PATCH /todos/{todo_id}` — 없으면 `NotFoundError`, 있으면 `None` 이 아닌 필드만 바꾸고 `updated_at` 을 지금으로 갱신해 돌려준다.
14. `DELETE /todos/{todo_id}` — 없으면 `NotFoundError`, 있으면 지우고 204.

4단계 — 실행
15. 파일을 직접 실행하면 문서 주소를 한 줄 출력하고 `uvicorn` 으로 `0.0.0.0:8000` 에서 서버를 띄운다.

**시작 코드**

```python
"""FastAPI CRUD 전체: 모델 -> 스키마 -> 라우터 -> 에러 처리"""
from __future__ import annotations
from datetime import datetime
from typing import Optional
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

# === 모델 ===
class TodoItem:
    def __init__(self, id: int, title: str, done: bool = False):
        # TODO: 다섯 속성 초기화 (두 시각은 datetime.now())
        ...

    def to_dict(self) -> dict:
        # TODO: 다섯 속성을 dict 로
        ...

# === 스키마 ===
class TodoCreate(BaseModel):
    title: str = ...  # TODO: Field 로 필수 · 1~200자 · examples=["장보기"]

class TodoUpdate(BaseModel):
    # TODO: title(선택, 1~200자), done(선택)
    ...

class TodoResponse(BaseModel):
    # TODO: 다섯 필드
    ...

class ErrorResponse(BaseModel):
    detail: str
    error_code: str

# === 저장소 ===
db: dict[int, TodoItem] = {}
id_counter = 0

def next_id() -> int:
    # TODO: 전역 카운터를 1 올려 돌려준다
    ...

# === 앱 · 예외 ===
app = FastAPI(title="Todo API", version="1.0.0")

class NotFoundError(HTTPException):
    def __init__(self, resource: str, resource_id: int):
        # TODO: 404 + "<resource> #<id> not found"
        ...

class DuplicateError(HTTPException):
    def __init__(self, title: str):
        # TODO: 409 + "Todo '<title>' already exists"
        ...

# === 라우터 ===
# TODO: @app.post("/todos", ...)            create_todo(body: TodoCreate)
# TODO: @app.get("/todos", ...)             list_todos(done, skip, limit)
# TODO: @app.get("/todos/{todo_id}", ...)   get_todo(todo_id: int)
# TODO: @app.patch("/todos/{todo_id}", ...) update_todo(todo_id: int, body: TodoUpdate)
# TODO: @app.delete("/todos/{todo_id}", ...) delete_todo(todo_id: int)

if __name__ == "__main__":
    import uvicorn
    print("Todo API 시작: http://localhost:8000/docs")
    # TODO: uvicorn 으로 app 실행 (host 0.0.0.0, port 8000)
```

**확인 방법** — 서버를 띄우고 브라우저에서 `http://localhost:8000/docs` 를 열어 다섯 경로를 하나씩 눌러 본다. 명령줄로는 아래처럼 확인한다.

```bash
python crud-fastapi.py
curl -X POST localhost:8000/todos -H "Content-Type: application/json" -d '{"title":"장보기"}'
curl -X POST localhost:8000/todos -H "Content-Type: application/json" -d '{"title":"장보기"}'   # 두 번째는 409
curl "localhost:8000/todos?done=false&skip=0&limit=10"
curl -X PATCH localhost:8000/todos/1 -H "Content-Type: application/json" -d '{"done":true}'
curl -X DELETE -i localhost:8000/todos/1   # 204
curl -i localhost:8000/todos/1             # 404
```

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
