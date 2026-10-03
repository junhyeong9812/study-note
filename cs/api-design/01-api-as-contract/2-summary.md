# api-design/01-api-as-contract — API는 공개 계약이다: 명시 계약·관찰 가능한 동작·Hyrum의 법칙 — 정리 (힌트)

## 해결하는 문제

API를 만든 팀과 쓰는 팀은 따로 배포한다. 서버를 고칠 때마다 모든 클라이언트를 같이 고칠 수는 없다.

```text
  서버 팀 ── 배포 ──>  [ API ]  <── 호출 ── 클라이언트 A (모바일 앱, 사용자가 업데이트 안 함)
                                 <── 호출 ── 클라이언트 B (다른 팀 배치 작업)
                                 <── 호출 ── 클라이언트 C (외부 회사, 연락처도 모름)

  서버가 바뀌어도 A·B·C가 계속 돌아야 한다
  → "무엇을 바꿔도 되고, 무엇은 못 바꾸나"를 미리 정한 것 = 계약
```

- *API 계약*: 제공자가 소비자에게 약속한 입력·출력·동작의 범위. 문서·스키마·상태 코드 규칙 등으로 적는다.
- 계약이 없으면 서버 팀은 무엇이 "안전한 변경"인지 판단할 근거가 없다. 소비자는 무엇에 기대도 되는지 모른다.

쉬운 예: 콘센트 규격이다.
- 전력 회사는 발전소를 바꿔도 된다. 전압·주파수·구멍 모양만 지키면 된다.
- 그런데 어떤 가전이 "전압이 늘 219V쯤"이라는 우연한 값에 맞춰 만들어졌다면, 규격 안의 변화(220V)에도 고장 난다.

똑같은 구조다.\
API에도 "문서에 적은 약속"과 "어쩌다 그렇게 동작하는 것"이 있다. 소비자가 많아지면 뒤쪽에도 누군가 기댄다.

실무 예(아래 실험에서 재현):
- 목록 API가 지금까지 생성 순서로 나왔다. 앱이 "마지막 원소 = 최근 가입자"로 썼다. 서버가 저장소를 바꾸자 엉뚱한 사람이 "최근 가입자"로 표시됐다. 에러는 나지 않았다.
- 에러 메시지 `"user u-7 not found"`를 문자열로 비교하던 클라이언트가, 문구를 다듬는 배포 뒤 "없는 사용자"를 "알 수 없는 오류"로 처리했다.

## 동작·원리

### 1. 계약의 세 겹

```text
  ┌──────────────────────────────────────────────┐
  │ 구현 (저장소·자료구조·쿼리·스레드 모델 ...)       │  ← 서버 팀이 바꾸고 싶은 것
  │  ┌────────────────────────────────────────┐  │
  │  │ 관찰 가능한 동작                         │  │  ← 소비자가 "보고" 기댈 수 있는 것
  │  │ (목록 순서, JSON 필드 순서, 에러 문구,      │  │     = 암묵 인터페이스
  │  │  응답 시간, 기본값, 빈 필드 생략 여부 ...)   │  │
  │  │  ┌──────────────────────────────────┐  │  │
  │  │  │ 명시 계약 (문서·스키마·상태 코드 규칙) │  │  │  ← 서버 팀이 "약속"한 것
  │  │  └──────────────────────────────────┘  │  │
  │  └────────────────────────────────────────┘  │
  └──────────────────────────────────────────────┘
```

- *명시 계약*: 문서에 적은 약속. 예) "`GET /users`는 사용자 배열을 준다. 순서는 보장하지 않는다."
- *관찰 가능한 동작*: 문서에 없지만 응답에서 보이는 것. 예) 지금 구현에서는 생성 순서로 나온다.
  - Hyrum Wright는 이것을 *암묵 인터페이스(implicit interface)* 라고 부른다(hyrumslaw.com).
- 서버 팀이 지킬 의무는 가운데 상자까지다. 하지만 소비자가 실제로 기대는 것은 바깥 상자까지 퍼진다.

### 2. Hyrum의 법칙 — 저자의 관찰

원문(hyrumslaw.com, SWE@G 1장):

> With a sufficient number of users of an API, it does not matter what you promise in the contract: all observable behaviors of your system will be depended on by somebody.

- 풀면: API 사용자가 충분히 많으면, 계약에 무엇을 약속했는지와 상관없이 관찰 가능한 동작마다 누군가는 기댄다.
- 측정에서 나온 정리가 아니라 **경험에서 나온 관찰**이다.
  - Hyrum Wright가 Google에서 대규모 인프라 이전을 하며 얻었다. "가장 단순한 라이브러리 변경도 먼 곳의 시스템을 깨뜨렸다"(hyrumslaw.com).
  - 이름은 Titus Winters가 붙였다(같은 페이지).
- 같은 페이지의 다른 표현: "충분히 쓰이면 비공개 구현이란 없다(Given enough use, there is no such thing as a private implementation)."
- 결과로 생기는 것: *버그 호환(bug-for-bug compatibility)*. 고친 버그에 기대던 소비자가 있어 버그를 못 고친다.
- SWE@G 1장의 예시는 해시 순회 순서다.
  - 해시 집합에서 꺼내는 순서는 정해지지 않았다고 다들 안다. 그래도 그 순서에 기대는 코드가 생긴다.
  - 해시 플러딩 공격 대응이나 더 빠른 해시 함수 도입은 순서를 바꾼다. 그때 숨은 의존이 드러난다.
  - 순서를 일부러 무작위로 바꾸는 언어도 있다. 그래도 "순회 순서를 값싼 난수로 쓰는 코드"가 생겼다는 예까지 든다(같은 장).

### 3. 무엇이 "깨지는 변경"인가 — 출처별 기준

같은 질문에 출처마다 답의 범위가 다르다. 섞지 않고 나눠 본다.

| 출처 | 판단 기준 | 이 노트와 관련된 규칙 |
|---|---|---|
| Google AIP-180 (회사 설계 지침) | 세 가지 호환: *소스* 호환, *와이어* 호환, *의미* 호환 | 필드·enum 값 추가는 같은 주 버전 안에서 가능. 기본값 변경 금지. 기본값 필드를 "생략하다 → 포함"으로 바꾸는 직렬화 변경도 비호환. 문서에 없는 동작이라도 합리적 사용자 코드를 깨뜨릴 변경은 하지 않는다(must not) |
| Google AIP-193 (에러) | 기계가 읽을 식별자를 따로 준다 | `ErrorInfo`(reason·domain·metadata)를 늘 줬던 RPC만 `Status.message`를 바꿀 수 있다. 그렇지 않았던 기존 API는 메시지를 같은 문구로 유지해야 한다(must) |
| Stripe 블로그 2017 (Brandur Leach) | 있던 필드는 계속 있고, 이름·타입을 유지한다 | 새 엔드포인트·새 필드 추가는 안전. `verified` 불린을 `status` 필드로 바꾼 2014년 변경을 비호환의 예로 든다 |
| RFC 9457 §3.1.4 (표준) | 문제 상세 형식 안의 사람용 문장 | 소비자는 `detail`을 파싱해 정보를 뽑지 않아야 한다(SHOULD NOT). 확장 멤버를 쓰라 |

- *소스 호환*: 이전 버전 기준으로 쓴 코드가 새 클라이언트 라이브러리로 컴파일·실행된다(AIP-180).
- *와이어 호환*: 이전 버전 기준 코드가 새 서버와 올바르게 통신한다. 직렬화·역직렬화 기대가 맞는다(AIP-180).
- *의미 호환*: 이전 코드가 "합리적인 개발자가 기대할 결과"를 계속 받는다. AIP-180도 판단이 필요하다고 적는다.
- AIP-180의 전제: 여러 언어의 소비자가 있고, 소비자 업데이트를 통제할 수 없는 API다. 같은 팀만 쓰거나 업데이트를 강제할 수 있는 API는 기준을 따로 정하라고 적는다.

### 4. 계약 = 사전조건·사후조건을 네트워크 너머로 옮긴 것

```text
  메서드 계약 (software-design/23)          API 계약
  ─────────────────────────────          ──────────────────────────────────
  사전조건: 호출자가 지킬 것                요청 스키마·필수 필드·인증·멱등 키 규칙
  사후조건: 구현이 보장할 것                응답 스키마·상태 코드·부작용(생성됐나?)
  불변식:   늘 참인 것                     자원 규칙(잔액 ≥ 0, id는 바뀌지 않음)
  하위 타입은 계약을 약화 못 함               새 버전은 옛 클라이언트를 깨면 안 됨(하위 호환)
```

- 같은 프로세스 안의 메서드 계약은 컴파일러·테스트가 함께 지켜 준다.
- 네트워크 API는 소비자 코드가 다른 저장소·다른 회사에 있다. 깨져도 서버 쪽 빌드는 초록색이다.
- 그래서 API 쪽은 (1) 계약을 기계가 읽을 수 있게 적고, (2) 약속하지 않은 것을 명시하고, (3) 변경 전에 소비자 기대를 검사하는 장치(계약 테스트, testing/13)가 필요하다.

### 실험: "무해한" 서버 변경 세 개가 클라이언트를 깨뜨린다

문서화한 계약은 아래 두 줄뿐이다.

```text
  GET /users       -> {"users":[{id,name,createdAt}...]}   순서는 보장하지 않는다(정렬은 createdAt으로)
  GET /users/{id}  -> 없으면 404 + {"code":"USER_NOT_FOUND","message":...}   message는 사람용
```

v1 → v2에서 서버 팀이 한 변경 세 가지. 셋 다 계약 안의 변경이다.

```text
  (1) 저장소: LinkedHashMap(삽입 순서) → ConcurrentHashMap(스레드 안전 "개선")
  (2) 응답 레코드 필드 선언 순서: (id, name, createdAt) → (name, id, createdAt)   (리팩터링)
  (3) 에러 문구: "user u-9999 not found" → "No user with id 'u-9999'"          (문구 다듬기)
```

클라이언트 네 종류(핵심 코드, Java 21 + Jackson 2.19.2):

```java
// A. 계약만 쓴다: 이름으로 읽고, 정렬은 직접, 에러는 상태 코드 + code로
List<JsonNode> sorted = new ArrayList<>(); users.forEach(sorted::add);
sorted.sort(Comparator.comparingLong(n -> n.get("createdAt").asLong()));
boolean aNotFound = nf.statusCode() == 404
        && M.readTree(nf.body()).get("code").asText().equals("USER_NOT_FOUND");

// B. 목록 순서에 기댄다: 첫 원소 = 가장 오래된, 끝 원소 = 최근 가입
String bNewest = users.get(users.size() - 1).get("name").asText();

// C. 원문 JSON에 정규식 (필드 순서 id → name 가정)
Pattern.compile("\\{\"id\":\"([^\"]+)\",\"name\":\"([^\"]+)\"").matcher(list);

// D. 에러 문구로 '없는 사용자' 판정
boolean dNotFound = msg.startsWith("user ") && msg.endsWith(" not found");
```

(실험, JDK 21.0.12 temurin + Jackson 2.19.2, `com.sun.net.httpserver` + JDK `HttpClient`, 사용자 12명, 2026-10-04)

```text
== 서버 v1
  GET /users 순서  -> u-1001,u-1002,u-1003,u-1004,u-1005,u-1006,u-1007,u-1008,u-1009,u-1010,u-1011,u-1012  첫 객체: {"id":"u-1001","name":"kim","createdAt":1700000000}
  GET /users/u-9999 -> 404 {"code":"USER_NOT_FOUND","message":"user u-9999 not found"}
  A 계약 클라이언트      : 가장 오래된=kim, 최근 가입=oh, 없는 사용자 판정=true
  B 목록 순서 가정       : 가장 오래된(첫 원소)=kim, 최근 가입(끝 원소)=oh
  C 정규식(필드 순서)    : 읽은 사용자 수=12 / 12
  D 에러 문구 파싱       : 없는 사용자 판정=true
== 서버 v2
  GET /users 순서  -> u-1001,u-1012,u-1002,u-1003,u-1004,u-1005,u-1006,u-1007,u-1008,u-1010,u-1011,u-1009  첫 객체: {"name":"kim","id":"u-1001","createdAt":1700000000}
  GET /users/u-9999 -> 404 {"code":"USER_NOT_FOUND","message":"No user with id 'u-9999'"}
  A 계약 클라이언트      : 가장 오래된=kim, 최근 가입=oh, 없는 사용자 판정=true
  B 목록 순서 가정       : 가장 오래된(첫 원소)=kim, 최근 가입(끝 원소)=jang
  C 정규식(필드 순서)    : 읽은 사용자 수=0 / 12
  D 에러 문구 파싱       : 없는 사용자 판정=false
```

관찰:
- v1에서는 네 클라이언트가 모두 맞는다. 테스트가 있었다면 넷 다 통과했을 것이다.
- v2에서 계약만 쓴 A만 맞다.
- B는 **반만** 틀렸다. 첫 원소는 여전히 `kim`이라 "가장 오래된 사용자" 기능은 멀쩡해 보인다. 끝 원소는 `jang`(u-1009)으로 바뀌었다.
  - 처음 5명으로 돌렸을 때는 ConcurrentHashMap 순서가 삽입 순서와 같게 나와 B가 전혀 깨지지 않았다. 숨은 의존은 **데이터가 바뀌어야** 드러난다.
- C는 예외 없이 0명을 읽었다. D는 예외 없이 오분류했다. 셋 다 **조용한 실패**다.
- Jackson 2.19.2는 레코드를 컴포넌트 선언 순서대로 썼다(관찰). 필드 순서는 리팩터링만으로 바뀐다.
  - 라이브러리 메이저 교체도 같은 종류의 변경이다. Jackson 3.x는 기본값이 `MapperFeature.SORT_PROPERTIES_ALPHABETICALLY=true`로 바뀌었다(jackson-databind 3.0 소스 `MapperFeature.java`). Jackson 2→3 교체만으로 출력 필드 순서가 바뀔 수 있다.

추가 관찰 — 같은 코드도 실행마다 순서가 다르다:

```java
System.out.println(Map.of("code", "USER_NOT_FOUND", "message", "user u-9999 not found").keySet());
```

(실험, JDK 21.0.12 temurin, JVM을 10번 새로 띄움, 2026-10-04)

```text
      6 [code, message]
      4 [message, code]
```

- 비율은 실행마다 다르다. 사실 점검 재실행(같은 명령, 10회)에서는 8:2였다.

- `Map.of`가 만드는 불변 맵은 순회 순서가 "정해지지 않았고 바뀔 수 있다"(JDK 21 `java.util.Map` Javadoc).
- 구현은 JVM 시작 때 `System.nanoTime()`으로 정한 `SALT32L`로 순서를 섞는다(jdk21u `ImmutableCollections.java`). Hyrum의 법칙에 대한 JDK 쪽 방어다.
- 이 실험의 서버도 에러 본문을 `Map.of`로 만들었다. 그래서 에러 JSON의 키 순서는 배포(재시작)마다 바뀔 수 있다.

## 쓰이는 자료구조·알고리즘

- **해시 테이블의 순회 순서**: 버킷 배열을 앞에서부터 돈다. 순서는 키의 해시값과 테이블 크기가 정한다. 삽입 순서와 무관하다. 크기가 커지면(재해시) 순서가 또 바뀐다 — [data-structure/05-hashmap](../../data-structure/05-hashmap/2-summary.md).
  - 실험에서 12명일 때 순서가 섞인 이유를 따로 찍어 봤다. 키를 1개씩 넣으며 순회 순서와 테이블 크기를 출력했다(`키@버킷 번호`).

(실험, JDK 21.0.12 temurin, `new ConcurrentHashMap<>()`, 2026-10-04)

```text
n= 9 table=16  1001@0 1002@1 1003@2 1004@3 1005@4 1006@5 1007@6 1008@7 1009@8
n=11 table=16  1001@0 1002@1 1003@2 1004@3 1005@4 1006@5 1007@6 1008@7 1009@8 1010@14 1011@15
n=12 table=32  1001@0 1012@0 1002@1 1003@2 1004@3 1005@4 1006@5 1007@6 1008@7 1010@14 1011@15 1009@24
```

  - 11명까지는 삽입 순서 그대로였다. `u-1010`의 해시값이 자리올림으로 22 뛰었지만(14번 버킷), 뒤쪽 버킷이라 순서는 안 바뀌었다.
  - 12번째 삽입에서 처음 섞였다. 기본 테이블 16칸의 임계값 12(0.75)에 닿아 32칸으로 커졌다(재해시).
  - 버킷 번호 = 확산 함수 `h ^ (h >>> 16)` 결과의 아래 비트다. `u-1012`는 `u-1001`과 같은 0번 버킷에 들어가 둘째 자리로 왔다. `u-1009`는 XOR로 섞인 상위 비트 때문에 32칸에서 24번 버킷(16칸에서는 8번)으로 가 맨 끝이 됐다.
  - 5명일 때 삽입 순서와 같았던 것도 이 키들에서 나온 우연이다. 확산 함수는 순서를 지키는 함수가 아니다. "지금은 맞다"가 "계약이다"를 뜻하지 않는 이유다.
- **연결 해시 맵(LinkedHashMap)**: 해시 테이블 + 이중 연결 리스트로 삽입 순서를 기억한다. v1이 "우연히" 생성 순서를 준 이유다.
- **결정적 정렬 키**: 순서를 계약에 넣으려면 정렬 키를 정하고, 같은 값끼리의 순서(tie-breaker, 보통 id)까지 정해야 한다. 페이지 나누기(06)의 커서가 이 정렬 키 위에 선다.
- **스키마 검사**: 요청·응답을 JSON Schema·OpenAPI(21)·Protobuf(08)로 적으면 "명시 계약"을 기계가 검사할 수 있다. 관찰 가능한 동작은 스키마로 다 잡히지 않는다(순서·문구·시간).

## 적용 — 풀어나가는 법

### 1. 순서

1. **약속할 것을 적는다.** 필드 의미·타입·필수 여부, 상태 코드 규칙, 기계용 에러 식별자(`code`·`type`).
2. **약속하지 않는 것도 적는다.** "목록 순서는 `orderBy`를 주지 않으면 정해지지 않는다", "JSON 필드 순서는 의미 없다", "`message`·`detail` 문구는 바뀔 수 있다. `code`로 분기하라."
3. **기댈 거리를 준다.** 정렬이 필요하면 `orderBy` 파라미터(12)를, 에러 분기가 필요하면 안정된 `code`(04)를 준다. 소비자가 우회로를 만들 이유를 없앤다.
4. **숨은 의존을 드러낸다.** 순서가 계약이 아니라면, 테스트·스테이징 환경에서 순서를 일부러 섞어 응답하는 방법이 있다(JDK `Map.of`가 하는 일). 운영에서도 섞을지는 비용(캐시 키, 디버깅 난이도)과 같이 판단한다.
5. **변경 전 소비자 기대를 검사한다.** 소비자 주도 계약 테스트([testing/13](../../testing/13-contract-testing/2-summary.md))로 "누가 무엇을 쓰는지"를 서버 빌드에서 본다.
6. **깨는 변경은 버전·폐기 절차로 한다** — [07-versioning-and-compatibility](../07-versioning-and-compatibility/2-summary.md).

### 2. 소비자 쪽: 관대한 리더(Tolerant Reader)

Fowler(2011, "TolerantReader")는 Postel의 법칙("보낼 때는 보수적으로, 받을 때는 관대하게")을 서비스 협업에 적용하라고 한다(저자 주장). 필요한 필드만 이름으로 읽고, 모르는 필드는 무시한다.

```java
// Jackson 2.x: 모르는 필드가 오면 기본은 실패한다
ObjectMapper strict = new ObjectMapper();
ObjectMapper tolerant = strict.copy()
        .disable(DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES);
```

(실험, Jackson 2.19.2, 서버가 `tier` 필드를 추가한 응답을 2필드 레코드로 읽음, 2026-10-04)

```text
FAIL_ON_UNKNOWN_PROPERTIES 기본값 = true
엄격 리더: UnrecognizedPropertyException - Unrecognized field "tier" (class Unknown$User), not marked as ignorable (2 known properties: "id", "name"])
관대한 리더: User[id=u-1, name=kim]
```

- 필드 추가는 AIP-180·Stripe 모두 "호환 변경"으로 본다. 그래도 Jackson 2.x 기본값 그대로 쓴 소비자는 깨진다.
  - Jackson 3.x는 이 기본값이 `false`다(jackson-databind 3.0 소스 `DeserializationFeature.java`). 같은 코드도 라이브러리 메이저 버전에 따라 결과가 달라진다. 계약의 양쪽이 모두 필요하다(07에서 enum 값 추가까지 이어서 다룬다).
- 관대함에도 한계가 있다. 모르는 필드를 무시하는 것과, 모르는 enum 값을 "기타"로 처리하는 것은 다르다. 후자는 소비자가 의미를 정해야 한다.

### 3. 진단 — 누가 무엇에 기대나

```bash
# 응답 원문을 그대로 본다: 필드 순서·목록 순서·에러 문구가 계약 밖의 것인지 확인
curl -s -i https://api.example.com/users | head -20

# 소비자 코드에서 숨은 의존 냄새 찾기 (예시 패턴)
grep -rnE 'get\(0\)|\[0\]|size\(\) ?- ?1|\.message\b.*(startsWith|contains|equals|match)' src/
grep -rnE 'Pattern\.compile\(.*\\"id\\"' src/      # 원문 JSON 정규식
```

- 서버 쪽에서는 접근 로그에 소비자 식별자(API 키·User-Agent)를 남긴다. 변경 전에 "이 필드·이 엔드포인트를 누가 부르나"를 셀 수 있어야 한다.

## 장애 시나리오와 대처

### 1. 정렬 순서에 기댄 클라이언트 → "버그 수정"이 장애 (⚠ 커리큘럼)

- **현상**: 서버가 목록 쿼리를 최적화했다. 일부 화면에 "최근 주문"이 엉뚱하게 나온다.
- **보이는 형태**: 에러 로그·5xx 없음. 고객 문의로 먼저 안다. 클라이언트 코드에 `list.get(0)`·`last()`가 있다.
- **원인**: 응답 순서는 계약이 아니었다. 이전 구현(삽입 순서 맵, 인덱스 순서 스캔)이 우연히 정렬된 결과를 줬다. 실험의 B와 같다.
- **대처**
  - 단기: 이전 순서를 임시로 되돌린다(버그 호환). 영향 소비자를 찾는다.
  - 장기: 순서가 필요하면 `orderBy`를 계약으로 만든다. 정렬 키 + tie-breaker를 문서화한다. 정렬을 주지 않는 경로는 "정해지지 않음"을 명시하고, 테스트 환경에서 섞는다.

### 2. 에러 문구 파싱 → 문구 다듬기가 장애 (⚠ 커리큘럼)

- **현상**: 에러 메시지 다국어화·문구 개선 배포 뒤, 특정 클라이언트가 "없는 사용자"를 일시 오류로 보고 재시도를 반복한다.
- **보이는 형태**: 같은 404 요청이 짧은 간격으로 반복된다. 클라이언트 로그에 "unknown error".
- **원인**: 클라이언트가 `message` 문자열로 분기했다. 실험의 D와 같다. 서버가 기계용 식별자를 주지 않았다면 소비자에게 다른 방법이 없었던 것이다.
- **대처**
  - 서버: 기계용 `code`(또는 RFC 9457 `type`)를 준다. AIP-193의 규칙처럼, 식별자를 준 적 없는 기존 API라면 메시지를 바꾸지 말고 새 필드로 개선 문구를 더한다.
  - 클라이언트: 상태 코드 + `code`로 분기한다. 문구는 표시만 한다.

### 3. 응답 원문을 정규식·문자열로 처리 → 필드 순서 변경에 조용히 0건

- **현상**: 배치 작업이 "처리 0건"으로 정상 종료된다.
- **보이는 형태**: 예외 없음. 처리 건수 지표가 0으로 떨어진다(지표가 없으면 아무도 모른다).
- **원인**: JSON 파서를 쓰지 않고 원문 문자열 패턴에 기댔다. 직렬화 라이브러리 교체·레코드 필드 순서 변경·공백 정책 변경에 깨진다(실험 C).
- **대처**: JSON 파서로 읽는다. 처리 건수 0을 이상 신호로 경보한다. RFC 8259 §1은 JSON 객체를 "순서 없는 모음(unordered collection)"으로 정의하고, §4는 멤버 순서에 기대지 않는 구현이라야 상호 운용된다고 적는다(직렬화 세부는 08).

### 4. 관찰 가능한 의미 변경 → 동기 반영을 비동기로 바꿨더니 "쓴 직후 읽기"가 깨진다

- **현상**: 생성 API 응답 직후 조회하면 404가 난다. 몇 초 뒤엔 보인다.
- **보이는 형태**: 생성 직후 GET의 404 비율이 배포 시점부터 오른다.
- **원인**: 이전 구현은 생성이 끝나면 바로 조회됐다. 소비자는 그것을 계약처럼 썼다. AIP-121은 관리 평면 메서드에 대해 "완료되면 자원 상태가 안정 상태에 도달해야 한다"를 요구한다(회사 지침). 그런 약속 없이 구현이 우연히 줬던 성질이었다면 Hyrum의 법칙이 그대로 적용된다.
- **대처**: 일관성 수준을 문서에 적는다. 바꿔야 하면 새 버전·새 메서드로 하고, 생성 응답에 자원 전체를 담아 바로 조회할 필요를 줄인다. 오래 걸리는 작업은 202 + 작업 자원(13)으로 계약 자체를 바꾼다.

### 5. 기본값·빈 필드 직렬화 변경 → 존재 여부로 분기하던 클라이언트 오동작

- **현상**: 서버가 "기본값이면 필드 생략"을 "항상 포함"으로 바꿨다. 일부 클라이언트가 "필드가 있으면 사용자가 직접 설정한 값"으로 해석해 화면이 바뀐다.
- **보이는 형태**: 응답 크기가 약간 커지고, 특정 기능의 표시가 일제히 바뀐다.
- **원인**: AIP-180은 기본값 필드의 직렬화 방식 변경을 같은 주 버전 안의 비호환 변경으로 분류한다. 소비자가 필드 존재 여부에 의미를 둘 수 있기 때문이다.
- **대처**: 생략/포함 규칙을 계약에 넣고 바꾸지 않는다. Jackson이라면 `@JsonInclude` 정책을 전역 설정 한 곳에 두고, 설정 변경을 API 리뷰 대상으로 삼는다.

## 핵심 문장

- API 계약은 명시한 약속(문서·스키마)이지만, 소비자가 실제로 기대는 범위는 관찰 가능한 동작 전체로 퍼진다(Hyrum의 법칙, 경험적 관찰).
- 순서·필드 순서·에러 문구·응답 시간·기본값처럼 "약속하지 않은 것"은 약속하지 않는다고 적고, 소비자가 기댈 대안(`orderBy`, 안정된 `code`)을 준다.
- 숨은 의존이 깨질 때는 대개 예외가 아니라 조용한 오답으로 나타난다 — 실험에서 4종 중 3종이 예외 없이 틀렸다.
- 깨지는 변경의 기준은 출처마다 범위가 다르다. AIP-180은 소스·와이어·의미 호환을, Stripe는 "있던 필드는 이름·타입 그대로"를, RFC 9457은 "detail을 파싱하지 말라"를 말한다.
- 필드 추가처럼 "호환"이라 분류되는 변경도, 엄격한 역직렬화(Jackson 2.x 기본 `FAIL_ON_UNKNOWN_PROPERTIES=true`) 소비자는 깨뜨린다. 계약은 제공자와 소비자 양쪽 규칙이다.

## 관련 주제·근거

- 선행
  - [software-design/23-design-by-contract](../../software-design/23-design-by-contract/2-summary.md) — 사전조건·사후조건·불변식, 하위 타입의 계약 규칙
- 후속(api-design)
  - [02-rest-and-resource-modeling](../02-rest-and-resource-modeling/2-summary.md) — 자원·균일 인터페이스: 계약을 HTTP 의미로 싣기
  - [03-status-codes-for-apis](../03-status-codes-for-apis/2-summary.md) · [04-error-format-problem-details](../04-error-format-problem-details/2-summary.md) — 에러를 기계가 읽을 계약으로
  - [07-versioning-and-compatibility](../07-versioning-and-compatibility/2-summary.md) · [08-schema-and-serialization](../08-schema-and-serialization/2-summary.md) · [12-filtering-sorting-search](../12-filtering-sorting-search/2-summary.md) · [21-api-documentation-openapi](../21-api-documentation-openapi/2-summary.md)
- 연결
  - [testing/13-contract-testing](../../testing/13-contract-testing/2-summary.md) — 소비자 기대를 제공자 빌드에서 검사
  - [data-structure/05-hashmap](../../data-structure/05-hashmap/2-summary.md) — 해시 순회 순서
  - [network/33-http-semantics](../../network/33-http-semantics/2-summary.md) — HTTP가 이미 정해 둔 계약(메서드·상태 코드)
- 근거
  - Hyrum Wright, "Hyrum's Law" <https://www.hyrumslaw.com/> — 법칙 원문, 암묵 인터페이스, 버그 호환, 이름 유래(Titus Winters)
  - Winters·Manshreck·Wright, *Software Engineering at Google*(O'Reilly, 2020) 1장 "What Is Software Engineering?" — Hyrum's Law 절, "Example: Hash Ordering" <https://abseil.io/resources/swe-book/html/ch01.html>
  - Google AIP-180 Backwards compatibility(소스·와이어·의미 호환, 기본값·직렬화 규칙, "Semantic changes") <https://google.aip.dev/180>
  - Google AIP-193 Errors("Changing error messages", `ErrorInfo` reason·domain·metadata) <https://google.aip.dev/193> · AIP-121 Resource-oriented design("Strong Consistency") <https://google.aip.dev/121>
  - Brandur Leach, "APIs as infrastructure: future-proofing Stripe with versioning", Stripe 블로그, 2017-08 <https://stripe.com/blog/api-versioning>
  - RFC 9457 §3.1.4 `detail` 파싱 금지(SHOULD NOT), §3.2 모르는 확장 멤버 무시(MUST) <https://www.rfc-editor.org/rfc/rfc9457>
  - Martin Fowler, "TolerantReader"(2011-05-09) <https://martinfowler.com/bliki/TolerantReader.html>
  - OpenJDK jdk21u 소스 `java/util/ImmutableCollections.java`(`SALT32L`, `REVERSE`), `java/util/Map.java` Javadoc("iteration order of mappings is unspecified")
- 실험 목록
  - 무해한 변경 3종(저장소 맵 교체·레코드 필드 순서·에러 문구) vs 클라이언트 4종 — JDK 21.0.12 temurin, Jackson 2.19.2, `com.sun.net.httpserver` + JDK `HttpClient`, 일회용 컨테이너 `--network none`
  - ConcurrentHashMap에 키를 1~12개 넣으며 순회 순서·테이블 크기·버킷 번호 출력(리플렉션으로 `table` 길이 확인) — JDK 21.0.12 temurin, `--network none`. 12번째 삽입에서 16→32 재해시와 함께 처음 섞임
  - `Map.of` 키 순서 — 같은 코드를 JVM 10회 새로 띄워 실행, 6:4로 갈림(사실 점검 재실행 8:2 — 실행마다 다름)
  - Jackson 2.19.2 `FAIL_ON_UNKNOWN_PROPERTIES` 기본값과 필드 추가 응답 역직렬화(엄격 vs 관대)
