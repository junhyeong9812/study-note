# java/java-project-structures/12 — 글로벌 에러 처리 — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 검증 실패 한 줄에 `details` 두 개가 `name` → `email` 순서로 붙는다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
  응답: ErrorResponse{code='VALIDATION_ERROR', status=400, message='입력값 검증 실패', details={name=이름은 필수입니다, email=올바른 이메일 형식이 아닙니다}}
```

**왜 그런가**
- 이름 `""` 은 `isBlank()` 가 참이라 `name` 에러가 먼저 들어간다.
- 이메일 `"invalid-email"` 에는 `@` 가 없어 `email` 에러가 그다음에 들어간다.
- 에러 맵이 `LinkedHashMap` 이라 넣은 차례 그대로 찍힌다.
- 핸들러의 첫 갈래가 `ValidationException` 이므로 `withDetails` 로 맵이 `details` 에 실리고, `toString()` 이 `, details=…` 를 붙인다.
- `timestamp` 는 `toString()` 에 없으니 줄에 나타나지 않는다.
- 근거: 2-summary 「동작 방식 (2)」 · 「(3)」 · 「(5)」, 「어디서 틀리나 4」.

### 2. 내부 메시지가 그대로 나간다 — 원칙에 어긋난다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
ErrorResponse{code='INTERNAL_ERROR', status=500, message='DB 연결 풀 고갈: pool=main'}
```

**왜 그런가**
- `SystemException` 은 `ValidationException` 이 아니므로 첫 갈래는 지나친다.
- 그러나 `BaseException` 의 자손이라 둘째 갈래에 걸리고, `be.getMessage()` 가 그대로 `message` 에 들어간다.
- 「500 에서는 내부 메시지를 노출하지 않는다」는 팁 · 주석의 의도와 어긋난다 — 셋째 갈래의 일반 메시지는 계층 **밖** 예외에만 쓰인다.
- 근거: 2-summary 「동작 방식 (3)」 끝 문단, 「어디서 틀리나 2」.

### 3. 상세는 오류 스트림에, 일반 메시지는 응답에 — 람다는 아무것도 찍지 않는다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
[System.err 쪽]
[UNEXPECTED] RuntimeException: NullPointerException at line 42
[System.out 쪽]
  응답: ErrorResponse{code='INTERNAL_ERROR', status=500, message='서버 내부 오류가 발생했습니다'}
```

**왜 그런가**
- 람다는 `"  응답: " + service.riskyOperation()` 을 먼저 계산하려다 예외를 만나므로 `println` 까지 가지 못한다.
- 던져진 것은 계층 밖의 평범한 `RuntimeException` 이라 핸들러의 셋째 갈래로 간다.
- 셋째 갈래는 `getSimpleName()` 과 원래 메시지를 `System.err` 에 남기고, 응답에는 일반 메시지와 500 만 넣는다.
- 두 줄은 서로 다른 스트림이라, 콘솔에 섞여 보이는 순서는 보장되지 않는다.
- 근거: 2-summary 「동작 방식 (3)」 · 「(4)」, 「어디서 틀리나 8」.

### 4. `DUPLICATE` · 409 · `email 중복: kim@test.com`

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
  응답: ErrorResponse{code='DUPLICATE', status=409, message='email 중복: kim@test.com'}
```

**왜 그런가**
- 이름 `"이영희"` 와 이메일 `"kim@test.com"` 은 검증을 모두 통과한다.
- 첫 등록이 `kim@test.com` 을 저장해 두었으므로 `containsValue` 가 참이 되어 `DuplicateResourceException("email", email)` 이 던져진다.
- 이 예외는 `BaseException` 갈래에서 `of` 로 바뀌고, `details` 가 비어 있어 `, details=…` 부분이 없다.
- 근거: 2-summary 「동작 방식 (1)」 · 「(5)」.

### 5. 순서를 바꾸면 필드별 `details` 를 잃는다

`ValidationException` 도 `BaseException` 의 자손이다.
넓은 `BaseException` 검사를 먼저 두면 검증 예외가 그 갈래에 먼저 걸려 `of(...)` 로 응답이 만들어진다.
그러면 `getFieldErrors()` 가 쓰이지 않아 응답에 필드별 상세가 빠진다.
그래서 좁은 타입을 위에, 넓은 타입을 아래에 둔다.
근거: 2-summary 「동작 방식 (3)」, 「어디서 틀리나 1」.

### 6. 언체크 예외라야 `throws` 없이 던지고 람다 안에서 부를 수 있다

`RuntimeException` 의 자손은 언체크 예외라서 서비스 메서드가 `throws` 를 선언하지 않아도 된다.
체크 예외였다면 `register` · `findById` 등 모든 서비스 메서드에 `throws` 가 붙고, 부르는 쪽마다 처리를 강제당한다.
또 컨트롤러는 서비스 호출을 `Runnable` 람다에 넣는데, `Runnable.run()` 은 체크 예외를 던지도록 선언돼 있지 않아 그 람다는 컴파일되지 않는다.
근거: 2-summary 「동작 방식 (1)」, 「문법 — 형태와 규칙」.

### 7. `Error` 갈래 — `Exception` 이 아니라서 그냥 지나간다

던질 수 있는 것의 뿌리 `Throwable` 은 `Exception` 과 `Error` 로 갈린다.
`catch (Exception e)` 는 `Exception` 쪽만 잡으므로, `Error`(JVM 수준의 문제 등)는 `safeExecute` 를 지나쳐 표준 응답으로 바뀌지 않는다.
근거: 2-summary 「동작 방식 (1)」 의 `Throwable` 그림 · 「(4)」, 「어디서 틀리나 7」.

### 8. 흔한 관례로는 403 이 더 맞다

HTTP 의 흔한 관례로 401 은 「누구인지 확인되지 않음(인증 실패)」, 403 은 「누구인지는 알지만 권한이 없음(인가 실패)」이다(확인 필요).
`adminOnly("USER")` 는 역할(`USER`)이 이미 알려진 상태에서 권한이 모자란 경우라 관례로는 403 쪽이다.
원본 주석은 「인증/인가 실패 → 401」로 둘을 하나로 묶었다.
근거: 2-summary 「어디서 틀리나 5」.

### 9. `@ControllerAdvice` 클래스 · `@ExceptionHandler` 메서드 · 프레임워크의 자동 적용

- `GlobalExceptionHandler` → `@ControllerAdvice` 를 붙인 클래스.
- `handle` 안의 `instanceof` 분기 하나하나 → 그 클래스의 `@ExceptionHandler` 메서드들.
- `safeExecute` → 필요 없다; Spring 이 모든 컨트롤러에 자동으로 적용해 예외를 핸들러로 보낸다.

이 예제는 Spring 없이 그 구조를 `safeExecute` 로 흉내 낸 것이다.
근거: 2-summary 「동작 방식 (6)」.

## 실습 정답

### 실습 1. 회원 서비스에 글로벌 에러 처리 붙이기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. 다섯 `final` 필드 | `ErrorResponse` 의 `code` · `message` · `status` · `timestamp` · `details` |
| 2. `private` 생성자, 시각 · 빈 맵 정규화 | `private ErrorResponse(...)` — `LocalDateTime.now().toString()`, `details != null ? details : Map.of()` |
| 3. 두 정적 팩토리 | `ErrorResponse.of` · `ErrorResponse.withDetails` |
| 4. `toString()` 꼴과 `details` 생략 | `toString()` 의 `det` 과 `String.format(...)` |
| 5. 계층의 뿌리 | `abstract class BaseException extends RuntimeException` — 생성자 둘, `getErrorCode` · `getHttpStatus` |
| 6. 4xx 부모 | `class BusinessException extends BaseException` |
| 7. 없음 404 | `EntityNotFoundException` — `"NOT_FOUND"`, `entity + " 없음: id=" + id`, `404` |
| 8. 중복 409 | `DuplicateResourceException` — `"DUPLICATE"`, `field + " 중복: " + value`, `409` |
| 9. 검증 400 + 필드 맵 | `ValidationException` — `fieldErrors`, `getFieldErrors()` |
| 10. 권한 401 | `UnauthorizedException` — `"UNAUTHORIZED"`, `401` |
| 11. 시스템 500 + 원인 | `SystemException` — `super("INTERNAL_ERROR", message, 500, cause)` |
| 12. 검증 예외 갈래 | `handle` 의 `if (e instanceof ValidationException ve)` |
| 13. 그 밖의 계층 예외 갈래 | `handle` 의 `if (e instanceof BaseException be)` |
| 14. 모르는 예외 갈래 | `System.err.println("[UNEXPECTED] " + ...)` 와 `ErrorResponse.of("INTERNAL_ERROR", ..., 500)` |
| 15. 저장소와 id | `MemberService` 의 `members`(`HashMap`) · `seq` |
| 16. 필드 에러 모아 던지기 | `register` 의 `LinkedHashMap` `errors` 와 `throw new ValidationException(errors)` |
| 17. 중복 검사와 저장 | `members.containsValue(email)` · `members.put(++seq, email)` |
| 18. 조회 | `findById` — `throw new EntityNotFoundException("회원", id)` |
| 19. 권한 확인 | `adminOnly` — `"ADMIN".equals(role)` |
| 20. 계층 밖 예외 | `riskyOperation` — `throw new RuntimeException("NullPointerException at line 42")` |
| 21. 의존성 받기 | `MemberController(MemberService, GlobalExceptionHandler)` |
| 22. 한 곳에서 잡기 | `safeExecute(Runnable printer)` 의 `try` / `catch (Exception e)` |
| 23. 네 공개 메서드 | `register` · `findById` · `adminOnly` · `riskyOperation` 의 람다 |
| 24. 여섯 장면 | `ErrorHandlingDemo.main` 의 제목 줄과 여섯 호출 |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`java/java-project-structures/reference/error-handling-global.java`

```java
// [실무 프로젝트 구조] 글로벌 에러 처리
// 설명: 예외 계층 설계, ControllerAdvice 패턴, 에러 응답 표준화를 구현
// 팁: 예외 계층은 BaseException → BusinessException(4xx) / SystemException(5xx)으로 분리하는 것이 일반적이다. 500 에러에서는 내부 메시지를 클라이언트에 노출하지 않는다. Spring에서는 @ControllerAdvice + @ExceptionHandler로 같은 패턴을 구현한다. 유효성 에러는 필드별 상세 메시지를 제공한다.

// === 글로벌 에러 처리 시스템 ===
// 예외 계층 + @ControllerAdvice 패턴 + 에러 응답 표준화
// 구조 의도: 예외 → 응답 매핑을 한 곳에 집중 → 비즈니스 코드의 try-catch 제거.
// 트레이드오프: 예외 계층 설계가 한 번 정해지면 광범위한 영향을 미치므로 초기 설계 비용이 크다.

import java.util.*;
// 응답 timestamp
import java.time.LocalDateTime;

// === 표준 에러 응답 ===
// 모든 에러를 동일 구조로 응답 → 클라이언트 일관 처리 가능
class ErrorResponse {
    // 비즈니스 식별 코드 (NOT_FOUND, DUPLICATE 등)
    private final String code;
    // 사람이 읽을 메시지
    private final String message;
    // HTTP 상태 코드
    private final int status;
    // 발생 시각
    private final String timestamp;
    // 필드별 상세 (유효성 검증용)
    private final Map<String, String> details;

    private ErrorResponse(String code, String message, int status, Map<String, String> details) {
        this.code = code;
        this.message = message;
        this.status = status;
        this.timestamp = LocalDateTime.now().toString();
        // null 안전 처리: 빈 맵으로 정규화
        this.details = details != null ? details : Map.of();
    }

    // 단순 에러용 팩토리
    public static ErrorResponse of(String code, String message, int status) {
        return new ErrorResponse(code, message, status, null);
    }

    // 필드 에러 포함 팩토리 (검증 실패용)
    public static ErrorResponse withDetails(String code, String message, int status,
                                             Map<String, String> details) {
        return new ErrorResponse(code, message, status, details);
    }

    @Override
    public String toString() {
        String det = details.isEmpty() ? "" : ", details=" + details;
        return String.format("ErrorResponse{code='%s', status=%d, message='%s'%s}",
            code, status, message, det);
    }
}

// === 예외 계층 구조 ===
// 모든 비즈니스/시스템 예외의 공통 부모. 응답 매핑에 필요한 정보(코드, HTTP 상태) 포함
abstract class BaseException extends RuntimeException {
    private final String errorCode;
    private final int httpStatus;

    protected BaseException(String errorCode, String message, int httpStatus) {
        super(message);
        this.errorCode = errorCode;
        this.httpStatus = httpStatus;
    }

    // 원인 예외와 함께 던질 수 있는 생성자
    protected BaseException(String errorCode, String message, int httpStatus, Throwable cause) {
        super(message, cause);
        this.errorCode = errorCode;
        this.httpStatus = httpStatus;
    }

    public String getErrorCode() { return errorCode; }
    public int getHttpStatus() { return httpStatus; }
}

// 비즈니스 예외 (4xx): 클라이언트 입력/요청에 의해 발생
class BusinessException extends BaseException {
    protected BusinessException(String errorCode, String message, int httpStatus) {
        super(errorCode, message, httpStatus);
    }
}

// 자원 없음 → 404
class EntityNotFoundException extends BusinessException {
    public EntityNotFoundException(String entity, Long id) {
        super("NOT_FOUND", entity + " 없음: id=" + id, 404);
    }
}

// 중복 → 409 Conflict
class DuplicateResourceException extends BusinessException {
    public DuplicateResourceException(String field, String value) {
        super("DUPLICATE", field + " 중복: " + value, 409);
    }
}

// 입력 검증 실패 → 400. 필드별 상세 에러를 함께 전달
class ValidationException extends BusinessException {
    private final Map<String, String> fieldErrors;

    public ValidationException(Map<String, String> fieldErrors) {
        super("VALIDATION_ERROR", "입력값 검증 실패", 400);
        this.fieldErrors = fieldErrors;
    }

    public Map<String, String> getFieldErrors() { return fieldErrors; }
}

// 인증/인가 실패 → 401
class UnauthorizedException extends BusinessException {
    public UnauthorizedException(String message) {
        super("UNAUTHORIZED", message, 401);
    }
}

// 시스템 예외 (5xx): 서버 내부 문제. 메시지 노출 금지
class SystemException extends BaseException {
    public SystemException(String message, Throwable cause) {
        super("INTERNAL_ERROR", message, 500, cause);
    }
}

// === GlobalExceptionHandler (@ControllerAdvice 패턴) ===
// 모든 Controller에서 발생한 예외를 한 곳에서 표준 응답으로 변환
class GlobalExceptionHandler {

    public ErrorResponse handle(Exception e) {
        // 검증 예외는 필드별 상세 에러를 함께 응답 (패턴 매칭)
        if (e instanceof ValidationException ve) {
            return ErrorResponse.withDetails(
                ve.getErrorCode(), ve.getMessage(), ve.getHttpStatus(), ve.getFieldErrors());
        }

        // 그 외 비즈니스 예외 → 코드/상태/메시지 그대로 노출
        if (e instanceof BaseException be) {
            return ErrorResponse.of(be.getErrorCode(), be.getMessage(), be.getHttpStatus());
        }

        // 알 수 없는 예외 → 500. 내부 메시지는 서버 로그에만 남기고 클라이언트엔 일반 메시지만
        System.err.println("[UNEXPECTED] " + e.getClass().getSimpleName() + ": " + e.getMessage());
        return ErrorResponse.of("INTERNAL_ERROR", "서버 내부 오류가 발생했습니다", 500);
    }
}

// === 서비스 (예외를 발생시키는 비즈니스 로직) ===
// Service는 try-catch 없이 예외를 그냥 던진다 (예외 처리는 글로벌 핸들러 책임)
class MemberService {
    private final Map<Long, String> members = new HashMap<>();
    private long seq = 0;

    // 가입: 검증 → 중복 검사 → 저장
    public String register(String name, String email) {
        // 필드별 에러 누적
        Map<String, String> errors = new LinkedHashMap<>();
        if (name == null || name.isBlank()) errors.put("name", "이름은 필수입니다");
        if (email == null || !email.contains("@")) errors.put("email", "올바른 이메일 형식이 아닙니다");
        if (!errors.isEmpty()) throw new ValidationException(errors);

        // 중복 검사
        if (members.containsValue(email)) throw new DuplicateResourceException("email", email);

        members.put(++seq, email);
        return "회원 가입 완료: " + name;
    }

    public String findById(Long id) {
        String email = members.get(id);
        if (email == null) throw new EntityNotFoundException("회원", id);
        return "회원: " + email;
    }

    // 권한 체크 데모
    public String adminOnly(String role) {
        if (!"ADMIN".equals(role)) throw new UnauthorizedException("관리자 권한이 필요합니다");
        return "관리자 페이지";
    }

    // 예상 못한 시스템 예외 시뮬레이션
    public String riskyOperation() {
        throw new RuntimeException("NullPointerException at line 42");
    }
}

// === Controller (글로벌 핸들러 통합) ===
// Spring에서는 @ControllerAdvice가 자동 적용 → 여기선 safeExecute 헬퍼로 모방
class MemberController {
    private final MemberService service;
    private final GlobalExceptionHandler exHandler;

    public MemberController(MemberService service, GlobalExceptionHandler exHandler) {
        this.service = service;
        this.exHandler = exHandler;
    }

    // 모든 핸들러를 감싸는 try-catch 래퍼 (보일러플레이트 제거)
    private Object safeExecute(Runnable printer) {
        try {
            printer.run();
            return null;
        } catch (Exception e) {
            ErrorResponse error = exHandler.handle(e);
            System.out.println("  응답: " + error);
            return error;
        }
    }

    public void register(String name, String email) {
        safeExecute(() -> System.out.println("  응답: " + service.register(name, email)));
    }

    public void findById(Long id) {
        safeExecute(() -> System.out.println("  응답: " + service.findById(id)));
    }

    public void adminOnly(String role) {
        safeExecute(() -> System.out.println("  응답: " + service.adminOnly(role)));
    }

    public void riskyOperation() {
        safeExecute(() -> System.out.println("  응답: " + service.riskyOperation()));
    }
}

public class ErrorHandlingDemo {
    public static void main(String[] args) {
        MemberController controller = new MemberController(
            new MemberService(), new GlobalExceptionHandler());

        // 1. 정상 등록
        System.out.println("=== 정상 등록 ===");
        controller.register("김철수", "kim@test.com");

        // 2. 유효성 검증 실패 (400) - details에 필드별 에러
        System.out.println("\n=== 유효성 검증 실패 ===");
        controller.register("", "invalid-email");

        // 3. 중복 (409)
        System.out.println("\n=== 중복 등록 ===");
        controller.register("이영희", "kim@test.com");

        // 4. 리소스 없음 (404)
        System.out.println("\n=== 존재하지 않는 회원 ===");
        controller.findById(99L);

        // 5. 권한 없음 (401)
        System.out.println("\n=== 권한 없음 ===");
        controller.adminOnly("USER");

        // 6. 예상치 못한 에러 (500) - 내부 메시지는 클라이언트에 노출하지 않음
        System.out.println("\n=== 시스템 에러 ===");
        controller.riskyOperation();
    }
}
```

**실행 결과** — 실행하지 않음 — Java 예제는 이 문서를 만들 때 컴파일 · 실행하지 않았다(JDK 로 돌려 확인한다).

**풀이 요점**
- 예외가 코드와 HTTP 상태를 들고 다니므로, 핸들러는 예외를 읽기만 하면 응답을 만들 수 있다.
- 핸들러 분기는 `ValidationException` → `BaseException` → 그 밖 순서다; 순서를 바꾸면 `details` 가 사라진다.
- 서비스에는 `try-catch` 가 없고, 잡는 곳은 `safeExecute` 한 곳뿐이다.
- 계층 밖 예외의 상세는 `System.err` 에만 남고, 응답에는 일반 메시지와 500 만 나간다.
- `SystemException` 은 둘째 갈래에 걸려 메시지가 응답에 실리므로, 원칙을 지키려면 따로 먼저 검사해야 한다(원본에 근거 없음 — 추론).
- 검증 에러를 `LinkedHashMap` 에 모았다 한 번에 던지므로 모든 필드 문제가 넣은 차례대로 한 응답에 담긴다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — Java 예제는 이 문서를 만들 때 컴파일 · 실행하지 않았다(JDK 로 돌려 확인한다) |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
