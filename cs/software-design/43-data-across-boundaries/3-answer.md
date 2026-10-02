# software-design/43-data-across-boundaries — 정답

## 정답

### 1. 세 가지 묶임

- DB 스키마 = API 계약: 컬럼이 추가되면 응답에도 조용히 나간다.
- 영속 수명 = 응답 수명: 직렬화 중 지연 로딩이 일어난다(세션 밖이면 예외, 열려 있으면 쿼리).
- 객체 그래프 = 응답 구조: 양방향 연관을 직렬화기가 끝없이 따라간다.

### 2. 네 모델

```text
 SignUpRequest ──> Member(도메인) <──> MemberEntity(@Entity)      MemberView(응답)
   웹 경계                          영속 경계                     웹 경계
```

- 요청·응답 모델: 클라이언트와의 계약 때문에 바뀐다.
- 도메인 모델: 업무 규칙 때문에 바뀐다.
- 영속 모델: 테이블 설계·성능 때문에 바뀐다.
- 합치면 한 이유의 변경이 나머지를 끌고 가고, 나누면 경계마다 매핑이 생긴다.

### 3. 엔티티 직렬화 실험

(실험, Hibernate 7.4.11 + Jackson 2.22.3, 2026-10-02)

```text
== 1) 세션 안에서 엔티티를 그대로 JSON으로 (양방향 연관)
JsonMappingException: Document nesting depth (1001) exceeds the maximum allowed (1000, ...
== 2) 세션이 닫힌 뒤 엔티티를 JSON으로 (LAZY 컬렉션)
JsonMappingException: Cannot lazily initialize collection of role 'Boundary$Member.orders' with key '1' (no session) ...
  cause = org.hibernate.LazyInitializationException
== 3) 컬렉션만 빼고 엔티티를 JSON으로
{"id":1,"name":"kim","passwordHash":"$2a$10$abcdefghijk"}
```

- ① 무한 재귀가 최대 중첩 깊이 1000에서 멈췄다. ② `LazyInitializationException`. ③ `passwordHash`가 그대로 나간다.

### 4. 왕복 수

(실험, 5ms 흉내 지연)

```text
주문 10건: 세밀한 인터페이스 왕복  23회  119ms | Remote Facade 왕복 1회  5ms
주문 50건: 세밀한 인터페이스 왕복 103회  527ms | Remote Facade 왕복 1회  5ms
```

- 세밀한 방식: `3 + 2N`(이름·등급·개수 + 주문마다 2번). 50건이면 103회.
- Remote Facade: 데이터 양과 무관하게 1회.

### 5. PoEAA 정의

- DTO: 호출 수를 줄이려고 프로세스 사이로 데이터를 실어 나르는 객체. 직렬화 가능해야 하고, 서버 쪽에서는 보통 어셈블러가 도메인 객체와 DTO 사이를 옮긴다.
- Remote Facade: 세밀한 객체들 위의 거친 파사드. **도메인 로직이 없다** — 거친 메서드를 안쪽 세밀한 객체 호출로 번역만 한다.

### 6. LocalDTO

- 비판: 로컬(같은 프로세스) 맥락의 DTO. 필요 없을 뿐 아니라 거친 API는 쓰기 어렵고 매핑 일이 생겨 해롭다. "나중에 분산할지 몰라서"도 투기적이라고 본다.
- 인정: 프레젠테이션 모델과 도메인 모델 사이 불일치가 클 때의 화면 전용 파사드·게이트웨이.
- HTTP 응답 모델은 원격 경계 + 클라이언트 계약이므로 DTO의 본래 자리다(해석). 비판 대상은 계층마다 1:1 복사하는 로컬 DTO다.

### 7. 매퍼 누락

(실험)

```text
== 세터식
MemberDto{name=kim, phone=null}
== 생성자식
ctor/Mapping.java:5: error: constructor MemberDto in record MemberDto cannot be applied to given types;
```

- 세터식: 조용히 `null`. 생성자식: 컴파일 오류로 누락 자리를 알려 준다(같은 타입 인자의 순서 뒤바뀜은 못 잡는다).

### 8. 직렬화 단계의 지연 로딩 예외

- 원인: 트랜잭션·세션이 끝난 뒤 직렬화기가 LAZY 컬렉션 프록시를 건드렸다. 서비스 테스트는 직렬화를 안 하니 통과한다.
- 대처: 트랜잭션 안에서 응답 DTO를 완성한다(실험 4: `{"id":1,"name":"kim","orderCount":2,"totalAmount":3000}`).
- Spring Boot 서블릿 웹 앱은 `spring.jpa.open-in-view`가 기본으로 켜져 있어(명시 안 하면 기동 경고) 응답 렌더링 중에도 세션이 열려 있다. 그러면 예외 대신 직렬화 중 쿼리(N+1)로 나타난다.

### 9. `@JsonIgnore`로 충분한가

- 아니다. 차단 목록 방식이라 나중에 추가되는 민감 컬럼은 다시 자동으로 나간다(엔티티 직렬화는 "새 필드는 기본 공개").
- 응답 모델(허용 목록)을 따로 두면 새 필드는 누군가 명시적으로 넣기 전까지 나가지 않는다.
