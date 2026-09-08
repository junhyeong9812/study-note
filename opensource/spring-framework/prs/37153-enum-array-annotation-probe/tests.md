# PR #37153 — 테스트 해설 (테스트 하나하나)

> `AttributeMethodsTests`에 추가된 6건. 각 테스트를 "무엇을 주장하나 / fix 전
> 결과와 이유 / 역할"로 해설한다. red/green 배치의 개념 정리는
> [guard-tests.md](guard-tests.md).

## 1. probe 대상 지정 여부 — red

첫 테스트는 mock도 예외도 없이 플래그 한 칸만 들여다보는 가장 좁은 재현이다.

```java
@Test
void canThrowTypeNotPresentExceptionWhenHasEnumArrayAttributeReturnsTrue() {
	AttributeMethods methods = AttributeMethods.forAnnotationType(EnumArrayValue.class);
	assertThat(methods.canThrowTypeNotPresentException(0)).isTrue();
}
```

- **주장**: enum 배열 속성은 "지연 실패 가능 -> probe 대상" 플래그가 true여야 한다.
- **fix 전**: 계산식에 enum 배열이 없어 false -> 단언 실패(red). mock도 예외도 없이
  "표시 자체가 안 된다"만 보는 가장 좁은 재현.
- **fix 후**: `(type.isArray() && type.componentType().isEnum())` 추가로 true.

## 2. canLoad 실패 케이스 — red

두 번째 테스트는 오염된 annotation을 mock으로 세워 조용한 출구가 그것을 걸러내는지 본다.

```java
@Test
void isValidWhenHasEnumConstantNotPresentExceptionReturnsFalse() {
	EnumArrayValue annotation = mockAnnotation(EnumArrayValue.class);
	given(annotation.value()).willThrow(new EnumConstantNotPresentException(ExampleEnum.class, "MISSING"));
	AttributeMethods attributes = AttributeMethods.forAnnotationType(annotation.annotationType());
	assertThat(attributes.canLoad(annotation, getClass())).isFalse();
}
```

- **주장**: `value()` 호출이 터지는 annotation은 `canLoad`가 false(필터링 대상).
- **mock의 의미**: `willThrow(EnumConstantNotPresentException)`는 "구버전 enum
  상수로 컴파일된 annotation + 그 상수가 제거된 신버전 enum이 로드된" 컴파일<->런타임
  어긋남(버전 스큐)을 한 줄로 시뮬레이션한 것. 단위 테스트에서 enum 2버전 컴파일과
  클래스로더 조작을 매번 할 수 없으므로, 그 상황에서 JDK가 던지는 바로 그 예외를
  Mockito로 흉내 낸다.
- **fix 전**: 플래그가 false라 canLoad가 `value()`를 **아예 호출하지 않고** true
  반환 -> 단언 실패(red). 예외가 "안 터져서"가 아니라 **터질 기회조차 없어서** 오판.
- **fix 후**: probe 수행 -> 예외 관측 -> `catch (Throwable)` -> false. 보고 방식은
  boolean — 예외를 밖으로 던지지 않는다.
- **형식 디테일**: 기존 Class 테스트는 `willThrow(TypeNotPresentException.class)`
  (클래스 넘김)이지만 `EnumConstantNotPresentException`은 no-arg 생성자가 없어
  인스턴스로 넘긴다.

## 3. canLoad 양성 가드 — 항상 green

세 번째 테스트는 반대 방향, 즉 멀쩡한 annotation이 새 probe에 걸리지 않는지를 고정한다.

```java
@Test
void isValidWhenDoesNotHaveEnumConstantNotPresentExceptionReturnsTrue() {
	EnumArrayValue annotation = mockAnnotation(EnumArrayValue.class);
	given(annotation.value()).willReturn(new ExampleEnum[] {ExampleEnum.ONE});
	AttributeMethods attributes = AttributeMethods.forAnnotationType(annotation.annotationType());
	assertThat(attributes.canLoad(annotation, getClass())).isTrue();
}
```

- **주장**: 멀쩡한(정상 배열을 반환하는) enum 배열 annotation은 canLoad true — 통과.
- **fix 전 green인 이유**: probe를 안 하면 무조건 true니까.
- **존재 이유는 fix 후**: probe가 실제로 돌지만 정상 값이라 예외가 없으니 여전히
  true. 즉 "새 probe가 무고한 annotation까지 걸러버리는 과잉 필터링을 하지 않는다"의
  직접 보증. 무회귀 질문("멀쩡한 annotation을 안 깨뜨린다는 확신은?")의 정답 절반.

## 4. validate 실패 케이스 — red

네 번째 테스트는 같은 오염을 시끄러운 출구에 걸어 예외로 보고되는지 본다.

```java
@Test
void validateWhenHasEnumConstantNotPresentExceptionThrowsException() {
	EnumArrayValue annotation = mockAnnotation(EnumArrayValue.class);
	given(annotation.value()).willThrow(new EnumConstantNotPresentException(ExampleEnum.class, "MISSING"));
	AttributeMethods attributes = AttributeMethods.forAnnotationType(annotation.annotationType());
	assertThatIllegalStateException().isThrownBy(() -> attributes.validate(annotation));
}
```

- **주장**: 같은 오염 상황에서 `validate`는 — canLoad와 달리 — `IllegalStateException`을
  **던져야** 한다(원인 예외를 cause로 감싸서, AttributeMethods.java의 catch(Throwable)
  -> `new IllegalStateException(..., ex)`).
- **fix 전**: probe 스킵 -> 아무것도 안 던짐 -> "던져져야 한다" 단언 실패(red).
- **canLoad와 별도 테스트인 이유**: 같은 probe의 **다른 출구**(조용한 false vs
  시끄러운 예외)가 각각의 계약이기 때문.

## 5. validate 양성 가드 — 항상 green

다섯 번째 테스트는 시끄러운 출구 쪽의 양성 가드로, 3번과 짝을 이룬다.

```java
@Test
void validateWhenDoesNotHaveEnumConstantNotPresentExceptionThrowsNothing() {
	EnumArrayValue annotation = mockAnnotation(EnumArrayValue.class);
	given(annotation.value()).willReturn(new ExampleEnum[] {ExampleEnum.ONE});
	AttributeMethods attributes = AttributeMethods.forAnnotationType(annotation.annotationType());
	attributes.validate(annotation);
}
```

- **주장**: 멀쩡한 annotation에 validate를 불러도 무예외(마지막 줄이 그냥 호출로
  끝나는 것 자체가 단언 — 던지면 실패).
- **역할**: 테스트 3의 validate 버전 양성 가드.

## 6. 비-enum 배열 음성 가드 — 항상 green (리뷰 반영으로 추가)

마지막 테스트는 새 조건이 enum 배열 밖으로 번지지 않는다는 경계를 못박는다.

```java
@Test
void canThrowTypeNotPresentExceptionWhenHasNonEnumArrayAttributeReturnsFalse() {
	AttributeMethods methods = AttributeMethods.forAnnotationType(StringArrayValue.class);
	assertThat(methods.canThrowTypeNotPresentException(0)).isFalse();
}
```

- **주장**: `String[]` 속성은 여전히 probe 대상이 아니다(false).
- **역할**: 새 조건이 "enum 배열"을 넘어 임의 배열로 과확장되는 미래의 잘못된
  수정(예: componentType 검사 누락)을 잡는 가드레일. 리뷰 open question에서 채택.

## fixture

여섯 테스트가 공유하는 재료는 실험용 annotation 둘과 enum 하나다.

```java
@Retention(RetentionPolicy.RUNTIME)
@interface EnumArrayValue { ExampleEnum[] value(); }

@Retention(RetentionPolicy.RUNTIME)
@interface StringArrayValue { String[] value(); }

enum ExampleEnum { ONE }
```

실험용 annotation·enum. 기존 fixture(`ClassValue`, `ClassArrayValue` 등)에 enum
계열이 없어 신규 추가. 명명은 `ClassArrayValue` 병렬.

## 실측 요약

실행 결과는 red/green 예측과 정확히 일치했다.

- fix 전: 20 tests 중 3 failed (1·2·4번) — 예측과 정확히 일치.
- fix 후: 21/21 green (6번 추가 포함) + annotation 패키지 733 tests 0 failures.
