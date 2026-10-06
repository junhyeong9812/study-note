# security/15-access-control-models — 접근 제어 모델: ACL·RBAC·ABAC·ReBAC와 객체 수준 인가 — 정리 (힌트)

## 해결하는 문제

로그인(인증)은 "누구인가"에만 답한다. "이 사람이 **이 객체**에 **이 동작**을 해도 되나"는 따로 물어야 한다.

```text
  GET /orders/1002   Authorization: Bearer <alice의 토큰>

  인증 (authentication)   alice 맞나?                     ── 예
  인가 (authorization)    alice가 주문 1002를 읽어도 되나? ── 주문 1002의 주인은 bob
                                                            → 물어보지 않으면 그대로 200
```

- 두 질문을 섞으면 생기는 사고가 **IDOR/BOLA**다. 로그인한 사용자가 URL의 ID만 바꿔 남의 데이터를 본다.
  - *인가(authorization)*: 주체(사용자·서비스)가 대상(객체)에 동작(읽기·쓰기·삭제)을 해도 되는지 판정하는 일.
  - *IDOR(Insecure Direct Object Reference)*: 클라이언트가 준 식별자로 객체를 바로 꺼내면서 소유·권한을 확인하지 않는 결함. CWE-639 "Authorization Bypass Through User-Controlled Key".
  - *BOLA(Broken Object Level Authorization)*: OWASP API Security Top 10 2023의 API1. API 엔드포인트가 객체 ID를 받아 동작하면서 그 객체에 대한 권한을 검사하지 않는 것. IDOR의 API판 이름이다.
- OWASP Top 10 2021은 Broken Access Control을 5위에서 A01(1위)로 올렸다. 원문은 "애플리케이션의 94%가 어떤 형태로든 접근 제어 결함 시험을 받았고 평균 발생률은 3.81%"라고 적는다(94%는 시험 범위이지 발견 비율이 아니다).
- 2025판에서도 A01이다. 원문 Background는 "시험한 애플리케이션 100%에서 어떤 형태로든 발견됐다"고 적는다. 같은 쪽 점수표의 수치는 최대 커버리지 100%, 평균 발생률 3.74%다.
- 쉬운 예: 호텔 카드키.
  - 프런트에서 신분 확인(인증)을 받았다고 아무 방이나 열리면 안 된다.
  - 카드키는 "이 손님 → 이 방"으로 묶여 있어야 한다. 방 번호만 바꿔 누르면 열리는 문이 IDOR다.
- 실무 예
  - `GET /api/orders/{id}`가 로그인만 확인하고 `findById(id)`로 응답한다. 번호를 1씩 올리면 남의 주문이 나온다.
  - 관리자 메뉴를 화면에서 숨겼을 뿐, `/admin/users` API는 일반 사용자 토큰으로도 200을 준다.

## 동작·원리

### 1. 인가 결정의 흐름 — 정책 집행 지점과 결정 지점

```text
  요청 ──> [PEP: 정책 집행 지점]  컨트롤러·필터·게이트웨이·DB 정책
              │  (주체, 동작, 대상, 환경)을 묶어 묻는다
              ▼
           [PDP: 정책 결정 지점]  "허용/거부"를 계산
              │  ← 정책(규칙)  ← 속성·관계 데이터(소유자, 역할, 부서, 시각)
              ▼
           허용 → 실행        거부 → 403 또는 404 (존재를 숨길 때)
                              판정 불가(오류) → 거부 (fail-safe 기본값)
```

- *PEP(Policy Enforcement Point)*: 요청을 가로채 결정을 받아 집행하는 곳. *PDP(Policy Decision Point)*: 정책과 데이터로 결정을 계산하는 곳. NIST SP 800-162(ABAC 지침)가 쓰는 용어다.
- Saltzer–Schroeder(1975)의 원칙 둘이 이 그림의 뼈대다.
  - *완전한 중재(complete mediation)*: "객체에 대한 접근은 하나도 빠짐없이 권한 검사를 받아야 한다"(원문 "Every access to every object must be checked for authority"). 한 경로라도 빠지면 그 경로가 우회로다.
  - *fail-safe 기본값*: "배제가 아니라 허가에 근거해 결정한다". 규칙에 없으면 거부다.
- OWASP Authorization Cheat Sheet도 같은 말을 한다. 요청마다 권한을 검증하고(AJAX든 서버 내부든), 기본은 거부, 검사는 서버 쪽에서 한다.

### 2. 권한 행렬 — 네 모델은 이 행렬을 저장·계산하는 방식이 다르다

```text
                 주문1001   주문1002   /admin/users
  alice           R W         -           -
  bob             -          R W          -
  admin           R           R          R
  (행 = 주체, 열 = 객체, 칸 = 허용 동작)

  ACL         열을 잘라 객체에 붙인다    주문1002: [bob: RW, admin: R]
  capability  행을 잘라 주체에 준다      alice: [주문1001: RW]
  RBAC        주체 → 역할 → 권한 두 단계로 압축
  ABAC        칸을 저장하지 않고 속성 규칙으로 계산
  ReBAC       칸을 관계 그래프의 경로 존재로 계산
```

- *ACL(Access Control List)*: 객체마다 "누가 무엇을 할 수 있나" 목록. 유닉스 파일 권한(소유자·그룹·기타 3칸)이 축약형이다(OSTEP 55.3).
- *capability*: 주체가 들고 다니는 "이 객체에 이 권한" 표. 열쇠·영화표에 비유된다(OSTEP 55.4). 위조 불가능해야 한다. 회수는 OS가 capability를 독점 관리하면 쉽고, 사용자 손에 있으면 어렵다(같은 절).
  - 흔한 오해: "UUID처럼 추측하기 어려워 보이는 ID를 주면 그게 권한이다". RFC 9562 §8은 UUID를 "보유만으로 접근을 주는 보안 수단(security capabilities)"으로 쓰면 안 된다(MUST NOT)고 적는다. 16번 식별자 노트에서 더 다룬다.

### 3. RBAC — 역할 그래프

```text
  사용자 ──(할당)──> 역할 ──(부여)──> 권한(동작, 대상 — 보통 종류 단위)

  alice ─> SUPPORT ─┐                  ┌─> order:read
                    ├─(상속) STAFF ────┤
  bob   ─> BILLING ─┘                  └─> profile:read
  carol ─> ADMIN ─(상속)─> STAFF,  ADMIN ─> user:manage
```

- *RBAC(Role-Based Access Control)*: 사용자에게 역할을, 역할에 권한을 준다. 사람이 바뀌어도 역할 할당만 고치면 된다(OSTEP 55.6).
  - NIST 모델(Sandhu·Ferraiolo·Kuhn 2000)이 2004년 ANSI/INCITS 359-2004 표준이 됐고, 2012년 INCITS 359-2012로 개정됐다(NIST CSRC RBAC 프로젝트 페이지).
- 역할 상속은 방향 그래프다. "carol이 order:read를 가지나"는 역할 그래프에서 권한까지 경로가 있나로 판정한다.
- 한계: NIST 모델의 권한은 (동작, 객체) 쌍이라 객체 하나하나에 권한을 줄 수는 있다(NIST RBAC 표준 초안 Definition 1, PRMS = 2^(OPS×OBS)). 하지만 실무 역할은 보통 `order:read`처럼 **종류** 단위로 부여된다. "자기 담당 고객의 주문만"처럼 계속 바뀌는 관계는 역할·권한 할당만으로 따라가기 어렵다. 이 틈이 IDOR가 사는 자리다.
  - 역할로 막으려다 `SUPPORT_TEAM_A`, `SUPPORT_TEAM_B_REGION_3`처럼 역할이 폭증한다(역할 폭발).

### 4. ABAC — 속성 규칙

```text
  허용 ⇔ subject.dept == resource.dept
         ∧ action ∈ {read}
         ∧ env.time ∈ 09:00–18:00
         ∧ resource.classification ≤ subject.clearance
```

- *ABAC(Attribute-Based Access Control)*: 주체·객체·동작·환경의 속성을 정책에 넣어 판정한다. NIST SP 800-162(2014-01, 2019-08 갱신)의 정의다.
- 객체 수준 조건("소유자 == 요청자")을 자연스럽게 쓴다. 대신 "누가 이 문서를 볼 수 있나"를 역으로 나열하기 어렵다. 속성 조합을 다 훑어야 한다.

### 5. ReBAC — 관계 튜플과 그래프 탐색 (Zanzibar)

```text
  관계 튜플  ⟨object⟩#⟨relation⟩@⟨user 또는 object#relation⟩     (Zanzibar 논문 표 1)
    doc:readme#owner@user:10
    doc:readme#viewer@group:eng#member       eng 그룹 멤버는 readme의 viewer
    doc:readme#parent@folder:A               readme는 폴더 A 안에 있다
    group:eng#member@user:11
    folder:A#viewer@user:12

  재작성 규칙 (그림 1):  owner ⊂ editor ⊂ viewer,  parent 폴더의 viewer ⊂ 문서의 viewer

  check(doc:readme#viewer, user:12)?
     doc:readme#viewer ──직접 튜플?── 없음
        ├─ group:eng#member ── user:11 (아님)
        ├─ doc:readme#editor ── doc:readme#owner ── user:10 (아님)
        └─ parent → folder:A#viewer ── user:12  ✔ 경로 있음 → 허용
```

- *ReBAC(Relationship-Based Access Control)*: "이 사용자와 이 객체 사이에 허용 관계의 경로가 있나"로 판정한다. 공유 문서·폴더 상속·조직 계층처럼 관계가 곧 권한인 곳에 맞다.
- Google Zanzibar(Pang 외, USENIX ATC 2019)
  - 초록: 수조 개의 ACL과 초당 수백만 건의 인가 요청을 처리하고, 3년 운영에서 95번째 백분위 지연 10ms 미만·가용성 99.999% 초과.
  - 관계 튜플 + 재작성 규칙(`_this`·`computed_userset`·`tuple_to_userset`)으로 그룹과 상속을 표현한다.
  - **"new enemy" 문제**: Alice가 Bob을 폴더 ACL에서 뺀 **뒤에** 새 문서를 넣었는데, 검사가 옛 ACL로 돌면 Bob이 새 문서를 본다. Zanzibar는 내용 변경 때 받은 *zookie*(시각을 담은 불투명 토큰)를 검사 요청에 실어 "이 시각 이후 스냅샷으로 판정"하게 한다.
- 탐색 비용: 그룹 중첩이 깊으면 경로 탐색이 깊어진다. 순환(그룹 A ⊂ B ⊂ A)을 끊는 방문 집합이 필요하다.

### 6. 객체 수준 vs 기능 수준, 수평 vs 수직

```text
                     같은 권한 등급 안에서             등급을 넘어
  객체 수준(BOLA)    수평 권한 상승: alice → bob의 주문     (드묾)
  기능 수준(BFLA)    —                                   수직 권한 상승: 일반 사용자 → /admin
```

- *BFLA(Broken Function Level Authorization)*: OWASP API Top 10 2023 API5. 호출하면 안 되는 **엔드포인트 자체**에 닿는 것. BOLA는 접근해도 되는 엔드포인트에서 **객체 ID**를 바꾸는 것이다.
- *수평 권한 상승*: 같은 등급의 다른 사용자 자원에 닿는다. *수직 권한 상승*: 더 높은 등급의 기능에 닿는다.

### 실험: IDOR·기능 수준 인가 누락과 고친 판, ReBAC 경로 탐색

`AccessDemo.java` — JDK 내장 `HttpServer`를 컨테이너 안 127.0.0.1 임의 포트에 띄우고 같은 JVM의 `HttpClient`로 부른다. 사용자·토큰은 가짜 값(`tok-alice` 등)이다.

```java
// 취약(v1): 인증만 확인하고 경로의 id로 바로 조회
Order o = ORDERS.get(id);
if (o == null) { send(ex, 404, "not found"); return; }
send(ex, 200, o.toString());

// 고친 판(v2): 소유 조건을 조회 자체에 넣는다 (SQL이면 WHERE id = ? AND owner = ?)
Optional<Order> o = Optional.ofNullable(ORDERS.get(id)).filter(x -> x.owner().equals(u.name()));
if (o.isEmpty()) { send(ex, 404, "not found"); return; }   // 남의 것과 없는 것을 같은 응답으로
```

(실험, OpenJDK 21.0.12 eclipse-temurin:21-jdk 컨테이너 `--network none`, 2026-10-07)

```text
tok-alice  GET /v1/orders/1001    -> 200 Order[id=1001, owner=alice, item=book]
tok-alice  GET /v1/orders/1002    -> 200 Order[id=1002, owner=bob, item=laptop]
tok-alice  GET /v2/orders/1001    -> 200 Order[id=1001, owner=alice, item=book]
tok-alice  GET /v2/orders/1002    -> 404 not found
tok-alice  GET /v2/orders/9999    -> 404 not found
(none)     GET /v2/orders/1001    -> 401 unauthenticated
tok-bob    GET /v1/admin/users    -> 200 all users: [admin, alice, bob]
tok-bob    GET /v2/admin/users    -> 403 forbidden
tok-admin  GET /v2/admin/users    -> 200 all users: [admin, alice, bob]
--- ReBAC check
doc:readme#viewer@user:10    -> true  doc:readme#viewer <- doc:readme#editor <- doc:readme#owner <- user:10
doc:readme#viewer@user:11    -> true  doc:readme#viewer <- group:eng#member <- user:11
doc:readme#viewer@user:12    -> true  doc:readme#viewer <- folder:A#viewer <- user:12
doc:readme#viewer@user:13    -> false 
doc:readme#editor@user:11    -> false
```

- 관찰
  - v1은 alice 토큰으로 bob의 주문 1002에 200을 줬다. 로그인은 정상이었다. 인가만 빠졌다.
  - v2는 남의 주문(1002)과 없는 주문(9999)에 같은 404를 줬다. 응답 차이로 "그 번호가 존재한다"가 새지 않는다.
  - 기능 수준: v1 관리자 API는 일반 사용자 bob에게 200, v2는 역할 검사로 403.
  - ReBAC: user:12는 문서에 직접 튜플이 없지만 부모 폴더 경로로 viewer가 됐다. user:11은 그룹 경로로 viewer지만 editor는 아니다.
- 해석: 결과 차이는 프레임워크가 아니라 **조회에 소유 조건이 들어갔나** 하나에서 나왔다.

## 쓰이는 자료구조·알고리즘

- **권한 행렬과 희소 표현**: 행렬 대부분이 빈칸이라 ACL(열 단위 리스트)·capability(행 단위 리스트)로 저장한다. 해시맵 `객체 → {주체 → 권한}`([data-structure/05-hashmap](../../data-structure/05-hashmap/2-summary.md)).
- **역할 그래프**: 역할 상속은 방향 그래프. 권한 판정 = 사용자에서 권한까지 도달 가능성. 상속 고리는 설계 오류이므로 저장 때 순환 검사(DFS 색칠, [algorithm/12-dfs](../../algorithm/12-dfs/2-summary.md))를 한다.
- **관계 그래프 탐색(Zanzibar)**: check = 객체#관계에서 사용자까지 경로가 있나(합집합 규칙만 쓸 때). Zanzibar 재작성 규칙에는 교집합·제외도 있어서 일반적으로는 경로를 따라가며 집합 연산까지 평가한다(Zanzibar 논문 §2.3.1). 실험은 방문 집합을 둔 DFS로 구현했다. 넓게 퍼진 그룹은 BFS로 레벨 단위 병렬 조회를 한다([algorithm/11-bfs](../../algorithm/11-bfs/2-summary.md), [data-structure/08-graph](../../data-structure/08-graph/2-summary.md)).
- **스냅샷 일관성**: Zanzibar의 zookie는 "이 시각 이후 스냅샷으로 읽어라"는 하한이다. MVCC 스냅샷([database/16-mvcc](../../database/16-mvcc/2-summary.md))과 같은 생각이다.
- **규칙 충돌 해소**: 허용·거부 규칙이 겹칠 때 거부 우선·구체성 우선 같은 메타 규칙이 필요하다([domain-modeling 28-authorization](../../domain-modeling/advanced/28-authorization/2-summary.md)).

## 적용 — 풀어나가는 법

### 1. 소유 조건을 조회에 넣는다 (Spring Data JPA)

```java
// 취약: id만으로 꺼낸다
@GetMapping("/orders/{id}")
OrderDto get(@PathVariable long id) {
    return OrderDto.of(orders.findById(id).orElseThrow(NotFound::new));
}

// 고친 판: 현재 사용자 조건이 조회 안에 있다 → 남의 것은 "없는 것"과 같다
interface OrderRepository extends JpaRepository<Order, Long> {
    Optional<Order> findByIdAndOwnerId(long id, long ownerId);
}
@GetMapping("/orders/{id}")
OrderDto get(@PathVariable long id, @AuthenticationPrincipal AppUser me) {
    return OrderDto.of(orders.findByIdAndOwnerId(id, me.id()).orElseThrow(NotFound::new));
}
```

- 쓰기도 같다. `UPDATE orders SET ... WHERE id = ? AND owner_id = ?`의 영향 행 수가 0이면 404다.
- 멀티테넌트면 테넌트 조건을 DB 쪽에 한 번 더 건다(PostgreSQL 행 수준 보안 — [database/43-row-level-security](../../database/43-row-level-security/2-summary.md)). 앱 조건을 하나 빠뜨려도 DB가 막는 심층 방어다.

### 2. 기능 수준은 경로·메서드 규칙으로, 기본 거부 (Spring Security)

```java
@Bean
SecurityFilterChain api(HttpSecurity http) throws Exception {
    http.authorizeHttpRequests(a -> a
        .requestMatchers("/admin/**").hasRole("ADMIN")
        .requestMatchers("/api/**").authenticated()
        .anyRequest().denyAll());          // 규칙에 없는 경로는 거부 (fail-safe 기본값)
    return http.build();
}
```

- 메서드 단위는 `@EnableMethodSecurity` + `@PreAuthorize("hasRole('ADMIN')")`. 거부되면 `AccessDeniedException` → `ExceptionTranslationFilter`가 403으로 바꾼다(Spring Security 7.1 문서 Method Security).
- `@PostAuthorize("returnObject.owner == authentication.name")`도 IDOR를 막는다(같은 문서). 단, 메서드가 **먼저 실행된 뒤** 검사한다. 쓰기 메서드에 쓰면 검사 전에 DB 변경이 일어난다(트랜잭션이 검사까지 감싸 거부 예외로 롤백되게 순서를 맞춘 경우는 예외 — 문서는 `@EnableTransactionManagement`를 `@EnableMethodSecurity`보다 앞에 두라고 한다. 외부 호출 같은 부수 효과는 롤백되지 않는다). 거부 응답은 403이라 존재 여부가 샌다. 같은 문서도 쓰기에는 권장하지 않으니 읽기 전용에만 쓴다.

### 3. 결정 지점을 한 곳으로 모은다

```java
// 컨트롤러마다 if를 흩지 않고 "주체·동작·대상"을 받는 한 함수로
public interface Authz {
    boolean can(AppUser who, Action what, ResourceRef target);   // 예외·타임아웃이면 false
}
```

- OWASP A01 예방 항목: "접근 제어 메커니즘을 한 번 구현해 애플리케이션 전체에서 재사용한다", "레코드 소유를 강제한다", "공개 자원을 빼고는 기본 거부".
- 관계가 복잡하면(공유·폴더 상속·조직 계층) ReBAC 엔진(Zanzibar 계열 오픈소스 구현)에 PDP를 맡긴다. 이때 PDP 장애 시 기본값이 허용으로 열리지 않게 한다.

### 4. 403이냐 404냐를 팀 규칙으로 정한다

- RFC 9110 §15.5.4: 존재를 숨기려는 서버는 403 대신 404를 줄 수 있다(MAY). 권한을 존재 확인보다 먼저 검사해 권한이 없으면 존재와 무관하게 403을 주는 방식도 있다([api-design/03-status-codes-for-apis](../../api-design/03-status-codes-for-apis/2-summary.md)).
- 피해야 할 것은 "남의 것 = 403, 없는 것 = 404"의 혼합이다. 번호를 훑어 존재하는 객체를 셀 수 있다.

### 5. 인가를 테스트로 고정한다

```java
@Test
void otherUsersOrderIsNotFound() throws Exception {
    mvc.perform(get("/orders/{id}", bobsOrderId).with(user("alice")))
       .andExpect(status().isNotFound());
}
@Test
void userCannotCallAdminApi() throws Exception {
    mvc.perform(get("/admin/users").with(user("bob").roles("USER")))
       .andExpect(status().isForbidden());
}
```

- 엔드포인트 × 역할 × "남의 객체" 행렬로 음성 테스트를 만든다. OWASP API1 예방 항목도 "인가 취약을 평가하는 테스트를 쓰고, 실패하면 배포하지 않는다"이다.
- 진단: 접근 로그에서 한 주체가 짧은 시간에 많은 서로 다른 객체 ID에 404·403을 받는지 본다. A01은 "접근 제어 실패를 기록하고, 반복되면 관리자에게 알린다"를 권한다(26번 보안 로그).

## 장애 시나리오와 대처

### 1. IDOR/BOLA — ID만 바꾸면 남의 데이터 (⚠ OWASP A01)

- **현상**: 고객 문의 "내 화면에 다른 사람 주소가 보였다", 또는 외부 제보.
- **보이는 형태**: 한 세션이 `/orders/1001`, `/orders/1002`, `/orders/1003`…을 연속 호출하고 전부 200. 응답의 `owner`가 요청자와 다르다.
- **원인**: 조회가 `findById(id)`뿐이다. 인증 필터가 있으니 "보호된 API"라고 착각했다.
- **대처**
  - 조회·수정·삭제 쿼리에 소유·테넌트 조건을 넣는다. 응답은 404로 통일한다.
  - 접근 로그로 노출 범위를 산정한다(어느 주체가 어느 객체를 읽었나 — 26번).
  - 랜덤 ID로 바꾸는 것은 추측을 어렵게 할 뿐 인가가 아니다(16번).

### 2. 수직 권한 상승 — 숨긴 관리자 API

- **현상**: 일반 사용자가 다른 사용자 계정을 정지시켰다.
- **보이는 형태**: 감사 로그에 `role=USER` 주체의 `POST /admin/users/{id}/suspend` 200.
- **원인**: 프런트에서 메뉴만 숨겼다. 서버 경로 규칙에 `/admin/**`가 빠졌고 기본이 `authenticated()`였다.
- **대처**: 경로 규칙을 기본 거부(`anyRequest().denyAll()`)로 바꾸고 허용을 명시한다. 관리자 기능은 메서드 보안을 한 번 더 건다.

### 3. 인가 서비스(PDP) 장애 → fail-open

- **현상**: 인가 서비스 타임아웃 동안 권한 없는 요청이 통과했다.
- **보이는 형태**: 인가 클라이언트 로그 `timeout`과 같은 시각에 평소 403이던 요청의 200.
- **원인**: `catch (Exception e) { return true; }` — 판정 불가를 허용으로 처리했다.
- **대처**: 판정 불가는 거부(fail-safe 기본값). 가용성이 문제면 PDP 결과 캐시(짧은 TTL)와 타임아웃·서킷 브레이커로 대응하되 기본값을 바꾸지 않는다([reliability/10-circuit-breaker](../../reliability/10-circuit-breaker/2-summary.md)).

### 4. 권한 회수가 늦게 반영된다 ("new enemy")

- **현상**: 팀에서 뺀 직원이 그 뒤에 올라온 문서를 열었다.
- **보이는 형태**: 멤버십 삭제 시각 < 문서 생성 시각 < 열람 시각인데 열람이 200.
- **원인**: 인가 결정을 캐시(또는 지연된 복제본)에서 읽었다. 회수가 반영되기 전 스냅샷으로 판정했다.
- **대처**: 회수·내용 변경 뒤의 검사는 그 변경 이후 스냅샷으로 하게 한다(Zanzibar zookie). 캐시 TTL을 짧게 두고, 회수 이벤트로 캐시를 무효화한다.

## 핵심 문장

- 인증은 "누구인가", 인가는 "이 객체에 이 동작을 해도 되나"다. 로그인 검사만 있는 API는 IDOR에 열려 있다.
- 접근은 경로마다 빠짐없이 검사하고(완전한 중재), 판정이 안 되면 거부한다(fail-safe 기본값).
- ACL·capability·RBAC·ABAC·ReBAC는 같은 권한 행렬을 저장·계산하는 방식이 다르다. 역할만 쓰는 기본 RBAC로는 객체 단위 조건을 표현하기 어렵다.
- 객체 수준 인가는 소유 조건을 조회 자체에 넣는 것이 가장 단단하다. 남의 것과 없는 것은 같은 응답으로 준다.
- ReBAC 판정은 관계 그래프의 경로 탐색이다. 회수 직후에는 회수 이후 스냅샷으로 판정해야 한다.

## 관련 주제·근거

- 선행·후속
  - [security 01 security-principles](../01-security-principles/2-summary.md)(완전한 중재·fail-safe·최소 권한) — 같은 영역
  - [16-identifiers-and-enumeration](../16-identifiers-and-enumeration/2-summary.md) — 랜덤 ID는 인가가 아니다
  - [17-refresh-token-rotation-and-revocation](../17-refresh-token-rotation-and-revocation/2-summary.md) — 권한 회수가 토큰에 반영되는 속도
  - [security 12 tokens-and-jwt](../12-tokens-and-jwt/2-summary.md)(토큰 안 역할 claim)·[26 security-logging-and-audit](../26-security-logging-and-audit/2-summary.md)
- 연결
  - [domain-modeling 28-authorization](../../domain-modeling/advanced/28-authorization/2-summary.md) — 규칙 충돌(거부 우선·구체성)·폴백·상속 축
  - [database/43-row-level-security](../../database/43-row-level-security/2-summary.md) — DB 쪽 테넌트 격리
  - [api-design/03-status-codes-for-apis](../../api-design/03-status-codes-for-apis/2-summary.md) — 401·403·404 선택
  - [reliability/10-circuit-breaker](../../reliability/10-circuit-breaker/2-summary.md)
- 1차 출처
  - Saltzer & Schroeder, "The Protection of Information in Computer Systems", Proc. IEEE 63(9), 1975 — Complete mediation·Fail-safe defaults·Least privilege <https://www.cs.virginia.edu/~evans/cs551/saltzer/>
  - OSTEP 55 "Access Control"(Peter Reiher) — 55.3 ACL, 55.4 capability, 55.5 MAC/DAC, 55.6 RBAC <https://pages.cs.wisc.edu/~remzi/OSTEP/security-access.pdf>
  - OWASP Top 10 2021 A01 Broken Access Control(94% 시험, 평균 발생률 3.81%, CWE 34개, IDOR·force browsing·JWT 무효화, 예방 목록) <https://owasp.org/Top10/2021/A01_2021-Broken_Access_Control/> · 2025 A01(100%, 평균 발생률 3.74%, CWE 40개, SSRF 포함) <https://owasp.org/Top10/2025/A01_2025-Broken_Access_Control/>
  - OWASP API Security Top 10 2023 API1 BOLA·API5 BFLA <https://owasp.org/API-Security/editions/2023/en/0xa1-broken-object-level-authorization/>
  - OWASP Authorization Cheat Sheet <https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html>
  - CWE-639 Authorization Bypass Through User-Controlled Key <https://cwe.mitre.org/data/definitions/639.html>
  - NIST SP 800-162 Guide to ABAC(2014-01, 2019-08-02 갱신) <https://csrc.nist.gov/pubs/sp/800/162/upd2/final> · NIST RBAC 프로젝트(ANSI/INCITS 359-2004) <https://csrc.nist.gov/projects/role-based-access-control>
  - Pang 외, "Zanzibar: Google's Consistent, Global Authorization System", USENIX ATC 2019 — 표 1 튜플, 그림 1 재작성, §2.2 new enemy, zookie <https://www.usenix.org/conference/atc19/presentation/pang>
  - Spring Security 7.1 Method Security(`@EnableMethodSecurity`, `@PreAuthorize`, `@PostAuthorize`의 returnObject 예, 거부 시 403) <https://docs.spring.io/spring-security/reference/servlet/authorization/method-security.html>
  - RFC 9110 §15.5.4 403 Forbidden(404로 숨길 수 있음, MAY)
- 실험: `AccessDemo.java`(JDK `HttpServer`·`HttpClient`, 127.0.0.1, 컨테이너 `--network none`) — v1/v2 주문 조회, v1/v2 관리자 API, 관계 튜플 DFS check
