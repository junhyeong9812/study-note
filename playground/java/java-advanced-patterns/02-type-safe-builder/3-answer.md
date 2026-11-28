# java/java-advanced-patterns/02 — Type-Safe Step Builder (타입 안전 스텝 빌더) — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. `body=''`, `html=false`, `cc='null'` — 선택 필드의 기본값이 그대로 들어간다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
이메일2: Email{from='noreply@example.com', to='user@example.com', subject='알림', body='', html=false, cc='null'}
```

**왜 그런가**
`subject()` 가 `OptionalStep` 을 돌려주고, `OptionalStep` 에 `build()` 가 있으므로 선택 메서드를 하나도 안 불러도 끝낼 수 있다.
`Builder` 의 선택 필드 초기값이 `body = ""`, `html = false`, `cc = null` 이고, 생성자가 이 값을 그대로 복사한다.
`toString()` 의 `%s` 에 `null` 을 넣으면 글자 `null` 이 들어가므로 `cc='null'` 꼴이 된다.
근거: 2-summary 「동작 방식 (3)」 · 「동작 방식 (4)」.

### 2. 컴파일 에러 — `SubjectStep` 에는 `build()` 가 없다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
이 줄은 실행에 이르지 못하고 컴파일 단계에서 실패한다.

**왜 그런가**
`.to("y")` 의 반환 타입은 `SubjectStep` 이다.
`SubjectStep` 에 선언된 메서드는 `subject()` 하나뿐이라, 그 정적 타입으로는 `build()` 를 부를 수 없다.
`build()` 는 `OptionalStep` 에만 있으므로 `subject()` 를 거쳐야 닿는다.
근거: 2-summary 「동작 방식 (1)」 · 「동작 방식 (5)」.

### 3. 두 `Email` 이 같은 `Builder` 를 공유한다 — `e2` 에도 `body` 가 남는다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
Email{from='a', to='b', subject='s', body='first', html=false, cc='null'}
Email{from='a', to='b', subject='s', body='first', html=true, cc='null'}
```

**왜 그런가**
모든 메서드가 `return this` 로 같은 객체를 돌려주므로 `base` 는 처음 만든 `Builder` 그 자체다.
`e1` 을 만들 때 `body` 가 `"first"` 로 적혔고, `e2` 를 만들 때는 그 위에 `html` 만 `true` 로 바뀌었다.
`e1` 은 `build()` 때 값을 `final` 필드로 복사해 갔으므로, 뒤에서 빌더가 바뀌어도 `html=false` 로 남는다.
근거: 2-summary 「어디서 틀리나 5」 · 「동작 방식 (2)」 · 「동작 방식 (4)」. (원본에 근거 없음 — 추론)

### 4. 호출 가능한 메서드는 실제 객체가 아니라 정적 타입이 정하기 때문이다

컴파일러는 식의 정적 타입을 보고 부를 수 있는 메서드를 정한다.
`builder()` 는 `FromStep` 으로, `from()` 은 `ToStep` 으로 선언되어 있으니, 같은 객체가 돌아와도 호출자 쪽에서는 단계마다 다른 인터페이스로 보인다.
`Builder` 는 `private` 이라 바깥에서 그 클래스 타입으로 다룰 길도 없다.
근거: 2-summary 「동작 방식 (1)」 · 「동작 방식 (2)」.

### 5. `build()` 에 닿았다는 것 자체가 필수 세 단계를 다 지났다는 뜻이기 때문이다

`build()` 는 `OptionalStep` 에만 있고, `OptionalStep` 은 `subject()` 만 돌려준다.
`subject()` 는 `SubjectStep` 에만, `SubjectStep` 은 `to()` 만, `ToStep` 은 `from()` 만 돌려준다.
그래서 인터페이스 체인이 「세 메서드를 차례로 불렀다」를 이미 보장한다고 본다 — 원본 주석의 「추가 검증 불필요」가 이 뜻이다.
다만 이 보장은 「불렀다」까지이고 값의 내용은 아니다(6번 참고).
근거: 2-summary 「동작 방식 (4)」 · 「동작 방식 (5)」.

### 6. 강제하는 것은 「메서드를 불렀다」까지 — 값의 내용은 아니다

강제하는 것: 필수 메서드를 빠뜨리거나 차례를 어긴 호출은 컴파일되지 않는다.
강제하지 못하는 것: `from(null)` · `to("")` 같은 값은 그대로 컴파일되고, `build()` 에 검사가 없어 `null` 이 `Email` 에 들어간다.
값의 형식까지 지키려면 단계 메서드나 생성자 안에서 따로 검사해야 한다.
근거: 2-summary 「어디서 틀리나 4」 · 「언제 쓰고 언제 안 쓰나」. (원본에 근거 없음 — 추론)

### 7. 캐스팅하면 차례 강제를 건너뛸 수 있다

실제 객체는 네 인터페이스를 모두 구현하므로, `SubjectStep` 으로 캐스팅해도 컴파일되고 실행 중에도 실패하지 않는다.
그러면 `from` · `to` 를 정하지 않고 `subject()` 와 `build()` 로 갈 수 있고, 두 필드는 `null` 로 남는다.
스텝 빌더의 안전은 정적 타입 검사에서 나오므로, 정적 타입을 일부러 바꾸는 캐스팅은 막지 못한다.
근거: 2-summary 「어디서 틀리나 6」 · 「구현 세부사항 대 언어 보장」. (원본에 근거 없음 — 추론)

### 8. 얻는 것은 컴파일 타임 검증, 치르는 것은 인터페이스 수

얻는 것: 필수 값 빠뜨림과 차례 어김을 실행 전에 컴파일러가 잡는다 — 일반 빌더는 이것을 `build()` 의 런타임 검사로 잡거나, 검사가 없으면 그냥 통과시킨다.
치르는 것: 필수 단계마다 인터페이스가 하나씩 늘어 코드가 길어지고, Lombok `@Builder` 로 자동 생성할 수도 없어 직접 써야 한다.
고르는 기준: 필수 값이 3개 이상이고 정하는 차례가 중요하면 스텝 빌더, 필수 값이 한두 개면 생성자 인자나 일반 빌더가 낫다.
근거: 2-summary 「동작 방식 (5)」 · 「어디서 틀리나 1~3」 · 「언제 쓰고 언제 안 쓰나」.

## 실습 정답

### 실습 1. 이메일을 만드는 스텝 빌더 구현하기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. 여섯 필드 `private final` | `Email` 의 `from` · `to` · `subject` · `body` · `html` · `cc` 선언 |
| 2. `private` 생성자가 빌더 값을 복사 | `private Email(Builder builder)` |
| 3. 필수 단계 인터페이스와 반환 타입 | `FromStep.from` → `ToStep`, `ToStep.to` → `SubjectStep`, `SubjectStep.subject` → `OptionalStep` |
| 4. 선택 단계 + `build()` | `OptionalStep` 의 `body` · `html` · `cc` · `build` |
| 5. 진입점 | `public static FromStep builder() { return new Builder(); }` |
| 6. 빌더가 네 인터페이스를 구현 | `private static class Builder implements FromStep, ToStep, SubjectStep, OptionalStep` |
| 7. 선택 필드 기본값 | `body = ""` · `html = false` · `cc = null` |
| 8. `this` 반환과 `build()` | 여섯 `@Override` 메서드의 `return this;` · `build()` 의 `return new Email(this);` |
| 9. 두 이메일을 만들어 찍기 | `main` 의 `email1` · `email2` 와 두 `System.out.println` |
| 10. 잘못된 호출 주석과 마지막 문장 | `// Email.builder().to("x");` 등 세 줄 · `"\n타입 안전: ..."` |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`java/java-advanced-patterns/reference/type-safe-builder.java`

```java
// [고급 패턴 & 기법] Type-Safe Step Builder (타입 안전 스텝 빌더)
// 설명: 컴파일 타임에 필수 파라미터 설정 순서를 강제하는 빌더 패턴. 각 단계마다 다른 타입을 반환
// 팁: Step Builder는 필수 파라미터가 3개 이상이고 설정 순서가 중요할 때 유용하다. 인터페이스 수가 많아져 코드가 길어지는 것이 단점이다. Lombok의 @Builder는 Step Builder를 지원하지 않으므로 직접 구현해야 한다. 컴파일 타임에 오류를 잡을 수 있어 런타임 예외보다 훨씬 안전하다.

// === Type-Safe Step Builder: 컴파일 타임에 필수 파라미터 강제 ===

// 이메일 전송 객체 - 반드시 from -> to -> subject 순서로 설정해야 함
// 불변 객체 + Step Builder 조합 — 안전성과 명확성을 동시에 확보
class Email {
    // 모든 필드 final → 생성 후 변경 불가
    private final String from;
    private final String to;
    private final String subject;
    private final String body;
    private final boolean html;
    private final String cc;

    // private 생성자 — Builder를 통해서만 생성 가능
    private Email(Builder builder) {
        this.from = builder.from;
        this.to = builder.to;
        this.subject = builder.subject;
        this.body = builder.body;
        this.html = builder.html;
        this.cc = builder.cc;
    }

    @Override
    public String toString() {
        return String.format("Email{from='%s', to='%s', subject='%s', body='%s', html=%s, cc='%s'}",
            from, to, subject, body, html, cc);
    }

    // === Step Builder 인터페이스 체인 ===
    // 각 단계마다 다른 인터페이스를 반환하여 순서를 강제
    // 트레이드오프: 인터페이스 수↑(보일러플레이트) ↔ 컴파일 타임 안전성↑

    // 1단계: 발신자 설정 → 다음은 ToStep만 노출
    public interface FromStep {
        ToStep from(String from);
    }

    // 2단계: 수신자 설정
    public interface ToStep {
        SubjectStep to(String to);
    }

    // 3단계: 제목 설정
    public interface SubjectStep {
        OptionalStep subject(String subject);
    }

    // 선택적 파라미터는 같은 인터페이스를 반환 + build() 제공
    // OptionalStep은 자기 자신을 반환 → 어떤 순서로든 호출 가능 + 언제든 build() 가능
    public interface OptionalStep {
        OptionalStep body(String body);
        OptionalStep html(boolean html);
        OptionalStep cc(String cc);
        Email build();
    }

    // 진입점
    // 사용자는 항상 FromStep만 받음 → 첫 호출은 from()으로 강제
    public static FromStep builder() {
        return new Builder();
    }

    // 하나의 Builder가 모든 Step 인터페이스를 구현
    // 외부에선 단계별 인터페이스만 노출되지만 내부는 동일 인스턴스 (this 반환 트릭)
    private static class Builder implements FromStep, ToStep, SubjectStep, OptionalStep {
        private String from;
        private String to;
        private String subject;
        // 선택 필드는 기본값
        private String body = "";
        private boolean html = false;
        private String cc = null;

        @Override
        public ToStep from(String from) {
            this.from = from;
            return this; // 다음 단계 타입을 반환
        }

        @Override
        public SubjectStep to(String to) {
            this.to = to;
            return this;
        }

        @Override
        public OptionalStep subject(String subject) {
            this.subject = subject;
            return this;
        }

        @Override
        public OptionalStep body(String body) {
            this.body = body;
            return this;
        }

        @Override
        public OptionalStep html(boolean html) {
            this.html = html;
            return this;
        }

        @Override
        public OptionalStep cc(String cc) {
            this.cc = cc;
            return this;
        }

        @Override
        public Email build() {
            // 모든 필수 필드는 인터페이스 체인으로 이미 보장됨 — 추가 검증 불필요
            return new Email(this);
        }
    }
}

public class TypeSafeBuilderDemo {
    public static void main(String[] args) {
        // 1. 올바른 사용: from -> to -> subject -> (선택) -> build
        // IDE 자동완성도 단계별로 다음 가능 메서드만 보여줌 (개발 경험 향상)
        Email email1 = Email.builder()
            .from("sender@example.com")    // FromStep -> ToStep
            .to("receiver@example.com")    // ToStep -> SubjectStep
            .subject("안녕하세요")            // SubjectStep -> OptionalStep
            .body("<h1>반갑습니다</h1>")     // OptionalStep -> OptionalStep
            .html(true)
            .cc("manager@example.com")
            .build();
        System.out.println("이메일1: " + email1);

        // 2. 필수 파라미터만으로 생성 (선택 파라미터 생략)
        // OptionalStep에서 바로 build() 가능
        Email email2 = Email.builder()
            .from("noreply@example.com")
            .to("user@example.com")
            .subject("알림")
            .build();
        System.out.println("이메일2: " + email2);

        // 3. 컴파일 에러 예시 (주석 해제하면 컴파일 안 됨)
        // Step Builder의 핵심 가치 — 잘못된 사용은 빌드 단계에서 차단
        // Email.builder().to("x");              // from() 없이 to() 호출 불가
        // Email.builder().from("x").subject("y"); // to() 없이 subject() 호출 불가
        // Email.builder().from("x").to("y").build(); // subject() 없이 build() 호출 불가

        System.out.println("\n타입 안전: 잘못된 순서는 컴파일 타임에 차단됨");

        // 출력:
        // 이메일1: Email{from='sender@example.com', to='receiver@example.com', subject='안녕하세요', body='<h1>반갑습니다</h1>', html=true, cc='manager@example.com'}
        // 이메일2: Email{from='noreply@example.com', to='user@example.com', subject='알림', body='', html=false, cc='null'}
        // 타입 안전: 잘못된 순서는 컴파일 타임에 차단됨
    }
}
```

**실행 결과** — 실행하지 않음 — Java 예제는 이 문서를 만들 때 컴파일 · 실행하지 않았다(JDK 로 돌려 확인한다).

**풀이 요점**
- 차례를 강제하는 것은 각 메서드의 **반환 타입 선언**이다 — 메서드 본문은 모두 값 저장과 `return this` 로 같다.
- `builder()` 의 반환 타입을 `FromStep` 으로 둔 덕에 첫 호출이 `from()` 으로 정해진다.
- `OptionalStep` 의 메서드가 자기 타입을 돌려주므로 선택 값은 아무 순서로 부르거나 생략할 수 있다.
- `Builder` 와 `Email` 생성자를 `private` 으로 막아, 바깥에서는 단계 인터페이스를 거치는 길밖에 없게 한다.
- `build()` 는 검사 없이 `new Email(this)` 만 하며, 값의 내용 검사가 필요하면 별도로 넣어야 한다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — Java 예제는 이 문서를 만들 때 컴파일 · 실행하지 않았다(JDK 로 돌려 확인한다) |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
