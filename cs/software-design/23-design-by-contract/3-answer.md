# software-design/23-design-by-contract — 정답

## 정답

### 1. 계약이 없을 때

- 극단 1 — 서로 미룸: 호출자는 공급자가, 공급자는 호출자가 검사한다고 가정해 아무도 안 막는다 → 무효 상태 저장.
- 극단 2 — 둘 다 검사(방어적 프로그래밍): 같은 검사가 여러 벌 생긴다.
- Meyer(1992)의 비판: "just in case" 중복 코드는 소프트웨어를 늘리고, 늘어난 코드가 또 오류원이 되어 더 많은 검사를 부른다. 복잡도는 "the single worst obstacle to software quality in general, and to reliability in particular"라는 주장이다.

### 2. 세 조각

- 사전조건: 호출자의 의무(공급자의 이익). 호출 직전에 참. 위반 = 호출자 버그.
- 사후조건: 공급자의 의무(호출자의 이익). 정상 종료 직후 참. 위반 = 공급자 버그.
- 클래스 불변식: 공급자의 의무. 생성 직후와 공개 메서드 호출 전후마다 참(Eiffel 문서는 "before and after"만 요구 — 실행 도중엔 잠시 깨져도 된다고 읽는 것은 해석). 위반 = 공급자 버그.

### 3. 세 구현과 `-ea`

(실험 A, JDK 21.0.12)

```text
== java Contract.java (기본)
(1) 계약 없음      : qty=-3  ← 무효 상태가 그대로 저장된다
(2) 계약 명시      : 사전조건 위반: 1 <= n <= 2, n=5, qty=2
(3) assert만       : qty=-3
== java -ea Contract.java
(1) 계약 없음      : qty=-3  ← 무효 상태가 그대로 저장된다
(2) 계약 명시      : 사전조건 위반: 1 <= n <= 2, n=5, qty=2
(3) assert만       : AssertionError: 사전조건 위반 n=5, qty=2
```

- `assert`는 JVM 기본값에서 꺼져 있어 (3)은 `-ea`일 때만 막는다. (2)는 플래그와 무관하게 막는다.

### 4. "never in both"

- Meyer 1992: 조건은 사전조건(Require)에 두거나 본문의 if로 처리하거나 **둘 중 하나**, 둘 다는 안 된다.
- 강하게(demanding, 호출자 부담) 할지 약하게(tolerant, 공급자 부담) 할지는 정해진 답이 없고, 기준은 전체 구조의 단순함("maximize the overall simplicity of the architecture")이다.

### 5. 중간 예외와 불변식

(실험 D)

```text
broken: 예외(user) 뒤 available=7 reserved=0 invariant=false
safe  : 예외(user) 뒤 available=10 reserved=0 invariant=true
```

- 상태 일부를 바꾼 뒤 예외가 나서 불변식(`reserved + available == total`)이 깨진 채 남았다.
- 고치기: 검사를 모두 먼저, 상태 변경은 마지막에 한꺼번에. DB까지 걸치면 트랜잭션으로 묶는다.

### 6. 하청 규칙

- 사전조건은 **약하게만**(더 많은 입력 허용), 사후조건은 **강하게만**(더 많이 보장) 바꿀 수 있다.
- Eiffel: 재정의에서 `require else`는 원래 사전조건과 or, `ensure then`은 원래 사후조건과 and로 합쳐진다. 그래서 문법상 강화·약화가 불가능하다. 자바에는 이 강제가 없다.

### 7. 하위 타입의 계약 위반

```text
StrictGateway -> IllegalArgumentException: amount >= 100 (하위 타입이 강화한 사전조건)
LenientGateway -> NullPointerException: Cannot invoke "String.toLowerCase()" because the return value of "Subcontract$Gateway.approve(long)" is null
```

- 강화된 사전조건 → 부모 계약상 유효한 50원이 거절됨. 약화된 사후조건 → 호출자가 믿은 "null 아님"이 깨져 NPE. 둘 다 컴파일은 통과한다.

### 8. 자바의 계약 표현

- 공개 메서드 사전조건: `IllegalArgumentException`·`IllegalStateException`·`Objects.requireNonNull` + javadoc `@throws`. 꺼지지 않는다.
- 사후조건·내부 불변식: `assert`. **꺼질 수 있다**(기본 꺼짐, `-ea`로 켬).
- 값 불변식: `record` 간결 생성자·정적 팩토리 — 모든 생성 경로가 지나간다(실험 C: `1000-3000 -> won >= 0: -2000`).
- 상속용 자기 호출 계약: javadoc `@implSpec`.

### 9. 규칙 변경 뒤 일부 경로 통과

- 의심: 같은 검사가 여러 층(컨트롤러·서비스·도메인)에 방어적으로 복제돼 있고, 규칙 변경 때 일부만 고쳤다. 또는 그 경로의 검사가 `assert`라 운영에서 꺼져 있다.
- 확인: 같은 검사식 grep(`if (... >= 1000)` 류), 경로별 호출 체인 확인.
- 고치기: 규칙의 책임자를 하나로(도메인 메서드나 값 타입 생성자) 정해 한 곳에만 두고, 나머지 복제 검사는 지운다. 공개 메서드 검사는 예외로.
