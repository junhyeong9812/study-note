# 개념: annotation의 enum 값은 이름으로 저장되고, 읽는 순간 해석된다

> PR #37153 학습 중 놓쳤던 개념. 질문의 형태: "컴파일할 때 BLUE가 있는지 검사하는데
> 어떻게 런타임에 없을 수가 있어?"

## 한 줄 요약

`@Marker(Color.BLUE)`를 컴파일하면 .class 파일에는 Color 객체가 아니라 **"enum
Color의 상수명 BLUE"라는 문자열**이 기록되고, JDK는 그 이름을 **속성을 읽는
순간에야** 지금 로드된 Color 클래스에서 찾는다(사실상 `Color.valueOf("BLUE")`).
그 사이에 Color가 바뀌어 있으면 `EnumConstantNotPresentException`이 난다.

## 왜 이름으로 저장하나

annotation은 클래스에 붙은 메타데이터다. 클래스 로드 시점에 모든 annotation의
모든 값을 미리 해석하면, 아무도 읽지 않을 annotation 하나 때문에 관련 클래스를
전부 로드해야 하고, 참조 하나만 깨져도 클래스 로드 자체가 실패한다. 그래서 JDK는
일부러 이름만 저장해 두고 해석을 미룬다 — 지연(lazy) 해석.

## 세 시점의 분리

컴파일, 클래스 로드, 속성 읽기라는 세 시점이 각각 무엇을 검사하는지 갈라 보면 폭탄이
어디에 심기고 어디서 터지는지가 드러난다.

| 시점 | 무슨 일이 일어나나 | BLUE 검사 여부 |
|---|---|---|
| 컴파일 (라이브러리 저자의 과거) | `Color.BLUE` 존재 확인 후 상수명을 바이트코드에 기록 | 그 시점의 Color 기준으로만 |
| 클래스 로드 / `getAnnotation()` | annotation 프록시 객체 정상 생성 — 못 찾은 값 자리에는 예외 폭탄(ExceptionProxy)만 심어둠 | 검사 안 함 |
| **속성 메서드 호출** | 이름을 현재 로드된 enum에서 조회 | **여기서 처음 대조** — 실패 시 `EnumConstantNotPresentException` |

중간 시점이 중요하다: **annotation 객체는 정상적으로 만들어진다.** JVM은 멀쩡히
기동하고, `getAnnotation()`도 성공한다. 터지는 건 값을 읽는 코드다. 그래서
"시한폭탄"이고, Spring `AttributeMethods`의 probe가 이 폭탄을 스캔 단계에서 미리
눌러보는 장치다.

## 같은 계열의 예외들

지연 해석이 실패하는 방식은 둘이고, 그 실패가 값처럼 실려 나가는 부수 경로가 하나 더 있다.

- `TypeNotPresentException` — `Class` 속성이 가리키는 타입 자체가 classpath에 없음
  (optional 의존성 미포함이 흔한 원인, `AttributeMethods` javadoc의 원조 사례는
  Google App Engine).
- `EnumConstantNotPresentException` — enum 타입은 있는데 그 상수가 없음(개명·제거).
- 부수 지식: JDK annotation 프록시의 내부 map(memberValues)에는 실패한 값 자리에
  예외(프록시)가 들어 있어서, 그 map을 우회 접근하는 코드는 **예외 객체 자체를
  값으로** 받을 수 있다 — PR #37153에서 `asMap()` 오염이 바로 이 경로였다.

## 관련

지연 해석의 앞뒤를 각각 맡는 두 문서가 있다.

- [classpath-version-skew.md](classpath-version-skew.md) — "그 사이에 Color가
  바뀌는" 상황이 실제로 어떻게 만들어지나
- [probe-pattern.md](probe-pattern.md) — Spring이 이 지연 실패를 다루는 방식
