# python/python-web/15 — GraphQL (Strawberry/Graphene) — 정리 (힌트)

> 출처 — study-site 항목 `python/graphql-python`(항목 데이터 `data/python/web-frameworks.json`) · 정답 코드 study-practice `python/python-web/reference/graphql-python.py`\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).\
> 실행 — 실행하지 않음 — 외부 라이브러리 `strawberry` 가 있어야 도는 예제다 — 그것 없이 만들어 실행하지 않았다.

## 한눈에 — 쉽게 말하면

**GraphQL 은 「반찬을 골라 적는 주문서」다.**
정식 메뉴(REST)는 정해진 접시가 통째로 나온다.
GraphQL 식당에서는 손님이 메뉴판을 보고 주문서에 먹을 반찬 칸만 적는다.
주방에는 칸마다 담당 요리사가 있어서, 적힌 칸의 요리사만 일한다.
Python 의 Strawberry 로 만든 GraphQL 서버도 똑같은 구조다.

| 비유 | 실체 |
|---|---|
| 메뉴판 | 스키마 (`strawberry.Schema(query=..., mutation=...)`) |
| 메뉴판의 요리 이름 | 타입 (`@strawberry.type` 클래스) |
| 반찬 한 칸 | 필드 (클래스 속성 또는 `@strawberry.field` 메서드) |
| 칸 담당 요리사 | 리졸버 (필드 값을 계산하는 메서드) |
| 「보여 주세요」 주문 | Query (읽기) |
| 「추가 · 변경 · 취소해 주세요」 주문 | Mutation (쓰기) |
| 주문 창구 | `/graphql` 엔드포인트 (`GraphQLRouter`) |

```text
 클라이언트 주문서                    서버(스키마)
 query {                         Query.post(id=1) ──► Post 객체
   post(id: 1) {                       │
     title          ◄───────────── title  (속성 그대로)
     author {       ◄───────────── Post.author() 리졸버 ──► Author
       name         ◄───────────── name   (속성 그대로)
     }
   }
 }
 → 적은 칸만 채워진 JSON 이 돌아온다
```

> **GraphQL** — 클라이언트가 받고 싶은 필드를 쿼리로 골라 요청하는 API 쿼리 언어.\
> 예: `{ post(id: 1) { title } }` 은 게시글 1 의 제목만 달라는 요청이다.

## 이 주제가 답하려는 질문

1. Python 클래스와 타입 힌트로 GraphQL 스키마를 어떻게 정의하나?
2. 필드 값은 누가 계산하나 — 그냥 속성인 필드와 리졸버 필드는 어떻게 다른가?
3. 읽기(Query)와 쓰기(Mutation)는 어떻게 나누고, 인자 · 입력 타입은 어떻게 받나?
4. 만든 스키마를 HTTP 로 내놓는 길과 HTTP 없이 바로 실행하는 길은 무엇인가?

## 동작 방식

### (1) 타입 힌트가 스키마가 된다

**언제 쓰나** — 클라이언트에게 보여 줄 데이터의 모양(타입 · 필드 · null 허용 여부)을 정할 때.

```text
@strawberry.type                     GraphQL 스키마에 생기는 것
class Author:              ──►       type Author {
    id: int                              id: Int!
    name: str                            name: String!
    email: str                           email: String!
    def post_count(...) -> int           postCount: Int!
                                     }
Optional[Post]             ──►       Post   (null 허용)
List[Post]                 ──►       [Post!]!
@strawberry.enum PostStatus ──►      enum PostStatus { DRAFT PUBLISHED ARCHIVED }
```

- `@strawberry.type` 을 붙인 클래스의 속성 하나하나가 필드가 된다.
- 속성의 타입 힌트(`int` · `str` · `datetime` …)가 필드의 GraphQL 타입이 된다.
- `Optional[T]` 로 감싼 것만 null 을 허용한다 — 감싸지 않은 필드는 null 을 돌려줄 수 없다고 선언한 셈이다.
- 파이썬 이름 `post_count` · `total_count` · `author_id` 는 쿼리에서 `postCount` · `totalCount` · `authorId` 로 쓴다(원본의 쿼리 예시가 그렇게 쓴다).
- `@strawberry.enum` 을 붙인 `Enum` 은 GraphQL enum 이 되고, 쿼리에서는 멤버 이름(`PUBLISHED`)으로 쓴다.

> **스키마** — 서버가 받을 수 있는 쿼리와 돌려줄 수 있는 데이터의 모양을 적은 계약서.\
> 예: `strawberry.Schema(query=Query, mutation=Mutation)`.

> **nullable** — 그 자리에 값 대신 null 이 올 수 있다는 뜻.\
> 예: `def post(self, id: int) -> Optional[Post]` 는 글이 없으면 null 을 돌려준다.

### (2) 리졸버 — 계산 필드 · 관계 필드 · 인자 받는 필드

**언제 쓰나** — 저장된 값을 그대로 내놓는 게 아니라 계산하거나, 다른 타입으로 건너가거나, 인자를 받아 모양을 바꿀 때.

```text
@strawberry.field 메서드의 세 쓰임

 계산 필드   Author.post_count()      POSTS_DB 를 훑어 author_id 가 같은 글 수 → int
 관계 필드   Post.author()            self.author_id 로 AUTHORS_DB 검색 → Author(**dict)
 인자 필드   Post.summary(length=100) 
               len(content) <= length → content 그대로
               아니면               → content[:length] + '...'
```

- 메서드에 `@strawberry.field` 를 붙이면 그 메서드가 필드가 되고, 반환 타입 힌트가 필드 타입이 된다.
- `post_count` 는 저장된 값이 없고 물을 때마다 계산된다.
- `author` 는 `Post` 에서 `Author` 로 건너가는 다리다 — 클라이언트는 `post { author { name } }` 처럼 한 쿼리로 따라간다.
- `Author(**author_data)` 는 dict 의 키를 키워드 인자로 풀어 객체를 만든다.
- `summary` 의 `length: int = 100` 은 GraphQL 필드 인자가 되고, 쿼리에서 `summary(length: 50)` 처럼 넘기며 빠뜨리면 100 이다.
- `summary` 는 문자 수를 기준으로 자른다 — 잘리면 앞 `length` 글자 뒤에 `'...'` 을 덧붙인다.

> **리졸버** — 필드 하나의 값을 계산해 돌려주는 함수.\
> 예: `Post.author` 는 `author_id` 로 저자를 찾아 `Author` 를 돌려준다.

### (3) Query 루트 — 조회 · 필터 · 페이지네이션

**언제 쓰나** — 모든 읽기의 진입점을 만들 때.

```text
posts(status, author_id, offset=0, limit=10)

 POSTS_DB (3개) ─► status 있으면 같은 것만 ─► author_id 있으면 같은 것만
                 ─► total = 남은 개수
                 ─► items = filtered[offset : offset+limit] 를 Post 로 변환
                 ─► has_next_page = (offset + limit) < total
                 ─► PostConnection(items, total_count, has_next_page)
```

- `Query` 클래스도 `@strawberry.type` 이다 — 그 필드(`post` · `posts` · `authors`)가 클라이언트가 고를 수 있는 읽기 입구다.
- `post(id)` 는 `next(..., None)` 으로 첫 일치를 찾고, 없으면 `None` → `Optional[Post]` 라 null 이 된다.
- `posts` 의 필터 인자는 둘 다 `Optional` + 기본값 `None` 이라 안 넘기면 필터를 건너뛴다.
- 필터는 `if status:` · `if author_id:` 처럼 참거짓으로 검사한다.
- `total_count` 는 자르기 **전** 개수, `items` 는 자른 **뒤** 목록이다.
- `PostConnection` 은 목록과 페이지 정보를 한 묶음으로 돌려주려고 만든 타입이다.
- 저장소의 `status` 는 소문자 문자열(`'published'`)이고, `post_from_dict` 가 `PostStatus(d['status'])` 로 enum 멤버로 바꾼다. 필터는 반대로 `status.value` 를 문자열과 견준다.

> **페이지네이션** — 긴 목록을 `offset`(건너뛸 개수)과 `limit`(가져올 개수)로 잘라 주는 것.\
> 예: `offset=0, limit=5` 는 앞 다섯 개.

### (4) Input 타입과 Mutation — 쓰기

**언제 쓰나** — 데이터를 만들고 · 고치고 · 지울 때.

```text
mutation { createPost(input: {title:"새 글", content:"…", authorId:1}) { success post { id } } }
        │
        ▼
 CreatePostInput(title, content, author_id, status=DRAFT 기본)
        │
 create_post: new_id = 최대 id + 1 → dict 만들어 POSTS_DB.append
        │
        ▼
 PostMutationResult(success=True, message='게시글이 생성되었습니다.', post=Post)
```

- `@strawberry.input` 클래스는 인자로만 받는 입력 타입이다 — 결과로 돌려주는 `@strawberry.type` 과 구분된다.
- `CreatePostInput.status` 는 기본값 `PostStatus.DRAFT` 라 넘기지 않으면 초안이 된다.
- `UpdatePostInput` 은 필드가 모두 `Optional[...] = None` 이다 — 바꿀 칸만 보내는 부분 업데이트용이다.
- `update_post` 는 `is not None` 인 칸만 갱신한다.
- `@strawberry.mutation` 은 쓰기 필드를 표시한다. `Mutation` 클래스가 쓰기의 진입점이다.
- 결과는 `MutationResult`(성공 여부 · 메시지) 또는 `PostMutationResult`(+ 바뀐 글)로 감싼다 — 실패해도 오류 대신 `success=False` 와 메시지를 돌려준다.
- `delete_post` 는 `global POSTS_DB` 를 선언한 뒤 걸러낸 새 리스트를 이름에 다시 묶는다. 줄어든 길이로 성공 여부를 판단한다.

> **Input 타입** — Mutation 등의 인자로 받는 묶음 전용 타입.\
> 예: `createPost(input: { title: "새 글" ... })` 의 `input`.

### (5) 쿼리 하나가 도는 길과 N+1

**언제 쓰나** — 목록에 관계 필드를 붙일 때 리졸버가 몇 번 도는지 가늠할 때.

```text
query { posts(limit: 10) { items { title author { name } } } }

 Query.posts()        ── 1번   (목록)
 Post.author()        ── 글마다 1번 → 10번
 합계 1 + N 번의 조회  ── 실제 DB 라면 쿼리 11번
```

- 리졸버는 필드 하나마다, 목록이면 원소마다 따로 불린다.
- 그래서 목록 조회 1번에 원소 수 N 만큼 관계 조회가 따라붙는다 — 이것이 N+1 문제다.
- 원본 팁: N+1 은 DataLoader 로 푼다 — 한 번에 들어온 키들(`author_id` 여럿)을 모았다가 한꺼번에 조회한다.
- 예제의 `post_count` 도 저자마다 `POSTS_DB` 전체를 훑는다. 주석대로 실제로는 DB 쿼리라 같은 문제가 생긴다.

> **N+1 문제** — 목록 1번 조회 뒤 원소 N 개마다 관계 조회가 1번씩 더 나가는 비효율.\
> 예: 글 10개의 저자를 따로따로 찾아 조회가 11번 나간다.

> **DataLoader** — 같은 순간에 요청된 키를 모아 한 번에 불러오는 일괄 로더.\
> 예: `author_id` 1 · 1 · 2 를 모아 `[1, 2]` 로 한 번 조회.

### (6) 스키마를 내놓기 — FastAPI 와 `execute_sync`

**언제 쓰나** — 서버로 띄울 때와, 테스트 · SSR 처럼 HTTP 없이 바로 돌려 볼 때.

```text
schema = strawberry.Schema(query=Query, mutation=Mutation)
   ├─ GraphQLRouter(schema) ─► fastapi_app.include_router(..., prefix='/graphql')
   │                            uvicorn main:fastapi_app --reload  → /graphql 로 요청
   └─ schema.execute_sync('{ post(id: 1) { title, status } }')
                                → result.data 에 dict 로 응답
```

- `strawberry.Schema` 가 Query · Mutation 루트를 묶어 스키마를 완성한다.
- `GraphQLRouter` 는 FastAPI 라우터다. 원본 주석은 엔드포인트와 Playground 를 제공한다고 적는다.
- `include_router(..., prefix='/graphql')` 로 `/graphql` 아래에 붙는다.
- FastAPI 는 ASGI 기반 비동기 프레임워크다.
- `execute_sync` 는 HTTP 없이 쿼리 문자열을 바로 실행하고, 결과 객체의 `.data` 에 응답 데이터가 dict 로 들어 있다.
- 원본의 `queries` 문자열은 쿼리 예시를 적어 둔 문자열일 뿐 실행되지 않는다.

> **ASGI** — Python 비동기 웹 서버와 앱 사이의 약속.\
> 예: `uvicorn` 이 ASGI 앱인 `fastapi_app` 을 띄운다.

## 문법 — 형태와 규칙

```python
import strawberry
from typing import Optional

@strawberry.type
class Book:
    id: int
    title: str

    @strawberry.field
    def shout(self, times: int = 1) -> str:
        return self.title.upper() * times

@strawberry.type
class Query:
    @strawberry.field
    def book(self, id: int) -> Optional[Book]:
        return Book(id=id, title="hi") if id == 1 else None

schema = strawberry.Schema(query=Query)
```

| 장식자 · 꼴 | 하는 일 |
|---|---|
| `@strawberry.type` | Object 타입(결과로 돌려주는 타입) |
| `@strawberry.field` | 메서드를 리졸버 필드로 노출 |
| `@strawberry.input` | 입력 타입(Mutation 인자용) |
| `@strawberry.mutation` | 쓰기 필드 |
| `@strawberry.enum` | `Enum` 을 GraphQL enum 으로 |
| `Optional[T]` | nullable 필드 · 선택 인자 |
| `List[T]` | 목록 필드 |
| `strawberry.Schema(query=, mutation=)` | 스키마 생성 |

- 리졸버 메서드의 첫 인자 `self` 는 그 타입의 객체이고, 나머지 인자가 GraphQL 인자가 된다.
- 인자에 기본값을 주면 쿼리에서 빠뜨려도 된다.
- 타입 힌트가 곧 스키마라서, 힌트를 빼면 필드 타입을 정할 수 없다.

## 어디서 틀리나

### 1. non-null 로 선언하고 `None` 을 돌려준다

`Post.author` 의 반환 타입은 `Author` 이지 `Optional[Author]` 가 아니다.
그런데 저자를 못 찾으면 `return None` 이다.
null 을 허용하지 않는 필드가 null 을 내면 응답에 오류가 실린다 — null 이 위쪽 nullable 필드(여기서는 `Optional[Post]` 인 `post`)까지 번질 수 있다(전파 세부는 확인 필요).
원본의 주장(관계 리졸버가 없으면 None) → 선언한 타입과 맞지 않는다. `Optional[Author]` 로 선언해야 일관된다.

### 2. 참거짓 검사로 필터를 건다

`if author_id:` 는 `author_id=0` 을 「필터 없음」과 똑같이 다룬다.
예제의 id 는 1부터라 지금은 문제가 드러나지 않지만, 0 이 쓰일 수 있는 값이면 `is not None` 으로 검사해야 한다.
`if status:` 는 enum 멤버라 넘기기만 하면 참이다.

### 3. 부분 업데이트는 `is not None` 으로

`update_post` 가 `if input.title:` 로 검사했다면 빈 문자열 `""` 로 바꾸려는 요청을 「안 보냄」으로 오해한다.
`None` 만 「안 보냄」으로 보고 그 밖의 값은 다 반영하려고 `is not None` 을 쓴다.

### 4. `global` 이 필요한 자리와 아닌 자리

`create_post` 의 `POSTS_DB.append(...)` 는 리스트 객체 안을 고칠 뿐 이름을 다시 묶지 않으므로 `global` 이 없어도 된다.
`delete_post` 는 `POSTS_DB = [...]` 로 이름에 새 리스트를 묶는다 — `global` 이 없으면 함수 안 지역 변수가 되어, 앞 줄 `len(POSTS_DB)` 부터 `UnboundLocalError` 가 난다.

### 5. 파이썬 이름 그대로 쿼리에 쓴다

쿼리에서는 `post_count` 가 아니라 `postCount`, `author_id` 가 아니라 `authorId` 다.
enum 은 값(`'published'`)이 아니라 이름(`PUBLISHED`)으로 쓴다.

### 6. 목록 + 관계 필드 = N+1

원본 팁: N+1 은 DataLoader 로 해결한다.
`posts { items { author { name } } }` 는 글마다 `author` 리졸버가 돈다.

### 7. over-fetching 과 Query · Mutation · Subscription 의 역할

원본 팁: GraphQL 은 클라이언트가 필요한 데이터만 요청하므로 over-fetching 을 막는다.
원본 팁: Query 는 읽기, Mutation 은 쓰기, Subscription 은 실시간 이벤트에 쓴다 — 예제에는 Subscription 이 없다.
읽기를 Mutation 에, 쓰기를 Query 에 두면 이 약속이 깨진다.

> **over-fetching** — 필요한 것보다 많은 데이터를 받아 오는 것.\
> 예: 제목만 필요한데 본문 · 작성일까지 다 오는 응답.

### 8. Strawberry 와 Graphene

원본 팁: Strawberry 는 타입 힌트 기반이라 Graphene 보다 현대적이다.
이것은 원본의 평가다 — 예제에는 Graphene 코드가 없다.

### 9. 원본 코드의 작은 흠

- `from dataclasses import dataclass` 는 쓰이지 않는다.
- 원본 주석은 `GraphQLRouter` 가 「Playground」를 준다고 적는다 → 제공하는 개발 도구의 이름 · 종류는 판에 따라 다를 수 있다(확인 필요).
- `uvicorn main:fastapi_app` 은 파일 이름이 `main.py` 일 때의 명령이다. `graphql-python.py` 처럼 `-` 가 든 이름은 모듈로 불러올 수 없다.

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| 타입 힌트로 스키마가 생긴다 | Strawberry 라이브러리 |
| `post_count` → `postCount` 이름 바꾸기 | Strawberry 의 기본 동작 (바꿀 설정이 있는지 확인 필요) |
| non-null 필드가 null 을 내면 오류 | GraphQL 명세 (전파 세부는 확인 필요) |
| enum 을 멤버 이름으로 쓴다 | GraphQL 명세(enum 은 이름) + Strawberry 의 매핑 |
| `GraphQLRouter` 가 개발 도구 화면을 준다 | Strawberry 판에 따라 다름 (확인 필요) |
| enum 멤버는 참이다 | Python 언어 (`Enum` 이 `__bool__` 을 따로 정하지 않을 때) |
| 이름을 다시 묶으려면 `global` | Python 언어 |
| 「Strawberry 가 Graphene 보다 현대적」 | 원본의 평가 — 보장 아님 |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 데이터 읽기 | Query 필드 | Mutation |
| 만들기 · 고치기 · 지우기 | Mutation + Input 타입 | Query |
| 없을 수 있는 값 | `Optional[T]` | non-null 선언 + `None` 반환 |
| 일부 칸만 고치기 | 모두 `Optional` 인 Input + `is not None` | 참거짓 검사 |
| 목록에 관계 필드 | DataLoader 로 일괄 조회 | 원소마다 따로 조회 |
| 테스트 · SSR | `schema.execute_sync` | 서버를 띄워 HTTP 요청 |
| 실시간 이벤트 | Subscription | Query 반복 호출 |

## 핵심 문장

1. **Strawberry 에서는 타입 힌트가 곧 스키마다** — `Optional` 이 아니면 null 이 될 수 없다.
2. **필드 값은 리졸버가 계산한다** — 속성은 그대로, `@strawberry.field` 메서드는 계산 · 관계 · 인자를 맡는다.
3. **Query 는 읽기, Mutation 은 쓰기, 입력은 `@strawberry.input`** 으로 받는다.
4. **리졸버는 필드마다 · 원소마다 불린다** — 목록의 관계 필드는 N+1 을 부르고 DataLoader 가 그것을 묶는다.
5. **스키마는 `GraphQLRouter` 로 HTTP 에, `execute_sync` 로 HTTP 없이** 실행된다.

## 관련 자료

- [django-rest](../05-django-rest/2-summary.md)
- [flask-api](../07-flask-api/2-summary.md)
- 원본: study-site 항목 데이터 `data/python/web-frameworks.json` 의 `graphql-python`

## 용어 풀이

- **GraphQL** — 필요한 필드를 골라 요청하는 API 쿼리 언어.
- **스키마** — 받을 수 있는 쿼리와 데이터 모양의 계약서.
- **타입 / 필드** — 객체의 모양 / 그 안의 칸 하나.
- **리졸버** — 필드 값을 계산하는 함수.
- **Query** — 읽기 작업의 루트 타입.
- **Mutation** — 쓰기 작업의 루트 타입.
- **Subscription** — 실시간 이벤트를 받는 작업.
- **Input 타입** — 인자 전용 묶음 타입.
- **nullable** — null 이 올 수 있음.
- **enum** — 정해진 몇 개 값 중 하나만 갖는 타입.
- **페이지네이션** — 목록을 잘라 주는 것.
- **over-fetching** — 필요 이상으로 받아 오는 것.
- **N+1 문제** — 목록 1번 + 원소마다 1번 조회.
- **DataLoader** — 키를 모아 한꺼번에 불러오는 로더.
- **ASGI** — Python 비동기 웹 서버와 앱 사이의 약속.
- **Strawberry / Graphene** — Python GraphQL 라이브러리.

## 더 들어가면

- GraphQL 명세는 Mutation 루트의 필드를 위에서부터 차례로 실행하고, Query 의 필드는 병렬로 실행해도 된다고 적는다(확인 필요).
- 한 문서 안에 이름 없는 operation 이 둘 이상이면 실행할 수 없다 — 원본 `queries` 문자열을 통째로 보내면 오류가 날 것이다(확인 필요).
- Strawberry 는 `async def` 리졸버를 지원하고, DataLoader 도 비동기로 쓰는 것이 일반적이다(확인 필요).
- 목록 페이지네이션에는 offset 대신 커서 기반(Relay Connection) 방식도 널리 쓰인다 — 예제의 `PostConnection` 은 이름만 빌린 단순형이다(확인 필요).
- Graphene 은 `graphene.ObjectType` 을 상속하고 필드를 `graphene.String()` 같은 객체로 선언하는 방식이다(확인 필요).
