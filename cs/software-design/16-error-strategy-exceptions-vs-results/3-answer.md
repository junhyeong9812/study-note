# software-design/16-error-strategy-exceptions-vs-results — 정답

## 정답

### 1. 세 종류

| 종류 | 예 | 대응 | 수단 |
|---|---|---|---|
| 도메인 실패 | 잔액 부족, 없는 계좌 | 업무 규칙·사용자 | 결과 타입 또는 도메인 예외(시그니처에 드러냄) |
| 인프라 장애 | 타임아웃, DB 끊김 | 재시도·운영자 | 예외, 경계에서 503·재시도로 번역 |
| 버그 | null 인자, 범위 밖 인덱스 | 개발자 | 예외로 fail-fast |

- 분류는 Wlaschin의 Domain Errors·Infrastructure Errors·Panics를 따른다. 인프라 장애를 도메인으로 모델링할지는 경우마다 다르다고 그는 적는다.

### 2. Railway

```text
 parseAmount ─ok─> loadAccount ─ok─> withdraw ─ok─> 200
      └─err InvalidAmount ───────────────────────────> 400
```

(실험 A)

```text
요청 id=1 amount=abc
  parseAmount(abc)
  => 400 InvalidAmount[amount=-1]
```

- `parseAmount`만 실행된다. 실패 선로에 들어가면 `flatMap`이 뒤 함수를 부르지 않는다.

### 3. 롤백 규칙

(실험 C, Spring Framework 6.2.19 + H2)

```text
checkedFail              -> 예외 InsufficientChecked: 잔액 부족 | 남은 ledger 행=1
checkedFailWithRule      -> 예외 InsufficientChecked: 잔액 부족 | 남은 ledger 행=0
resultFailAfterWrite     -> 정상 반환 | 남은 ledger 행=1
```

- checked 예외: 기본 롤백 대상이 아니라 쓰기가 커밋된다(6.2의 전역 `rollbackOn = ALL_EXCEPTIONS`를 켜지 않은 기본 설정).
- `rollbackFor` 지정: 롤백된다.
- 쓰기 후 `Result.err` 반환: 정상 반환이므로 커밋된다. 결정을 쓰기 앞에 두면 0행이다(`resultFailBeforeWrite`).

### 4. 잡고 계속하기

```text
outer.catchAndContinue   -> 예외 UnexpectedRollbackException: Transaction rolled back because it has been marked as rollback-only | 남은 ledger 행=0
```

- 안쪽 `@Transactional`(기본 전파 REQUIRED)이 같은 트랜잭션을 rollback-only로 표시했다. 바깥이 예외를 잡아도 커밋 시점에 `UnexpectedRollbackException`이 나고 바깥의 쓰기까지 롤백된다.

### 5. 전수 검사

```text
exh/e16/Railway.java:28: error: the switch expression does not cover all possible input values
```

- sealed 계층 + `default` 없는 `switch`는 빠진 경우를 컴파일 오류로 만든다(JDK 21).
- 예외 계층은 열려 있어 컴파일을 통과하고, 경계의 가장 일반적인 처리기(보통 500)로 떨어진다.
- 반대 비용: 실패 종류를 추가할 때마다 그 `switch`를 쓰는 곳을 다 고쳐야 한다. 공개 API의 에러 타입이면 호환성 문제가 된다.

### 6. 재시도 폭풍

(실험 D)

```text
잔액 부족 -> 409           요청=1000 성공=700 실패=300 서버가 받은 호출=1000
잔액 부족 -> 500           요청=1000 성공=700 실패=300 서버가 받은 호출=1900
```

- 409: 1000. 500: 1900(실패 300건 × 추가 3번 = 900 추가). 성공 수는 같고 부하만 는다.

### 7. `get()`과 Result의 한계

- 실패면 런타임 예외(실험 A: `IllegalStateException: get() on Err: InvalidAmount[amount=-1]`)다. 결과 타입을 예외로 되돌린 셈이다.
- Wlaschin("Against Railway-Oriented Programming")은 8개 소제목으로 정리한다. 예: 진단 정보(스택 트레이스·에러 위치)가 필요할 때(#1), Result로 예외(try-catch)를 재발명하려 할 때(#2), fail fast가 맞을 때(#3), I/O에서 날 수 있는 모든 오류를 Result로 모델링하려 할 때(#6 — "조심하라"는 항목). 그 밖에 아무도 보지 않거나 신경 쓰지 않는 에러, 성능·상호운용이 중요한 경우가 있다.

### 8. Special Case

- 맞을 때: 특별한 경우의 할 일이 기본 동작으로 정해져 있을 때(모르는 고객 → 이름 "occupant", 할인 없음 → 원가). 호출자가 null 검사를 반복하지 않아도 된다(PoEAA Special Case, Refactoring "Introduce Special Case").
- 숨길 때: 호출자가 실패를 알아야 하는 경우(잔액 부족)에 쓰면 실패가 정상처럼 흘러간다.

### 9. 실패 응답인데 쓰기가 남음

- 원인 후보 1: 도메인 예외가 checked이고 `rollbackFor`가 없다 → 커밋. 확인: 예외 클래스 계층과 `@Transactional` 속성.
- 원인 후보 2: 결과 타입(`Err`)을 쓰기 **뒤에** 반환했다 → 정상 반환으로 커밋. 확인: 메서드 안에서 쓰기와 실패 판단의 순서.
- 대처: 롤백 규칙 명시, 결정 → 쓰기 순서, 필요하면 `setRollbackOnly()`.
