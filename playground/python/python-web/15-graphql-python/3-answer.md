# python/python-web/15 — GraphQL (Strawberry/Graphene) — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 제목 `'GraphQL 입문'` 과 상태 `'PUBLISHED'` 가 담긴 dict

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
{'post': {'title': 'GraphQL 입문', 'status': 'PUBLISHED'}}
```

**왜 그런가**
- `Query.post(id=1)` 이 `POSTS_DB` 의 첫 글을 찾아 `post_from_dict` 로 `Post` 를 만든다.
- 저장된 `'published'` 는 `PostStatus('published')` 즉 `PostStatus.PUBLISHED` 가 된다.
- GraphQL enum 은 멤버 이름으로 나가므로 `'PUBLISHED'` 다(2-summary 「동작 방식 (1)」 · 「(3)」).
- 응답은 쿼리에 적은 칸(`title` · `status`)만 담고 `post` 아래에 놓인다.

### 2. `totalCount` 2 · `hasNextPage` 참 · `items` 는 id 1 하나

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
{'posts': {'totalCount': 2, 'hasNextPage': True, 'items': [{'id': 1}]}}
```

**왜 그런가**
- `status.value` 는 `'published'` 라 id 1 · 2 만 남는다 → `total = 2`.
- `filtered[0:1]` 이라 `items` 는 id 1 하나다.
- `(0 + 1) < 2` 가 참이라 `hasNextPage` 는 참이다(2-summary 「동작 방식 (3)」).
- 응답 dict 의 키 차례는 쿼리에 적은 차례를 따른다고 보았다(원본에 근거 없음 — 추론).

### 3. `'작성 중....'` — 다섯 글자 뒤에 `'...'`

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
{'post': {'summary': '작성 중....'}}
```

**왜 그런가**
- `'작성 중...'` 은 `작` · `성` · 공백 · `중` · `.` · `.` · `.` 로 7글자라 5 보다 길다.
- `content[:5]` 는 `'작성 중.'` 이고 여기에 `'...'` 이 붙어 점이 넷이 된다(2-summary 「동작 방식 (2)」).

### 4. Strawberry 가 파이썬 이름을 GraphQL 관례 이름으로 바꿔 내놓기 때문이다

파이썬 쪽은 `snake_case`, GraphQL 쿼리 쪽은 `camelCase` 를 쓴다.
Strawberry 가 스키마를 만들 때 `post_count` → `postCount`, `author_id` → `authorId` 로 바꾼다.
그래서 코드에서는 `post_count`, 쿼리에서는 `postCount` 로 부른다.
이는 GraphQL 명세가 아니라 Strawberry 의 기본 동작이다.
근거: 2-summary 「동작 방식 (1)」 · 「어디서 틀리나 5」 · 「구현 세부사항 대 언어 보장」.

### 5. `delete_post` 만 이름을 새 리스트에 다시 묶기 때문이다

`create_post` 의 `POSTS_DB.append(...)` 는 이미 있는 리스트 객체 안을 고칠 뿐이라 전역 이름을 읽기만 한다.
`delete_post` 의 `POSTS_DB = [...]` 는 이름에 새 값을 대입한다.
함수 안 대입은 그 이름을 지역 변수로 만들므로 `global` 이 없으면 앞 줄 `len(POSTS_DB)` 에서 `UnboundLocalError` 가 난다.
근거: 2-summary 「어디서 틀리나 4」.

### 6. 빈 문자열 같은 「거짓인 값」으로 바꾸려는 요청이 무시된다

`UpdatePostInput` 에서 `None` 은 「이 칸은 안 보냄」이다.
`if input.title:` 로 검사하면 `title: ""` 처럼 거짓으로 평가되는 값을 보낸 요청도 「안 보냄」으로 보고 건너뛴다.
`is not None` 은 `None` 만 걸러 내고 나머지 값은 다 반영한다.
근거: 2-summary 「동작 방식 (4)」 · 「어디서 틀리나 3」.

### 7. 리졸버가 `None` 을 돌려주지만 `author` 는 non-null 이라 응답에 오류가 실린다

`Post.author` 는 저자를 못 찾으면 `return None` 이다.
반환 타입이 `Optional[Author]` 가 아닌 `Author` 라 null 을 허용하지 않는 필드다.
그래서 `author` 칸은 정상 값으로 채워지지 않고 오류가 생기며, null 이 위쪽 nullable 필드까지 번질 수 있다(전파 세부는 확인 필요).
고치려면 반환 타입을 `Optional[Author]` 로 둔다.
근거: 2-summary 「어디서 틀리나 1」.

### 8. 0 은 거짓이라 필터를 걸지 않은 것과 같다

`posts` 는 `if author_id:` 로 검사한다.
`0` 은 거짓이라 필터가 건너뛰어지고 모든 글이 대상이 된다.
예제의 id 는 1 부터라 겉으로 드러나지 않을 뿐이다 — `is not None` 으로 검사하면 0 도 필터로 쓴다.
근거: 2-summary 「어디서 틀리나 2」.

### 9. 목록 1번 + 글마다 1번, 합계 N+1 번 — DataLoader 로 묶는다

`Query.posts` 가 1번 돌고, `items` 의 글마다 `Post.author` 리졸버가 따로 돈다.
실제 DB 라면 조회가 1 + N 번 나간다.
원본 팁대로 DataLoader 가 같은 순간에 요청된 `author_id` 들을 모아 한 번에 불러온다.
근거: 2-summary 「동작 방식 (5)」 · 「어디서 틀리나 6」.

### 10. 필요한 칸만 적어 받는다 — Query 는 읽기, Mutation 은 쓰기, Subscription 은 실시간 이벤트

REST 는 정해진 응답이 통째로 와서 쓰지 않는 칸까지 받기 쉽다(over-fetching).
GraphQL 은 클라이언트가 쿼리에 칸을 골라 적고, 적은 칸의 리졸버만 돌아 그 칸만 돌아온다.
원본 팁: Query 는 읽기, Mutation 은 쓰기, Subscription 은 실시간 이벤트에 쓴다.
근거: 2-summary 「한눈에」 · 「어디서 틀리나 7」.

## 실습 정답

### 실습 1. 게시글 GraphQL API 만들기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. enum 노출 | `@strawberry.enum class PostStatus(Enum)` |
| 2. `Author` 와 글 수 | `@strawberry.type class Author` · `post_count` |
| 3. `Post` 필드 · 관계 · 요약 | `@strawberry.type class Post` · `author` · `summary(self, length: int = 100)` |
| 4. 페이지 묶음 | `class PostConnection` (`items` · `total_count` · `has_next_page`) |
| 5. dict → Post | `post_from_dict` 의 `PostStatus(d['status'])` |
| 6. 단일 조회 | `Query.post` → `Optional[Post]` |
| 7. 필터 + 페이지네이션 | `Query.posts` 의 `filtered` · `total` · `filtered[offset:offset + limit]` · `(offset + limit) < total` |
| 8. 저자 목록 | `Query.authors` → `List[Author]` |
| 9. 입력 타입 | `@strawberry.input CreatePostInput` (`status = PostStatus.DRAFT`) · `UpdatePostInput` |
| 10. 결과 타입 | `MutationResult` · `PostMutationResult` (`post = None`) |
| 11. 생성 | `create_post` 의 `max(...) + 1` · `POSTS_DB.append` |
| 12. 부분 수정 | `update_post` 의 `is not None` 세 줄 |
| 13. 삭제 | `delete_post` 의 `global POSTS_DB` · `len(POSTS_DB) < before` |
| 14. 스키마 · FastAPI | `strawberry.Schema(query=Query, mutation=Mutation)` · `GraphQLRouter(schema)` · `include_router(..., prefix='/graphql')` |
| 15. HTTP 없이 실행 | `schema.execute_sync(...)` · `result.data` |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`python/python-web/reference/graphql-python.py`

```python
# [웹 프레임워크] GraphQL (Strawberry/Graphene)
# 설명: Python에서 GraphQL 스키마 정의, Query/Mutation, 리졸버 구현
# 팁: GraphQL은 클라이언트가 필요한 데이터만 요청하므로 over-fetching을 방지한다. Strawberry는 Python 타입 힌트 기반으로 Graphene보다 현대적이다. N+1 문제는 DataLoader로 해결한다. Query는 읽기, Mutation은 쓰기, Subscription은 실시간 이벤트에 사용한다.

# GraphQL with Strawberry - 현대적 Python GraphQL
# pip install strawberry-graphql[fastapi] uvicorn

# strawberry: 타입 힌트 기반 GraphQL 라이브러리
import strawberry
# FastAPI 통합 라우터 (FastAPI는 ASGI 기반)
from strawberry.fastapi import GraphQLRouter
from typing import Optional, List
from datetime import datetime
from dataclasses import dataclass
from enum import Enum


# === 1. 타입 정의 ===
# @strawberry.enum: GraphQL enum 타입으로 노출
@strawberry.enum
class PostStatus(Enum):
    DRAFT = 'draft'
    PUBLISHED = 'published'
    ARCHIVED = 'archived'


# @strawberry.type: GraphQL Object 타입 정의
@strawberry.type
class Author:
    # 클래스 속성 = GraphQL 필드 (타입 힌트로 스키마 자동 생성)
    id: int
    name: str
    email: str

    # @strawberry.field: 메서드를 리졸버 필드로 노출
    @strawberry.field
    def post_count(self) -> int:
        """계산 필드 (리졸버)"""
        # 동적 계산 - 실제로는 DB 쿼리
        return len([p for p in POSTS_DB if p['author_id'] == self.id])


@strawberry.type
class Post:
    id: int
    title: str
    content: str
    status: PostStatus
    created_at: datetime
    author_id: int

    # 관계 필드 - 다른 타입을 반환하는 리졸버
    @strawberry.field
    def author(self) -> Author:
        """관계 리졸버"""
        author_data = next(
            (a for a in AUTHORS_DB if a['id'] == self.author_id), None
        )
        if author_data:
            # ** 언패킹으로 dict -> 객체 변환
            return Author(**author_data)
        return None

    # 인자를 받는 필드 (GraphQL field arguments)
    @strawberry.field
    def summary(self, length: int = 100) -> str:
        """인자를 받는 필드"""
        if len(self.content) <= length:
            return self.content
        return self.content[:length] + '...'


# 페이지네이션을 위한 커스텀 타입
@strawberry.type
class PostConnection:
    """페이지네이션용 타입"""
    items: List[Post]
    total_count: int
    has_next_page: bool


# 임시 데이터 (실제로는 DB 사용)
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


# dict -> Post 변환 헬퍼 (status 문자열을 enum으로 변환)
def post_from_dict(d):
    return Post(
        id=d['id'], title=d['title'], content=d['content'],
        status=PostStatus(d['status']), author_id=d['author_id'],
        created_at=d['created_at']
    )


# === 2. Query 정의 ===
# Query 루트 타입: 모든 읽기 작업의 진입점
@strawberry.type
class Query:
    # 단일 객체 조회 (Optional은 nullable)
    @strawberry.field
    def post(self, id: int) -> Optional[Post]:
        """단일 게시글 조회"""
        data = next((p for p in POSTS_DB if p['id'] == id), None)
        return post_from_dict(data) if data else None

    # 필터 + 페이지네이션 조회
    @strawberry.field
    def posts(
        self,
        # Optional: nullable 인자 (선택적 필터)
        status: Optional[PostStatus] = None,
        author_id: Optional[int] = None,
        offset: int = 0,
        limit: int = 10,
    ) -> PostConnection:
        """게시글 목록 (필터 + 페이지네이션)"""
        filtered = POSTS_DB
        # 필터 조건 적용
        if status:
            filtered = [p for p in filtered if p['status'] == status.value]
        if author_id:
            filtered = [p for p in filtered if p['author_id'] == author_id]

        total = len(filtered)
        items = [post_from_dict(p) for p in filtered[offset:offset + limit]]
        return PostConnection(
            items=items,
            total_count=total,
            has_next_page=(offset + limit) < total
        )

    # 리스트 반환 필드
    @strawberry.field
    def authors(self) -> List[Author]:
        return [Author(**a) for a in AUTHORS_DB]


# === 3. Input 타입 & Mutation ===
# @strawberry.input: Mutation 인자용 입력 타입
@strawberry.input
class CreatePostInput:
    title: str
    content: str
    author_id: int
    # 기본값으로 선택적 입력
    status: PostStatus = PostStatus.DRAFT


@strawberry.input
class UpdatePostInput:
    # 부분 업데이트용 - 모두 Optional
    title: Optional[str] = None
    content: Optional[str] = None
    status: Optional[PostStatus] = None


# 응답용 결과 타입
@strawberry.type
class MutationResult:
    success: bool
    message: str


@strawberry.type
class PostMutationResult:
    success: bool
    message: str
    post: Optional[Post] = None


# Mutation 루트 타입: 모든 쓰기 작업의 진입점
@strawberry.type
class Mutation:
    # @strawberry.mutation: 쓰기 작업 필드
    @strawberry.mutation
    def create_post(self, input: CreatePostInput) -> PostMutationResult:
        # 새 ID 생성
        new_id = max(p['id'] for p in POSTS_DB) + 1 if POSTS_DB else 1
        new_post = {
            'id': new_id,
            'title': input.title,
            'content': input.content,
            # enum -> 값 추출
            'status': input.status.value,
            'author_id': input.author_id,
            'created_at': datetime.now(),
        }
        POSTS_DB.append(new_post)
        return PostMutationResult(
            success=True,
            message='게시글이 생성되었습니다.',
            post=post_from_dict(new_post)
        )

    @strawberry.mutation
    def update_post(
        self, id: int, input: UpdatePostInput
    ) -> PostMutationResult:
        post_data = next((p for p in POSTS_DB if p['id'] == id), None)
        if not post_data:
            return PostMutationResult(
                success=False, message='게시글을 찾을 수 없습니다.'
            )
        # 부분 업데이트: None 아닌 필드만 갱신
        if input.title is not None:
            post_data['title'] = input.title
        if input.content is not None:
            post_data['content'] = input.content
        if input.status is not None:
            post_data['status'] = input.status.value
        return PostMutationResult(
            success=True,
            message='게시글이 수정되었습니다.',
            post=post_from_dict(post_data)
        )

    @strawberry.mutation
    def delete_post(self, id: int) -> MutationResult:
        # 전역 변수 수정
        global POSTS_DB
        before = len(POSTS_DB)
        POSTS_DB = [p for p in POSTS_DB if p['id'] != id]
        if len(POSTS_DB) < before:
            return MutationResult(success=True, message='삭제 완료')
        return MutationResult(success=False, message='게시글을 찾을 수 없습니다.')


# === 4. 스키마 생성 & FastAPI 통합 ===
# Schema: Query/Mutation 루트를 묶어 GraphQL 스키마 구성
schema = strawberry.Schema(query=Query, mutation=Mutation)

# FastAPI 통합 (ASGI 기반 비동기 프레임워크)
from fastapi import FastAPI
fastapi_app = FastAPI()
# GraphQLRouter: GraphQL 엔드포인트 + Playground 제공
graphql_app = GraphQLRouter(schema)
# include_router로 prefix 하위에 GraphQL 마운트 (FastAPI의 의존성 주입과 자연스럽게 결합)
fastapi_app.include_router(graphql_app, prefix='/graphql')

# uvicorn main:fastapi_app --reload
# GraphQL Playground: http://localhost:8000/graphql


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

# 프로그래밍 방식 실행 - 테스트나 SSR에 유용
# execute_sync: HTTP 없이 직접 쿼리 실행
result = schema.execute_sync('{ post(id: 1) { title, status } }')
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

**실행 결과** — 실행하지 않음 — 외부 라이브러리 `strawberry` 가 있어야 도는 예제다 — 그것 없이 만들어 실행하지 않았다.

**풀이 요점**
- 타입 힌트가 곧 스키마라서 모든 필드에 힌트를 단다 — `Optional` 이 아니면 non-null 이다.
- `author` 는 `Author` 로 선언했지만 `None` 을 돌려줄 수 있다 — 정답 코드의 이 불일치는 「어디서 틀리나 1」의 그대로다.
- 저장소는 소문자 문자열, 스키마는 enum — `post_from_dict` 와 `status.value` 가 두 세계를 잇는다.
- 쓰기는 실패해도 오류 대신 `success=False` 결과 객체로 알린다.
- `delete_post` 만 이름을 다시 묶으므로 `global` 이 필요하다.
- `uvicorn main:fastapi_app` 으로 띄우려면 파일 이름을 `main.py` 로 둔다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — 외부 라이브러리 `strawberry` 가 있어야 도는 예제다 — 그것 없이 만들어 실행하지 않았다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
