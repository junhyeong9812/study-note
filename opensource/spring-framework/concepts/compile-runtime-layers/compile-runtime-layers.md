# 컴파일 타임과 두 개의 런타임 — 제네릭 정보는 어디에 살아 있는가

> 이 3층 구분을 실제로 구현하는 스프링 실구조(ResolvableType·SerializableTypeWrapper·
> TypeDescriptor)는 [reflection-type-metadata-layer.md](../reflection-type-metadata-layer/reflection-type-metadata-layer.md) 참조.

## 0. 정향

이 문서는 PR #36913(Optional 변환 판별) 작업 중에 드러난 개념 공백을 메우기 위해 쓴다.
그 공백은 "이 검사는 컴파일 타임의 일인가, 런타임의 일인가"라는 질문에 답하지 못한
것이었다. 결론부터 말하면 층은 둘이 아니라 셋이고, Spring의 타입 판별 코드는 그중
가운데 층 — "런타임에 선언 메타데이터를 읽는 층" — 에서 동작한다. 이 문서를 읽고
나면 `TypeDescriptor`, `ResolvableType` 같은 클래스가 왜 존재하는지 설명할 수 있어야
한다.

## 1. 출발점: 우리가 이미 아는 두 층

자바 개발자가 보통 아는 층은 두 개다. 컴파일 타임에는 javac가 타입을 검사하고,
런타임에는 객체가 만들어져 메서드가 실행된다. 이 그림에서 제네릭은 컴파일 타임의
도구다. `Optional<? extends Number>` 변수에 `Optional<String>`을 대입하면 컴파일
에러가 나고, 그 검사가 끝나면 제네릭은 소거(type erasure)되어 바이트코드의 객체에는
남지 않는다.

여기서 자연스러운 오해가 생긴다. "소거되었다면, 런타임에 `Optional<? extends
Number>`라는 정보를 읽는 코드는 존재할 수 없지 않은가?" 실제로 **객체**만 보면
맞는 말이다. `Optional.of(42)`라는 객체는 자기가 `Optional<Integer>`로 선언된
자리에 들어왔는지 전혀 모른다. 객체의 클래스는 그냥 `java.util.Optional`이다.

## 2. 세 번째 층: 선언 메타데이터를 읽는 런타임

소거는 객체에만 적용되고, **선언에는 적용되지 않는다**. 필드 선언, 메서드
시그니처, 클래스의 extends 절에 적힌 제네릭 정보는 컴파일된 클래스 파일 안에
그대로 남는다(Signature 속성). 그리고 리플렉션이 그것을 읽을 수 있다:

```java
private Optional<? extends Number> boundedWildcardOptional;   // 선언

Field field = OptionalConversionTests.class.getDeclaredField("boundedWildcardOptional");
field.getType();          // Optional.class — 소거된 타입
field.getGenericType();   // java.util.Optional<? extends java.lang.Number> — 선언 그대로
```

`getGenericType()`이 돌려주는 것은 객체의 타입이 아니라 **선언의 타입**이다. 이
호출은 분명 런타임에 실행되지만, 읽는 내용은 컴파일러가 남겨 둔 선언 정보다. 그래서
층을 셋으로 나눠야 정확해진다.

층을 정리하면 다음과 같다.

| 층 | 시점 | 다루는 것 | 담당자 |
|---|---|---|---|
| 1. 컴파일 타임 | 빌드 | 소스 코드의 타입 규칙 | javac |
| 2. 선언 메타데이터 런타임 | 실행 중 | 클래스 파일에 남은 선언 정보 | 리플렉션, ResolvableType |
| 3. 값 런타임 | 실행 중 | 실제 객체와 값 | 애플리케이션 코드, 변환기 |

## 3. Spring이 2층에 세운 도구들

`java.lang.reflect`의 원시 API(`Type`, `WildcardType`, `ParameterizedType`)는 쓰기
불편하다. Spring은 그 위에 두 개의 추상을 얹었다.

`ResolvableType`은 선언 타입 하나를 감싸고 "이 타입의 제네릭 인자는 무엇인가",
"와일드카드라면 상한은 무엇인가" 같은 질문에 답한다. PR #36913에서 본
`resolveBounds`가 그 예다. 상한이 `Object`이면 정보가 없다고 보고 null을 돌려주고,
`Number`처럼 구체적이면 그 타입을 돌려준다. 이 판정 전체가 2층에서 일어난다 —
객체는 아직 등장하지 않았다.

`TypeDescriptor`는 `ResolvableType`에 애노테이션과 소스 위치(필드, 메서드 파라미터,
프로퍼티)를 더한 카드다. 변환 시스템의 `canConvert(TypeDescriptor, TypeDescriptor)`가
받는 것이 바로 이 카드 두 장이다. 그래서 `canConvert`는 값 없이도 동작한다 —
"이 선언에서 저 선언으로 갈 수 있는 변환기가 등록돼 있는가"만 묻기 때문이다.

## 4. 3층이 2층의 카드를 들고 다니는 이유

값을 실제로 변환하는 순간(3층)에도 2층의 카드가 함께 다닌다.
`convert(Optional.of(42), sourceType, targetType)`처럼 값 옆에 `TypeDescriptor`를
붙여 넘기는 이유는 1층에서 소거가 일어났기 때문이다. 객체 스스로는 자신의 선언
맥락을 모르니, 선언 정보를 아는 쪽(2층 카드)이 동행해서 "이 42는 `? extends
Number` 자리에서 온 값이다"를 알려 준다.

이 구조를 이해하면 PR #36911의 `Property`도 같은 그림에 들어온다. `Property`는
"클래스의 논리적 속성 하나"에 대한 2층 카드이고, `resolveName()`의
`getDeclaredField` 호출은 2층에서 선언(필드 존재)을 확인하는 것이지 값을 읽는 것이
아니다. 두 PR 모두 3층(값 처리)은 건드리지 않고 2층(선언 해석)만 고친 수정이다.

## 5. 판별 질문 세 개

어떤 코드를 볼 때 층을 가려내려면 이 세 질문을 쓰면 된다. 첫째, 이 검사가 실패하면
빌드가 깨지는가? 그렇다면 1층이다. 둘째, 실행 중이지만 실제 객체 없이 `Class`,
`Field`, `Method`, `TypeDescriptor`만으로 동작하는가? 그렇다면 2층이다. 셋째, 실제
값이 인자로 들어와 그 내용이 결과를 좌우하는가? 그렇다면 3층이다.

PR #36913의 사례로 검산하면: `canConvert(...)`는 값이 없으니 2층, `convert(
Optional.of(42), ...)`는 42를 꺼내 변환하니 3층, `Optional<String>`을
`Optional<? extends Number>` 변수에 못 넣게 막는 것은 1층이다.

## 6. 한 문장 요약

제네릭은 컴파일 타임(1층)에 검사된 뒤 객체에서는 소거되지만 선언에는 남고, Spring의
타입 판별 코드(`ResolvableType`, `TypeDescriptor`, `Property`)는 런타임에 그 남은
선언 정보를 읽는 2층에서 동작하며, 실제 값을 다루는 3층은 소거 때문에 2층의 카드를
들고 다닌다.
