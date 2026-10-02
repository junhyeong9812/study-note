# software-design/15-error-handling-design — 에러 처리 설계: fail-fast·예외 경계·에러를 정의로 없애기 — 정리 (힌트)

## 해결하는 문제

에러 처리 코드는 정상 경로보다 덜 실행되고 덜 시험된다. 그래서 설계 없이 두면 두 방향으로 망가진다.

```text
 (1) 너무 시끄럽다                         (2) 너무 조용하다
 repo   catch → log → throw               save() { try { ... } catch (Exception e) { } }
 service catch → log → throw                     │
 controller catch → log → throw                  └→ 호출자는 "성공"으로 안다
 최상위 handler → log                              데이터는 없다, 로그도 없다
   → 같은 장애가 로그 4건·스택 트레이스 4벌         → 며칠 뒤 고객 문의로 발견
```

- *fail-fast*: 잘못된 상태를 발견한 그 자리에서 바로 실패시킨다. 잘못된 값이 멀리 흘러가 엉뚱한 곳에서 터지는 것을 막는다.
- *예외 경계(exception boundary)*: 예외를 잡아 **최종 처리**(기록·응답 번역·재시도 결정)하는 자리. 요청 하나의 가장 바깥, 메시지 소비자 하나의 가장 바깥 같은 곳이다.
- *삼킨 예외(swallowed exception)*: 잡고 아무것도 하지 않는 `catch`. 실패가 성공처럼 보인다.

쉬운 예: 택배 분류장에서 주소가 틀린 상자를 발견했다. 그 자리에서 빼내 반송함에 넣으면 끝난다(fail-fast + 경계 한 곳). 직원마다 "이상하네" 메모만 붙이고 다음 칸으로 넘기면 메모 4장이 붙은 상자가 결국 엉뚱한 집에 간다. 아무 메모 없이 바닥에 내려놓으면 상자는 그냥 사라진다.\
똑같은 구조다.\
실무 예: 주문 저장이 DB 연결 끊김으로 실패했다. 계층마다 잡아서 로그를 찍고 다시 던지면 ERROR 4건이 쌓이고 알람이 네 번 운다. 반대로 저장 메서드가 예외를 삼키면 주문은 "접수 완료" 화면을 보여 주고 DB에는 없다.

이 노트는 **어디서 실패시키고, 어디서 잡고, 어떤 에러는 아예 없애나**를 다룬다. 예외냐 결과 타입이냐는 [16](../16-error-strategy-exceptions-vs-results/2-summary.md), 로그 레벨과 메시지는 [17](../17-error-messages-and-log-level-policy/2-summary.md), "없음"은 [18](../18-absence-and-null-design/2-summary.md)에서 다룬다. 언어별 에러 모델(checked/unchecked, 에러 값, panic)은 language/08 error-handling-models — 미작성([language README](../../language/README.md)).

## 동작·원리

### 1. 세 자리: 던지는 곳 · 지나가는 곳 · 잡는 곳

```text
   [던지는 곳]               [지나가는 곳]                      [잡는 곳 = 경계]
   불변식이 깨진 것을         잡지 않는다                         한 번 기록
   발견한 자리                (또는 번역만: 원인을 붙여 다시 던짐)   응답으로 번역(500·409…)
                                                                 재시도·보상 결정
   repo ──IOException──> repo가 DataAccessFailure(원인 포함)로 번역 ──> service ──> controller ──> 경계
```

- *번역(translation)*: 아래 계층의 예외를 이 계층의 말로 바꿔 다시 던진다. 원인(`cause`)을 붙이면 원래 스택 트레이스가 남는다. Bloch 『Effective Java』 3판 Item 73 "Throw exceptions appropriate to the abstraction"이 이 자리다(Pearson 목차로 제목 확인).
- 지나가는 곳은 **잡지 않는 것**이 기본이다. 잡아야 하는 경우는 셋이다: 이 자리에서 실제로 회복할 수 있을 때, 추상화에 맞게 번역할 때, 자원 정리(`try-with-resources`·`finally`)가 필요할 때.
- 잡는 곳은 적을수록 좋다. 경계가 하나면 "기록은 한 번, 응답 번역은 한 표"가 된다.

### 실험 1: catch-log-rethrow vs 경계에서 한 번

같은 장애(저장소의 `IOException: connection reset`)를 3계층(repo → service → controller)에 통과시켰다. A는 계층마다 잡고 기록하고 다시 던진다. B는 repo가 번역만 하고 경계에서 한 번 기록한다. 로그는 `java.util.logging`으로 모아 줄을 셌다.

```java
// A: 계층마다
static void serviceA(long id) {
    try { repoA(id); }
    catch (RuntimeException e) { log.log(Level.SEVERE, "service 실패", e); throw new RuntimeException("service 실패", e); }
}
// B: 번역 + 경계 한 번
static void repoB(long id) {
    try { throw new IOException("connection reset"); }
    catch (IOException e) { throw new DataAccessFailure("주문 조회 실패 id=" + id, e); } // 원인 보존
}
static void boundary(Runnable r) {
    try { r.run(); } catch (RuntimeException e) { log.log(Level.SEVERE, "요청 실패", e); }
}
```

(실험, JDK 21.0.12 eclipse-temurin `--cpus=2`, `scratchpad/sd/15/e15/ErrDesign.java`, 2026-10-01)

```text
== 1. catch-log-rethrow (3계층)
SEVERE 레코드=4, 전체 로그 줄=62, 'connection reset' 등장=4
  SEVERE app repo 실패 id=42
  SEVERE app service 실패
  SEVERE app controller 실패
  SEVERE app 최상위 핸들러

== 2. 경계에서 한 번
SEVERE 레코드=1, 전체 로그 줄=16, 'connection reset' 등장=1
  SEVERE app 요청 실패
  ErrDesign$DataAccessFailure: 주문 조회 실패 id=42
  Caused by: java.io.IOException: connection reset
```

- 장애는 하나인데 A는 SEVERE 4건·로그 62줄, B는 1건·16줄이다(이 3계층 코드에서). 계층이 늘면 A의 건수도 는다.
- A의 레코드마다 원인 체인 전체가 다시 찍혀서 근본 원인 문장이 4번 나온다. 로그 검색에서 "같은 일이 네 번 일어났다"로 오해하기 쉽다.
- B도 원인은 잃지 않았다. 번역 예외(`DataAccessFailure`)가 문맥(주문 id)을 붙이고, `Caused by`가 원래 예외를 보여 준다.

### 2. 삼킨 예외는 조용한 실패가 된다

(실험, 같은 환경 — id가 4의 배수면 저장소가 `IOException`을 던지고, 저장 메서드가 `catch (Exception e) { }`로 삼킨다)

```text
== 3. 삼킨 예외
save 호출=20, 예외 없음, 실제 저장=15, 사라진 주문=[4, 8, 12, 16, 20]
```

- 호출자 쪽에서는 20건 모두 정상 반환이었다. 로그도 없다. 5건이 사라진 것은 저장소를 직접 세어야 보인다.
- Bloch 『Effective Java』 3판 Item 77 제목이 "Don't ignore exceptions"다(목차 확인). 같은 Item은 무시를 택한다면 catch 블록에 그 이유를 주석으로 남기고 변수 이름을 `ignored`로 지으라고 한다(책 본문 미열람 — Item 77 원문을 옮긴 2차 자료로 확인). PMD `EmptyCatchBlock`도 기본 설정에서 예외 변수 이름이 `ignored`·`expected`인 빈 catch는 건너뛴다(`allowExceptionNameRegex` 기본값 `^(ignored|expected)$`, PMD 규칙 문서).

### 3. fail-fast: 생성 시점에 검사한다

```text
 늦은 실패:  new Order(null, 1000)  ──(아무 일 없음)──>  … 몇 계층 뒤 …  shipLabel()에서 NPE
                    ↑ 진짜 원인                                         ↑ 증상이 보이는 곳
 fail-fast:  new Order(null, 1000)  ──> 생성자에서 즉시 NPE("customer")
```

(실험, 같은 환경, 2026-10-02 재실행 — 두 경우 모두 트레이스 위 3프레임 `[0]~[2]`를 같은 방식으로 출력)

```text
== 5. fail-fast
OrderLoose 생성 성공: OrderLoose[customer=null, amount=1000]
나중에 터짐: Cannot invoke "String.toUpperCase()" because the return value of "ErrDesign$OrderLoose.customer()" is null
  [0] ErrDesign.shipLabel(ErrDesign.java:60)
  [1] ErrDesign.main(ErrDesign.java:93)
  [2] java.base/jdk.internal.reflect.DirectMethodHandleAccessor.invoke(DirectMethodHandleAccessor.java:103)
생성 시점에 터짐: customer
  [0] java.base/java.util.Objects.requireNonNull(Objects.java:259)
  [1] ErrDesign$OrderStrict.<init>(ErrDesign.java:58)
  [2] ErrDesign.main(ErrDesign.java:95)
```

- 검사가 없는 `OrderLoose`는 잘못된 채로 만들어졌고, 실패는 `shipLabel`에서 났다. 실제 서비스라면 그 사이에 DB 저장·메시지 발행이 끼어 있을 수 있다.
- 검사가 있는 `OrderStrict`는 생성자(`<init>`)에서 바로 실패했다. 맨 위 `[0]`은 검사 도구 `Objects.requireNonNull`이고, 바로 아래 `[1]`이 원인 자리(생성자)다.
- 프로세스 수준의 fail-fast(감독자에게 재시작을 맡기기)는 [reliability/49-steady-state-fail-fast-and-supervision](../../reliability/49-steady-state-fail-fast-and-supervision/2-summary.md)에서 다룬다. 여기서는 함수·객체 수준이다.

### 4. 에러를 정의로 없애기 (APOSD 10장)

Ousterhout는 APOSD 10장 "Define Errors Out Of Existence"에서 예외 처리를 복잡도의 큰 원천으로 보고, 처리해야 할 예외 자체를 줄이는 API 설계를 권한다. 2판 저자 페이지는 2판의 큰 변경으로 새 장 "Decide What Matters", 6장 개정, 두 장에 넣은 Clean Code 비교 절을 꼽고, 10장 개정은 언급하지 않는다. 장 안의 기법 이름(정의로 없애기·예외 감추기(mask)·예외 모으기(aggregate)·그냥 죽기(just crash))과 예(파일 삭제, Java `substring`)는 2차 요약 두 곳으로 확인했다(책 본문 미열람).

```text
 기법                  질문                                  예
 ─────────────────────────────────────────────────────────────────────────────
 정의로 없애기          그 상황을 "에러"가 아니게 정의할 수 있나?   deleteIfExists, Map.remove, 범위를 잘라 주는 substring
 감추기(mask)           아래 계층에서 처리하고 위에는 안 보이게?    TCP가 패킷 손실을 재전송으로 감춘다(해석·예시)
 모으기(aggregate)      여러 자리의 예외를 한 처리기로?             요청 경계의 핸들러 하나(1절의 B)
 그냥 죽기(just crash)  처리할 가치가 없고 드문가?                  메모리 부족 같은 것
```

(실험, 같은 환경)

```text
== 4. 에러를 정의로 없애기
String.substring(2,10): Range [2, 10) out of bounds for length 5
substringClamped(2,10): "llo"
Files.delete(없는 파일): NoSuchFileException
Files.deleteIfExists(없는 파일): false
Map.remove(없는 키): null
```

- `Files.delete`는 "이미 없음"을 예외로 정의했고, `Files.deleteIfExists`는 "결과적으로 없으면 성공"으로 정의했다. 호출자의 목적이 "없게 만들기"라면 후자는 처리할 예외가 하나 줄어든다.
- 경계: 정의로 없애면 **정말 알아야 할 실수까지 숨길 수 있다**. 범위를 잘라 주는 `substring`은 호출자의 인덱스 계산 버그를 감춘다. APOSD도 이 기법을 지나치게 쓸 수 있다고 경계한다고 2차 요약이 전한다("you can go too far says the author", thedeployguy 요약 — 책 본문 미열람). 판단 기준: 그 상황에서 호출자가 할 일이 "아무것도 안 함"뿐인가.

## 쓰이는 자료구조·알고리즘

- **호출 스택과 예외 전파(스택 되감기)** — 예외는 잡는 `catch`를 만날 때까지 호출 스택을 거꾸로 올라간다. 각 프레임의 `finally`·`try-with-resources`가 정리를 맡는다. 호출 스택 기초는 [systems/call-stack](../../systems/call-stack/README.md).
- **원인 체인(cause chain)** — 예외가 원인 예외를 가리키는 연결 리스트다. 번역할 때 원인을 붙여야 체인이 끊기지 않는다. 체인을 끊으면(`throw new X(e.getMessage())`) 원래 스택 트레이스가 사라진다.
- **경계 처리기 = 예외 타입 → 처리의 디스패치 표** — Spring `@ExceptionHandler`·`@ControllerAdvice`처럼 예외 클래스를 키로 처리 함수를 고른다. 한 컨트롤러 또는 한 `@ControllerAdvice` 클래스 안에서는 ① 던진 예외 자체(root)에 맞는 처리기를 먼저 찾고, 하나도 없을 때만 `getCause()`로 내려가 cause에 맞는 처리기를 찾는다. ② 같은 단계에서 여러 처리기가 맞으면 상속 거리가 가장 가까운 타입을 고른다(Spring Framework 6.2.x 소스 `ExceptionHandlerMethodResolver.resolveExceptionMapping`, 정렬은 `ExceptionDepthComparator` — 6.2는 미디어 타입도 비교). 그래서 `Exception` 포괄 처리기가 같은 클래스에 있으면, 다른 예외에 감싸여 온 `OrderLookupFailed`는 포괄 처리기로 간다. advice 빈이 여럿이면 우선순위(order)가 먼저다 — 높은 우선순위 advice의 cause 매치가 낮은 우선순위 advice의 root 매치보다 앞선다(Spring 문서 "Exceptions").
- **불변식 검사 = 술어** — 생성자·팩토리에서 술어를 평가해 거짓이면 던진다. 타입으로 검사를 옮기는 방법은 [24 types-as-invariants](../24-types-as-invariants/2-summary.md).

## 적용 — 풀어나가는 법

### 1. 순서

1. **경계를 정한다.** HTTP 요청 하나, 메시지 하나, 배치 항목 하나마다 가장 바깥에 처리기 하나. 거기서만 기록하고 응답으로 번역한다.
2. **안쪽은 잡지 않는다.** 잡는다면 회복·번역·정리 셋 중 하나여야 한다. "로그만 찍고 다시 던지기"는 넷째 이유가 아니다.
3. **번역할 때는 원인과 문맥을 붙인다.** `new DataAccessFailure("주문 조회 실패 id=" + id, e)`. Item 75 "Include failure-capture information in detail messages"(목차 확인).
4. **입구에서 fail-fast.** 생성자·팩토리·공개 메서드 첫 줄에서 인자를 검사한다(Item 49 "Check parameters for validity", 목차 확인). 안쪽에서는 검사된 값만 다룬다.
5. **처리할 예외를 줄인다.** 멱등한 삭제, 빈 컬렉션 반환([18](../18-absence-and-null-design/2-summary.md)), 기본값으로 정의할 수 있는지 먼저 본다.
6. **실패해도 상태가 반쯤 바뀌지 않게.** Item 76 "Strive for failure atomicity"(목차 확인) — 검사를 먼저 하고 쓰기는 나중에. 트랜잭션이 이 일을 돕지만 롤백 규칙을 알아야 한다([16](../16-error-strategy-exceptions-vs-results/2-summary.md)의 실험).

### 2. 코드 (Java, Spring MVC 경계)

```java
// 안쪽: 번역만
class OrderRepository {
    Order find(long id) {
        try { return jdbc.queryForObject(SQL, mapper, id); }
        catch (DataAccessException e) { throw new OrderLookupFailed(id, e); }   // 원인 보존
    }
}

// 경계: 한 번 기록 + 응답 번역 (Spring Framework 6.x)
@RestControllerAdvice
class ApiBoundary {
    private static final Logger log = LoggerFactory.getLogger(ApiBoundary.class);

    @ExceptionHandler(OrderLookupFailed.class)
    ProblemDetail lookupFailed(OrderLookupFailed e) {
        log.error("order lookup failed id={}", e.orderId(), e);   // 여기서만 기록
        return ProblemDetail.forStatus(HttpStatus.SERVICE_UNAVAILABLE);
    }
}
```

- `ProblemDetail`은 Spring Framework 6.x의 RFC 9457 응답 표현이다(Spring 문서 "Error Responses"). 메시지 설계는 [17](../17-error-messages-and-log-level-policy/2-summary.md).

### 3. 진단 — 코드베이스에서 냄새 찾기

```bash
# 빈 catch 블록(삼킨 예외) 후보
grep -rnE 'catch \([^)]*\) *\{ *\}' --include=*.java src/

# catch 안에서 로그 찍고 다시 던지는 자리 (log.* 다음 몇 줄 안에 throw)
grep -rn -A3 'catch (' --include=*.java src/ | grep -B2 'throw ' | grep -E 'log\.(error|warn)'

# 원인을 버리는 번역 (getMessage만 넘김)
grep -rnE 'throw new \w+\([a-z]+\.getMessage\(\)\)' --include=*.java src/
```

- 정적 분석 규칙도 있다. PMD `EmptyCatchBlock`(errorprone 범주, PMD 규칙 문서)이 빈 catch를, Sonar Java 규칙 S2139가 "로그 찍고 다시 던지기"를 잡는다. S2139의 메시지는 "Either log this exception and handle it, or rethrow it with some contextual information."이다(sonar-java 소스 `LoggedRethrownExceptionsCheck.java`).
- 운영에서는 **같은 요청 ID로 ERROR가 여러 건**인 비율을 본다. 1건보다 많으면 어딘가에서 catch-log-rethrow가 일어난다.

## 장애 시나리오와 대처

### 1. 계층마다 catch-log-rethrow → 로그 중복·원인 은폐 (⚠ 커리큘럼)

- 현상: 장애 1건에 ERROR 로그가 여러 건, 알람도 여러 번. 로그를 읽는 사람이 어느 것이 근본 원인인지 찾지 못한다.
- 보이는 형태: 같은 요청 ID로 ERROR 4건, 근본 원인 문장(`connection reset`)이 4번(실험 1의 A). 중간 계층이 `new RuntimeException("service 실패")`처럼 문맥 없는 메시지로 감싸면 맨 위 메시지는 쓸모가 없다.
- 원인: "잡으면 일단 기록"이라는 습관. 기록 책임이 경계에 모여 있지 않다.
- 대처: 기록은 경계에서 한 번. 안쪽은 번역(원인+문맥)만. 리뷰 규칙으로 "로그 찍고 다시 던지기"를 막는다.

### 2. 삼킨 예외 → 조용한 실패 (⚠ 커리큘럼)

- 현상: 기능은 "성공"을 보여 주는데 데이터가 없다. 며칠 뒤 고객 문의나 정산 불일치로 발견된다.
- 보이는 형태: 에러 로그 0, 에러율 0. 대신 건수 지표(주문 접수 수 vs 저장된 주문 수)가 어긋난다(실험 2: 호출 20, 저장 15).
- 원인: `catch (Exception e) { }` 또는 `catch (...) { return null; }`. 컴파일러가 checked 예외 처리를 강제하자 일단 비워 둔 자리가 많다.
- 대처: 빈 catch를 정적 분석으로 막는다. 무시가 정말 맞으면 이유를 주석으로 남긴다. 건수 대조 지표(들어온 수 = 처리된 수 + 실패 수)를 둔다.

### 3. 원인을 버린 번역 → 디버깅 불가

- 현상: 로그에 "저장 실패"만 있고 무엇 때문인지 없다.
- 보이는 형태: 스택 트레이스가 번역 지점에서 시작하고 `Caused by`가 없다.
- 원인: `throw new SaveFailed(e.getMessage())` — 원인 객체를 넘기지 않았다.
- 대처: 생성자에 `cause`를 넘긴다. 진단 grep(적용 3)으로 찾는다.

### 4. 늦은 실패 → 잘못된 데이터가 이미 저장된 뒤 터진다

- 현상: 출고 라벨 생성에서 NPE. 그런데 주문은 이미 저장·결제됐다.
- 보이는 형태: 스택 트레이스 맨 위가 증상 자리(`shipLabel`)이고, 원인 자리(주문 생성)는 트레이스에 없다(3절 fail-fast 실험).
- 원인: 생성 시점에 불변식을 검사하지 않았다.
- 대처: 생성자·팩토리에서 fail-fast. 이미 들어간 잘못된 데이터는 따로 찾아 고친다(검사 추가만으로는 과거 데이터가 고쳐지지 않는다).

### 5. 정의로 없애기를 과하게 → 버그가 조용히 지나간다

- 현상: 인덱스 계산이 틀렸는데 결과 문자열이 조금 짧을 뿐 아무 에러가 없다.
- 보이는 형태: 에러 없음. 출력이 미묘하게 틀림.
- 원인: 범위를 잘라 주는 API가 호출자의 실수까지 "정상"으로 정의했다.
- 대처: 정의로 없애는 것은 "호출자가 할 일이 없는" 상황에 한정한다. 프로그래머 실수(인덱스·null 인자)는 fail-fast가 맞다.

## 핵심 문장

- 예외는 던지는 곳·지나가는 곳·잡는 곳으로 나뉜다. 지나가는 곳은 잡지 않거나 원인을 붙여 번역만 한다.
- 기록은 경계에서 한 번 한다. 실험에서 3계층 catch-log-rethrow는 장애 하나에 SEVERE 4건·62줄, 경계 한 번은 1건·16줄이었다.
- 삼킨 예외는 실패를 성공으로 바꾼다. 실험에서 20건 중 5건이 에러 없이 사라졌다.
- fail-fast는 실패를 원인 자리로 당긴다. 생성자에서 검사하면 원인 자리(생성자)가 트레이스 맨 위 근처(검사 도구 프레임 바로 아래)에 나온다.
- APOSD 10장은 처리할 예외 자체를 줄이라고 권한다. 단 호출자의 실수까지 감추면 버그가 조용해진다.

## 관련 주제·근거

- 선행
  - language/08 error-handling-models — 미작성([language README](../../language/README.md))
  - [01-complexity](../01-complexity/2-summary.md) — 복잡도의 증상. 에러 처리는 unknown unknowns의 큰 원천
- 후속
  - [16-error-strategy-exceptions-vs-results](../16-error-strategy-exceptions-vs-results/2-summary.md) — 예외 vs 결과 타입, 트랜잭션 롤백 규칙
  - [17-error-messages-and-log-level-policy](../17-error-messages-and-log-level-policy/2-summary.md) — 한 번만 로깅, 레벨 정의, 사용자 메시지
  - [18-absence-and-null-design](../18-absence-and-null-design/2-summary.md) — "없음"을 에러로 만들지 않기
  - [23 design-by-contract](../23-design-by-contract/2-summary.md), [24 types-as-invariants](../24-types-as-invariants/2-summary.md)
  - [reliability/49-steady-state-fail-fast-and-supervision](../../reliability/49-steady-state-fail-fast-and-supervision/2-summary.md) — 프로세스 수준 fail-fast
  - [reliability/15-logging](../../reliability/15-logging/2-summary.md) — 로그 파이프라인
- 글·문서
  - John Ousterhout, 『A Philosophy of Software Design』 2판(2021) 10장 "Define Errors Out Of Existence". 2판 변경 범위: 저자 페이지 <https://web.stanford.edu/~ouster/cgi-bin/aposd.php>. 장 안의 기법·예는 2차 요약으로 확인 <https://hamersoft.com/2022/05/27/60-review-a-philosophy-of-software-design-chapter-10/> · <https://thedeployguy.com/2019-06-16-a-philosophy-of-software-design-summary-part-2-cp10-end/>
  - Joshua Bloch, 『Effective Java』 3판(2018) Item 49·73·75·76·77 — 제목은 Pearson 목차 PDF로 확인, 본문 미열람 <https://www.pearson.de/media/muster/toc/toc_9780134686073.pdf>
  - Martin Fowler, 『Refactoring』 2판 카탈로그 "Replace Error Code with Exception"·"Replace Exception with Precheck"·"Introduce Assertion" <https://refactoring.com/catalog/>
  - JDK 21 API: `Files.delete`(`NoSuchFileException`)·`Files.deleteIfExists`, `String.substring` — 실험으로 동작 확인
  - PMD `EmptyCatchBlock` <https://pmd.github.io/pmd/pmd_rules_java_errorprone.html> · Sonar S2139 <https://github.com/SonarSource/sonar-java/blob/master/java-checks/src/main/java/org/sonar/java/checks/LoggedRethrownExceptionsCheck.java>
  - Spring Framework 문서 "Exceptions"(`@ExceptionHandler` 매칭 규칙) <https://docs.spring.io/spring-framework/reference/web/webmvc/mvc-controller/ann-exceptionhandler.html> · 소스 <https://github.com/spring-projects/spring-framework/blob/6.2.x/spring-web/src/main/java/org/springframework/web/method/annotation/ExceptionHandlerMethodResolver.java>
  - Effective Java Item 77 원문을 옮긴 2차 자료(`ignored` 관례) <https://github.com/Jiayongbao/Effective-Java-3rd-edition-Chinese-English-bilingual/blob/dev/Chapter-10/Chapter-10-Item-77-Don’t-ignore-exceptions.md>
  - Spring Framework 문서 "Error Responses"(`ProblemDetail`, RFC 9457) <https://docs.spring.io/spring-framework/reference/web/webmvc/mvc-ann-rest-exceptions.html>
- 실험 목록 (코드: scratchpad `sd/15/e15/ErrDesign.java`, JDK 21.0.12 eclipse-temurin `--cpus=2`, `java ErrDesign.java`)
  - 1 catch-log-rethrow 3계층 vs 경계 한 번 — SEVERE 4/62줄 vs 1/16줄
  - 2 삼킨 예외 — 20건 중 5건 무음 유실
  - 3 에러를 정의로 없애기 — `substring`·`Files.delete`·`deleteIfExists`·`Map.remove`
  - 4 fail-fast — 생성 시점 vs 사용 시점 실패 위치(2026-10-02 재실행: 두 경우 모두 트레이스 `[0]~[2]`를 출력하도록 고친 사본 scratchpad `sd/adj-02/ErrDesign.java`)
