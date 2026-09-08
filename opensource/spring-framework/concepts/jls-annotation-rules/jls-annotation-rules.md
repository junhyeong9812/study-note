# 개념: JLS와 annotation 멤버 타입 규칙 — 재귀 probe가 무한히 돌 수 없는 이유

> F1(nested annotation 재귀 probe) 작업 중 나온 질문의 배경 문서. 핵심 주장:
> "annotation 값 구조를 따라가는 재귀는 항상 유한하다 — JLS가 그렇게 만들었다."

## JLS란

JLS(Java Language Specification)는 Java 언어의 공식 명세 — 언어의 헌법이다.
"컴파일러가 무엇을 허용하고 무엇을 컴파일 에러로 거부해야 하는가"를 정의하는
문서이므로, JLS가 금지한 구조는 **어떤 Java 코드로도 만들어질 수 없다**. 런타임
방어 코드를 설계할 때 "이 입력은 올 수 있는가?"의 최종 근거가 된다. 우리가 쓰는
근거는 annotation 타입 선언을 다루는 **JLS §9.6(Annotation Interfaces)**이다.

## 규칙 1: annotation 멤버가 가질 수 있는 타입은 닫힌 목록이다

JLS §9.6.1 — annotation 멤버(속성 메서드)의 반환 타입은 다음만 허용된다:

- primitive 타입 (int, boolean, ...)
- `String`
- `Class` (또는 `Class<...>` 형태)
- enum 타입
- **annotation 타입**
- 위 타입들의 **1차원 배열**

이 목록이 닫혀 있다는 것이 `AttributeMethods`류 코드의 전제다. probe 대상 판별이
`Class`/`Class[]`/enum/enum[]/annotation/annotation[] 몇 갈래의 검사로 완결될 수
있는 이유이고, "다차원 배열은 어떡하지?"라는 걱정이 불필요한 이유이기도 하다 —
`Color[][]`는 목록에 없으므로 컴파일 자체가 안 된다. `componentType()` 1단계
검사로 충분하다.

## 규칙 2: 멤버 타입의 순환은 컴파일 에러다

JLS §9.6.1 — annotation 타입 T가 **직접적으로든 간접적으로든** T 타입의 멤버를
가지면 컴파일 에러다:

```java
@interface Self { Self value(); }          // 직접 순환 — 컴파일 에러

@interface A { B value(); }
@interface B { A value(); }                // 간접(상호) 순환 — 컴파일 에러
```

따라서 annotation **값**의 중첩 구조(`@Outer(@Mid(@Inner(...)))`)는 언제나 유한
깊이의 트리다. 순환하는 값 그래프는 문법상 존재할 수 없으므로, 값 구조를 따라
내려가는 재귀(F1의 nested probe)는 **visited 집합 같은 순환 방어 없이도** 종료가
보장된다. "안에 annotation이 더 없으면 끝난다"는 실용적 종료 조건에 더해, "끝이
없는 구조 자체가 만들어질 수 없다"는 구조적 보장이 이 규칙이다.

## 혼동 주의: 메타-annotation 그래프는 순환할 수 있다

위 규칙은 **멤버 타입**(값의 타입)에 대한 것이고, annotation을 annotation **위에
붙이는 것**(메타-annotation)과는 별개다. 메타-annotation 그래프는 순환이 실제로
존재한다:

```java
// JDK 표준 라이브러리의 실례
@Documented                 // @Documented의 선언 자체에
@Retention(RUNTIME)         // @Retention이 붙어 있고,
public @interface Retention { ... }
// @Retention의 선언에도 @Documented가 붙어 있다 — 상호 순환
```

그래서 Spring의 메타-annotation 탐색(`AnnotationTypeMappings`)은 visited 집합으로
순환을 방어한다. 반면 F1의 재귀는 메타-annotation 그래프가 아니라 **멤버 값
트리**를 내려가므로 그 방어가 필요 없다. 같은 "annotation 재귀"라도 어느 축을
따라가는지에 따라 종료 보장의 근거가 완전히 다르다:

| 재귀 축 | 순환 가능? | 종료 보장 |
|---|---|---|
| 멤버 값 트리 (F1 nested probe) | 불가 (JLS §9.6.1 컴파일 에러) | 구조적 — 방어 코드 불필요 |
| 메타-annotation 그래프 (AnnotationTypeMappings) | 가능 (@Retention 실례) | visited 집합으로 런타임 방어 |

## 이 문서가 답하는 실전 질문

위 두 규칙을 설계 판단에 그대로 대입하면 세 질문이 정리된다.

- "nested probe 재귀에 depth 제한이나 visited 집합을 넣어야 하나?" 넣을 필요가 없다.
  멤버 값 트리는 JLS가 유한을 보장한다.
- "annotation 배열의 배열이 오면?" 올 수 없다. 멤버 타입 목록은 1차원 배열까지다.
- "그럼 왜 AnnotationTypeMappings는 순환 방어를 하나?" 그쪽은 메타-annotation
  그래프를 걷기 때문이다 — 다른 축이다.

## 관련

- `../../prs/37153-enum-array-annotation-probe/probe-pattern.md` — probe의 개념과 두 출구
- `../../prs/37153-enum-array-annotation-probe/jdk-vs-spring-annotation-handling.md` — JDK 층/Spring 층 역할 분담
