# java/java-project-structures/12 — 글로벌 에러 처리 — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 이름과 이메일이 둘 다 잘못된 가입 (예측)

```java
// 질문용 발췌
controller.register("", "invalid-email");
```

- 이 호출 뒤 `"  응답: "` 으로 시작하는 줄은 어떤 꼴인가?
- `details` 안에서 `name` 과 `email` 은 어느 차례로 나오나?

### 2. 핸들러에 `SystemException` 을 직접 넘기면 (예측)

```java
// 질문용 발췌
ErrorResponse r = new GlobalExceptionHandler().handle(
    new SystemException("DB 연결 풀 고갈: pool=main", new IllegalStateException()));
System.out.println(r);
```

- 찍히는 문자열의 `message` 자리에는 무엇이 들어가나?
- 그 결과는 「500 에서는 내부 메시지를 노출하지 않는다」는 원칙에 맞나?

### 3. `riskyOperation` 을 부르면 (예측)

```java
// 질문용 발췌
controller.riskyOperation();
```

- `System.err` 쪽과 `System.out` 쪽에는 각각 무엇이 찍히나?
- 람다 안의 `System.out.println` 은 무언가를 찍나?

### 4. `kim@test.com` 으로 두 번째 가입 (예측)

- 정상 등록 뒤 `register("이영희", "kim@test.com")` 을 부르면 응답의 `code` · `status` · `message` 는 무엇인가?

### 5. `handle` 이 `ValidationException` 을 `BaseException` 보다 먼저 검사하는 까닭 (왜)

- 두 `instanceof` 검사의 순서를 바꾸면 무엇을 잃나?

### 6. `BaseException` 이 `RuntimeException` 을 잇는 까닭 (왜)

- 이 계층이 체크 예외였다면 서비스 메서드와 컨트롤러의 람다에서 무엇이 걸리나?

### 7. `safeExecute` 의 그물이 닿지 않는 곳 (경계)

- `catch (Exception e)` 로 잡히지 않아 표준 응답으로 바뀌지 않는 던짐은 어떤 갈래인가?

### 8. 역할이 `USER` 인 요청에 401 (경계)

- 권한이 모자란 요청에 401 을 주는 것은 HTTP 의 흔한 관례와 맞나?

### 9. Spring 으로 옮기면 (연결)

- 이 예제의 `GlobalExceptionHandler` · `handle` 안의 분기 · `safeExecute` 는 Spring 에서 각각 무엇이 맡나?

## 실습

### 실습 1. 회원 서비스에 글로벌 에러 처리 붙이기

**만들 것** — 예외 계층 · 표준 에러 응답 · 글로벌 핸들러 · 회원 서비스 · 컨트롤러를 만들고, `main` 에서 정상 1건과 에러 5종(400 · 409 · 404 · 401 · 500)을 차례로 일으켜 응답을 찍는다.

**준비물** — JDK 하나면 된다(`instanceof` 패턴 매칭을 쓰므로 그 문법을 받는 버전, 버전은 확인 필요). Spring 은 쓰지 않고 `@ControllerAdvice` 의 구조를 손으로 흉내 낸다.

**요구 조건**

1단계 — 표준 에러 응답 `ErrorResponse`
1. 필드는 `code` · `message` · `status` · `timestamp` · `details` 다섯 개이고 모두 `final` 이다.
2. 생성자는 `private` 이다; `timestamp` 는 만들 때의 `LocalDateTime.now().toString()` 이고, `details` 가 `null` 이면 빈 맵(`Map.of()`)으로 바꿔 넣는다.
3. 정적 팩토리 `of(code, message, status)` 는 `details` 없이, `withDetails(code, message, status, details)` 는 `details` 를 담아 만든다.
4. `toString()` 은 `ErrorResponse{code='…', status=…, message='…'}` 꼴이며, `details` 가 비어 있지 않을 때만 끝에 `, details=…` 를 붙인다(`timestamp` 는 찍지 않는다).

2단계 — 예외 계층
5. `abstract class BaseException` 은 `RuntimeException` 을 잇고 `errorCode` · `httpStatus` 와 그 getter 를 갖는다; 생성자는 (코드, 메시지, 상태) 와 (코드, 메시지, 상태, 원인) 둘이다.
6. `BusinessException` 은 `BaseException` 을 잇는 4xx 갈래의 부모다.
7. `EntityNotFoundException(entity, id)` 는 `NOT_FOUND` · `"<entity> 없음: id=<id>"` · 404 다.
8. `DuplicateResourceException(field, value)` 는 `DUPLICATE` · `"<field> 중복: <value>"` · 409 다.
9. `ValidationException(fieldErrors)` 는 `VALIDATION_ERROR` · `"입력값 검증 실패"` · 400 이고, 필드 에러 맵을 `getFieldErrors()` 로 내준다.
10. `UnauthorizedException(message)` 는 `UNAUTHORIZED` · 받은 메시지 · 401 이다.
11. `SystemException(message, cause)` 는 `BaseException` 을 바로 잇고 `INTERNAL_ERROR` · 500 · 원인 예외를 넘긴다.

3단계 — `GlobalExceptionHandler.handle(Exception e)`
12. `ValidationException` 이면 `withDetails` 로 필드 에러를 담아 돌려준다.
13. 그 밖의 `BaseException` 이면 `of` 로 예외의 코드 · 메시지 · 상태를 돌려준다.
14. 둘 다 아니면 `System.err` 에 `"[UNEXPECTED] " + 클래스 단순 이름 + ": " + 메시지` 를 남기고, `INTERNAL_ERROR` · `"서버 내부 오류가 발생했습니다"` · 500 을 돌려준다.

4단계 — `MemberService` (`try-catch` 없이 던지기만 한다)
15. 회원은 `HashMap<Long, String>`(id → 이메일)에 담고, `seq` 를 하나씩 늘려 id 로 쓴다.
16. `register(name, email)` 은 이름이 `null` 이거나 비었으면 `name` → `"이름은 필수입니다"`, 이메일이 `null` 이거나 `@` 가 없으면 `email` → `"올바른 이메일 형식이 아닙니다"` 를 `LinkedHashMap` 에 모으고, 하나라도 있으면 `ValidationException` 을 던진다.
17. 검증을 통과해도 같은 이메일이 이미 있으면 `DuplicateResourceException("email", email)` 을 던지고, 아니면 저장한 뒤 `"회원 가입 완료: " + name` 을 돌려준다.
18. `findById(id)` 는 없으면 `EntityNotFoundException("회원", id)`, 있으면 `"회원: " + 이메일` 을 돌려준다.
19. `adminOnly(role)` 은 역할이 `"ADMIN"` 이 아니면 `UnauthorizedException("관리자 권한이 필요합니다")`, 맞으면 `"관리자 페이지"` 를 돌려준다.
20. `riskyOperation()` 은 계층 밖의 `RuntimeException("NullPointerException at line 42")` 을 던진다.

5단계 — `MemberController`
21. 생성자로 서비스와 핸들러를 받는다.
22. `private Object safeExecute(Runnable printer)` 는 `printer` 를 돌려 성공이면 `null` 을, 예외면 핸들러로 바꾼 `ErrorResponse` 를 `"  응답: " + error` 로 찍고 돌려준다.
23. 공개 메서드 `register` · `findById` · `adminOnly` · `riskyOperation` 은 각각 「`"  응답: " + 서비스 결과` 를 찍는 람다」를 `safeExecute` 에 넘긴다.

6단계 — `ErrorHandlingDemo.main`
24. 제목 줄을 찍고 차례로 부른다: 정상 등록(`"김철수"`, `"kim@test.com"`) → 유효성 실패(`""`, `"invalid-email"`) → 중복(`"이영희"`, `"kim@test.com"`) → 없는 회원(`99L`) → 권한 없음(`"USER"`) → 시스템 에러.

**시작 코드**

```java
import java.util.*;
import java.time.LocalDateTime;

// === 표준 에러 응답 ===
class ErrorResponse {
    private final String code;
    private final String message;
    private final int status;
    private final String timestamp;
    private final Map<String, String> details;

    private ErrorResponse(String code, String message, int status, Map<String, String> details) {
        this.code = code;
        this.message = message;
        this.status = status;
        // TODO: timestamp 는 지금 시각 문자열
        // TODO: details 가 null 이면 빈 맵으로 바꿔 넣기
        this.timestamp = null;
        this.details = null;
    }

    // TODO: public static ErrorResponse of(String code, String message, int status)
    // TODO: public static ErrorResponse withDetails(String code, String message, int status, Map<String, String> details)

    @Override
    public String toString() {
        String det = ""; // TODO: details 가 비어 있지 않으면 ", details=" + details
        return String.format("ErrorResponse{code='%s', status=%d, message='%s'%s}",
            code, status, message, det);
    }
}

// === 예외 계층 ===
// TODO: abstract class BaseException extends RuntimeException (errorCode, httpStatus, 생성자 둘, getter)
// TODO: class BusinessException extends BaseException
// TODO: EntityNotFoundException / DuplicateResourceException / ValidationException / UnauthorizedException
// TODO: class SystemException extends BaseException (원인 예외 포함)

// === 글로벌 핸들러 ===
class GlobalExceptionHandler {
    public ErrorResponse handle(Exception e) {
        // TODO: 1) ValidationException → withDetails
        // TODO: 2) BaseException → of
        // TODO: 3) 그 밖 → System.err 에 남기고 일반 메시지 500
        return null;
    }
}

// === 서비스 ===
class MemberService {
    private final Map<Long, String> members = new HashMap<>();
    private long seq = 0;

    public String register(String name, String email) {
        // TODO: 필드 에러를 LinkedHashMap 에 모아 한꺼번에 ValidationException
        // TODO: 같은 이메일이면 DuplicateResourceException
        members.put(++seq, email);
        return "회원 가입 완료: " + name;
    }

    public String findById(Long id) {
        // TODO: 없으면 EntityNotFoundException("회원", id)
        return "회원: " + members.get(id);
    }

    public String adminOnly(String role) {
        // TODO: ADMIN 이 아니면 UnauthorizedException
        return "관리자 페이지";
    }

    public String riskyOperation() {
        // TODO: 계층 밖의 RuntimeException 던지기
        return "";
    }
}

// === 컨트롤러 ===
class MemberController {
    private final MemberService service;
    private final GlobalExceptionHandler exHandler;

    public MemberController(MemberService service, GlobalExceptionHandler exHandler) {
        this.service = service;
        this.exHandler = exHandler;
    }

    private Object safeExecute(Runnable printer) {
        // TODO: printer 실행, 예외면 handle 로 바꿔 "  응답: " + error 를 찍고 돌려준다
        return null;
    }

    public void register(String name, String email) {
        safeExecute(() -> System.out.println("  응답: " + service.register(name, email)));
    }

    // TODO: findById / adminOnly / riskyOperation — register 와 같은 꼴
}

public class ErrorHandlingDemo {
    public static void main(String[] args) {
        MemberController controller = new MemberController(
            new MemberService(), new GlobalExceptionHandler());

        System.out.println("=== 정상 등록 ===");
        // TODO
        System.out.println("\n=== 유효성 검증 실패 ===");
        // TODO
        System.out.println("\n=== 중복 등록 ===");
        // TODO
        System.out.println("\n=== 존재하지 않는 회원 ===");
        // TODO
        System.out.println("\n=== 권한 없음 ===");
        // TODO
        System.out.println("\n=== 시스템 에러 ===");
        // TODO
    }
}
```

**확인 방법** — `javac ErrorHandlingDemo.java && java ErrorHandlingDemo` 로 돌려, 여섯 제목 아래에 성공 응답 하나와 `VALIDATION_ERROR`(400, details 두 개) · `DUPLICATE`(409) · `NOT_FOUND`(404) · `UNAUTHORIZED`(401) · `INTERNAL_ERROR`(500, 일반 메시지) 응답이 차례로 찍히는지, 그리고 `[UNEXPECTED] …` 줄이 오류 스트림 쪽에 따로 남는지 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
