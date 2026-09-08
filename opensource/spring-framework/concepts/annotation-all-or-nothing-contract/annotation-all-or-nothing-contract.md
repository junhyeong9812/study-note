# 개념: annotation 격리는 왜 all-or-nothing인가 — 부분 숨김이 불가능한 타입 계약

> F1(nested annotation probe) 작업 중 나온 설계 질문의 배경 문서. 질문의 형태:
> "깨진 속성(config)만 숨기고 멀쩡한 속성(name)은 보이면 안 되나?"

## 질문의 무대

```java
@Outer(config = @Inner(color = 깨진 enum 상수),   // 이 멤버만 오염
       name   = "정상값")                          // 이건 멀쩡
class MyService { }
```

Spring의 probe(`AttributeMethods.canLoad`)가 오염을 감지하면 `@Outer` **전체**를
스캔에서 격리한다(`isPresent=false`). `name`만 쓰던 사용자도 annotation이 사라지는
경험을 하는데, 왜 속성 단위로 숨기지 않는가?

## 답: annotation 타입 계약이 "부분만 있는" 상태를 허용하지 않는다

`isPresent(Outer) == true`로 보고하는 순간, `Outer`라는 **타입의 계약**상 모든
속성 메서드가 호출 가능해야 한다. 깨진 `config()`에 대해 가능한 선택지는 셋뿐이고
전부 나쁘다:

| 선택지 | 결과 |
|---|---|
| 예외를 던진다 | fix 전의 누출 동작 그대로 — 원점 회귀 |
| null을 반환한다 | annotation 메서드는 null을 반환하지 않는다는 Java 계약 위반 — 모든 소비 코드가 NPE 지뢰밭 |
| 기본값을 지어낸다 | 있지도 않은 값의 silent fabrication — 조용히 틀린 동작, 제일 위험 |

즉 "config만 없는 Outer"라는 객체는 타입 시스템 안에서 정합하게 표현될 수 없다.

## 소비자들은 속성을 골라 읽지 않는다

`asMap()`, `synthesize()`, annotation의 `equals`/`hashCode`/`toString`은 **전 속성을
순회**한다. 부분 annotation을 통과시키면 이 경로들이 전부 깨진 속성에서 걸려
넘어진다 — 반쪽짜리 객체는 결국 어디선가 터진다. "속성 하나만 숨긴다"는 것은
소비자 전원의 순회 관행과 충돌하는 표현이다.

## 이미 그런 의미론이다

`canLoad`의 javadoc은 "return **true if all values are present**"다 — 로드
가능성의 단위는 처음부터 속성이 아니라 annotation 전체였다. `Class` 속성 하나가
깨져도, 단일 enum이 깨져도, 원래부터 annotation 통째로 격리됐다. nested probe
확장(F1)은 이 all-or-nothing 규칙을 새로 만든 게 아니라 기존 규칙의 커버리지를
넓힌 것이다.

## 실패 방향의 안전성

두 선택지는 실패하는 방향이 다르고, 그 방향이 안전성의 차이를 만든다.

- **전체 격리** = 보수적 실패: 안 보임 + warn 로그가 원인(어느 annotation의 어느
  속성)을 지목 — 진단 가능하고, 반쯤 깨진 데이터가 하류로 흐르지 않는다.
- **부분 노출** = 위장된 fail-open: "있다"고 믿게 해놓고 일부가 지뢰 — 터지는
  위치가 원인에서 멀어지고, silent corruption의 온상이 된다.

## 그래서 사용자의 선택지는

격리된 annotation을 다시 보이게 하려는 사용자에게는 길이 둘 있다.

1. **classpath를 고친다** — 근본 해결. warn 로그가 지목한 annotation/상수가 단서.
2. 정말 부분 접근이 필요하면 **JDK 직접 경로**(`clazz.getAnnotation(...)`)는 여전히
   열려 있다 — 단 Spring 스캔의 보증(사전 probe) 없이, 읽는 쪽이 위험을 진다
   (JDK의 원래 계약으로 돌아가는 것).

## 일반화 — 계약 설계의 교훈

"불완전한 값을 어디까지 노출할 것인가"는 계약 설계의 반복 질문이다. 원칙:
**타입이 약속한 것을 다 지킬 수 없는 값은, 부분적으로 노출하지 말고 통째로
없는 것으로 취급하되 이유를 진단 가능하게 남겨라.** 반쪽 값의 노출은 실패
지점을 원인에서 멀리 옮기고, 조작된 기본값은 실패를 아예 숨긴다 — 둘 다
격리보다 나쁘다.

## 관련

- `../../prs/37153-enum-array-annotation-probe/probe-pattern.md` — 격리를 수행하는 장치(canLoad)의 원리
- `../../prs/37153-enum-array-annotation-probe/jdk-vs-spring-annotation-handling.md` — JDK 지연 계약과 Spring 격리
  의미론의 역할 분담
- `jls-annotation-rules.md` — annotation 타입 계약의 언어 차원 근거
