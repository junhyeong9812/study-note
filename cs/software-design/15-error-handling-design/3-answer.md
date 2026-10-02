# software-design/15-error-handling-design — 정답

## 정답

### 1. 두 방향

- 너무 시끄럽다: 계층마다 잡아서 기록하고 다시 던진다. 장애 하나에 ERROR 여러 건·알람 여러 번, 같은 원인이 반복 출력돼 근본 원인을 찾기 어렵다.
- 너무 조용하다: 예외를 삼킨다. 호출자는 성공으로 알고, 에러 로그도 에러율도 0이다. 데이터 불일치로 늦게 발견된다.

### 2. 세 자리

```text
 던지는 곳(불변식 깨짐 발견) ──> 지나가는 곳(잡지 않음 / 번역만) ──> 잡는 곳 = 경계(기록 1회·응답 번역·재시도 결정)
```

- 지나가는 곳에서 `catch`가 정당한 경우: 이 자리에서 실제로 회복할 수 있을 때, 추상화에 맞게 번역할 때(원인 보존), 자원을 정리할 때(`try-with-resources`·`finally`).

### 3. catch-log-rethrow의 비용

(실험, JDK 21.0.12, 2026-10-01)

```text
SEVERE 레코드=4, 전체 로그 줄=62, 'connection reset' 등장=4
...
SEVERE 레코드=1, 전체 로그 줄=16, 'connection reset' 등장=1
```

- 계층마다 기록: SEVERE 4건(repo·service·controller·최상위), 레코드마다 원인 체인이 다시 찍혀 근본 원인 문장이 4번.
- 경계에서 한 번: SEVERE 1건, 원인 1번. 번역 예외가 문맥(주문 id)을, `Caused by`가 원래 예외를 보여 준다.

### 4. 삼킨 예외

```text
save 호출=20, 예외 없음, 실제 저장=15, 사라진 주문=[4, 8, 12, 16, 20]
```

- 호출자는 20건 모두 정상 반환을 받는다. 에러 로그는 없다. 실제 저장은 15건, 5건이 조용히 사라진다.

### 5. fail-fast의 위치

```text
나중에 터짐: Cannot invoke "String.toUpperCase()" because the return value of "ErrDesign$OrderLoose.customer()" is null
  [0] ErrDesign.shipLabel(ErrDesign.java:60)
  [1] ErrDesign.main(ErrDesign.java:93)
  [2] java.base/jdk.internal.reflect.DirectMethodHandleAccessor.invoke(DirectMethodHandleAccessor.java:103)
생성 시점에 터짐: customer
  [0] java.base/java.util.Objects.requireNonNull(Objects.java:259)
  [1] ErrDesign$OrderStrict.<init>(ErrDesign.java:58)
  [2] ErrDesign.main(ErrDesign.java:95)
```

- 늦은 실패는 트레이스 맨 위가 증상 자리(`shipLabel`)라 원인(누가 null로 만들었나)을 거슬러 찾아야 한다.
- fail-fast는 생성자(`<init>`)에서 터진다. 맨 위 `[0]`은 검사 도구 `Objects.requireNonNull`이고, 바로 아래 `[1]`이 원인 자리(생성자)다.
- 늦은 실패의 진짜 비용: 그 사이에 잘못된 데이터가 저장·발행·결제됐을 수 있다. 검사를 추가해도 이미 들어간 데이터는 고쳐지지 않는다.

### 6. 정의로 없애기와 그 한계

- `Files.delete`는 "이미 없음"을 `NoSuchFileException`으로 정의한다. `Files.deleteIfExists`는 "결과적으로 없으면 됨"으로 정의해 `false`를 돌려준다(실험). 목적이 "없게 만들기"인 호출자는 처리할 예외가 하나 준다.
- 쓰면 안 되는 상황: 호출자가 알아야 할 실수(잘못된 인덱스·null 인자 같은 프로그래머 오류)까지 정상으로 바꿀 때. 범위를 잘라 주는 `substring`은 인덱스 계산 버그를 감춘다. 기준은 "그 상황에서 호출자가 할 일이 없는가".

### 7. 번역할 때 붙일 것

- 원인 예외(`cause`)와 문맥(어떤 id·어떤 작업). 예: `new DataAccessFailure("주문 조회 실패 id=" + id, e)`.
- `throw new SaveFailed(e.getMessage())`는 원인 객체를 버려 원래 스택 트레이스(`Caused by`)를 잃는다. 메시지 문자열만 남고 어디서 왜 났는지가 사라진다.

### 8. 에러 0건인데 데이터가 모자람

- 삼킨 예외(빈 `catch`, `catch`에서 `null` 반환)를 의심한다. 에러 지표로는 보이지 않으므로 **건수 대조**(접수 수 vs 저장 수 vs 실패 수)로 어긋남을 확인한다.
- 코드에서는 빈 catch를 grep·PMD `EmptyCatchBlock`으로 찾고, 저장 경로의 `catch`를 하나씩 본다.

### 9. Spring의 경계

- `@RestControllerAdvice`(또는 `@ControllerAdvice`) 안의 `@ExceptionHandler`가 요청 경계다. 여기서만 기록하고 `ProblemDetail`(RFC 9457 표현)로 응답을 번역한다.
- 한 컨트롤러·한 advice 클래스 안에서는 던진 예외 자체(root)에 맞는 처리기가 cause에 맞는 처리기보다 먼저다(root 매치가 하나도 없을 때만 cause로 내려간다). 같은 단계에서 여러 처리기가 맞으면 상속 거리가 가장 가까운 타입의 처리기를 고른다(Spring Framework 6.2.x `ExceptionHandlerMethodResolver.resolveExceptionMapping` → `ExceptionDepthComparator`). advice가 여럿이면 우선순위(order)가 먼저 적용된다(Spring 문서 "Exceptions").
