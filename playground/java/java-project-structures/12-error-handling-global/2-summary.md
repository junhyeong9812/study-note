# java/java-project-structures/12 — 글로벌 에러 처리 — 정리 (힌트)

> 출처 — study-site 항목 `java/error-handling-global`(항목 데이터 `data/java/project-structures.json`) · 정답 코드 study-practice `java/java-project-structures/reference/error-handling-global.java`\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).\
> 실행 — 실행하지 않음 — Java 예제는 이 문서를 만들 때 컴파일 · 실행하지 않았다(JDK 로 돌려 확인한다).

## 한눈에 — 쉽게 말하면

**글로벌 에러 처리는 「회사의 민원 창구 한 곳」이다.**
각 부서는 문제가 생겨도 손님에게 직접 답장하지 않는다.
대신 종류가 적힌 「문제 쪽지」를 위로 올려 보낸다.
민원 창구 한 곳이 쪽지의 종류를 보고 정해진 양식으로 답장을 쓴다.
쪽지 종류에 없는 정체불명의 사고(기계 고장 같은 내부 사정)는 손님에게 자세히 말하지 않는다.
「내부 사정으로 처리하지 못했다」고만 답하고, 자세한 내용은 사내 일지에만 적는다.
글로벌 에러 처리도 똑같은 구조다.

| 비유 | 실체 |
|---|---|
| 부서 | `MemberService` 같은 서비스 |
| 문제 쪽지 | 던져진 예외 객체 |
| 쪽지의 종류 | 예외 클래스 계층(`BaseException` 아래 클래스들) |
| 민원 창구 | `GlobalExceptionHandler` |
| 쪽지를 창구로 모으는 통로 | `MemberController.safeExecute` 의 `try-catch` |
| 답장 양식 | `ErrorResponse` |
| 내부 사고 · 사내 일지 | 계층 밖의 예외 · `System.err` 기록 |

```text
 MemberService ──throw──▶ 예외 객체 (종류 = 클래스)
                               │
                               ▼
               MemberController.safeExecute   (catch 는 여기 한 곳)
                               │
                               ▼
               GlobalExceptionHandler.handle
               ├─ ValidationException   → 400 + 필드별 details
               ├─ 그 밖의 BaseException  → 예외에 담긴 코드·상태·메시지
               └─ 모르는 예외            → 500 + 일반 메시지 (상세는 서버 로그)
                               │
                               ▼
                       ErrorResponse (한 가지 꼴)
```

## 이 주제가 답하려는 질문

1. 예외를 어떤 계층으로 나눠야 응답 상태(4xx · 5xx)를 한 곳에서 정할 수 있나?
2. 모든 에러 응답을 어떤 한 가지 꼴로 맞추나?
3. 예외를 응답으로 바꾸는 일을 어디 한 곳에 모으고, 비즈니스 코드의 `try-catch` 를 어떻게 없애나?
4. 클라이언트에게 무엇을 보여 주고 무엇을 숨기나?

## 동작 방식

### (1) 예외 계층 — 예외 객체가 응답에 필요한 정보를 들고 다닌다

**언제 쓰나** — 예외의 종류마다 응답 코드와 HTTP 상태가 정해져 있을 때 쓴다.
예외를 던지는 쪽이 「무엇이 잘못됐나」를 클래스와 필드로 함께 실어 보낸다.

```text
RuntimeException
└─ BaseException (abstract)              errorCode, httpStatus
   ├─ BusinessException  (4xx · 클라이언트 요청 탓)
   │  ├─ EntityNotFoundException      NOT_FOUND         404
   │  ├─ DuplicateResourceException   DUPLICATE         409
   │  ├─ ValidationException          VALIDATION_ERROR  400  + fieldErrors
   │  └─ UnauthorizedException        UNAUTHORIZED      401
   └─ SystemException    (5xx · 서버 내부 탓)
                                      INTERNAL_ERROR    500  + cause
```

- 맨 위 `BaseException` 은 `abstract` 라서 직접 만들 수 없고, 모든 하위 예외가 `errorCode` 와 `httpStatus` 를 물려받는다.
- `BaseException` 의 생성자는 둘이다 — 메시지만 받는 것과 원인 예외(`cause`)까지 받는 것.
- `BusinessException` 은 4xx 갈래의 부모이고, 그 아래 클래스들은 생성자에서 코드 · 메시지 · 상태를 고정한다.
- 예를 들어 `new EntityNotFoundException("회원", 99L)` 은 코드 `NOT_FOUND`, 메시지 `회원 없음: id=99`, 상태 `404` 를 갖는다.
- `DuplicateResourceException("email", "kim@test.com")` 의 메시지는 `email 중복: kim@test.com` 이다.
- `ValidationException` 은 메시지가 늘 `입력값 검증 실패` 이고, 대신 필드별 에러 맵(`fieldErrors`)을 따로 든다.
- `SystemException` 은 5xx 갈래로, 원인 예외를 함께 받아 `super(message, cause)` 로 넘긴다.

> **예외 계층** — 예외 클래스들을 상속으로 묶어 「큰 종류 → 작은 종류」 나무로 만든 것.\
> 예: `EntityNotFoundException` 은 `BusinessException` 이고, `BusinessException` 은 `BaseException` 이다.

맨 위가 `RuntimeException` 인 데는 까닭이 있다.
`RuntimeException` 의 자손은 언체크 예외라서, 던지는 메서드가 `throws` 를 선언하지 않아도 된다.
그래서 `MemberService` 의 메서드들은 시그니처가 깨끗하고, 호출하는 쪽도 `try-catch` 를 강제로 쓰지 않는다.
또 컨트롤러는 서비스 호출을 `Runnable` 람다 안에 넣는데, `Runnable.run()` 은 체크 예외를 던지도록 선언돼 있지 않다.
예외가 체크 예외였다면 그 람다 안에서 서비스를 부를 수 없었다(컴파일 오류).

> **언체크 예외** — `RuntimeException` 이나 그 자손처럼 `throws` 선언 · `catch` 가 강제되지 않는 예외.\
> 예: `throw new EntityNotFoundException("회원", id);` 를 던지는 메서드에 `throws` 가 없다.

Java 에서 던질 수 있는 모든 것의 뿌리는 `Throwable` 이고, 그 아래가 `Exception` 과 `Error` 로 갈린다.
`RuntimeException` 은 `Exception` 의 자손이다.
`Error`(예: 메모리 부족 같은 JVM 수준의 문제)는 `Exception` 이 아니다.

```text
Throwable
├─ Error              ← catch (Exception e) 에 안 걸린다
└─ Exception
   └─ RuntimeException
      └─ BaseException …
```

### (2) 표준 에러 응답 — `ErrorResponse`

**언제 쓰나** — 어떤 에러든 클라이언트가 같은 꼴로 받아 한 가지 코드로 처리하게 하고 싶을 때 쓴다.

`ErrorResponse` 는 다섯 필드를 갖는다.

| 필드 | 뜻 |
|---|---|
| `code` | 비즈니스 식별 코드(`NOT_FOUND` · `DUPLICATE` …) |
| `message` | 사람이 읽을 메시지 |
| `status` | HTTP 상태 코드 |
| `timestamp` | 발생 시각(`LocalDateTime.now().toString()`) |
| `details` | 필드별 상세(유효성 검증용) |

```text
ErrorResponse.of("NOT_FOUND", "회원 없음: id=99", 404)
      │  details = null 로 생성자 호출
      ▼
생성자: details 가 null → Map.of() (빈 맵) 으로 바꿔 넣는다
      ▼
toString(): details 가 비었으니 details 부분을 빼고
      ▼
ErrorResponse{code='NOT_FOUND', status=404, message='회원 없음: id=99'}   ← 코드를 읽어 만든 꼴
```

- 생성자는 `private` 이라 바깥에서는 두 정적 팩토리로만 만든다.
- `of(code, message, status)` 는 단순 에러용으로, `details` 자리에 `null` 을 넘긴다.
- `withDetails(code, message, status, details)` 는 필드 에러를 담는 검증 실패용이다.
- 생성자는 `null` 인 `details` 를 빈 맵으로 바꿔 둔다 — 그 뒤로는 `details` 가 `null` 일 일이 없다.
- `toString()` 은 `timestamp` 를 찍지 않는다.
- `details` 가 비어 있으면 `, details=…` 부분이 아예 빠지고, 있으면 맵의 `toString()` 이 그대로 붙는다.

> **정적 팩토리 메서드** — 생성자 대신 쓰는, 객체를 만들어 돌려주는 `static` 메서드.\
> 예: `ErrorResponse.of(...)` · `ErrorResponse.withDetails(...)`.

### (3) `GlobalExceptionHandler.handle` — 위에서부터 차례로 검사한다

**언제 쓰나** — 「예외 → 응답」 바꾸기 규칙을 프로그램 전체에서 한 곳에만 두고 싶을 때 쓴다.

```text
handle(e)
  │
  ├─ e instanceof ValidationException ve ?
  │     예 → withDetails(코드, 메시지, 상태, ve.getFieldErrors())
  │
  ├─ e instanceof BaseException be ?
  │     예 → of(be.getErrorCode(), be.getMessage(), be.getHttpStatus())
  │
  └─ 둘 다 아님
        System.err 에 "[UNEXPECTED] 클래스이름: 메시지" 를 남기고
        → of("INTERNAL_ERROR", "서버 내부 오류가 발생했습니다", 500)
```

- 첫 검사는 가장 좁은 `ValidationException` 이다 — 필드별 에러를 `details` 로 실어야 하기 때문이다.
- 둘째 검사는 넓은 `BaseException` 이다 — 예외에 담긴 코드 · 상태 · 메시지를 그대로 응답에 옮긴다.
- 차례가 중요하다: `ValidationException` 도 `BaseException` 이므로, 넓은 검사를 먼저 하면 검증 예외가 그쪽에 먼저 걸려 `details` 가 사라진다.
- 셋째 갈래는 계층 밖의 예외다 — 클래스 단순 이름(`getSimpleName()`)과 원래 메시지는 서버 쪽 `System.err` 에만 남는다.
- 클라이언트가 받는 응답에는 일반 메시지 `서버 내부 오류가 발생했습니다` 만 들어간다.
- `e instanceof ValidationException ve` 는 검사와 동시에 그 타입의 변수 `ve` 를 만드는 패턴 매칭 문법이다.

> **패턴 매칭 `instanceof`** — 타입 검사가 참이면 그 타입으로 바뀐 변수를 바로 쓰게 해 주는 꼴.\
> 예: `if (e instanceof BaseException be) return be.getErrorCode();`

주의할 점이 하나 있다.
`SystemException` 도 `BaseException` 이므로 둘째 갈래에 걸린다.
그러면 `SystemException` 의 메시지가 그대로 응답에 실린다(→ 「어디서 틀리나 2」).

### (4) 컨트롤러의 `safeExecute` — 잡는 곳을 한 곳으로 모은다

**언제 쓰나** — 컨트롤러 메서드마다 같은 `try-catch` 를 되풀이하지 않으려고 쓴다.

```text
controller.findById(99L)
  │
  ▼
safeExecute( () -> System.out.println("  응답: " + service.findById(99L)) )
  │  try { printer.run(); }
  ▼
"  응답: " + service.findById(99L) 을 먼저 계산하려다
service 가 EntityNotFoundException 을 던진다 → println 은 불리지 않는다
  │
  ▼
catch (Exception e) → exHandler.handle(e) → ErrorResponse
  │
  ▼
System.out.println("  응답: " + error)
```

- 컨트롤러의 공개 메서드 넷(`register` · `findById` · `adminOnly` · `riskyOperation`)은 모두 서비스 호출을 람다로 감싸 `safeExecute` 에 넘긴다.
- 람다는 「서비스 결과를 `"  응답: "` 뒤에 붙여 찍기」 한 일만 한다.
- 문자열 이어 붙이기가 `println` 보다 먼저 계산되므로, 서비스가 예외를 던지면 람다는 아무것도 찍지 않는다.
- 예외는 `catch (Exception e)` 에 걸려 핸들러로 가고, 바뀐 `ErrorResponse` 가 `"  응답: "` 뒤에 찍힌다.
- 성공이면 `null`, 실패면 `ErrorResponse` 를 돌려주지만, 부르는 쪽은 그 값을 쓰지 않는다.
- 서비스(`MemberService`)에는 `try-catch` 가 하나도 없다 — 예외를 던지기만 하고, 처리는 글로벌 핸들러 책임이다.
- `catch (Exception e)` 는 `Error` 를 잡지 못한다 — (1)의 나무에서 `Error` 는 `Exception` 의 바깥이다.

### (5) 한 번의 `main` 이 지나가는 여섯 갈래

`MemberService` 는 `HashMap<Long, String>` 에 회원 이메일을 담고, `seq` 를 하나씩 늘려 id 로 쓴다.
`register` 는 검증 → 중복 검사 → 저장 순서로 일한다.
검증은 에러를 `LinkedHashMap` 에 **모았다가** 하나라도 있으면 한꺼번에 `ValidationException` 으로 던진다.
이름이 `null` 이거나 비어 있으면(`isBlank()`) `name` 에러, 이메일이 `null` 이거나 `@` 가 없으면 `email` 에러다.
중복 검사는 `members.containsValue(email)` 로 한다.

| 차례 | 호출 | 일어나는 일 | 응답의 code · status |
|---|---|---|---|
| 1 | `register("김철수", "kim@test.com")` | 통과, id 1 로 저장 | 성공(에러 아님) |
| 2 | `register("", "invalid-email")` | 두 필드 모두 검증 실패 | `VALIDATION_ERROR` · 400 + details |
| 3 | `register("이영희", "kim@test.com")` | 검증 통과, 이메일 중복 | `DUPLICATE` · 409 |
| 4 | `findById(99L)` | 99번 없음 | `NOT_FOUND` · 404 |
| 5 | `adminOnly("USER")` | 역할이 `"ADMIN"` 아님 | `UNAUTHORIZED` · 401 |
| 6 | `riskyOperation()` | 계층 밖 `RuntimeException` | `INTERNAL_ERROR` · 500 |

- `adminOnly` 는 `"ADMIN".equals(role)` 꼴로 비교한다 — 상수 쪽에서 `equals` 를 부르면 `role` 이 `null` 이어도 `NullPointerException` 이 나지 않는다.
- `riskyOperation` 은 `"NullPointerException at line 42"` 라는 메시지의 평범한 `RuntimeException` 을 던져, 예상하지 못한 내부 오류를 흉내 낸다.
- 6번에서 그 메시지는 `System.err` 쪽에만 남고 응답에는 일반 메시지만 실린다.

### (6) Spring 에서는

Spring 에서는 같은 패턴을 `@ControllerAdvice` 와 `@ExceptionHandler` 로 만든다.
`@ControllerAdvice` 를 붙인 클래스가 이 예제의 `GlobalExceptionHandler` 자리이고, 그 안의 `@ExceptionHandler` 메서드들이 `handle` 안의 분기 하나하나에 해당한다.
프레임워크가 모든 컨트롤러에 자동으로 적용하므로, 이 예제의 `safeExecute` 같은 감싸기 헬퍼가 필요 없다.
이 예제는 Spring 없이 그 구조를 `safeExecute` 로 흉내 낸 것이다.

> **`@ControllerAdvice`** — 여러 컨트롤러에 공통으로 적용할 예외 처리 등을 모아 두는 Spring 애너테이션.\
> 예: `@ControllerAdvice class GlobalExceptionHandler { @ExceptionHandler(...) ... }`.

## 문법 — 형태와 규칙

```java
abstract class AppException extends RuntimeException {
    final int status;
    AppException(String msg, int status) { super(msg); this.status = status; }
}
class NotFound extends AppException {
    NotFound(long id) { super("없음: id=" + id, 404); }
}
class Handler {
    String handle(Exception e) {
        if (e instanceof NotFound nf) return "404 " + nf.getMessage();   // 좁은 것 먼저
        if (e instanceof AppException ae) return ae.status + " " + ae.getMessage();
        System.err.println("[UNEXPECTED] " + e);                           // 상세는 서버에만
        return "500 서버 내부 오류";
    }
}
```

- 계층의 뿌리는 `RuntimeException` 을 잇는다 — 던지는 쪽 · 람다 안에서 `throws` 부담이 없다.
- 뿌리에 응답에 필요한 정보(코드 · 상태)를 필드로 두고, 하위 클래스 생성자에서 값을 고정한다.
- 원인 예외를 받는 생성자를 두고 `super(message, cause)` 로 넘겨 원인 연결을 잃지 않는다.
- 핸들러의 `instanceof` 분기는 **좁은 타입 → 넓은 타입** 순서로 쓴다.
- 마지막 갈래(모르는 예외)는 상세를 서버 로그에만 남기고 일반 메시지와 500 을 돌려준다.
- 응답 객체는 한 클래스로 통일하고, 필드 에러가 없을 때도 빈 맵으로 맞춰 `null` 을 없앤다.

## 어디서 틀리나

### 1. 핸들러 분기를 넓은 타입부터 쓴다
`if (e instanceof BaseException …)` 을 먼저 두면 `ValidationException` 이 그 갈래에 걸린다.
그러면 `of(...)` 로 응답이 만들어져 필드별 `details` 가 빠진다.
좁은 타입을 위에, 넓은 타입을 아래에 둔다.

### 2. `SystemException` 의 메시지가 클라이언트에 나간다
원본의 주장 → 정답 코드 주석은 `SystemException` 을 「서버 내부 문제. 메시지 노출 금지」라고 하고, 팁도 「500 에러에서는 내부 메시지를 클라이언트에 노출하지 않는다」고 한다.
왜 의심스러운가 → `SystemException` 은 `BaseException` 의 자손이라 `handle` 의 둘째 갈래(`e instanceof BaseException be`)에 걸린다.
그 갈래는 `be.getMessage()` 를 그대로 응답에 넣으므로, `SystemException` 에 담은 내부 메시지가 500 응답에 실린다.
예제의 `main` 에서는 `SystemException` 을 던지는 곳이 없어 드러나지 않을 뿐이다.
막으려면 `SystemException`(또는 상태가 500 인 예외)을 따로 먼저 검사해 일반 메시지로 바꿔야 한다(원본에 근거 없음 — 추론).

### 3. 500 응답에 `e.getMessage()` 를 넣는다
팁 그대로, 500 에서는 내부 메시지를 노출하지 않는다.
`"NullPointerException at line 42"` 같은 메시지는 코드 위치 · 내부 구조를 드러낸다.
상세는 서버 로그(`System.err`)로, 클라이언트에는 일반 메시지로 나눈다.

### 4. 유효성 에러를 첫 번째 하나만 알려 준다
팁은 「유효성 에러는 필드별 상세 메시지를 제공한다」고 한다.
에러를 찾는 즉시 던지면 클라이언트는 고치고 다시 보내기를 여러 번 되풀이해야 한다.
예제처럼 `LinkedHashMap` 에 필드별로 모은 뒤 한 번에 던지면 모든 문제를 한 응답에 담는다.
`LinkedHashMap` 이라서 `details` 의 순서가 검사한 순서(`name` → `email`)와 같다.

### 5. 「권한 없음」에 401 을 쓴다
원본의 주장 → 정답 코드 주석은 「인증/인가 실패 → 401」이라 하고, `adminOnly("USER")` 처럼 역할이 모자란 경우에도 401 을 준다.
왜 의심스러운가 → HTTP 의 흔한 관례로 401 은 「누구인지 확인되지 않음(인증 실패)」, 403 은 「누구인지는 알지만 권한이 없음(인가 실패)」을 뜻한다(확인 필요).
그 관례를 따르면 `adminOnly` 의 경우는 403 이 더 맞다.

### 6. 예외 계층을 가볍게 정한다
정답 코드 주석의 트레이드오프 그대로, 예외 계층은 한 번 정하면 영향이 넓어 초기 설계 비용이 크다.
코드 · 상태를 어디에 두고 4xx/5xx 를 어떻게 가를지 처음에 정해 두어야 나중에 고칠 곳이 적다.

### 7. `catch (Exception e)` 가 모든 것을 잡는다고 믿는다
`Error` 는 `Exception` 이 아니므로 `safeExecute` 를 그냥 지나간다.
그런 문제는 이 핸들러의 표준 응답으로 바뀌지 않는다.

### 8. `System.err` 와 `System.out` 의 줄 순서를 믿는다
6번 갈래에서 `[UNEXPECTED] …` 는 `System.err` 로, `응답: …` 은 `System.out` 으로 나간다.
두 흐름은 따로라서, 콘솔에서 두 줄이 어떤 순서로 섞여 보일지는 보장되지 않는다.

### 9. 서비스 안에서 예외를 잡아 삼킨다
구조의 의도는 「예외 → 응답 매핑을 한 곳에 모아 비즈니스 코드의 `try-catch` 를 없애는 것」이다.
서비스가 예외를 잡아 문자열 따위로 바꿔 버리면 글로벌 핸들러가 볼 기회가 없다.

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| `RuntimeException` 의 자손은 `throws` 선언 없이 던질 수 있다 | Java 언어 명세 |
| `Runnable.run()` 은 체크 예외를 던지도록 선언돼 있지 않다 | Java 표준 라이브러리 API |
| `catch (Exception e)` 는 `Error` 를 잡지 않는다 | Java 언어 명세(예외 타입 나무) |
| `LinkedHashMap` 은 넣은 순서대로 순회 · 출력된다 | Java 표준 라이브러리 API 문서 |
| `HashMap` 의 순회 순서는 정해져 있지 않다 | Java 표준 라이브러리 API 문서(순서를 약속하지 않음) |
| `System.out` 과 `System.err` 가 콘솔에 섞여 보이는 순서 | 보장 없음 — 콘솔 · 실행 환경에 따른다 |
| `LocalDateTime.now().toString()` 의 문자열 꼴 | Java 표준 라이브러리 API(ISO-8601 꼴, 소수 자릿수 등은 확인 필요) |
| `@ControllerAdvice` 가 모든 컨트롤러에 자동 적용된다 | Spring 프레임워크 — 언어가 아니다 |
| 401 = 인증 실패, 403 = 권한 없음 | HTTP 관례(확인 필요) — 언어와 무관 |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 여러 컨트롤러가 같은 꼴의 에러 응답을 내야 한다 | 글로벌 핸들러 + `ErrorResponse` 하나 | 컨트롤러마다 따로 만든 에러 문자열 |
| 클라이언트 요청 탓의 실패(없음 · 중복 · 검증) | `BusinessException` 하위 예외(4xx) | 500 응답 |
| 서버 내부의 예상 못한 실패 | 일반 메시지 + 500, 상세는 서버 로그 | 예외 메시지 · 스택을 응답에 싣기 |
| 입력 필드가 여럿 틀렸다 | 필드별로 모은 `details` | 첫 에러만 알리고 멈추기 |
| 서비스 로직에서 실패를 알린다 | 예외를 던지기만 | 서비스 안의 `try-catch` 로 삼키기 |
| Spring 을 쓴다 | `@ControllerAdvice` + `@ExceptionHandler` | `safeExecute` 같은 손수 만든 감싸기 |

## 핵심 문장

1. **예외 객체가 응답 정보(코드 · 상태)를 들고 다니게 하면 응답 변환을 한 곳에 모을 수 있다.**
2. **계층은 `BaseException` → `BusinessException`(4xx) / `SystemException`(5xx) 으로 가르고, 뿌리는 `RuntimeException` 이다.**
3. **핸들러는 좁은 타입부터 검사하고, 모르는 예외는 500 + 일반 메시지로 바꾼다.**
4. **500 의 내부 메시지는 서버 로그에만 두고, 검증 실패는 필드별 상세를 준다.**
5. **모든 에러는 한 가지 꼴(`ErrorResponse`)로 나가 클라이언트가 한 가지 코드로 처리한다.**

## 관련 자료

- [rest-controller-full](../02-rest-controller-full/2-summary.md)
- `logging-system` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- `auth-flow` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- 원본: study-site 항목 데이터 `data/java/project-structures.json` 의 `error-handling-global`

## 용어 풀이

- **글로벌 에러 처리** — 프로그램 전체의 예외를 한 곳에서 표준 응답으로 바꾸는 구조.
- **예외 계층** — 예외 클래스들을 상속으로 묶은 「큰 종류 → 작은 종류」 나무.
- **언체크 예외** — `RuntimeException` 과 그 자손처럼 `throws` · `catch` 가 강제되지 않는 예외.
- **체크 예외** — `RuntimeException` 이 아닌 `Exception` 의 자손으로, 선언하거나 잡아야 컴파일되는 예외.
- **`Error`** — `Throwable` 의 다른 갈래로, `catch (Exception)` 에 걸리지 않는 JVM 수준의 문제.
- **원인 예외(`cause`)** — 새 예외를 던지게 만든 원래 예외로, 생성자에 넘겨 연결해 둔다.
- **표준 에러 응답** — 모든 에러를 같은 필드 구성으로 돌려주는 응답 꼴(여기서는 `ErrorResponse`).
- **정적 팩토리 메서드** — 생성자 대신 객체를 만들어 돌려주는 `static` 메서드.
- **패턴 매칭 `instanceof`** — 타입 검사가 참이면 그 타입의 변수를 바로 만들어 주는 꼴.
- **`@ControllerAdvice` / `@ExceptionHandler`** — Spring 에서 공통 예외 처리 클래스와 그 안의 예외별 처리 메서드를 표시하는 애너테이션.
- **HTTP 상태 코드** — 응답의 결과 종류를 나타내는 세 자리 수(4xx 는 요청 쪽 문제, 5xx 는 서버 쪽 문제).
- **보일러플레이트** — 여러 곳에 되풀이되는 판에 박힌 코드(여기서는 컨트롤러마다의 `try-catch`).

## 더 들어가면

- `instanceof` 패턴 매칭은 Java 16 에서 정식 기능이 됐다고 알려져 있다(확인 필요).
- `Map.of()` 는 Java 9 에 들어온 불변 맵 팩토리이며, 돌려준 맵을 고치려 하면 `UnsupportedOperationException` 이 난다(확인 필요).
- 실무 Spring 에서는 핸들러 메서드가 `ResponseEntity<ErrorResponse>` 를 돌려줘 HTTP 상태와 본문을 함께 정하는 꼴이 흔하다(확인 필요).
- 표준 에러 응답 꼴로 RFC 7807(Problem Details)이 있고, Spring 6 에는 `ProblemDetail` 클래스가 있다고 알려져 있다(확인 필요).
- 에러 코드 · 상태 · 기본 메시지를 `enum ErrorCode` 하나에 모아 예외가 그 enum 을 들고 다니게 하는 설계도 흔하다(확인 필요).
- 500 갈래에서는 메시지만이 아니라 스택 트레이스를 로거로 남겨야 원인을 찾기 쉽다(확인 필요).
- `HashMap.containsValue` 는 모든 값을 훑으므로 회원이 많아지면 느려진다 — 실제로는 이메일을 키로 하는 색인이나 DB 유니크 제약을 쓴다(확인 필요).
