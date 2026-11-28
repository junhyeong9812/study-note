# java/java-advanced-patterns/02 — Type-Safe Step Builder (타입 안전 스텝 빌더) — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 필수 값만 정하고 `build()` 한 이메일의 문자열 (예측)

```java
// 질문용 발췌
Email email2 = Email.builder()
    .from("noreply@example.com")
    .to("user@example.com")
    .subject("알림")
    .build();
System.out.println("이메일2: " + email2);
```

- 이 줄이 찍는 문자열에서 `body` · `html` · `cc` 자리는 각각 어떤 꼴인가?

### 2. `subject()` 를 건너뛰고 `build()` 를 부르면 (예측)

```java
// 질문용 발췌
Email e = Email.builder().from("x").to("y").build();
```

- 이 줄은 언제, 어떤 이유로 어떻게 되는가?

### 3. 중간 단계를 변수에 담아 두 번 `build()` 하면 (예측)

```java
// 질문용 발췌
Email.OptionalStep base = Email.builder().from("a").to("b").subject("s");
Email e1 = base.body("first").build();
Email e2 = base.html(true).build();
System.out.println(e1);
System.out.println(e2);
```

- `e1` 과 `e2` 의 `body` · `html` 값은 각각 무엇인가?

### 4. 객체는 `Builder` 하나인데 차례가 강제되는 까닭 (왜)

- 같은 객체가 네 인터페이스를 다 구현하는데, 왜 호출자는 단계마다 한 가지 메서드만 부를 수 있는가?

### 5. `build()` 에 필수 값 검사가 없는 까닭 (왜)

- 이 설계는 왜 `build()` 안에서 `from` · `to` · `subject` 를 따로 검사하지 않아도 된다고 보는가?

### 6. `from(null)` 은 막히는가 (경계)

- 스텝 빌더가 컴파일 타임에 강제해 주는 것과 강제해 주지 못하는 것의 경계는 어디인가?

### 7. 캐스팅 앞의 타입 안전 (경계)

- `Email.builder()` 의 결과를 `SubjectStep` 으로 캐스팅하면 차례 강제는 어떻게 되는가?

### 8. 일반 빌더 · 생성자와 견주기 (연결)

- 모든 메서드가 같은 빌더를 돌려주는 일반 빌더와 비교할 때, 스텝 빌더는 무엇을 얻고 무엇을 치르며 언제 고르는가?

## 실습

### 실습 1. 이메일을 만드는 스텝 빌더 구현하기

**만들 것** — `from` → `to` → `subject` 를 반드시 이 차례로 정해야 하고, `body` · `html` · `cc` 는 선택인 불변 `Email` 객체와 그 스텝 빌더를 만든다.
데모에서 선택 값을 다 채운 이메일과 필수 값만 채운 이메일을 하나씩 만들어 찍는다.

**요구 조건**

1. 1단계 — `Email` 은 `from` · `to` · `subject` · `body` · `cc`(문자열)와 `html`(불리언) 여섯 필드를 모두 `private final` 로 가진다.
2. 1단계 — `Email` 의 생성자는 `private` 이고, `Builder` 를 받아 그 필드 값을 여섯 필드에 그대로 복사한다.
3. 2단계 — `FromStep` 의 `from(String)` 은 `ToStep` 을, `ToStep` 의 `to(String)` 은 `SubjectStep` 을, `SubjectStep` 의 `subject(String)` 은 `OptionalStep` 을 반환하도록 선언한다.
4. 2단계 — `OptionalStep` 은 `body(String)` · `html(boolean)` · `cc(String)` 를 선언하고 셋 다 `OptionalStep` 을 반환하며, `Email` 을 반환하는 `build()` 도 선언한다.
5. 3단계 — 진입점 `public static FromStep builder()` 는 새 `Builder` 를 만들어 돌려준다.
6. 4단계 — `Builder` 는 `private static class` 이고 네 단계 인터페이스를 모두 구현한다.
7. 4단계 — `Builder` 의 선택 필드 기본값은 `body` 가 빈 문자열, `html` 이 `false`, `cc` 가 `null` 이다.
8. 4단계 — 값을 받는 여섯 메서드는 각자 필드에 값을 적고 `this` 를 반환하며, `build()` 는 검사 없이 `new Email(this)` 를 반환한다.
9. 5단계 — `main` 에서 필수 세 값과 선택 세 값(`html` 은 `true`)을 모두 정한 `email1` 과, 필수 세 값만 정한 `email2` 를 만들어 `"이메일1: "` · `"이메일2: "` 를 앞에 붙여 찍는다.
10. 5단계 — 차례를 어긴 세 호출(`from` 없이 `to` · `to` 없이 `subject` · `subject` 없이 `build`)을 주석으로 남기고, 마지막에 줄바꿈 문자로 시작하는 `타입 안전: 잘못된 순서는 컴파일 타임에 차단됨` 을 찍는다.

**시작 코드**

```java
class Email {
    private final String from;
    private final String to;
    private final String subject;
    private final String body;
    private final boolean html;
    private final String cc;

    // TODO: private 생성자 — Builder 를 받아 여섯 필드를 복사한다

    @Override
    public String toString() {
        return String.format("Email{from='%s', to='%s', subject='%s', body='%s', html=%s, cc='%s'}",
            from, to, subject, body, html, cc);
    }

    // TODO: 단계 인터페이스 FromStep / ToStep / SubjectStep / OptionalStep
    //       (각 메서드의 반환 타입이 다음 단계를 정한다)

    // TODO: 진입점 builder() — 반환 타입을 첫 단계 인터페이스로

    private static class Builder /* TODO: 네 단계 인터페이스를 구현 */ {
        private String from;
        private String to;
        private String subject;
        // TODO: 선택 필드 body / html / cc 와 기본값

        // TODO: from / to / subject / body / html / cc — 값을 적고 this 반환

        // TODO: build()
    }
}

public class TypeSafeBuilderDemo {
    public static void main(String[] args) {
        Email email1 = null; // TODO: 필수 세 값 + body("<h1>반갑습니다</h1>"), html(true), cc("manager@example.com")
        System.out.println("이메일1: " + email1);

        Email email2 = null; // TODO: 필수 세 값만
        System.out.println("이메일2: " + email2);

        // TODO: 차례를 어긴 세 호출을 주석으로 남긴다

        System.out.println("\n타입 안전: 잘못된 순서는 컴파일 타임에 차단됨");
    }
}
```

**확인 방법** — `TypeSafeBuilderDemo.java` 로 저장한 뒤 `javac TypeSafeBuilderDemo.java && java TypeSafeBuilderDemo` 로 돌려 두 이메일의 필드 값을 본다.
주석으로 남긴 잘못된 호출 하나를 풀어 `javac` 가 컴파일 에러를 내는지도 확인한다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
