# python/python-web/15 — GraphQL (Strawberry/Graphene) — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. `execute_sync` 로 게시글 1 의 제목과 상태를 물으면 (예측)

```python
# 질문용 발췌
result = schema.execute_sync('{ post(id: 1) { title, status } }')
print(result.data)
```

- `result.data` 에는 어떤 dict 가 들어 있나?

### 2. 공개 글을 한 개씩 잘라 물으면 (예측)

```python
# 질문용 발췌
schema.execute_sync('{ posts(status: PUBLISHED, limit: 1) { totalCount hasNextPage items { id } } }')
```

- `totalCount` · `hasNextPage` · `items` 는 각각 무엇인가?

### 3. 초안 글의 요약을 짧게 물으면 (예측)

```python
# 질문용 발췌 — POSTS_DB 의 id 3 글: content='작성 중...'
schema.execute_sync('{ post(id: 3) { summary(length: 5) } }')
```

- `summary` 칸에 오는 문자열은 무엇인가?

### 4. 파이썬의 `post_count` 를 쿼리에서 `postCount` 로 쓰는 까닭 (왜)
- 같은 필드를 왜 두 이름으로 부르게 되나?

### 5. `delete_post` 에만 `global POSTS_DB` 가 있는 까닭 (왜)
- `create_post` 는 `global` 없이 되는데 `delete_post` 는 왜 필요한가?

### 6. 부분 업데이트를 `is not None` 으로 검사하는 까닭 (왜)
- `if input.title:` 로 바꾸면 어떤 요청이 잘못 처리되나?

### 7. 저자 목록에 없는 `author_id` 를 가진 글의 `author` (경계)
- 그 글에 `author { name }` 을 물으면 응답은 어떻게 되나?

### 8. `posts(authorId: 0)` 처럼 0 을 넘기면 (경계)
- 이 필터는 어떻게 동작하나?

### 9. 글 목록마다 저자 이름을 붙이는 쿼리 (연결)
- 글이 N 개면 리졸버 조회는 몇 번 나가고, 원본 팁은 이를 무엇으로 푸나?

### 10. 같은 화면을 REST 로 만들 때와 견주면 (연결)
- GraphQL 은 over-fetching 을 어떻게 막고, Query · Mutation · Subscription 은 각각 어떤 일에 쓰나?

## 실습

### 실습 1. 게시글 GraphQL API 만들기

**만들 것** — Strawberry 로 저자 · 게시글 스키마를 정의하고, 조회 · 생성 · 수정 · 삭제를 지원한 뒤 FastAPI 에 붙이고 `execute_sync` 로 한 번 실행해 본다.

**준비물** — `strawberry-graphql[fastapi]` 와 `uvicorn` 이 필요하다. 데이터는 DB 대신 모듈 안 리스트(`AUTHORS_DB` · `POSTS_DB`)로 흉내 낸다.

**요구 조건**

1단계 — 타입
1. `PostStatus` 를 GraphQL enum 으로 노출한다(멤버 `DRAFT` · `PUBLISHED` · `ARCHIVED`, 값은 소문자 문자열).
2. `Author` 타입: `id` · `name` · `email` 필드와, `POSTS_DB` 에서 이 저자의 글 수를 세는 `post_count` 리졸버.
3. `Post` 타입: `id` · `title` · `content` · `status` · `created_at` · `author_id` 필드, `author_id` 로 `AUTHORS_DB` 를 찾아 `Author` 를 돌려주는 `author` 리졸버(못 찾으면 `None`), `length`(기본 100)보다 길면 잘라 `'...'` 을 붙이는 `summary` 리졸버.
4. `PostConnection` 타입: `items`(Post 목록) · `total_count` · `has_next_page`.

2단계 — 변환과 Query
5. `post_from_dict` 는 dict 를 `Post` 로 바꾸며 `status` 문자열을 `PostStatus` 로 바꾼다.
6. `Query.post(id)` 는 그 글을, 없으면 `None` 을 돌려준다(nullable).
7. `Query.posts(status, author_id, offset=0, limit=10)` 는 넘긴 조건으로 거르고, 자르기 전 개수를 `total_count` 로, `offset`~`offset+limit` 구간을 `items` 로, `(offset + limit) < total` 을 `has_next_page` 로 돌려준다.
8. `Query.authors()` 는 모든 저자를 돌려준다.

3단계 — Input 과 Mutation
9. `CreatePostInput`(title · content · author_id · status 기본 `DRAFT`)과 모두 `Optional` 인 `UpdatePostInput`(title · content · status)을 입력 타입으로 만든다.
10. 결과 타입 `MutationResult`(success · message)와 `PostMutationResult`(success · message · post 기본 `None`).
11. `create_post` 는 최대 id + 1 로 새 글을 `POSTS_DB` 에 넣고 성공 결과와 새 글을 돌려준다.
12. `update_post` 는 글이 없으면 실패 결과를, 있으면 `None` 이 아닌 칸만 고치고 성공 결과를 돌려준다.
13. `delete_post` 는 그 id 를 뺀 새 리스트로 `POSTS_DB` 를 바꾸고, 줄었으면 `'삭제 완료'`, 아니면 실패 메시지를 돌려준다.

4단계 — 스키마와 실행
14. `Query` · `Mutation` 으로 `schema` 를 만들고, `GraphQLRouter` 를 `fastapi_app` 의 `/graphql` 아래에 붙인다.
15. `schema.execute_sync('{ post(id: 1) { title, status } }')` 의 `data` 를 찍는다.

**시작 코드**

```python
# main.py
# pip install strawberry-graphql[fastapi] uvicorn
import strawberry
from strawberry.fastapi import GraphQLRouter
from typing import Optional, List
from datetime import datetime
from dataclasses import dataclass
from enum import Enum


# === 1. 타입 정의 ===
# TODO: GraphQL enum 으로 노출
class PostStatus(Enum):
    DRAFT = 'draft'
    PUBLISHED = 'published'
    ARCHIVED = 'archived'


# TODO: Object 타입으로 노출
class Author:
    # TODO: id · name · email 필드
    # TODO: post_count 리졸버
    pass


class Post:
    # TODO: id · title · content · status · created_at · author_id 필드
    # TODO: author 관계 리졸버
    # TODO: summary(length=100) 리졸버
    pass


class PostConnection:
    """페이지네이션용 타입"""
    # TODO: items · total_count · has_next_page
    pass


# 임시 데이터 (그대로 둔다)
AUTHORS_DB = [
    {'id': 1, 'name': 'Alice', 'email': 'alice@example.com'},
    {'id': 2, 'name': 'Bob', 'email': 'bob@example.com'},
]

POSTS_DB = [
    {'id': 1, 'title': 'GraphQL 입문', 'content': 'GraphQL은 API 쿼리 언어입니다...',
     'status': 'published', 'author_id': 1,
     'created_at': datetime(2024, 1, 15)},
    {'id': 2, 'title': 'Strawberry 가이드', 'content': 'Strawberry는 Python GraphQL 라이브러리...',
     'status': 'published', 'author_id': 1,
     'created_at': datetime(2024, 1, 20)},
    {'id': 3, 'title': '초안 글', 'content': '작성 중...',
     'status': 'draft', 'author_id': 2,
     'created_at': datetime(2024, 1, 25)},
]


def post_from_dict(d):
    # TODO: dict -> Post (status 문자열을 PostStatus 로)
    pass


# === 2. Query 정의 ===
class Query:
    # TODO: post(id) -> Optional[Post]
    # TODO: posts(status, author_id, offset, limit) -> PostConnection
    # TODO: authors() -> List[Author]
    pass


# === 3. Input 타입 & Mutation ===
class CreatePostInput:
    pass  # TODO


class UpdatePostInput:
    pass  # TODO


class MutationResult:
    pass  # TODO


class PostMutationResult:
    pass  # TODO


class Mutation:
    # TODO: create_post / update_post / delete_post
    pass


# === 4. 스키마 생성 & FastAPI 통합 ===
schema = None  # TODO

from fastapi import FastAPI
fastapi_app = FastAPI()
# TODO: GraphQLRouter 를 '/graphql' 에 붙인다

# uvicorn main:fastapi_app --reload


# === 5. 쿼리 예시 ===
queries = """
# 게시글 조회
query {
  post(id: 1) {
    title
    content
    summary(length: 50)
    author {
      name
      postCount
    }
  }
}

# 목록 (필터 + 페이지네이션)
query {
  posts(status: PUBLISHED, limit: 5) {
    items { id, title, status }
    totalCount
    hasNextPage
  }
}

# 생성
mutation {
  createPost(input: {
    title: "새 글"
    content: "내용입니다."
    authorId: 1
  }) {
    success
    message
    post { id, title }
  }
}
"""

result = None  # TODO: execute_sync 로 '{ post(id: 1) { title, status } }' 실행
print(f"\nGraphQL 실행 결과: {result.data}")

print("\nGraphQL Python 핵심 정리")
print("="*50)
print("@strawberry.type: GraphQL 타입 정의")
print("@strawberry.field: 리졸버 함수")
print("@strawberry.input: 입력 타입 (Mutation용)")
print("@strawberry.mutation: 데이터 변경 작업")
print("Query: 읽기 / Mutation: 쓰기")
print("Optional[T]: nullable 필드")
print("Strawberry는 타입 힌트 기반으로 스키마 자동 생성")
```

**확인 방법** — `pip install "strawberry-graphql[fastapi]" uvicorn` 뒤 `python main.py` 로 게시글 1 의 제목 · 상태가 찍히는지 본다. 이어서 `uvicorn main:fastapi_app --reload` 로 띄워 브라우저로 `/graphql` 경로를 열고, `queries` 문자열의 쿼리를 하나씩 넣어 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
