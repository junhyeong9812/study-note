# software-design/16-error-strategy-exceptions-vs-results — 예외 vs 결과 타입: 실패의 종류로 고른다 — 정리 (힌트)

## 해결하는 문제

"잔액 부족"과 "DB 연결 끊김"은 둘 다 실패지만 성격이 다르다. 하나의 수단(전부 예외, 또는 전부 결과 타입)으로 다루면 한쪽이 어긋난다.

```text
 실패의 종류                   예                         누가 대응하나            어울리는 수단
 ─────────────────────────────────────────────────────────────────────────────────────────────
 도메인 실패(예상 가능)         잔액 부족, 잘못된 금액,      업무 규칙·사용자           결과 타입(Result) 또는
                               없는 계좌                                             도메인 전용 예외
 인프라 장애                    네트워크 타임아웃, DB 끊김   재시도·운영자              예외(경계에서 처리)
 버그(프로그래머 실수)          null 인자, 범위 밖 인덱스   개발자(코드 수정)          예외(fail-fast)
```

- *결과 타입(Result, Either)*: 함수가 "성공 값 또는 실패 값" 중 하나를 **반환값으로** 돌려준다. 실패가 시그니처에 드러나 호출자가 무시하기 어렵다.
- *예외*: 정상 반환 대신 호출 스택을 거슬러 올라가 잡는 곳까지 간다. 시그니처에 안 드러날 수 있고(unchecked), 중간 계층을 건너뛴다.
- 이 3분류는 Scott Wlaschin의 분류(Domain Errors·Panics·Infrastructure Errors, 『Domain Modeling Made Functional』, 블로그 "Against Railway-Oriented Programming"에서 재인용)를 따른다. 그는 인프라 장애를 도메인으로 모델링할지 패닉처럼 다룰지는 경우마다 다르다고 적는다.

쉬운 예: 은행 창구에서 "잔액이 부족합니다"는 정상 업무 응답이다. 창구 직원이 비상벨을 누르지 않는다. 금고 문이 고장 나면 비상벨이 맞다.\
똑같은 구조다.\
실무 예: 송금 API에서 잔액 부족을 `RuntimeException`으로 던지면, 그 예외는 업무 응답인데도 트랜잭션 롤백·에러 로그·500 번역 같은 "장애용 경로"를 탄다. 반대로 DB 끊김을 `Result.err(DbDown)`으로 감싸 돌려주면 스택 트레이스가 사라지고, 계층마다 그 값을 손으로 전달해야 한다.

기초(어디서 던지고 어디서 잡나, 한 번만 기록)는 [15-error-handling-design](../15-error-handling-design/2-summary.md)에 있다. 이 노트는 **수단의 선택**과 그 선택이 트랜잭션·HTTP·클라이언트 재시도에 미치는 영향을 실험으로 본다.

## 동작·원리

### 1. Railway — 결과 타입을 이어 붙이는 법

```text
            parseAmount           loadAccount            withdraw
 성공 선로 ──[ok]──────────────>──[ok]──────────────>──[ok]──────────> 200 잔액
              \                     \                     \
 실패 선로 ────[err InvalidAmount]──[err NotFound]────────[err Insufficient]──> 4xx로 번역
              (실패 선로에 들어가면 뒤 함수는 실행되지 않는다)
```

- *Railway Oriented Programming*: Wlaschin이 2014년 NDC London 등에서 발표한 비유. 함수마다 성공·실패 두 선로를 가지고, `bind`(Java에서는 `flatMap`)가 선로를 이어 붙인다(fsharpforfunandprofit.com/rop).
- *bind / flatMap*: "성공이면 다음 함수에 값을 넘기고, 실패면 실패를 그대로 흘려보낸다". Wlaschin은 ROP 글에서 Haskell 용어(Either 모나드)를 일부러 쓰지 않았다고 밝힌다. 이유는 그 글이 모나드 튜토리얼이 아니라 에러 처리 문제에 집중하고, F# 입문자 대부분이 모나드에 익숙하지 않아 그림 비유가 더 직관적이기 때문이라고 적는다(fsharpforfunandprofit.com/rop "Relationship to the Either monad").

```java
// 합 타입: 성공 아니면 실패 (Java 17 sealed + Java 16 record)
public sealed interface Result<T> {
    record Ok<T>(T value) implements Result<T> {}
    record Err<T>(DomainError error) implements Result<T> {}

    default <U> Result<U> flatMap(Function<T, Result<U>> f) {
        return switch (this) {                    // Java 21 switch 패턴 매칭
            case Ok<T> ok -> f.apply(ok.value());
            case Err<T> err -> new Err<>(err.error());
        };
    }
}
public sealed interface DomainError {
    record InvalidAmount(long amount) implements DomainError {}
    record AccountNotFound(long id) implements DomainError {}
    record InsufficientBalance(long balance, long requested) implements DomainError {}
}

Result<Long> r = parseAmount(raw).flatMap(a -> loadAccount(id, a)).flatMap(Railway::withdraw);
```

### 실험 A: 선로 따라가기와 경계 번역

(실험, JDK 21.0.12 eclipse-temurin `--cpus=2`, `scratchpad/sd/15/e16/src/e16/Railway.java`, 2026-10-01)

```text
요청 id=1 amount=300
  parseAmount(300)
  loadAccount(1)
  withdraw(1000,300)
  => 200 잔액=700
요청 id=1 amount=abc
  parseAmount(abc)
  => 400 InvalidAmount[amount=-1]
요청 id=9 amount=300
  parseAmount(300)
  loadAccount(9)
  => 404 AccountNotFound[id=9]
요청 id=1 amount=5000
  parseAmount(5000)
  loadAccount(1)
  withdraw(1000,5000)
  => 409 InsufficientBalance[balance=1000, requested=5000]
결과를 무시하고 get():
  parseAmount(abc)
  java.lang.IllegalStateException: get() on Err: InvalidAmount[amount=-1]
```

- `abc`는 `parseAmount`에서 실패 선로로 갔고 `loadAccount`·`withdraw`는 호출되지 않았다. 예외의 "건너뛰기"를 반환값으로 흉내 낸 것이다.
- 경계 번역 `toHttp(DomainError)`는 `switch`로 실패 종류마다 상태 코드를 고른다(400·404·409).
- 마지막 줄: 결과를 검사하지 않고 `get()`으로 꺼내면 런타임 예외가 난다. 결과 타입은 "무시하기 어렵게" 만들 뿐, `get()`·`unwrap()`이라는 비상구가 있다.

### 실험 B: 새 실패 종류를 추가하면 컴파일러가 알려 준다

`DomainError`에 `AccountFrozen`을 추가하고 `toHttp`는 그대로 둔 채 컴파일했다.

(실험, 같은 환경, `scratchpad/sd/15/e16/exh/`)

```text
exh/e16/Railway.java:28: error: the switch expression does not cover all possible input values
        return switch (e) {
               ^
1 error
```

- sealed 계층 위의 `switch`(default 없음)는 빠진 경우를 컴파일 오류로 만든다(JDK 21, JEP 441).
- 예외로 같은 일을 하면 새 예외 클래스는 컴파일을 통과하고, 경계에서 가장 일반적인 처리기(`Exception` → 500)로 떨어진다. 놓친 것이 운영에서야 보인다.
- 반대 비용: 실패 종류를 하나 추가하면 그 `switch`를 쓰는 모든 곳을 고쳐야 한다. 공개 라이브러리의 에러 타입이라면 이것이 호환성 문제가 된다.

### 2. 예외를 고른 경우 — 트랜잭션 롤백 규칙과의 만남

Spring Framework 문서: 기본 설정에서 트랜잭션은 **unchecked 예외(`RuntimeException`의 하위)와 `Error`**에서만 롤백한다. checked 예외는 기본으로 롤백하지 않는다. `rollbackFor`·`noRollbackFor`로 바꾼다. Spring Framework 6.2부터는 `@EnableTransactionManagement(rollbackOn = RollbackOn.ALL_EXCEPTIONS)`로 전역 기본을 "모든 예외에서 롤백"으로 바꿀 수도 있다(소스 `EnableTransactionManagement.rollbackOn()` `@since 6.2`, 기본값 `RUNTIME_EXCEPTIONS`). 아래 실험은 기본값이다.

```text
 @Transactional 메서드 ── 예외/반환 ──> 트랜잭션 인터셉터의 판단
                                       RuntimeException·Error   → 롤백
                                       checked Exception        → 커밋 (기본)
                                       정상 반환(Result.err 포함) → 커밋
```

### 실험 C: 같은 "잔액 부족"을 여섯 방식으로

각 메서드는 `@Transactional`이고, `ledger` 표에 한 줄을 쓴 뒤(또는 쓰기 전에) 잔액 부족을 알린다. 끝난 뒤 남은 행을 셌다. H2 메모리 DB, `DataSourceTransactionManager`.

```java
@Transactional public void runtimeFail() { writeLedger("runtime"); throw new InsufficientRuntime("잔액 부족"); }
@Transactional public void checkedFail() throws InsufficientChecked { writeLedger("checked"); throw new InsufficientChecked("잔액 부족"); }
@Transactional(rollbackFor = InsufficientChecked.class)
public void checkedFailWithRule() throws InsufficientChecked { writeLedger("checked+rollbackFor"); throw new InsufficientChecked("잔액 부족"); }
@Transactional public Result<Long> resultFailAfterWrite() { writeLedger("result-after-write"); return Result.err(new InsufficientBalance(100, 500)); }
@Transactional public Result<Long> resultFailBeforeWrite() {
    if (bal < req) return Result.err(new InsufficientBalance(bal, req));   // 결정 먼저, 쓰기는 나중
    writeLedger("result-before-write"); return Result.ok(bal - req);
}
// 바깥 트랜잭션이 안쪽 @Transactional 빈의 RuntimeException을 잡고 계속 진행
@Transactional public void catchAndContinue() {
    svc.writeLedger("outer");
    try { inner.check(); } catch (InsufficientRuntime e) { /* 잡고 계속 */ }
}
```

(실험, Spring Framework 6.2.19 + H2 2.3.232, JDK 21.0.12 `--cpus=2`, `scratchpad/sd/15/e16/src/e16/TxDemo.java`, 2026-10-01)

```text
Spring Framework 6.2.19, JDK 21.0.12
runtimeFail              -> 예외 InsufficientRuntime: 잔액 부족 | 남은 ledger 행=0
checkedFail              -> 예외 InsufficientChecked: 잔액 부족 | 남은 ledger 행=1
checkedFailWithRule      -> 예외 InsufficientChecked: 잔액 부족 | 남은 ledger 행=0
    반환값: Err[error=InsufficientBalance[balance=100, requested=500]]
resultFailAfterWrite     -> 정상 반환 | 남은 ledger 행=1
    반환값: Err[error=InsufficientBalance[balance=100, requested=500]]
resultFailBeforeWrite    -> 정상 반환 | 남은 ledger 행=0
    (바깥이 잡음: 잔액 부족(안쪽))
outer.catchAndContinue   -> 예외 UnexpectedRollbackException: Transaction rolled back because it has been marked as rollback-only | 남은 ledger 행=0
```

- `checkedFail`: 실패를 알렸는데 쓰기가 **커밋됐다**. checked 예외는 기본 롤백 대상이 아니다. `rollbackFor`를 주면 롤백됐다.
- `resultFailAfterWrite`: 결과 타입은 "정상 반환"이라 트랜잭션 인터셉터가 실패를 모른다. 쓰기가 커밋됐다. 결과 타입을 쓰면 **결정을 쓰기보다 앞에** 둬야 한다(`resultFailBeforeWrite`는 0행).
  - 참고: Spring 문서는 Vavr `Try`의 실패 반환을 롤백으로 다루는 지원을 언급한다. 직접 만든 `Result`는 그 대상이 아니다(위 출력).
- `catchAndContinue`: 안쪽 빈의 `@Transactional`(기본 전파 REQUIRED, 같은 트랜잭션에 참여)이 런타임 예외로 트랜잭션을 rollback-only로 표시했다. 바깥이 예외를 잡고 정상 종료해도 커밋 시점에 `UnexpectedRollbackException`이 났다. 도메인 실패를 예외로 던지고 "잡아서 흐름 제어"하면 이 함정에 빠진다.

### 3. 경계에서의 번역 — HTTP와 메시지

```text
 도메인 실패        →  HTTP 4xx (409 Conflict, 422, 404 …) + RFC 9457 problem+json
 인프라 장애        →  503(재시도 가능) 또는 500
 버그               →  500, 상세는 서버 로그에만
 메시지 소비자       →  도메인 실패: 거절 이벤트 발행 / 일시 장애: 재시도 / 독 메시지: DLQ
```

- RFC 9457(2023, RFC 7807 대체)의 problem details는 `type`·`title`·`status`·`detail`·`instance`와 확장 필드를 둔다. `detail`은 클라이언트가 문제를 고치는 데 초점을 두고 디버깅 정보를 담지 말라고 적는다(§3.1.4).
- 4xx와 5xx 구분은 클라이언트의 **재시도 판단**과 직결된다. 흔한 클라이언트 재시도 정책은 5xx·타임아웃만 재시도한다.

### 실험 D: 잔액 부족을 500으로 번역하면

클라이언트는 5xx면 최대 3번 재시도(총 4번 시도), 4xx면 재시도하지 않는다. 요청 1000건 중 30%가 잔액 부족이다(재시도해도 결과가 같다).

(실험, JDK 21.0.12, `scratchpad/sd/15/e16/src/e16/RetryStorm.java`, 2026-10-01 — 결정적 시뮬레이션)

```text
잔액 부족 -> 409           요청=1000 성공=700 실패=300 서버가 받은 호출=1000
잔액 부족 -> 500           요청=1000 성공=700 실패=300 서버가 받은 호출=1900
```

- 결과(성공 700)는 같은데 서버 부하만 1.9배가 됐다. 재시도해도 안 바뀌는 실패를 "서버 장애"라고 알린 대가다.
- 재시도 정책 쪽 이야기는 [reliability/06-retry-backoff-jitter](../../reliability/06-retry-backoff-jitter/2-summary.md).

### 4. Special Case / Null Object — 실패가 아니라 "특별한 경우"일 때

- Fowler PoEAA "Special Case": null이나 이상한 값 대신, 호출자가 기대하는 것과 **같은 인터페이스**를 가진 특별한 객체를 돌려준다(예: 정체 모를 고객 "occupant"). PoEAA 18장(Base Patterns).
- 『Refactoring』 2판의 "Introduce Special Case"(별칭 Introduce Null Object)가 이 방향의 리팩터링이다(refactoring.com 카탈로그).
- 경계: Special Case는 "할 일이 기본 동작으로 정해진" 경우에 맞다(알 수 없는 고객 → 이름 "occupant", 할인 없음 → 원가). 호출자가 실패를 알아야 하는 경우(잔액 부족)에 쓰면 실패를 숨긴다. 코드는 [18](../18-absence-and-null-design/2-summary.md)에서.

## 쓰이는 자료구조·알고리즘

- **합 타입(sum type)** — "Ok 또는 Err", "InvalidAmount 또는 NotFound 또는 Insufficient". Java는 `sealed interface` + `record`(JDK 17 JEP 409, JDK 16 JEP 395). 경우의 수가 닫혀 있어 컴파일러가 빠짐을 검사한다(실험 B).
- **bind 체인(모나드적 합성)** — `flatMap`이 "성공이면 다음, 실패면 통과"를 한 곳에 담아, 함수마다 `if (err) return err;`를 반복하지 않게 한다.
- **에러 계층(합 타입 트리)** — 도메인 실패를 한 sealed 계층으로 모으면 경계 번역이 전수 `switch` 하나가 된다. 예외 계층(클래스 상속 트리)은 열려 있어 전수 검사가 없다.
- **예외 타입 → 처리기 디스패치** — 경계 처리기는 예외 클래스로 처리 함수를 고르는 표다. Spring(6.2.x)은 한 클래스 안에서 던진 예외 자체(root)에 맞는 처리기를 cause에 맞는 처리기보다 먼저 고르고, 같은 단계 안에서는 상속 거리가 가장 가까운 처리기를 고른다. advice가 여럿이면 우선순위가 먼저다([15](../15-error-handling-design/2-summary.md)).

## 적용 — 풀어나가는 법

### 1. 선택 순서

1. **이 실패를 업무 담당자가 이름으로 부르나?** ("잔액 부족", "한도 초과") → 도메인 실패. 결과 타입이나 도메인 전용 예외로 시그니처에 드러낸다.
2. **재시도·운영자 개입으로 풀리나?** (타임아웃, DB 끊김) → 인프라 장애. 예외로 두고 경계에서 503·재시도로 번역한다. Wlaschin도 I/O에서 날 수 있는 모든 경우를 Result로 모델링하지 말라고 적는다.
3. **코드를 고쳐야만 풀리나?** (null 인자, 불변식 위반) → 버그. 예외로 fail-fast([15](../15-error-handling-design/2-summary.md)).
4. 팀 언어·프레임워크 관례를 따른다. Java + Spring 코드베이스에서 결과 타입을 쓰면 트랜잭션 롤백(실험 C)과 경계 번역을 직접 챙겨야 한다.

- Bloch 『Effective Java』 3판 Item 69 "Use exceptions only for exceptional conditions", Item 70 "Use checked exceptions for recoverable conditions and runtime exceptions for programming errors"(Pearson 목차로 제목 확인). Java의 전통적 답은 "회복 가능한 실패 = checked 예외"였다. 실험 C의 checked 예외 커밋 동작과 함께 고려해야 한다.

### 2. 결과 타입을 쓸 때의 규칙

```java
@Transactional
public Result<Receipt> transfer(TransferCommand cmd) {
    Account from = accounts.get(cmd.from());
    Result<Withdrawal> decision = from.decideWithdraw(cmd.amount());   // 순수한 결정 먼저
    return switch (decision) {
        case Result.Err<Withdrawal> err -> new Result.Err<>(err.error()); // 아무것도 안 썼다
        case Result.Ok<Withdrawal> ok -> {
            ledger.append(ok.value());                                   // 쓰기는 결정 뒤에
            yield Result.ok(Receipt.of(ok.value()));
        }
    };
}
```

- 쓰기 전에 결정한다(실험 C의 before/after 차이). 이것은 [26 functional-core-imperative-shell](../26-functional-core-imperative-shell/2-summary.md)의 "읽기 → 결정 → 쓰기"와 같은 모양이다.
- `get()`·`orElseThrow()`는 경계나 테스트에서만. 비즈니스 코드에서 쓰면 결과 타입을 예외로 되돌린 것이다.
- 결과 안에 예외 객체·스택 트레이스를 담지 않는다(Wlaschin: "Don't use Result to reinvent exceptions").

### 3. 예외를 쓸 때의 규칙

- 도메인 예외는 `RuntimeException` 하위로 두고, 롤백하지 않을 것은 `noRollbackFor`로 **명시**한다. checked로 둔다면 `rollbackFor`를 단다(실험 C).
- 도메인 예외를 같은 트랜잭션 안에서 잡아 흐름을 이어 가지 않는다(실험 C의 `UnexpectedRollbackException`). 안쪽 검사는 예외 대신 boolean·결과 값을 돌려주는 질의 메서드로 바꾼다(Refactoring "Replace Exception with Precheck").

### 4. 진단

```bash
# @Transactional 메서드에서 checked 예외를 던지는데 rollbackFor가 없는 곳
grep -rn -A2 '@Transactional' --include=*.java src/ | grep -E 'throws [A-Z]' | grep -v rollbackFor

# 결과 타입을 비즈니스 코드에서 강제로 꺼내는 곳
grep -rnE '\.(get|orElseThrow|unwrap)\(\)' --include=*.java src/main/ | grep -v '/test/'
```

- 운영 지표: 4xx 중 409·422 비율과 5xx 비율을 따로 본다. 도메인 실패가 5xx로 잡히고 있으면 에러율 SLO가 업무 실패 때문에 소진된다.

## 장애 시나리오와 대처

### 1. 도메인 실패를 예외로 → 롤백 규칙 오작동 (⚠ 커리큘럼)

- 현상 (a): "잔액 부족"으로 실패 응답을 받았는데 원장에 출금 기록이 남았다.
- 보이는 형태: 응답은 실패, DB에는 행이 있다. 예외 클래스가 `Exception`(checked) 하위다.
- 원인: Spring 기본 롤백 규칙은 unchecked와 `Error`만 롤백한다(실험 C `checkedFail` 1행). 6.2의 전역 `rollbackOn = ALL_EXCEPTIONS`를 켠 프로젝트라면 이 경우는 롤백된다.
- 현상 (b): 바깥 서비스가 안쪽 서비스의 "잔액 부족" 예외를 잡고 다른 계좌로 시도했는데 전체가 실패했다.
- 보이는 형태: `UnexpectedRollbackException: Transaction rolled back because it has been marked as rollback-only`(실험 C).
- 원인: 안쪽 `@Transactional`이 같은 트랜잭션을 rollback-only로 표시했다. 예외를 흐름 제어에 쓴 결과다.
- 대처: 롤백 규칙을 예외마다 명시한다. 안쪽 검사는 질의 메서드·결과 값으로 바꾼다. 꼭 별도 트랜잭션이 필요하면 전파 속성을 의도적으로 고른다.

### 2. 결과 타입을 무시하고 `.get()` → 런타임 panic (⚠ 커리큘럼)

- 현상: "실패가 타입에 드러나니 안전하다"던 코드에서 런타임 예외.
- 보이는 형태: `IllegalStateException: get() on Err: …`(실험 A). Vavr 0.10.x `Either.get()`이 Left면 `NoSuchElementException: get() on Left`, `Try.get()`이 Failure면 담긴 원래 예외를 다시 던진다(Vavr 소스). Rust는 ``called `Result::unwrap()` on an `Err` value`` panic이다(Rust `core/src/result.rs`). Vavr·Rust는 소스로만 확인했고 실행하지 않았다.
- 원인: 결과를 검사하지 않고 꺼냈다. 결과 타입은 무시를 어렵게 할 뿐 막지는 않는다.
- 대처: 비즈니스 코드에서 `get()`류 금지(리뷰·정적 분석). `switch`/`fold`로 두 경우를 다 다룬다.

### 3. 모든 실패를 500으로 번역 → 재시도 폭풍 (⚠ 커리큘럼)

- 현상: 프로모션 날 잔액 부족 요청이 몰리자 서버 부하가 두 배 가까이 됐다.
- 보이는 형태: 같은 요청 ID·멱등 키로 들어오는 호출이 여러 번, 5xx 비율 급증, 그런데 성공 수는 그대로(실험 D: 호출 1000 → 1900).
- 원인: 재시도해도 안 바뀌는 도메인 실패를 5xx로 알렸다. 클라이언트·게이트웨이 재시도 정책이 5xx를 재시도한다.
- 대처: 도메인 실패는 4xx(409·422 등) + problem+json으로. 일시 장애만 503 + `Retry-After`.

### 4. 결과 타입 반환 전에 이미 썼다 → 부분 커밋

- 현상: 실패 결과를 돌려준 요청의 쓰기가 남아 있다.
- 보이는 형태: 응답 `Err`, DB에 행 1(실험 C `resultFailAfterWrite`). 에러 로그 없음.
- 원인: 트랜잭션 인터셉터는 정상 반환을 커밋으로 처리한다.
- 대처: 결정 → 쓰기 순서. 불가피하면 `TransactionAspectSupport.currentTransactionStatus().setRollbackOnly()`로 명시하거나 실패 시 예외로 바꾼다.

### 5. 새 실패 종류가 500으로 샌다

- 현상: 새로 만든 "계좌 동결" 실패가 사용자에게 "일시적인 오류"로 보인다.
- 보이는 형태: 특정 기능에서만 500, 로그에 `AccountFrozenException`.
- 원인: 예외 계층은 열려 있어 경계 처리기에 새 타입을 추가하지 않아도 컴파일된다. 가장 일반적인 처리기(500)로 떨어졌다.
- 대처: 도메인 실패를 sealed 계층으로 닫고 `default` 없는 `switch`로 번역해 누락을 컴파일 오류로 만든다(실험 B). 예외를 유지한다면 경계 처리기 테스트에 "도메인 예외 전부가 4xx로 매핑되는가"를 넣는다.

## 핵심 문장

- 실패를 도메인 실패·인프라 장애·버그로 나누고, 도메인 실패만 결과 타입이나 도메인 예외로 시그니처에 드러낸다.
- 결과 타입은 bind 체인으로 이어 붙인다. 실패 선로에 들어가면 뒤 함수는 실행되지 않는다.
- Spring 기본 롤백은 unchecked 예외와 `Error`뿐이다. 실험에서 checked 예외와 실패 결과 반환은 쓰기를 커밋했다.
- 같은 트랜잭션 안에서 도메인 예외를 잡아 흐름을 이어 가면 `UnexpectedRollbackException`이 난다.
- 재시도해도 안 바뀌는 실패를 500으로 알리면 클라이언트 재시도가 부하만 늘린다. 실험에서 서버 호출이 1000에서 1900이 됐다.

## 관련 주제·근거

- 선행
  - [15-error-handling-design](../15-error-handling-design/2-summary.md) — 던지는 곳·잡는 곳, 한 번만 기록
  - [language/08-error-handling-models](../../language/08-error-handling-models/2-summary.md)
- 후속·연결
  - [17-error-messages-and-log-level-policy](../17-error-messages-and-log-level-policy/2-summary.md) — 에러 코드·사용자 메시지·로그 레벨
  - [18-absence-and-null-design](../18-absence-and-null-design/2-summary.md) — Special Case·Null Object 코드
  - [24 types-as-invariants](../24-types-as-invariants/2-summary.md), [26 functional-core-imperative-shell](../26-functional-core-imperative-shell/2-summary.md)
  - [api-design/04-error-format-problem-details](../../api-design/04-error-format-problem-details/2-summary.md)
  - [reliability/06-retry-backoff-jitter](../../reliability/06-retry-backoff-jitter/2-summary.md) — 무엇을 재시도하나
- 글·문서
  - Scott Wlaschin, "Railway Oriented Programming"(NDC London 2014 등) <https://fsharpforfunandprofit.com/rop/> · "Against Railway-Oriented Programming"(2019-12-20, 에러 3분류·Result를 쓰지 말아야 할 때) <https://fsharpforfunandprofit.com/posts/against-railway-oriented-programming/>
  - Martin Fowler, PoEAA "Special Case"(18장) <https://martinfowler.com/eaaCatalog/specialCase.html> · Refactoring 2판 "Introduce Special Case" <https://refactoring.com/catalog/introduceSpecialCase.html> · "Replace Exception with Precheck" <https://refactoring.com/catalog/>
  - John Ousterhout, APOSD 2판 10장 — 예외가 복잡도를 늘리는 이유([15](../15-error-handling-design/2-summary.md)에서 정리)
  - RFC 9457 "Problem Details for HTTP APIs"(2023-07, RFC 7807 대체) §3.1.4·§5 <https://www.rfc-editor.org/rfc/rfc9457>
  - Spring Framework 6.2.x 소스 `EnableTransactionManagement.java`(`rollbackOn`, `@since 6.2`) <https://github.com/spring-projects/spring-framework/blob/6.2.x/spring-tx/src/main/java/org/springframework/transaction/annotation/EnableTransactionManagement.java>
  - Vavr 0.10.5 소스 `Either.java`·`Try.java`(get 동작) · Rust `library/core/src/result.rs`(unwrap 메시지)
  - Spring Framework 문서 "Rolling Back a Declarative Transaction"(기본 롤백 규칙, rollbackFor, Vavr Try) <https://docs.spring.io/spring-framework/reference/data-access/transaction/declarative/rolling-back.html>
  - Joshua Bloch, 『Effective Java』 3판 Item 69·70 — Pearson 목차로 제목 확인 <https://www.pearson.de/media/muster/toc/toc_9780134686073.pdf>
  - OpenJDK JEP 409(Sealed Classes, JDK 17)·JEP 395(Records, JDK 16)·JEP 441(Pattern Matching for switch, JDK 21)
- 실험 목록 (코드: scratchpad `sd/15/e16/src/e16/`, JDK 21.0.12 eclipse-temurin `--cpus=2`, `javac -cp 'libs/*' -d out src/e16/*.java`)
  - A Railway 체인과 경계 번역, `get()` 런타임 예외 — `java -cp out e16.Railway`
  - B 새 실패 종류 추가 시 전수 `switch` 컴파일 오류 — `javac exh/e16/*.java`
  - C `@Transactional` 롤백 규칙 6경우(Spring Framework 6.2.19 + H2 2.3.232, Maven Central에서 받음) — `java -cp 'out:libs/*' e16.TxDemo`
  - D 도메인 실패 409 vs 500과 클라이언트 재시도 — `java -cp out e16.RetryStorm`
