# api-design/17-graphql — GraphQL: 스키마·리졸버·N+1·쿼리 비용 제한 — 정리 (힌트)

## 해결하는 문제

화면 하나를 그리려고 REST 자원 여러 개를 따로 부르는 상황이 있다.

```text
  모바일 "글 목록" 화면 (REST만 있을 때)
  앱 ── GET /posts?limit=10 ─────────────> 글 10개 (작성자 id만 있음)
  앱 ── GET /users/3 ────────────────────> 작성자 1
  앱 ── GET /users/7 ────────────────────> 작성자 2
  ...  (작성자 수만큼 왕복)
  → 왕복이 많다(under-fetching). 반대로 /posts가 화면에 안 쓰는 필드 30개를 주면 over-fetching.
```

- 해법: 클라이언트가 **필요한 필드 모양을 쿼리로 적어 보내고**, 서버가 그 모양대로 채워 준다.
  - *GraphQL*: 타입 시스템(스키마)으로 데이터 그래프를 정의하고, 클라이언트가 보낸 쿼리 문서를 그 스키마에 맞춰 검증·실행하는 질의 언어와 실행 규칙. 명세는 spec.graphql.org(최신 릴리스 September 2025판).
- 쉬운 예: 식당 메뉴판(스키마)을 보고 "밥 + 국 + 반찬 2개"로 주문서(쿼리)를 쓰면 주방(리졸버)이 그 구성대로 한 쟁반에 담아 준다.
- 똑같은 구조다. 대신 **주문서를 손님이 마음대로 쓴다**는 점이 새 문제를 만든다.
  - 반찬 하나 담을 때마다 창고에 따로 다녀오면 느리다 → **N+1**.
  - "반찬의 반찬의 반찬…"처럼 무한히 겹친 주문서 하나로 주방을 멈출 수 있다 → **깊이·복잡도 제한**.
- 실무 예: 여러 화면(웹·iOS·Android)이 같은 백엔드를 서로 다른 모양으로 쓴다. 화면마다 엔드포인트를 새로 만드는 대신 스키마 하나에 쿼리만 바꾼다(BFF 대안 — [19](../19-api-gateway-and-bff/2-summary.md)).

## 동작·원리

### 1. 요청 하나가 처리되는 길

```text
  클라이언트                          GraphQL 서버
  POST /graphql                        ┌──────────────────────────────────────────┐
  {"query":"{ posts(limit:10)    ──>   │ 1. 파싱    문서 → AST                       │
     { title author { name } } }"}     │ 2. 검증    AST를 스키마·검증 규칙에 대조      │
                                       │ 3. 실행    필드마다 리졸버 호출 (트리 순회)     │
                                       │ 4. 응답    {"data": {...}, "errors": [...]} │
                                       └──────────────────────────────────────────┘
```

- *스키마(schema)*: 타입과 필드, 필드의 인자·반환 타입을 적은 계약이다. 예: `type Post { title: String!  author: User! }`.
  - *`!`*: non-null. 이 필드는 null이 될 수 없다.
- *리졸버(resolver)*: 필드 하나의 값을 만드는 함수. `Post.author`의 리졸버는 글 객체를 받아 작성자를 돌려준다.
- 실행은 쿼리 트리를 위에서 아래로 내려가며 필드마다 리졸버를 부른다. 목록 필드면 원소마다 하위 필드 리졸버를 부른다.

### 2. N+1 — 리졸버가 필드 단위라서 생긴다

```text
  { posts(limit: 10) { title author { name } } }

  Query.posts   ── SELECT * FROM post LIMIT 10              (1번)
   ├ post0.author ── SELECT * FROM user WHERE id = 0          ┐
   ├ post1.author ── SELECT * FROM user WHERE id = 1          │ 글 수(N)만큼
   ├ ...                                                      │
   └ post9.author ── SELECT * FROM user WHERE id = 9          ┘
  합계 = 1 + N
```

- 각 리졸버는 "내 글의 작성자"만 안다. 옆 글의 리졸버가 무엇을 읽는지 모른다. 그래서 같은 테이블을 N번 따로 읽는다.
- graphql.org "Performance" 페이지도 이 문제를 들고, 짧은 시간 동안 요청을 모아 한 번에 보내는 배치(DataLoader)를 흔한 해법으로 든다.

### 3. DataLoader — 한 틱 동안 모았다가 한 번에

```text
  같은 이벤트 루프 틱 안에서
  loader.load(0) ─┐
  loader.load(1) ─┤   큐에 키를 모은다 (같은 키는 캐시로 한 번만)
  ...             ├──> 틱이 끝나면 batchFn([0,1,...,9]) 1번
  loader.load(9) ─┘        └─ SELECT * FROM user WHERE id IN (0,...,9)
                         결과 배열을 키 순서대로 돌려준다 → 각 load()의 Promise가 풀린다
```

- *DataLoader*: 키 하나씩 부르는 `load(key)` API를 주되, 같은 실행 틱에 모인 키를 배치 함수 한 번으로 보내고 결과를 기억하는 라이브러리(graphql/dataloader).
- README가 정한 배치 함수 계약
  - 반환 배열 길이 = 키 배열 길이.
  - i번째 값 = i번째 키의 결과. DB가 다른 순서로 주면 **다시 정렬**해야 한다. 없는 키는 `null`이나 `Error`로 자리를 채운다.
- 캐시는 **요청 하나 범위**다. README는 여러 사용자의 요청이 같은 인스턴스를 공유하지 말라고 한다 — 다른 사용자의 데이터가 섞여 보일 수 있다. 공유 캐시(Redis 등)를 대신하지 않는다.

### 실험: N+1 vs DataLoader, 깊이에 따른 비용

(실험, node 22.23.2 · graphql-js 16.14.2 · dataloader 2.2.3, `node:22-alpine` 컨테이너, `--cpus=2`, 2026-10-04)

가짜 DB(사용자 10명, 글 100개, 글 i의 작성자 = i % 10)에 SQL 문자열을 기록하게 하고 쿼리 수를 셌다.

```js
// 핵심 부분 — 같은 스키마, 리졸버만 다르다
const loader = new DataLoader(async ids => db.usersByIds(ids)); // 요청마다 새로 만든다
const resolvers = {
  Query: { posts: (_, { limit }) => db.posts(limit) },
  Post:  { author: p => useLoader ? loader.load(p.authorId) : db.userById(p.authorId) },
  User:  { posts: u => db.postsByAuthor(u.id) },          // 이쪽은 배치하지 않았다
};
```

```text
N=10 리졸버 그대로                 SQL   11개  errors=0
N=10 DataLoader              SQL    2개  errors=0
    SELECT * FROM post LIMIT 10 | SELECT * FROM user WHERE id IN (0,1,2,3,4,5,6,7,8,9)
N=50 리졸버 그대로                 SQL   51개  errors=0
N=50 DataLoader              SQL    2개  errors=0
    SELECT * FROM post LIMIT 50 | SELECT * FROM user WHERE id IN (0,1,2,3,4,5,6,7,8,9)
N=100 리졸버 그대로                SQL  101개  errors=0
N=100 DataLoader             SQL    2개  errors=0
    SELECT * FROM post LIMIT 100 | SELECT * FROM user WHERE id IN (0,1,2,3,4,5,6,7,8,9)
```

- 관찰: 리졸버 그대로면 `1 + N`. DataLoader면 N과 무관하게 2개였다.
- N=50·100에서도 `IN` 목록은 사용자 10명뿐이다. 같은 작성자 키는 캐시가 한 번만 보낸다(중복 제거).

깊이를 키운 쿼리 — `posts(limit:10) { author { posts { author { ... name } } } }`처럼 `posts { author { } }`를 d번 더 감쌌다. `Post.author`는 DataLoader, `User.posts`는 배치 없음.

```text
깊이+0: 응답      261 바이트, SQL 2개, 3ms
깊이+1: 응답     2741 바이트, SQL 12개, 6ms
깊이+2: 응답    27541 바이트, SQL 112개, 58ms
깊이+3: 응답   275541 바이트, SQL 1112개, 359ms
깊이 제한 검증: [ 'query depth 9 exceeds 5' ]
```

- 관찰: 목록 필드를 한 단계 더 겹칠 때마다 응답 크기가 약 10배(사용자당 글 10개)로 커졌다. 응답 크기·SQL 수는 실행마다 같다. 시간은 실행마다 다르다(같은 환경에서 네 번 돌려 깊이+3이 294~379ms, 깊이+2가 58~72ms).
- 해석: 쿼리 문자열 길이는 거의 그대로인데 서버 일은 지수로 는다. 이것이 "쿼리 하나로 DoS"의 모양이다. DataLoader는 N+1만 줄일 뿐, 데이터 양 자체의 폭발은 막지 못한다.
- 마지막 줄은 직접 만든 깊이 제한 검증 규칙(최대 5)이 깊이 9인 쿼리를 **실행 전에** 거절한 결과다.

### 4. 쿼리 비용 제한 — 실행 전에 거절한다

```text
  파싱 ──(토큰 수 상한)──> 검증 ──(깊이·복잡도·별칭 수 규칙)──> 실행 ──(타임아웃·페이지 상한)──> 응답
         maxTokens              커스텀 검증 규칙                    리졸버 안 제한
```

- graphql.org "Security" 페이지가 드는 방어
  - *깊이 제한*: 한 연산의 필드 중첩 깊이 상한. 목록 중첩에는 더 작은 별도 상한을 권한다.
  - *폭·배치 제한*: 최상위 필드·별칭(alias) 수, 한 배치 요청의 연산 수 상한.
  - *복잡도(비용) 분석*: 타입·필드에 가중치를 매겨 요청 비용을 추정하고, 상한을 넘으면 거절.
  - *신뢰 문서(trusted documents, persisted queries)*: 허용된 연산 목록만 실행. 1차 클라이언트(자사 앱)에서만 쓸 수 있다.
  - 목록 필드는 페이지 단위로 내보내 한 번에 나가는 항목 수를 제한한다([06-pagination](../06-pagination/2-summary.md)).
  - 1차 클라이언트(자사 앱)만 쓰는 API라면 개발 외 환경에서 인트로스펙션을 막을 수 있다. 이것만으로는 부족하다(숨기기일 뿐 — 신뢰 문서·인가가 더 효과적).
  - 상세 오류 메시지는 개발 외 환경에서 가린다(실행 중 오류의 내부 정보 포함).
- graphql-js 16.14 기준
  - 일반 깊이 제한 규칙은 **내장돼 있지 않다**. `specifiedRules`에는 인트로스펙션 쿼리 전용 `MaxIntrospectionDepthRule`(목록 깊이 3)만 들어 있다(소스 `validation/specifiedRules.js`). 일반 깊이 제한은 커스텀 규칙이나 별도 라이브러리로 붙인다.
  - `parse()`에 `maxTokens` 옵션이 있다. 타입 정의 주석: 파싱은 검증보다 먼저라 잘못된 쿼리도 CPU·메모리를 태울 수 있으니 토큰 수 상한을 두라는 설명이다.

### 5. 오류 형식 — HTTP 상태가 아니라 응답 본문에

```text
  { boom  posts(limit: 1) { title } }     ← boom 리졸버가 예외를 던짐

  {"errors":[{"message":"internal: db timeout","locations":[{"line":1,"column":3}],"path":["boom"]}],
   "data":{"boom":null,"posts":[{"title":"t0"}]}}
```

(실험 출력 그대로, 위와 같은 환경)

- GraphQL 명세(October 2021판 7.1·7.1.2)
  - `errors`의 각 항목은 `message`가 필수다. 결과의 특정 필드와 연결되는 오류(필드 오류)는 `path`를 넣어야 한다(must). 문서 위치와 연결되면 `locations`를 넣는다(should). `extensions`는 선택.
  - 실행 전 요청 오류(파싱·검증 실패)면 `data`가 없다. 실행 중 필드 오류면 `data`가 있고 그 필드가 null이 된다 — **부분 성공**.
  - non-null 필드가 오류를 내면 null이 부모로 번진다. 루트까지 번지면 `data` 전체가 null.
- 위 출력에서 `boom`은 nullable이라 그 자리만 null이 됐고 `posts`는 정상으로 왔다.
- 내부 예외 문구(`internal: db timeout`)가 그대로 나갔다. graphql.org Security 페이지가 권하는 "상세 오류 가리기"가 필요한 이유다([04-error-format-problem-details](../04-error-format-problem-details/2-summary.md)).
- HTTP 상태 코드는 GraphQL 명세가 아니라 **GraphQL over HTTP 명세**(현재 Working Draft)가 다룬다.
  - 문서 파싱 실패 400, 검증 실패 422(SHOULD). 결과에 `data`가 있고 null이 아니면(일부 필드 오류 포함) 2xx(MUST).
  - `data`와 `errors`가 함께 있으면 294 Partial Success를 권한다(SHOULD, 2026-10-04에 연 Working Draft 기준). 294는 IANA에 등록되지 않은 자체 코드라, 모르는 클라이언트는 200처럼 다룬다. 같은 초안의 예시 절은 아직 "실행 오류가 있어도 200"이라고 적는다 — 판마다 바뀌는 초안이다.
  - 옛 클라이언트가 `application/json`만 받겠다고 하면 같은 규칙으로 처리하되, 2xx 응답의 `Content-Type`만 `application/json`으로 바꾼다.
  - 다만 같은 초안 6.1은 294를 `application/graphql-response+json`과 **함께만** 권한다(뜻을 미디어 타입이 밝혀 주므로). 그래서 `application/json` 응답의 부분 성공은 294 대신 200으로 두는 쪽이 6.1에 맞는다(해석 — 초안 안의 두 문장이 아직 맞물리지 않는다).
  - 그래서 4xx·5xx만 오류로 세는 **HTTP 상태 모니터링은 필드 오류를 못 센다**([03-status-codes-for-apis](../03-status-codes-for-apis/2-summary.md)). `errors` 개수를 따로 지표로 낸다.

## 쓰이는 자료구조·알고리즘

- **트리 순회**: 쿼리 문서는 AST(트리)다. 실행은 선택 집합(selection set)을 깊이 우선으로 내려가며 필드마다 리졸버를 부른다. 깊이 제한 규칙도 같은 DFS로 최대 깊이를 잰다 → [algorithm/12-dfs](../../algorithm/12-dfs/2-summary.md).
- **배치 + 메모이제이션(DataLoader)**: 키 큐(배열) + 키→Promise 맵(캐시). 같은 틱에 모인 키를 한 번에 보내고, 같은 키는 맵에서 바로 꺼낸다 → [data-structure/05-hashmap](../../data-structure/05-hashmap/2-summary.md).
- **비용 추정**: 필드 가중치 × 목록 크기(`first`·`limit` 인자)를 트리 위로 곱해 올라가는 계산. 목록이 겹치면 곱이 되므로 깊이만이 아니라 인자도 봐야 한다.
- **스키마 = 그래프**: 타입이 노드, 필드가 간선이다. `User.posts`·`Post.author`처럼 순환이 있으면 쿼리 깊이가 무한해질 수 있다 → [data-structure/08-graph](../../data-structure/08-graph/2-summary.md).

## 적용 — 풀어나가는 법

### 1. 설계 순서

1. 스키마를 화면이 아니라 **도메인 그래프**로 그린다. 목록 필드는 처음부터 페이지 인자(`first`·`after`)와 상한을 둔다.
2. 다른 테이블·서비스를 읽는 필드 리졸버는 처음부터 DataLoader로 감싼다. 로더는 **요청마다** 새로 만든다(컨텍스트에 넣는다).
3. 실행 전 방어: `maxTokens` → 깊이 제한 → 복잡도 상한 → 별칭·배치 수 상한. 자사 앱만 쓰면 신뢰 문서(허용 목록)가 가장 강하다.
4. 실행 중 방어: 요청 타임아웃, 리졸버별 타임아웃, 페이지 크기 상한.
5. 관측: HTTP 상태 대신 `errors` 수, 연산 이름별 지연, 리졸버별 DB 쿼리 수를 지표로 낸다.

### 2. Java — graphql-java의 DataLoader (형태)

graphql-java는 JS DataLoader를 옮긴 `java-dataloader`를 쓴다. 아래는 모양만 보이는 코드다(이 노트에서 실행하지 않았다). API 이름은 java-dataloader README·`DataLoaderRegistry.java`와 graphql-java `DataFetchingEnvironment.getDataLoader(String)`(두 저장소 master, 2026-10-04 확인)에 맞췄다.

```java
// 요청마다 레지스트리를 새로 만든다 — 사용자 간 캐시 공유 금지
DataLoaderRegistry registry = new DataLoaderRegistry();
BatchLoader<Long, User> userBatch = ids -> CompletableFuture.supplyAsync(() -> {
    Map<Long, User> byId = userRepo.findAllById(ids).stream()
        .collect(Collectors.toMap(User::id, u -> u));
    return ids.stream().map(byId::get).toList();   // 키 순서대로, 없는 키는 null
});
registry.register("user", DataLoaderFactory.newDataLoader(userBatch));

// Post.author 리졸버
DataFetcher<CompletableFuture<User>> author = env -> {
    Post p = env.getSource();
    return env.<Long, User>getDataLoader("user").load(p.authorId());
};
```

- 옛 판에는 없는 메서드가 있을 수 있으니 쓰는 버전의 문서를 본다. 핵심은 JS와 같다: **키 순서 정렬**과 **요청 범위 레지스트리**.

### 3. 진단

- N+1 의심: 요청 하나당 DB 쿼리 수를 로그·APM에서 본다. 목록 크기에 비례해 쿼리 수가 늘면 N+1이다(위 실험의 11·51·101).
- 비싼 쿼리 찾기: 연산 이름(`operationName`)별 지연·응답 크기 분포. 이름 없는 익명 쿼리가 많으면 신뢰 문서 도입을 검토한다.
- 공격 의심: 짧은 쿼리 문자열인데 응답이 크고 느린 요청. 깊이·별칭 수를 로그에 남긴다.

## 장애 시나리오와 대처

### 1. 목록 화면이 데이터가 늘수록 느려진다 — N+1 (⚠)

- **현상**: 글 10개일 땐 빠르던 화면이 100개에서 눈에 띄게 느려진다.
- **보이는 형태**: 요청 하나에 같은 모양 SQL(`WHERE id = ?`)이 수십~수백 번. DB 커넥션 풀 대기 증가.
- **원인**: 필드 리졸버가 원소마다 따로 조회한다. 실험에서 N=100이면 101개였다.
- **대처**: DataLoader로 배치(실험에서 2개). 배치 함수가 키 순서를 지키는지 테스트한다. 로더 인스턴스를 전역으로 두지 않는다.

### 2. 쿼리 하나로 서버가 멈춘다 — 깊이·복잡도 제한 없음 (⚠)

- **현상**: 특정 요청 하나가 들어온 뒤 CPU·메모리가 튀고 다른 요청이 밀린다.
- **보이는 형태**: 요청 본문은 수백 바이트인데 응답이 수백 KB~MB, 처리 시간이 길다. 실험에서 깊이를 한 단계 늘릴 때마다 응답이 약 10배였다.
- **원인**: `User.posts`·`Post.author` 같은 순환 관계를 제한 없이 겹친 쿼리. 별칭으로 같은 필드를 수백 번 부르는 변형도 있다.
- **대처**: 실행 전 깊이·복잡도·별칭 수 검증, `maxTokens`, 목록 페이지 상한, 요청 타임아웃. 자사 앱이면 신뢰 문서로 임의 쿼리 자체를 막는다.

### 3. 에러율 대시보드는 0%인데 사용자는 화면이 비었다고 한다

- **현상**: 일부 위젯이 비어 있다.
- **보이는 형태**: HTTP 200, 본문 `errors`에 항목이 있고 해당 필드가 null.
- **원인**: GraphQL은 부분 성공을 2xx로 돌려준다(GraphQL over HTTP 초안 기준 `data`가 null이 아니면 2xx — 200, 또는 초안이 권하는 294). 4xx·5xx만 세는 모니터링에는 안 잡힌다.
- **대처**: 서버에서 `errors` 수·`path`별 오류를 지표로 낸다. 클라이언트는 `errors`를 무시하지 않고 필드별 대체 UI를 둔다.

### 4. 다른 사용자의 데이터가 보인다 — DataLoader 캐시 공유

- **현상**: 드물게 다른 사람의 이름·권한 정보가 화면에 나온다.
- **보이는 형태**: 재현이 어렵고, 부하가 높을 때만 나온다.
- **원인**: DataLoader 인스턴스를 서버 전역으로 만들어 요청 간 캐시가 섞였다. README가 명시적으로 피하라고 한 사용법이다.
- **대처**: 로더를 요청 컨텍스트에서 생성한다. 권한별로 결과가 다른 조회는 키에 사용자 범위를 넣거나 로더를 분리한다.

### 5. 내부 예외 문구가 그대로 나간다

- **현상**: 응답 `errors[].message`에 SQL·호스트명·스택 일부가 보인다.
- **원인**: 리졸버 예외 메시지를 그대로 직렬화한다(실험의 `internal: db timeout`).
- **대처**: 오류 포매터에서 내부 예외는 일반 문구 + 추적 ID로 바꾸고, 원문은 서버 로그에만 남긴다. 클라이언트가 분기할 정보는 `extensions.code`처럼 정해진 칸에 둔다.

## 핵심 문장

- GraphQL은 클라이언트가 필드 모양을 쿼리로 적어 보내고, 서버가 스키마로 검증한 뒤 필드마다 리졸버를 불러 채운다.
- 리졸버가 필드 단위라서 목록 아래 필드는 원소마다 조회되기 쉽다(1 + N). DataLoader는 같은 틱의 키를 모아 한 번에 보내고 요청 범위로 캐시한다.
- 목록 필드가 겹치면 쿼리 길이는 그대로인데 일은 곱으로 는다. 깊이·복잡도·토큰 수 제한은 실행 **전에** 걸어야 한다.
- GraphQL은 부분 성공을 `data` + `errors`로 돌려주고 HTTP는 2xx일 수 있다. 오류 관측은 본문 `errors`를 기준으로 한다.
- graphql-js 16에는 일반 깊이 제한 규칙이 내장돼 있지 않다 — 직접 붙인다.

## 관련 주제·근거

- 선행
  - [02-rest-and-resource-modeling](../02-rest-and-resource-modeling/2-summary.md) — 자원·균일 인터페이스
- 후속·연결
  - [18-api-style-selection](../18-api-style-selection/2-summary.md) — REST·gRPC·GraphQL 중 무엇을 고르나, GraphQL POST와 HTTP 캐시
  - [19-api-gateway-and-bff](../19-api-gateway-and-bff/2-summary.md) — BFF 대안으로서의 GraphQL
  - [06-pagination](../06-pagination/2-summary.md) · [03-status-codes-for-apis](../03-status-codes-for-apis/2-summary.md) · [04-error-format-problem-details](../04-error-format-problem-details/2-summary.md) · [14-rate-limit-and-quota-contracts](../14-rate-limit-and-quota-contracts/2-summary.md) — 영역 표: [curriculum](../curriculum.md)
  - network [34-http-caching](../../network/34-http-caching/2-summary.md) — POST 응답이 캐시되지 않는 이유
  - reliability [11-rate-limiter](../../reliability/11-rate-limiter/2-summary.md) · [05-timeouts-and-deadline-propagation](../../reliability/05-timeouts-and-deadline-propagation/2-summary.md)
  - reliability [40-batching-and-round-trips](../../reliability/40-batching-and-round-trips/2-summary.md) — 배치로 왕복 줄이기
- 명세·문서
  - GraphQL 명세 September 2025판(최신), October 2021판 7장 Response(7.1.2 Errors: `message` 필수, 필드 오류면 `path` must, `locations` should, `extensions` 선택) <https://spec.graphql.org/>
  - GraphQL over HTTP (Working Draft, 2026-10-04 열람) — GET은 쿼리만, 뮤테이션 GET 금지(405 권장), 5.4 Status Codes의 400·422·2xx(MUST)·294(SHOULD) 규칙, 6.1 Partial success <https://http-spec.graphql.org/draft/>
  - graphql.org "Security"(깊이·폭·배치 제한, 복잡도 분석, 신뢰 문서, 페이지, 1차 클라이언트 API의 인트로스펙션 차단, 오류 가리기) <https://graphql.org/learn/security/>
  - graphql.org "Performance"(N+1과 DataLoader, GET 캐시와 persisted queries) <https://graphql.org/learn/performance/>
  - graphql/dataloader README(배치 함수 계약, 요청 범위 캐시) <https://github.com/graphql/dataloader>
  - graphql-js 16.14.2 소스 — `language/parser.d.ts`의 `maxTokens`, `validation/specifiedRules.js`의 `MaxIntrospectionDepthRule`
- 실험 목록
  - N+1 vs DataLoader 쿼리 수(N=10·50·100), 깊이별 응답 크기·SQL 수·시간, 커스텀 깊이 제한 규칙, 부분 성공 오류 형식 — node 22.23.2 · graphql 16.14.2 · dataloader 2.2.3, `node:22-alpine` 컨테이너(`--network none`, `--cpus=2`). 사실 점검에서 두 번 다시 돌려 시간 외 출력이 같았다
