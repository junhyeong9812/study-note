# api-design/17-graphql — 정답

## 정답

### 1. GraphQL이 줄이는 것과 새 문제

- 줄이는 것: 화면 하나에 필요한 데이터를 **요청 한 번**에, **필요한 필드만** 받는다. REST 자원을 여러 번 왕복하는 under-fetching과 안 쓰는 필드를 받는 over-fetching이 준다.
- 새 문제
  - **N+1**: 리졸버가 필드 단위라 목록 아래 필드가 원소마다 조회된다.
  - **쿼리 비용 폭발**: 순환 관계(`User.posts`·`Post.author`)를 겹친 짧은 쿼리 하나가 서버 일을 곱으로 늘린다 → DoS.

### 2. 리졸버 그대로면 1 + N

```text
  Query.posts          ── SELECT * FROM post LIMIT 10        1번
   ├ post0.author      ── SELECT * FROM user WHERE id = 0    ┐
   ├ ...                                                      │ 10번
   └ post9.author      ── SELECT * FROM user WHERE id = 9    ┘
```

- 합계 11번. 실험(graphql-js 16.14.2)에서도 `N=10 리졸버 그대로 SQL 11개`였다.
- `Post.author` 리졸버는 자기 글 하나만 받는다. 옆 글의 리졸버가 무엇을 읽는지 모르니 각자 따로 조회한다.

### 3. DataLoader면 2개, `IN`에는 10개

- 실험 출력: `N=100 DataLoader SQL 2개`. 글 조회 1번 + 사용자 일괄 조회 1번.
- `IN` 목록에는 id 10개(0~9)만 들어간다. 같은 틱에 `load()`가 100번 불려도 같은 키는 캐시가 한 번만 배치에 넣는다(실험 출력 `SELECT * FROM user WHERE id IN (0,1,2,3,4,5,6,7,8,9)`).
- 리졸버 그대로면 같은 조건에서 101개였다.

### 4. 배치 함수 계약

- 반환 배열의 **길이 = 키 배열의 길이**.
- **i번째 값 = i번째 키의 결과**.
- DB가 다른 순서로 주면 키 순서대로 다시 정렬한다. 없는 키 자리에는 `null`이나 `Error`를 넣는다(graphql/dataloader README의 `[2, 9, 6, 1]` 예).
- 이를 어기면 다른 글에 다른 작성자가 붙는 식의 **조용한 오답**이 난다.

### 5. 전역 DataLoader의 문제

- DataLoader 캐시는 "요청 하나 안에서 같은 키를 다시 읽지 않기" 위한 메모이제이션이다.
- 전역으로 두면 요청 간에 캐시가 공유된다. 권한에 따라 결과가 다른 데이터가 다른 사용자에게 보일 수 있고, 갱신된 값 대신 옛 값이 계속 나온다.
- README: 여러 사용자의 요청이 같은 인스턴스를 쓰지 말라. 보통 요청이 시작될 때 만들고 끝나면 버린다. 공유 캐시(Redis·Memcache)를 대신하지 않는다.

### 6. 깊이에 따른 폭발

- 실험 출력

```text
깊이+0: 응답      261 바이트, SQL 2개, 3ms
깊이+1: 응답     2741 바이트, SQL 12개, 6ms
깊이+2: 응답    27541 바이트, SQL 112개, 58ms
깊이+3: 응답   275541 바이트, SQL 1112개, 359ms
```

- 한 단계마다 응답이 약 10배(사용자당 글 10개). SQL도 `User.posts`가 배치되지 않아 10배씩 늘었다. 시간은 실행마다 다르다(깊이+3이 네 번 실행에서 294~379ms).
- DataLoader는 같은 종류의 조회를 묶어 **왕복 수**를 줄일 뿐이다. 클라이언트가 요구한 **데이터 양**은 그대로라 응답 크기·직렬화·메모리 비용은 줄지 않는다. 막으려면 실행 전에 거절해야 한다.

### 7. 쿼리 비용 방어

| 단계 | 방어 |
|---|---|
| 파싱 전·중 | 요청 본문 크기 상한, graphql-js `parse()`의 `maxTokens` |
| 검증 | 깊이 제한, 복잡도(가중치) 상한, 별칭·최상위 필드 수 상한, 배치 연산 수 상한, 신뢰 문서(허용 목록) |
| 실행 중 | 요청·리졸버 타임아웃, 목록 페이지 크기 상한, 비싼 필드에 대한 속도 제한 |

- graphql-js 16.14.2의 `specifiedRules`에는 인트로스펙션 쿼리 전용 `MaxIntrospectionDepthRule`만 있다. 일반 깊이 제한 규칙은 **내장돼 있지 않다** — 실험에서는 DFS로 깊이를 재는 커스텀 규칙을 붙였고 `query depth 9 exceeds 5`로 실행 전에 거절됐다.

### 8. 200인데 위젯이 비었다

- 응답 본문 `errors`를 본다. 해당 필드가 null이고 `errors[].path`가 그 필드를 가리킨다(부분 성공).
- 실험 출력: `{"errors":[{"message":"internal: db timeout",...,"path":["boom"]}],"data":{"boom":null,"posts":[{"title":"t0"}]}}`
- GraphQL over HTTP(Working Draft, 2026-10-04 열람): 결과에 `data`가 있고 null이 아니면 2xx를 써야 한다(MUST). `data`와 `errors`가 함께 있으면 294 Partial Success를 권한다(SHOULD — IANA 미등록 자체 코드, 모르는 클라이언트는 200처럼 다룬다). `application/json`만 받는 옛 클라이언트에는 같은 규칙을 쓰고 2xx의 `Content-Type`만 `application/json`으로 바꾸라고 적지만, 6.1은 294를 `application/graphql-response+json`과 함께만 권한다 — `application/json` 응답의 부분 성공은 200이 6.1에 맞는다(해석). 문서 파싱 실패 400, 검증 실패 422가 권고다. 어느 쪽이든 2xx라 4xx·5xx만 세는 에러율에는 잡히지 않는다.
- 대처: 서버에서 `errors` 수·`path`별 오류를 지표로 내고, 클라이언트는 필드별 대체 UI를 둔다.

### 9. 내부 오류 문구 노출

- 문제: 리졸버 예외 메시지가 그대로 직렬화돼 SQL·호스트 같은 내부 정보가 공격자에게 보인다. graphql.org Security 페이지가 상세 오류를 가리라고 권한다.
- 대처: 오류 포매터에서 내부 예외를 일반 문구 + 추적 ID로 바꾸고 원문은 서버 로그에만 남긴다. 클라이언트가 분기할 값은 `extensions.code` 같은 정해진 칸으로 준다([04-error-format-problem-details](../04-error-format-problem-details/2-summary.md)의 같은 원칙).
